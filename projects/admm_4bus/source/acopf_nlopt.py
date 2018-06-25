from numpy import *
from scipy.sparse import *
import nlopt

baseMVA = 100
class ACopf_nlopt:
    def __init__(self, z_pk, z_qk, bus, n, z, nu, rh0, node_type, ref, gen=[]):
        self.z_pk = z_pk
        self.z_qk = z_qk
        self.bus = bus
        # self.x0 = x0
        self.n = n
        self.z = z
        self.nu = nu
        self.rh0 = rh0
        self.node_type = node_type
        # self.neighbors = neighbors
        self.gen = gen
        self.ref = ref

    def obj(self, x, grad):
        v = asmatrix(x)
        if grad.size > 0:
            grad[:] = self.z_pk * v.T + asmatrix(self.nu).T + self.rh0 * (v.T - asmatrix(self.z).T)
        return float(0.5 * v[:,[0,3]] * self.z_pk * v.T) + float(dot(self.nu, x)) + float((self.rh0/2) * (linalg.norm(x - self.z)**2))

    def power_constraint(self, result, x, grad, p, q, min=1):
        # min = -1 if inequality Pmin
        v = asmatrix(x)
        if grad.size > 0:
            grad[0] = (2 * self.z_pk * v.T) * min
            grad[1] = (2 * self.z_qk * v.T) * min
        result[0] = (v[:,[0,3]] * self.z_pk * v.T + p) * min
        result[1] = (v[:,[0,3]] * self.z_qk * v.T + q) * min

    def voltage_constraint(self, result, x, grad, v_limit, min=1):
        # min = -1 if inequality v_min
        ib = range(self.n)
        idx_v_real = arange(0, self.n)
        idx_v_image = arange(self.n, 2*self.n)
        if grad.size > 0:
            dh_dVre = 2 * csr_matrix((x[idx_v_real], (ib, ib))) * x[idx_v_real]
            dh_dVim = 2 * csr_matrix((x[idx_v_image], (ib, ib))) * x[idx_v_image]
            grad[:] = hstack([dh_dVre, dh_dVim])

        result[:] = (x[idx_v_real] ** 2 + x[idx_v_image] ** 2 - v_limit ** 2) * min

    def solve_opf(self):
        opt = nlopt.opt(nlopt.LN_COBYLA, 2 * self.n)
        lb = -1.1 * ones(2*self.n)
        ub = 1.1 * ones(2*self.n)
        x0 = zeros(2*self.n)
        x0[range(self.n)] = ones(self.n)
        if self.ref <4:
            lb[self.ref] = 1.0
            lb[self.ref + 3] = 0.0
            ub[self.ref] = 1.0 + 1e-8
            ub[self.ref + 3] = 0.0 + 1e-8
        opt.set_xtol_rel(1e-8)
        opt.set_ftol_rel(1e-8)

        opt.set_lower_bounds(lb)
        opt.set_upper_bounds(ub)

        opt.add_inequality_mconstraint(lambda result, x, grad: self.voltage_constraint(result, x, grad, 1.1*ones(self.n)), 1e-8*ones(self.n))
        opt.add_inequality_mconstraint(lambda result, x, grad: self.voltage_constraint(result, x, grad, 0.9 * ones(self.n), min=-1), 1e-8 * ones(self.n))

        if self.node_type == 1:
            opt.add_equality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, self.bus[2]/baseMVA, self.bus[3]/baseMVA), 1e-8*ones(2))
        else:
            p_max = (self.bus[2] - self.gen[8])/baseMVA
            p_min = (self.bus[2] - self.gen[9]) / baseMVA
            q_max = (self.bus[3] - self.gen[3]) / baseMVA
            q_min = (self.bus[3] - self.gen[4]) / baseMVA
            opt.add_inequality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, p_max, q_max), 1e-8 * ones(2))
            opt.add_inequality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, p_min, q_min, min=-1), 1e-8 * ones(2))

        opt.set_min_objective(self.obj)
        x = opt.optimize(x0)
        minf = opt.last_optimum_value()
        status = opt.last_optimize_result()
        return [x, minf, status]