from numpy import array, r_, float64, dot
from scipy.sparse import csr_matrix
from pips import pips

def f2(x):
    f = -x[0] * x[1] - x[1] * x[2]
    df = -r_[x[1], x[0] + x[2], x[1]]
    # actually not used since 'hess_fcn' is provided
    d2f = -array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], float64)
    return f, df
def gh2(x):
    h = dot(array([[1, -1, 1],[1,  1, 1]]), x**2) + array([-2.0, -10.0])
    dh = 2 * csr_matrix(array([[ x[0], x[0]], [-x[1], x[1]],[ x[2], x[2]]]))
    g = array([])
    dg = None
    return h, g, dh, dg
def hess2(x, lam, cost_mult=1):
    mu = lam["ineqnonlin"]
    a = r_[dot(2 * array([1, 1]), mu), -1, 0]
    b = r_[-1, dot(2 * array([-1, 1]), mu),-1]
    c = r_[0, -1, dot(2 * array([1, 1]), mu)]
    Lxx = csr_matrix(array([a, b, c]))
    return Lxx

x0 = array([1, 1, 0], float64)
solution = pips(f2, x0, gh_fcn=gh2, hess_fcn=hess2)
print(round(solution["f"], 11))

print(solution["output"]["iterations"])