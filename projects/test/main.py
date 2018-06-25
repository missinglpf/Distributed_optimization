from numpy import *
from case4 import case4
from scipy.sparse import *
import nlopt

ppc = case4()
bus = ppc["bus"]
branch = ppc["branch"]
gen = ppc["gen"]
baseMVA = ppc["baseMVA"]

nb = 4 #number of bus
nl = 4 #number of branch
ng = 2 #number of generator

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

#index of variables
idx = arange(nb*2+ng*2)
idx_v_real = idx[0:nb]
idx_v_image = idx[nb:2*nb]
idx_pg = idx[2*nb:(2*nb+ng)]
idx_qg = idx[(2*nb+ng):(nb*2+ng*2)]

gbus = gen[:, 0]                   ## what buses are they at?

## connection matrix, element i, j is 1 if gen on(j) at bus i is ON
Cg = csr_matrix((ones(ng), (gbus, range(ng))), (nb, ng))

# power injected by gens plus power injected by loads converted to p.u.
# Sbus = ( Cg * (gen[:, 1] + 1j * gen[:, 2]) - (bus[:, 2] + 1j * bus[:, 3]) ) / baseMVA

ib = range(nb)
ig = range(ng)

class ACOPT_NLOPT:
    def opt_obj(self, x, grad):
        if grad.size >0:
            grad = r_[zeros(2*nb), ones(ng), zeros(ng)]
        return sum(x[idx_pg])

    def power_constraints(self, result, x, grad):
        V = x[idx_v_real] + 1j * x[idx_v_image]
        Pg = x[idx_pg] * baseMVA
        Qg = x[idx_qg] * baseMVA

        gen[:, 1] = Pg
        gen[:, 2] = Qg

        Ibus = Ybus * V

        diagV = csr_matrix((V, (ib, ib)))
        diagIbus = csr_matrix((Ibus, (ib, ib)))

        if grad.size > 0:
            dg_dVre = conj(diagIbus) + diagV*conj(Ybus)
            dg_dVim = 1j * dg_dVre
            dg_dPg = Cg
            dg_dQg = dg_dPg

            ## construct Jacobian of equality constraints (power flow)
            grad[:] = lil_matrix((2*nb, 2*nb+2*ng))
            blank = csr_matrix((nb, ng))
            grad = vstack([
                ## P mismatch w.r.t Vre, Vim, Pg, Qg
                hstack([dg_dVre.real, dg_dVim.real, dg_dPg, blank]),
                ## P mismatch w.r.t Vre, Vim, Pg, Qg
                hstack([dg_dVre.imag, dg_dVim.imag, blank, dg_dQg])]
            , "csr")
            # gra = gra.T

        Sbus = asmatrix(Cg * (gen[:, 1] + 1j * gen[:, 2]) - (bus[:, 2] + 1j * bus[:, 3])) / baseMVA
        g = V * conj(Ibus) - Sbus
        result[:] = r_[g.real, g.imag]

    def voltage_upper_constraints(self, result, x, grad):
        if grad.size > 0:
            dh1_dVre = 2 * csr_matrix((x[idx_v_real], (self.ib, self.ib)))*x[idx_v_real]
            dh1_dVim = 2 * csr_matrix((x[idx_v_image], (self.ib, self.ib)))*x[idx_v_image]
            blank = csr_matrix((nb, ng))
            # grad[:] = lil_matrix((nb, 2 * nb + 2 * ng))
            grad[:] = hstack([
                dh1_dVre, dh1_dVim, blank, blank]
            , "csr")
            # gra = gra.T
        v_max = asmatrix(1.1*ones(nb))
        result[:] = [csr_matrix((x[idx_v_real], (ib, ib)))*x[idx_v_real] + csr_matrix((x[idx_v_image], (ib, ib)))*x[idx_v_image] - v_max**2]

    def voltage_lower_constraints(self, result, x, grad):
        if grad.size > 0:
            dh2_dVre = -2 * csr_matrix((x[idx_v_real], (self.ib, self.ib)))*x[idx_v_real]
            dh2_dVim = -2 * csr_matrix((x[idx_v_image], (self.ib, self.ib)))*x[idx_v_image]
            blank = csr_matrix((nb, ng))
            # grad[:] = lil_matrix((nb, 2 * nb + 2 * ng))
            grad[:, idx] = hstack([
                dh2_dVre, dh2_dVim, blank, blank]
            , "csr")
            # gra = gra.T
        v_min = asmatrix(0.9 * ones(nb))
        result[:] = [-csr_matrix((x[idx_v_real], (ib, ib))) * x[idx_v_real] - csr_matrix((x[idx_v_image], (ib, ib))) * x[
            idx_v_image] + v_min ** 2]

    def __init__(self):
        self.x0 = zeros(2*nb+2*ng)
        self.x0.flat[idx_v_real] = ones(nb)
        self.lb = zeros(2 * nb + 2 * ng)
        self.lb.flat[[idx_v_real, idx_v_image]] = -1.1*ones(2*nb)
        self.lb.flat[idx_pg] = gen[:, 9] / baseMVA
        self.lb.flat[idx_qg] = gen[:, 4] / baseMVA
        self.ub = zeros(2 * nb + 2 * ng)
        self.ub.flat[[idx_v_real, idx_v_image]] = 1.1 * ones(2 * nb)
        self.ub.flat[idx_pg] = gen[:, 8] / baseMVA
        self.ub.flat[idx_qg] = gen[:, 3] / baseMVA
        self.n = 2*nb + 2*ng

    def solve_opf(self):

        opt = nlopt.opt(nlopt.LN_COBYLA, self.n)

        opt.set_xtol_rel(1e-5)
        opt.set_ftol_rel(1e-8)

        opt.add_equality_mconstraint(lambda result, x, grad: self.power_constraints(result, x, grad), 1e-8*ones(2*nb))
        opt.add_inequality_mconstraint(lambda result, x, grad: self.voltage_lower_constraints(result, x, grad), 1e-8*ones(nb))
        opt.add_inequality_mconstraint(lambda result, x, grad: self.voltage_upper_constraints(result, x, grad), 1e-8*ones(nb))
        opt.set_lower_bounds(self.lb)
        opt.set_upper_bounds(self.ub)
        opt.set_min_objective(self.opt_obj)
        x = opt.optimize(self.x0)
        minf = opt.last_optimum_value()
        status = opt.last_optimize_result()
        return [x, minf, status]

ac_opt = ACOPT_NLOPT()
results = ac_opt.solve_opf()
xopt = results[0]
print(xopt)




