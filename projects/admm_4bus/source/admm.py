from numpy import *

from scipy.sparse import *
import nlopt
from case4 import case4gs
from acopf_nlopt import ACopf_nlopt

ppc = case4gs()
bus = ppc["bus"]
branch = ppc["branch"]
gen = ppc["gen"]
baseMVA = ppc["baseMVA"]

nb = size(bus,0) #number of bus
nl = size(branch,0) #number of branch
ng = size(gen,0) #number of generator

#calculate Ybus, this part from pypower
stat = ones(nb)
Ys = stat / (branch[:, 2] + 1j * branch[:, 3])  ## series admittance
Bc = stat * branch[:, 4]              ## line charging susceptance

Ytt = Ys + 1j * Bc / 2
Yff = Ytt
Yft = - Ys
Ytf = - Ys

## build connection matrices
f = branch[:, 0]                           ## list of "from" buses
t = branch[:, 1]                           ## list of "to" buses

## connection matrix for line & from buses
Cf = csr_matrix((ones(nl), (range(nl), f)), (nl, nb))
## connection matrix for line & to buses
Ct = csr_matrix((ones(nl), (range(nl), t)), (nl, nb))

## build Yf and Yt such that Yf * V is the vector of complex branch currents injected
## at each branch's "from" bus, and Yt is the same for the "to" bus end
i = r_[range(nl), range(nl)]  ## double set of row indices

Yf = csr_matrix((r_[Yff, Yft], (i, r_[f, t])), (nl, nb))
Yt = csr_matrix((r_[Ytf, Ytt], (i, r_[f, t])), (nl, nb))

## build Ybus
Ybus = Cf.T * Yf + Ct.T * Yt

G = Ybus.real
B = Ybus.imag

z_p = vstack([
    hstack([G, -B]),
    hstack([B, G])],
    "csr")

z_q = vstack([
    hstack([-B, -G]),
    hstack([G, -B])],
    "csr")

ib = arange(nb)
ig = arange(ng)

#index of variables
idx = arange(nb*2)
idx_v_real = idx[0:nb]
idx_v_image = idx[nb:2*nb]

load_bus = bus[[i for i in ib if bus[i, 1] == 1], 0].astype(int)
gen_bus = bus[[i for i in ib if bus[i, 1] > 1], 0].astype(int)

def make_zk(me_and_neighbors):
    idx = me_and_neighbors
    idx.extend([x+nb for x in idx])

    aux1 = z_p[[idx[0], idx[0] + nb], :]
    aux2 = z_q[[idx[0], idx[0] + nb], :]
    z_pk = aux1[:, idx]
    z_qk = aux2[:, idx]

    return z_pk, z_qk

z_pk0, z_qk0 = make_zk([0, 1, 2])
z_pk1, z_qk1 = make_zk([1, 0, 3])
z_pk2, z_qk2 = make_zk([2, 0, 3])
z_pk3, z_qk3 = make_zk([3, 1, 2])
print(z_qk3.toarray())
max_iter = 300

x0 = {}
x1 = {}
x2 = {}
x3 = {}

beta0 = {}
beta1 = {}
beta2 = {}
beta3 = {}
beta0[0] = zeros(3*2, dtype=float_)
beta1[0] = zeros(3*2, dtype=float_)
beta2[0] = zeros(3*2, dtype=float_)
beta3[0] = zeros(3*2, dtype=float_)

z0 = {}
z1 = {}
z2 = {}
z3 = {}
z0[0] = np.ones(3*2, dtype=float_) * 1.1
z1[0] = np.ones(3*2, dtype=float_) * 1.1
z2[0] = np.ones(3*2, dtype=float_) * 1.1
z3[0] = np.ones(3*2, dtype=float_) * 1.1

nu0 = {}
nu1 = {}
nu2 = {}
nu3 = {}
nu0[0] = np.zeros(3*2, dtype=float_)
nu1[0] = np.zeros(3*2, dtype=float_)
nu2[0] = np.zeros(3*2, dtype=float_)
nu3[0] = np.zeros(3*2, dtype=float_)

z_received = {}
beta_received = {}
admm_it = 0
rho = 250
# for i in range(1, max_iter+1):
check = True
while check:
    problem_0 = ACopf_nlopt(z_pk0, z_qk0, bus[0, :], 3, z0[admm_it], nu0[admm_it], rho, 3, 0, gen=gen[0,:]) #     node 0
    problem_1 = ACopf_nlopt(z_pk1, z_qk1, bus[1, :], 3, z1[admm_it], nu1[admm_it], rho, 1, 1)  # node 1
    problem_2 = ACopf_nlopt(z_pk2, z_qk2, bus[2, :], 3, z2[admm_it], nu2[admm_it], rho, 1, 1)  # node 2
    problem_3 = ACopf_nlopt(z_pk3, z_qk3, bus[3, :], 3, z3[admm_it], nu3[admm_it], rho, 2, 5, gen=gen[1, :])  # node 3

    result0 = problem_0.solve_opf()
    result1 = problem_1.solve_opf()
    result2 = problem_2.solve_opf()
    result3 = problem_3.solve_opf()

    xopt0 = result0[0]
    xopt1 = result1[0]
    xopt2 = result2[0]
    xopt3 = result3[0]

    admm_it += 1

    x0[admm_it] = xopt0
    x1[admm_it] = xopt1
    x2[admm_it] = xopt2
    x3[admm_it] = xopt3

    beta0[admm_it] = (1 / rho) * nu0[admm_it - 1] + xopt0
    beta1[admm_it] = (1 / rho) * nu1[admm_it - 1] + xopt1
    beta2[admm_it] = (1 / rho) * nu2[admm_it - 1] + xopt2
    beta3[admm_it] = (1 / rho) * nu3[admm_it - 1] + xopt3

    z = zeros(8)
    z[0] = float((beta0[admm_it][0]+beta1[admm_it][1]+beta2[admm_it][1]) / float(3))
    z[4] = float((beta0[admm_it][3]+beta1[admm_it][4]+beta2[admm_it][4]) / float(3))
    z[1] = float((beta1[admm_it][0]+beta0[admm_it][1]+beta3[admm_it][1]) / float(3))
    z[5] = float((beta1[admm_it][3]+beta0[admm_it][4]+beta3[admm_it][4]) / float(3))
    z[2] = float((beta2[admm_it][0]+beta0[admm_it][2]+beta3[admm_it][2]) / float(3))
    z[6] = float((beta2[admm_it][3]+beta0[admm_it][5]+beta3[admm_it][5]) / float(3))
    z[3] = float((beta3[admm_it][0]+beta1[admm_it][2]+beta2[admm_it][2]) / float(3))
    z[7] = float((beta3[admm_it][3]+beta1[admm_it][5]+beta2[admm_it][5]) / float(3))

    z0[admm_it] = [z[0], z[1], z[2], z[4], z[5], z[6]]
    z1[admm_it] = [z[1], z[0], z[3], z[5], z[4], z[7]]
    z2[admm_it] = [z[2], z[0], z[3], z[6], z[4], z[7]]
    z3[admm_it] = [z[3], z[1], z[2], z[7], z[5], z[6]]

    nu0[admm_it] = nu0[admm_it - 1] + rho * (x0[admm_it] - z0[admm_it])
    nu1[admm_it] = nu1[admm_it - 1] + rho * (x1[admm_it] - z1[admm_it])
    nu2[admm_it] = nu2[admm_it - 1] + rho * (x2[admm_it] - z2[admm_it])
    nu3[admm_it] = nu3[admm_it - 1] + rho * (x3[admm_it] - z3[admm_it])
    print("iter ",admm_it,":  ", z)
    # print(admm_it, x1[admm_it])
    # print(admm_it, x2[admm_it])
    # print(admm_it, x3[admm_it])
    tol = 1e-4
    T0 = array(z0[admm_it]) - array(z0[admm_it - 1])
    T1 = array(z0[admm_it]) - array(z0[admm_it - 1])
    max_value0 = max(abs(T0))
    max_value1 = max(abs(T1))
    check = max([max_value0, max_value1]) > tol
    print(max([max_value0, max_value1]))

print(x0[admm_it])
print(x1[admm_it])
print(x2[admm_it])
print(x3[admm_it])
v0 = asmatrix(x0[admm_it])
print(v0[:,[0,3]] * z_pk0* v0.T + bus[0, 2]/baseMVA)
v3 = asmatrix(x3[admm_it])
print(v3[:,[0,3]]* z_pk3*v3.T + bus[3, 2]/baseMVA)
v1 = asmatrix(x1[admm_it])
print(v1[:,[0,3]] * z_pk1* v1.T + bus[1, 2]/baseMVA)
v2 = asmatrix(x2[admm_it])
print(v2[:,[0,3]] * z_pk2* v2.T + bus[2, 2]/baseMVA)
v=z[idx_v_real] + 1j*z[idx_v_image]
print(v*conjugate(Ybus*v) + bus[:, 2]/baseMVA + 1j*bus[:, 3]/baseMVA)