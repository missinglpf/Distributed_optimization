import numpy as np
from scipy.sparse import *
import nlopt

baseMVA = 100
class ACopf_nlopt:
    def __init__(self, x0, z_pk, z_qk, lb, ub, pd, qd, p_max, p_min, q_max, q_min, node_type, n, z, nu, rh0):
        self.z_pk = np.array(z_pk)
        self.z_qk = np.array(z_qk)
        self.lb = lb
        self.ub = ub
        self.x0 = x0
        self.n = n
        self.z = z
        self.nu = nu
        self.rh0 = rh0
        self.node_type = node_type
        self.pd = pd
        self.qd = qd
        self.p_max = p_max
        self.p_min = p_min
        self.q_max = q_max
        self.q_min = q_min

    def obj(self, x, grad):
        if grad.size > 0:
            grad[:] = (self.z_pk + self.z_pk.T)*x + self.nu + self.rh0 * (x - self.z)
        return np.dot(x, np.dot(self.z_pk, x)) + np.dot(self.nu, x) + (self.rh0/2) * np.linalg.norm(x - self.z)**2

    def power_constraint(self, result, x, grad, p, q, min=1):
        if grad.size > 0:
            grad[0] = (self.z_pk + self.z_pk.T)* x * min
            grad[1] = (self.z_qk + self.z_qk.T)* x * min
        result[0] = (np.dot(x, np.dot(self.z_pk, x)) + p) * min
        result[1] = (np.dot(x, np.dot(self.z_qk, x)) + q) * min

    def voltage_constraint(self, result, x, grad, v_limit, min=1):
        # min = -1 if inequality v_min
        ib = range(self.n)
        idx_v_real = np.arange(0, self.n)
        idx_v_image = np.arange(self.n, 2*self.n)
        if grad.size > 0:
            dh_dVre = 2 * csr_matrix((x[idx_v_real], (ib, ib)))
            dh_dVim = 2 * csr_matrix((x[idx_v_image], (ib, ib)))
            grad[:] = hstack([dh_dVre, dh_dVim])

        result[:] = (x[idx_v_real] ** 2 + x[idx_v_image] ** 2 - v_limit ** 2) * min

    def solve_opf(self):
        opt = nlopt.opt(nlopt.LN_COBYLA, 2 * self.n)

        opt.set_xtol_rel(1e-8)
        opt.set_ftol_rel(1e-8)

        opt.set_lower_bounds(self.lb)
        opt.set_upper_bounds(self.ub)

        opt.add_inequality_mconstraint(lambda result, x, grad: self.voltage_constraint(result, x, grad, 1.23*np.ones(self.n)), 1e-8*np.ones(self.n))
        opt.add_inequality_mconstraint(lambda result, x, grad: self.voltage_constraint(result, x, grad, 0.8 * np.ones(self.n), min=-1), 1e-8 * np.ones(self.n))

        if self.node_type == 1:
            opt.add_equality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, self.pd, self.qd), 1e-8*np.ones(2))
        else:
            p_max = self.pd - self.p_max
            p_min = self.pd - self.p_min
            q_max = self.qd - self.q_max
            q_min = self.qd - self.q_min
            opt.add_inequality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, p_max, q_max), 1e-8 * np.ones(2))
            opt.add_inequality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, p_min, q_min, min=-1), 1e-8 * np.ones(2))

        opt.set_min_objective(self.obj)
        x = opt.optimize(self.x0)
        minf = opt.last_optimum_value()
        status = opt.last_optimize_result()
        return [x, minf, status]