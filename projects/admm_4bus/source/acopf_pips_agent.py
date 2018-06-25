from numpy import *
from scipy.sparse import *
import nlopt
import sys
sys.path.append('D:/phd/These_asys/source/nlopt_test/admm/opf_pypower')
from pips import pips

baseMVA = 100
class ACopf_pips:
    def __init__(self, x0, z_pk, z_qk, lb, ub, pd, qd, p_max, p_min, q_max, q_min, node_type, n, z, nu, rho):
        self.z_pk = csr_matrix(z_pk,dtype=float)
        self.z_qk = csr_matrix(z_qk, dtype=float)
        self.lb = lb
        self.ub = ub
        self.x0 = x0
        self.n = n
        self.z = z
        self.nu = nu
        self.rho = rho
        self.node_type = node_type
        # self.neighbors = neighbors
        self.pd = pd
        self.qd = qd
        self.p_max = p_max
        self.p_min = p_min
        self.q_max = q_max
        self.q_min = q_min
        # print((self.z_pk + self.z_pk.T))
        # print(self.nu-self.z)
        # print(self.rho*(self.nu-self.z))
    def f(self, x, return_hessian=False):
        v = asmatrix(x)
        f = asscalar(v * self.z_pk * v.T + dot(self.nu, x) + (self.rho/2) * (linalg.norm(x - self.z)**2))
        df = (self.z_pk + self.z_pk.T)*x + self.nu + self.rho * (x - self.z)
        # df = array([1,1,1,1,1,1])
        # df = (self.z_pk + self.z_pk.T) * v.T + asmatrix(self.nu).T + self.rho * (v.T - asmatrix(self.z).T)
        if not return_hessian:
            return f, df
        d2f = (self.z_pk + self.z_pk.T) + self.rho * eye(2*self.n, dtype=float)
        return f, df, d2f

    def gh(self, x, gen):
        v = asmatrix(x)
        ib = range(self.n)
        idx_v_real = arange(0, self.n)
        idx_v_image = arange(self.n, 2 * self.n)
        v_max = 1.1*ones(self.n)
        v_min = 0.9*ones(self.n)
        if gen:
            # h = zeros(4+2*self.n)h1, h2, h3, h4,
            h1 = v * self.z_pk * v.T + self.pd - self.p_max
            h2 = -(v * self.z_pk * v.T + self.pd - self.p_min)
            h3 = v * self.z_qk * v.T + self.qd - self.q_max
            h4 = -(v * self.z_qk * v.T + self.qd - self.q_min)
            h5 = r_[x[idx_v_real] ** 2 + x[idx_v_image] ** 2 - v_max ** 2]
            h6 = r_[-(x[idx_v_real] ** 2 + x[idx_v_image] ** 2 - v_min ** 2)]
            h = r_[asscalar(h1), asscalar(h2), asscalar(h3), asscalar(h4), h5, h6]

            # dh = csr_matrix((2*self.n, 4+2*self.n))
            dh1 = (self.z_pk + self.z_pk.T) * v.T
            dh2 = -(self.z_pk + self.z_pk.T) * v.T
            dh3 = (self.z_qk + self.z_qk.T) * v.T
            dh4 = -(self.z_qk + self.z_qk.T) * v.T
            dh_x_real = 2 * csr_matrix((x[idx_v_real], (ib, ib)))
            dh_x_imag = 2 * csr_matrix((x[idx_v_image], (ib, ib)))
            dh5 = vstack([dh_x_real, dh_x_imag], "csr")
            dh6 = -dh5
            dh = hstack([dh1, dh2, dh3, dh4, dh5, dh6], "csr")

            g = array([])
            dg = None
        else:
            # h = zeros(2*self.n)
            h1 = x[idx_v_real] ** 2 + x[idx_v_image] ** 2 - v_max ** 2
            h2 = -(x[idx_v_real] ** 2 + x[idx_v_image] ** 2 - v_min ** 2)
            h = r_[h1, h2]

            dh = csr_matrix((2*self.n, 2*self.n))
            # dh_x_real = 2 * csr_matrix((x[idx_v_real], (ib, ib)))
            # dh_x_imag = 2 * csr_matrix((x[idx_v_image], (ib, ib)))
            #
            dh[0:self.n,0:self.n] = 2 * csr_matrix((x[idx_v_real], (ib, ib)))
            dh[self.n:2*self.n,self.n:2*self.n] = -2 * csr_matrix((x[idx_v_image], (ib, ib)))

            g = zeros(2)
            g[0] = v * self.z_pk * v.T + self.pd
            g[1] = v * self.z_qk * v.T + self.qd

            dg = csr_matrix((2*self.n, 2))
            dg[:,0] = (self.z_pk + self.z_pk.T) * v.T
            dg[:,1] = (self.z_qk + self.z_qk.T) * v.T
        return h, g, dh, dg

    def hess(self, x, lam, cost_mult, gen):
        # _, _, d2f = self.f(self, x, return_hessian=True)
        d2f = 0.5 * (self.z_pk + self.z_pk.T) + self.rho * eye(2 * self.n, dtype=float)
        d2f = cost_mult * d2f
        lmbda = lam['eqnonlin']
        mu = lam['ineqnonlin']
        if gen:
            d2g = csr_matrix((2*self.n, 2*self.n))

            d2h = csr_matrix((2*self.n, 2*self.n))
            d2h += mu[0]*(self.z_pk + self.z_pk.T)
            d2h += -mu[1]*(self.z_pk + self.z_pk.T)
            d2h += mu[2]*(self.z_qk + self.z_qk.T)
            d2h += -mu[3]*(self.z_qk + self.z_qk.T)
            for i in arange(4, 4+self.n):
                d2h += mu[i]*2*csr_matrix(([1,1],([i-4, i-4+self.n], [i-4, i-4+self.n])),(2*self.n, 2*self.n),dtype=float)
            for i in arange(4+self.n,4+2*self.n):
                d2h += -mu[i]*2*csr_matrix(([1,1],([i-4-self.n, i-4], [i-4-self.n, i-4])),(2*self.n, 2*self.n),dtype=float)

        else:
            d2h = csr_matrix((2 * self.n, 2 * self.n),dtype=float)
            for i in arange(0, self.n):
                d2h += mu[i]*2*csr_matrix(([1,1],([i, i+self.n], [i, i+self.n])),(2*self.n, 2*self.n),dtype=float)
            for i in arange(self.n, 2*self.n):
                d2h += -mu[i]*2*csr_matrix(([1,1],([i-self.n, i], [i-self.n, i])),(2*self.n, 2*self.n),dtype=float)

            d2g = csr_matrix((2 * self.n, 2 * self.n), dtype=float)
            d2g += lmbda[0] * (self.z_pk + self.z_pk.T)
            d2g += lmbda[1] * (self.z_qk + self.z_qk.T)
        return d2f+d2g+d2h

    def solve_opf(self):
        if self.node_type == 1:
            gen = False
        else:
            gen = True

        f_fcn = lambda x, return_hessian=False: self.f(x, return_hessian)
        gh_fcn = lambda x: self.gh(x, gen)
        hess_fcn = lambda x, lmbda, cost_mult=1: self.hess(x, lmbda, cost_mult, gen)

        solution = pips(f_fcn, self.x0, xmin=self.lb, xmax=self.ub, gh_fcn=gh_fcn, hess_fcn=hess_fcn)
        x, f, s, lam, _ = solution["x"], solution["f"], solution["eflag"], \
                          solution["lmbda"], solution["output"]

        return [x, f, s]