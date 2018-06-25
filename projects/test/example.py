import nlopt
from numpy import *
from scipy.sparse import *

def opf_obj(x, grad):
    if grad.size > 0:
        grad = [1.0, 1.0]
    return x[0] + x[1]

def h(result, x, grad):
    if grad.size > 0:
        dh1_dx = -2 * csr_matrix((ones(2), (arange(0, 2), arange(0, 2))))*x
        dh2_dx = 2 * csr_matrix((ones(2), (arange(0, 2), arange(0, 2))))*x
        # dh1_dx = array([[-2.0, 0.0], [0.0, -2.0]]) * x
        # dh2_dx = array([[2.0, 0.0], [0.0, 2.0]]) * x
        grad[:,:] = r_[dh1_dx, dh2_dx]
        # grad = array(grad).T
    y=x**2
    h1 = 1.0 - y[0] - y[1]
    h2 = y[0] + y[1] - 2.0
    # result[:] = [h1, h2]
    result[0] = h1
    result[1] = h2
# def h1(x, grad):
#     if grad.size > 0:
#         grad = dot(array([[-2, 0], [0, -2]]), x).T
#     return 1 - x[0]**2 - x[1]**2
#
# def h2(x, grad):
#     if grad.size > 0:
#         grad = dot(array([[2, 0], [0, 2]]), x).T
#     return x[0]**2 + x[1]**2 - 2

opt = nlopt.opt(nlopt.LN_COBYLA, 2)
lb= [1.0, 0.0]
opt.set_lower_bounds(lb)
opt.set_upper_bounds([1.0+100e-8, float('inf')])
opt.set_min_objective(opf_obj)
opt.add_inequality_mconstraint(lambda result, x,grad: h(result, x, grad), [1e-8, 1e-8])
# opt.add_inequality_constraint(lambda x,grad: h1(x, grad), 1e-8)
# opt.add_inequality_constraint(lambda x,grad: h2(x, grad), 1e-8)
opt.set_xtol_rel(1e-5)
opt.set_ftol_rel(1e-8)
x0= [1.0,0.0]
x = opt.optimize(x0)
minf = opt.last_optimum_value()
print "optimum at ", x[0],x[1]

print "minimum value = ", minf
print "result code = ", opt.last_optimize_result()


