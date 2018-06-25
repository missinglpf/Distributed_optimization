from pips import pips
from numpy import *

def f(x, return_hessian=False):
    f = -x[0]*x[1] - x[1]*x[2]
    df = -array([[x[1]],
                 [x[0]+x[2]],
                 [x[1]]])
    if not return_hessian:
        return f, df
    d2f = -array([[0, 1, 0],
                 [1, 0, 1],
                 [0, 1, 0]])
    return f, df, d2f

def gh(x):
    h = array([[1, -1, 1], [1, 1, 1]])*x**2