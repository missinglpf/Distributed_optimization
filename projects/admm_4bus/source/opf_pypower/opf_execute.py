from sys import stdout, stderr

from numpy import array, arange, pi, zeros, r_
from pipsopf_solver import pipsopf_solver
from idx_bus import VM
from idx_gen import GEN_BUS, VG
from idx_brch import MU_ANGMIN, MU_ANGMAX
def opf_execute(om, ppopt, z, nu, rho):
    ##-----  setup  -----
    alg = ppopt['OPF_ALG']

    ## get indexing
    vv, ll, nn, _ = om.get_idx()

    ## if OPF_ALG not set, choose best available option
    if alg == 0:
        alg = 560                ## MIPS

    ppopt['OPF_ALG_POLY'] = alg

    results, success = pipsopf_solver(om, ppopt, z, nu, rho)

    if success:
        ## copy bus voltages back to gen matrix
        results['gen'][:, VG] = results['bus'][results['gen'][:, GEN_BUS].astype(int), VM]

    return results, success