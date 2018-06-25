from numpy import *
from scipy.sparse import *
import nlopt
import sys
sys.path.append('D:/phd/These_asys/source/nlopt_test/admm/opf_pypower')
from pips import pips

def f6(x, return_hessian=False):
    f = -x[0] * x[1] - x[1] * x[2]
    df = -array([x[1], x[0] + x[2], x[1]])
    if not return_hessian:
        return f, df
    d2f = -csr_matrix([[0, 1, 0],
                   [1, 0, 1],
                   [0, 1, 0]], dtype=float)
    return f, df, d2f

def gh6(x):
    h = dot([[1.0, -1.0, 1.0],
             [1.0,  1.0, 1.0]], x**2) + [-2.0, -10.0]
    dh = 2 * csr_matrix([[ x[0], x[0]],
                     [-x[1], x[1]],
                     [ x[2], x[2]]], dtype=float)
    g = array([])
    dg = None
    return h, g, dh, dg

def hess6(x, lam, cost_mult=1):
    mu = lam['ineqnonlin']
    Lxx = cost_mult * \
        csr_matrix([[ 0, -1,  0],
                [-1,  0, -1],
                [ 0, -1,  0]], dtype=float) + \
        csr_matrix([[2 * dot([1, 1], mu),  0, 0],
                [0, 2 * dot([-1, 1], mu), 0],
                [0, 0,  2 * dot([1, 1], mu)]], dtype=float)
    return Lxx

f_fcn = f6
gh_fcn = gh6
hess_fcn = hess6
x0 = array([1.0, 1.0, 0.0])
# solution = pips(f_fcn, x0, gh_fcn=gh_fcn, hess_fcn=hess_fcn, opt={'verbose': 2, 'comptol': 1e-9})
solution = pips(f_fcn, x0, gh_fcn=gh_fcn, hess_fcn=hess_fcn)
x, f, s, lam, out = solution["x"], solution["f"], solution["eflag"], \
        solution["lmbda"], solution["output"]
print(x,s)