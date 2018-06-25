import math
from numpy import *
import pprint
from scipy.sparse import *
from cigre_matrix import cigre_matrix

PATH = "../config_files/default"
# PATH = "E:/lam/Distributed_optimization/projects/admm_cigre/config_files/default"
def make_zk(me_and_neighbors):
    n = len(me_and_neighbors)
    idx = me_and_neighbors
    # idxn = [idx[i] + n for i in arange(n)]
    # idx += idx
    print(idx)
    count = 0
    idx_internal = idx
    for i in idx:
        idx_internal[count] = busIdx.index(i)
        count += 1
    idx_internaln = [idx_internal[i] + nb for i in arange(n)]
    idx_internal += idx_internaln

    aux1 = z_p[[idx_internal[0], idx_internal[0] + nb], :]
    aux2 = z_q[[idx_internal[0], idx_internal[0] + nb], :]
    z_pk = lil_matrix((len(idx), len(idx)))
    z_qk = lil_matrix((len(idx), len(idx)))
    # print(aux1[:, idx_internal].toarray())
    # print(len(me_and_neighbors))
    # print(z_pk[[0, len(me_and_neighbors)], :].toarray())

    z_pk[[0, n], :] = aux1[:, idx_internal]
    z_qk[[0, n], :] = aux2[:, idx_internal]

    return z_pk, z_qk

ppc = cigre_matrix()
Sbase = ppc["baseMVA"]# nominal power of the network
Vbase = ppc["basekV"]# nominal voltage of the network
## bus data
bus = ppc["bus"]
## generator data
gen = ppc["gen"]
## branch data(ohm)
branch = ppc["branch"]
nb = size(bus,0) #number of bus
nl = size(branch,0) #number of branch
ng = size(gen,0) #number of generator

busIdx = bus[:, 0].astype(int)
busIdx= busIdx.tolist()
genIdx = gen[:, 0].astype(int)
genIdx = genIdx.tolist()
loadIdx = [b for b in busIdx if b not in genIdx]  # indices of the loads

# ip address of the raspberry PI for the wired and wireless communication
PI_wired_addr = ['169.254.35.101', '169.254.35.102', '169.254.35.103', '169.254.35.104', '169.254.35.105',
                 '169.254.35.106', '169.254.35.107', '169.254.35.108', '169.254.35.109', '169.254.35.100']
PI_wireless_addr = ['192.168.1.101', '192.168.1.102', '192.168.1.103', '192.168.1.104', '192.168.1.105',
                    '192.168.1.106', '192.168.1.107', '192.168.1.108', '192.168.1.109', '192.168.1.110']

#PI_addr = PI_wireless_addr  # use the wireless IP addresses to create the configuration files
# PI_addr = PI_wired_addr  # use the wired IP addresses to create the configuration files
PI_addr = ["localhost"]*13
bus2PI = range(1, 11) + [1, 2, 3]
# bus2Port = [8000]*lamda10 + [8001]*3
# bus2PI = ["localhost"]*13
bus2Port = range(8000, 8014)
#url_opal = "http://169.254.35.121:8000/asyncsrv/"  # URL address of the opal5600 web server
url_opal = "http://169.254.35.122:8000/asyncsrv/"  # URL address of the opal5000 web server
var1 = range(0, 13)  # indices of the first interface variable (P load from Opal) (P gen to Opak)
var2 = range(13, 26)  # indices of the first interface variable (P load from Opal) (Q gen to Opal)
var3 = range(26, 39)  # indices of the first interface variable (U bus) from Opal

## communication links
# fbus, tbus, delay[s], loss[%]
comm_links_default = [
        [ 1,    2, 0.0, 0.0],
        [ 2,    3, 0.0, 0.0],
        [ 3,    4, 0.0, 0.0],
        [ 4,    5, 0.0, 0.0],
        [ 5,    6, 0.0, 0.0],
        [ 6,    7, 0.0, 0.0],
        [ 7,    8, 0.0, 0.0],
        [ 8,    9, 0.0, 0.0],
        [ 9,   10, 0.0, 0.0],
        [10,   11, 0.0, 0.0],
        [11,    4, 0.0, 0.0],
        [ 3,    8, 0.0, 0.0],
        [ 1,   13, 0.0, 0.0],
        [13,   14, 0.0, 0.0]
    ]
comm_links = comm_links_default  # configuration of the communication links

ts_opal = 0.05  # sampling time of the OPAL

v_min = 0.9  # minimum p.u. voltage
v_max = 1.1  # maximum p.u. voltage
v_nom = 1.0  # nominal p.u. voltage

rho = 250  # gain of the ADMM algorithm
max_iter = 300  # number of iterations of the ADMM algorithm

#Ybus


stat = ones(nl)
Ys = stat / (branch[:, 2] + 1j * branch[:, 3])  ## series admittance
Bc = stat * branch[:, 4]              ## line charging susceptance

Ytt = Ys + 1j * Bc / 2
Yff = Ytt
Yft = - Ys
Ytf = - Ys

## build connection matrices
f = branch[:, 0].tolist()                           ## list of "from" buses
t = branch[:, 1].tolist()           ## list of "to" buses
f_internal = zeros(nl)
t_internal = zeros(nl)
count = 0
for i in f:
    f_internal[count] = busIdx.index(i)
    count += 1
count = 0
for i in t:
    t_internal[count] = busIdx.index(i)
    count += 1

## connection matrix for line & from buses
Cf = csr_matrix((ones(nl), (range(nl), f_internal)), (nl, nb))
## connection matrix for line & to buses
Ct = csr_matrix((ones(nl), (range(nl), t_internal)), (nl, nb))

## build Yf and Yt such that Yf * V is the vector of complex branch currents injected
## at each branch's "from" bus, and Yt is the same for the "to" bus end
i = r_[range(nl), range(nl)]  ## double set of row indices

Yf = csr_matrix((r_[Yff, Yft], (i, r_[f_internal, t_internal])), (nl, nb))
Yt = csr_matrix((r_[Ytf, Ytt], (i, r_[f_internal, t_internal])), (nl, nb))

## build Ybus
Ybus = Cf.T * Yf + Ct.T * Yt
# print(Ybus.toarray())

G = Ybus.real
B = Ybus.imag

z_p = vstack([
    hstack([G, -B]),
    hstack([B, G])],
    "csr")
# z_p =z_p.toarray()
z_q = vstack([
    hstack([-B, -G]),
    hstack([G, -B])],
    "csr")
# z_q = z_q.toarray()
ib = arange(nb)
ig = arange(ng)

json_tmpl = '{{\n\t"me" : {}, ' \
            '\n\t"start" : 1,' \
            '\n\t"partners" : {},' \
            '\n\t"ts_opal" : {},' \
            '\n\t"url_opal" : "{}",' \
            '\n\t"opal_get_ids" : {{"P" : {}, "Q" : {}, "V" : {}}},' \
            '\n\t"opal_set_ids" : {{"P" : {}, "Q" : {}}},' \
            '\n\t"opal_default_set" : {{"P" : {:.10f}, "Q" : {:.10f}}},' \
            '\n\t"s_base" : {:.10f},' \
            '\n\t"v_base" : {:.10f},' \
            '\n\t"z_pk" : {},' \
            '\n\t"z_qk" : {},' \
            '\n\t"node_type" : {}, ' \
            '\n\t"v_min" : {:.10f}, ' \
            '\n\t"v_max" : {:.10f},' \
            '\n\t"v_nom" : {:.10f},' \
            '\n\t"p_d" : {:.10f},' \
            '\n\t"q_d" : {:.10f},' \
            '\n\t"p_max" : {:.10f},' \
            '\n\t"p_min" : {:.10f},' \
            '\n\t"q_max" : {:.10f},' \
            '\n\t"q_min" : {:.10f},' \
            '\n\t"rho" : {:.10f},' \
            '\n\t"max_iter" : {}' \
            '\n}}'
cnt = 0
set_printoptions(precision=10)
branch = branch.tolist()

for i in busIdx:
    ids = []
    c=0
    partners = '['
    for row in branch:
        neigh = -1
        row_idx = branch.index(row)
        # print(row[0])
        # print(row[1])
        if int(row[0]) == i:
            neigh = row[1]
        if int(row[1]) == i:
            neigh = row[0]
        print(neigh)
        if neigh > 0:
            ids += [int(neigh)]
            s = '[{}, "{}", {}, {}, {}],\n'.format(int(neigh), PI_addr[bus2PI[busIdx.index(neigh)]-1],
                                                   bus2Port[busIdx.index(neigh)],comm_links[row_idx][2],
                                                   comm_links[row_idx][3])
            partners += s
    partners = partners[:-2]
    partners += ']'
    ids.sort()
    ids = [i] + ids
    zpk, zqk = make_zk(ids)
    me = '[[{}, "{}", {}]]'.format(i, PI_addr[bus2PI[busIdx.index(i)] - 1], bus2Port[busIdx.index(i)])
    bus_idx = busIdx.index(i)

    node_type = bus[bus_idx, 1]
    # test if the curent bus is a generator

    if node_type > 1:
        gen_idx = genIdx.index(i)
        p_def = 0  # zero default power demand
        q_def = 0  # zero default power demand
        p_max = gen[gen_idx, 8]/Sbase
        p_min = gen[gen_idx, 9]/Sbase
        q_max = gen[gen_idx, 3]/Sbase
        q_min = gen[gen_idx, 4]/Sbase
    else:
        p_def = 0  # zero default power demand
        q_def = 0  # zero default power demand
        p_max = 0
        p_min = 0
        q_max = 0
        q_min = 0

    p_d = bus[bus_idx, 2]/Sbase
    q_d = bus[bus_idx, 3]/Sbase

    json_dump = json_tmpl.format(me, partners, ts_opal, url_opal, var1[cnt], var2[cnt], var3[cnt], var1[cnt], var2[cnt],
                                 p_def, q_def, Sbase, Vbase, pprint.pformat(zpk.toarray().tolist()), pprint.pformat(zqk.toarray().tolist()),
                                 node_type, v_min, v_max, v_nom, p_d, q_d, p_max, p_min, q_max, q_min, rho, max_iter)
    file_name = PATH + '/config_A_{}.json'.format(i)
    config_file = open(file_name, 'w')
    config_file.write(json_dump)
    config_file.close()
    cnt += 1