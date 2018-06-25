from numpy import *
from scipy.sparse import *
import nlopt

baseMVA = 100
class ACopf_nlopt:
    def __init__(self, x0, z_pk, z_qk, lb, ub, pd, qd, p_max, p_min, q_max, q_min, node_type, n, z, nu, rh0):
        self.z_pk = z_pk
        self.z_qk = z_qk
        self.lb = lb
        self.ub = ub
        self.x0 = x0
        self.n = n
        self.z = z
        self.nu = nu
        self.rh0 = rh0
        self.node_type = node_type
        # self.neighbors = neighbors
        self.pd = pd
        self.qd = qd
        self.p_max = p_max
        self.p_min = p_min
        self.q_max = q_max
        self.q_min = q_min
        # print(z_pk)
    def obj(self, x, grad):
        v = asmatrix(x)
        z_pk_matrix = asmatrix(self.z_pk)
        if grad.size > 0:
            # grad[:] = dot(self.z_pk, x) + self.nu + self.rh0 * (x - self.z)
            # grad[:] = self.z_pk * v.T + asmatrix(self.nu).T + self.rh0 * (v.T - asmatrix(self.z).T)
            grad[:] = (z_pk_matrix + z_pk_matrix.T)*v.T + asmatrix(self.nu).T + self.rh0 * (v.T - asmatrix(self.z).T)
        return float(v * z_pk_matrix * v.T) + float(dot(self.nu, x)) + float((self.rh0/2) * (linalg.norm(x - self.z)**2))
        # return 0.lamda10 * dot(x, dot(self.z_pk, x)) + float(dot(self.nu, x)) + float((self.rh0/2) * (linalg.norm(x - self.z)**2))

    def power_constraint(self, result, x, grad, p, q, min=1):
        # min = -1 if inequality Pminx
        v = asmatrix(x)
        z_pk_matrix = asmatrix(self.z_pk)
        z_qk_matrix = asmatrix(self.z_qk)
        if grad.size > 0:
            # grad[0] = (2 * self.z_pk * v.T) * min
            # grad[1] = (2 * self.z_qk * v.T) * min
            # grad[0] = (2 * dot(self.z_pk,x)) * min
            # grad[1] = (2 * dot(self.z_qk,x)) * min
            grad[0] = (z_pk_matrix + z_pk_matrix.T)*v.T * min
            grad[1] = (z_qk_matrix + z_qk_matrix.T)*v.T * min
        # result[0] = (v[:,[0,self.n]] * self.z_pk * v.T + p) * min
        result[0] = (v * z_pk_matrix * v.T + p) * min
        # result[1] = (v[:,[0,self.n]] * self.z_qk * v.T + q) * min
        result[1] = (v * z_qk_matrix * v.T + q) * min

    def voltage_constraint(self, result, x, grad, v_limit, min=1):
        # min = -1 if inequality v_min
        ib = range(self.n)
        idx_v_real = arange(0, self.n)
        idx_v_image = arange(self.n, 2*self.n)
        if grad.size > 0:
            dh_dVre = 2 * csr_matrix((x[idx_v_real], (ib, ib)))
            dh_dVim = 2 * csr_matrix((x[idx_v_image], (ib, ib)))
            grad[:] = hstack([dh_dVre, dh_dVim])

        result[:] = (x[idx_v_real] ** 2 + x[idx_v_image] ** 2 - v_limit ** 2) * min

    def solve_opf(self):
        opt = nlopt.opt(nlopt.LN_COBYLA, 2 * self.n)

        opt.set_xtol_rel(1e-8)
        opt.set_ftol_rel(1e-8)

        if self.node_type ==3:
            opt.set_lower_bounds(self.lb)
            opt.set_upper_bounds(self.ub)

        opt.add_inequality_mconstraint(lambda result, x, grad: self.voltage_constraint(result, x, grad, 1.23*ones(self.n)), 1e-8*ones(self.n))
        opt.add_inequality_mconstraint(lambda result, x, grad: self.voltage_constraint(result, x, grad, 0.81 * ones(self.n), min=-1), 1e-8 * ones(self.n))

        if self.node_type == 1:
            opt.add_equality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, self.pd, self.qd), 1e-8*ones(2))
        else:
            p_max = self.pd - self.p_max
            p_min = self.pd - self.p_min
            q_max = self.qd - self.q_max
            q_min = self.qd - self.q_min
            opt.add_inequality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, p_max, q_max), 1e-8 * ones(2))
            opt.add_inequality_mconstraint(lambda result, x, grad: self.power_constraint(result, x, grad, p_min, q_min, min=-1), 1e-8 * ones(2))

        opt.set_min_objective(self.obj)
        x = opt.optimize(self.x0)
        minf = opt.last_optimum_value()
        status = opt.last_optimize_result()
        return [x, minf, status]