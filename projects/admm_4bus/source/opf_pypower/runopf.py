from sys import stdout, stderr

from os.path import dirname, join

from ppoption import ppoption
from opf import opf
from printpf import printpf
from case4 import case4gs

def runopf(z, nu, rho, casedata=None, ppopt=None, fname='', solvedcase=''):
    ppopt = ppoption(ppopt)
    ##-----  run the optimal power flow  -----
    r = opf(z, nu, rho, casedata)
    printpf(r, stdout, ppopt)
    return r

# if __name__ == '__main__':
#     ppc = case4gs()
#     results = runopf(z, nu, rho, casedata=ppc)
#     print(results["x"])