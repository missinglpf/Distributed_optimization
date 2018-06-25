from time import time

from numpy import zeros, c_, shape, ix_

from idx_bus import MU_VMIN
from idx_gen import PG, QG, MU_QMIN, MU_PMAX, MU_PMIN
from idx_brch import PF, QF, PT, QT, MU_SF, MU_ST, MU_ANGMIN, MU_ANGMAX

from opf_args import opf_args2
from opf_setup import opf_setup
from opf_execute import opf_execute

from ext2int import ext2int
from int2ext import int2ext

def opf( z, nu, rho, casefile):
    ##----- initialization -----
    t0 = time()         ## start timer

    ## process input arguments
    ppc, ppopt = opf_args2(casefile)

    ## add zero columns to bus, gen, branch for multipliers, etc if needed
    nb   = shape(ppc['bus'])[0]    ## number of buses
    nl   = shape(ppc['branch'])[0] ## number of branches
    ng   = shape(ppc['gen'])[0]    ## number of dispatchable injections

    ##-----  convert to internal numbering, remove out-of-service stuff  -----
    ppc = ext2int(ppc)

    ##-----  construct OPF model object  -----
    om = opf_setup(ppc, ppopt)

    ##-----  execute the OPF  -----
    results, success = opf_execute(om, ppopt, z, nu, rho)

    ##-----  revert to original ordering, including out-of-service stuff  -----
    results = int2ext(results)

    ##-----  finish preparing output  -----
    et = time() - t0      ## compute elapsed time
    results['et'] = et
    results['success'] = success

    return results