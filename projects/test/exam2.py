import nlopt
from numpy import *

def myfunc(x, grad):
    if grad.size > 0:
        grad[0] = 0.0
        grad[1] = 0.5 / sqrt(x[1])
    return sqrt(x[1])

def myconstraint(result, x, grad):
    a=2
    b=0
    a1 = -1
    b1 = 1
    if grad.size > 0:
        grad[0,0] = 3 * a * (a*x[0] + b)**2
        grad[1, 0] = -1.0

        grad[0,1] = 3 * a1 * (1*x[0] + b1)**2
        grad[1,1] = -1.0
    result = [(a*x[0] + b)**3 - x[1], (a1*x[0] + b1)**3 - x[1]]

opt = nlopt.opt(nlopt.LD_MMA, 2)
opt.set_lower_bounds([-float('inf'), 0])
opt.set_min_objective(myfunc)
opt.add_inequality_mconstraint(lambda result, x,grad: myconstraint(result, x, grad), ([1e-8,1e-8]))
# opt.add_inequality_constraint(lambda x,grad: myconstraint2(x,grad), 1e-8)
opt.set_xtol_rel(1e-4)
x = opt.optimize([1.234, 5.678])
minf = opt.last_optimum_value()
print "optimum at ", x[0],x[1]
print "minimum value = ", minf
print "result code = ", opt.last_optimize_result()