from numpy import *
from case4 import case4
from case6ww_1 import case6ww
from scipy.sparse import *
import nlopt

ppc = case4()
# ppc = case6ww()
bus = ppc["bus"]
branch = ppc["branch"]
gen = ppc["gen"]
baseMVA = ppc["baseMVA"]

nb = len(bus) #number of bus
nl = len(branch) #number of branch
ng = len(gen) #number of generator
print(nb, nl,ng)
#calculate Ybus, this part from pypower
stat = ones(nl)
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
# print(Ybus.toarray())
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
print(load_bus, gen_bus)

# calculate z_pk, z_qk
z_pk = {}
z_qk = {}
for i in ib:
    z_pk[i] = lil_matrix((2 * nb, 2 * nb))
    z_pk[i][[i, i + nb], :] = z_p[[i, i + nb], :]
    z_qk[i] = lil_matrix((2 * nb, 2 * nb))
    z_qk[i][[i, i + nb], :] = z_q[[i, i + nb], :]

def equality_power_constraint(result, x, grad):
    v = asmatrix(x)
    if grad.size>0:
        idx_grad = int(0)
        for i in load_bus:
            grad[idx_grad * 2] = 2 * float(z_pk[i]* v.T)
            grad[idx_grad * 2 + 1] = 2 * float(z_qk[i] * v.T)
            idx_grad += 1

    idx_result = int(0)
    for i in load_bus:
        v = asmatrix(x)
        result[idx_result*2] = float(v * z_pk[i] * v.T) + bus[i, 2]/baseMVA
        result[idx_result * 2 + 1] = float(v * z_qk[i] * v.T) + bus[i, 3]/baseMVA
        idx_result += 1

def inequality_power_constraint(result, x, grad):
    v = asmatrix(x)
    if grad.size>0:
        idx_grad = int(0)
        for i in gen_bus:
            grad[idx_grad * 2] = float(2 * z_pk[i]* v.T)
            grad[idx_grad * 2 + 1] = float(2 * z_qk[i] * v.T)

            idx_grad += 1

    idx_result = int(0)
    for i in gen_bus:
        result[idx_result*2] = float(v * z_pk[i] * v.T) + bus[i, 2]/baseMVA - gen[[j for j in ig if gen[j, 0] == i], 8]/baseMVA
        result[idx_result * 2 + 1] = float(v * z_qk[i] * v.T) + bus[i, 3]/baseMVA - gen[[j for j in ig if gen[j, 0] == i],3]/baseMVA

        idx_result += 1

def inequality_power_constraint_min(result, x, grad):
    v = asmatrix(x)
    if grad.size>0:
        idx_grad = int(0)
        for i in gen_bus:
            grad[idx_grad * 2] = float(-2 * z_pk[i] * v.T)
            grad[idx_grad * 2 + 1] = float(-2 * z_qk[i] * v.T)

            idx_grad += 1

    idx_result = int(0)
    for i in gen_bus:
        v = asmatrix(x)
        result[idx_result*2] = -(float(v * z_pk[i] * v.T) + bus[i, 2]/baseMVA - gen[[j for j in ig if gen[j, 0] == i], 9]/baseMVA)
        result[idx_result * 2 + 1] = -(float(v * z_qk[i] * v.T) + bus[i, 3]/baseMVA - gen[[j for j in ig if gen[j, 0] == i],4]/baseMVA)

        idx_result += 1

def obj(x, grad):
    v = asmatrix(x)
    if grad.size > 0:
        grad = 2 * z_p * v.T
    return float(v * z_p * v.T)

def v_upper(result, x, grad):
    if grad.size > 0:
        dh1_dVre = 2 * csr_matrix((x[idx_v_real], (ib, ib))) * x[idx_v_real]
        dh1_dVim = 2 * csr_matrix((x[idx_v_image], (ib, ib))) * x[idx_v_image]

        grad[:] = hstack([dh1_dVre, dh1_dVim])
    v_max = 1.1
    result[:] = x[idx_v_real]**2 + x[idx_v_image]**2 - v_max ** 2

def v_lower(result, x, grad):
    if grad.size > 0:
        dh2_dVre = -2 * csr_matrix((x[idx_v_real], (ib, ib))) * x[idx_v_real]
        dh2_dVim = -2 * csr_matrix((x[idx_v_image], (ib, ib))) * x[idx_v_image]

        grad[:] = hstack([dh2_dVre, dh2_dVim])

    v_min = -1.1
    result[:] = -x[idx_v_real]**2 - x[idx_v_image]**2 + v_min ** 2

opt = nlopt.opt(nlopt.LN_COBYLA, 2*nb)
x0 = zeros(2*nb)
x0[idx_v_real] = ones(nb)*1

# x0= [1.0,1.0,1.0,1.0,0.0,0.0,0.0,0.0]
lb = -1.1*ones(2*nb)
lb[0] = 1.0
lb[nb] = 0.0
ub = 1.1 * ones(2 * nb)
ub[0] = 1.00+10e-5
ub[nb] = 0.00+10e-5

opt.set_xtol_rel(1e-5)
opt.set_ftol_rel(1e-5)
opt.add_equality_mconstraint(lambda result, x, grad: equality_power_constraint(result, x, grad), 1e-10*ones(2*2))
opt.add_inequality_mconstraint(lambda result, x, grad: inequality_power_constraint(result, x, grad), 1e-10*ones(2*2))
opt.add_inequality_mconstraint(lambda result, x, grad: inequality_power_constraint_min(result, x, grad), 1e-10*ones(2*2))
opt.add_inequality_mconstraint(lambda result, x, grad: v_lower(result, x, grad), 1e-10*ones(nb))
opt.add_inequality_mconstraint(lambda result, x, grad: v_upper(result, x, grad), 1e-10*ones(nb))
opt.set_lower_bounds(lb)
opt.set_upper_bounds(ub)
opt.set_min_objective(obj)
x = opt.optimize(x0)
minf = opt.last_optimum_value()
status = opt.last_optimize_result()
print(x)
print(minf)
print(status)
v=x[idx_v_real] + 1j*x[idx_v_image]
# print(absolute(v))
# # print(angle(v, deg=1))
# for i in gen_bus:
#     x = asmatrix(x)
#     print(x * z_pk[i] * x.T + bus[i, 2]/baseMVA)
# for i in load_bus:
#
#     print(x * z_pk[i] * x.T + bus[i, 2]/baseMVA)
#
# v = asmatrix(x)
# print(v * z_p * v.T + sum(bus[:, 2])/baseMVA)
# v=x[idx_v_real] + 1j*x[idx_v_image]
s=v*conjugate(Ybus*v) + bus[:, 2]/baseMVA + 1j*bus[:, 3]/baseMVA
print(s)
print(sum(s))
v=asmatrix(x)
print(bus[:, 2]/baseMVA + 1j*bus[:, 3]/baseMVA)



