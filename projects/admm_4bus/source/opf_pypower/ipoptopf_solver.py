from numpy import ones, zeros, shape, Inf, pi, exp, conj, r_, arange
from numpy import flatnonzero as find

from scipy.sparse import issparse, tril, vstack, hstack, csr_matrix as sparse
from scipy.sparse import eye as speye

from idx_bus import BUS_TYPE, REF, VM, VA, MU_VMAX, MU_VMIN, LAM_P, LAM_Q
from idx_brch import F_BUS, T_BUS, RATE_A, PF, QF, PT, QT, MU_SF, MU_ST
from idx_gen import GEN_BUS, PG, QG, VG, MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN

from makeYbus import makeYbus


def ipoptopf_solver(om, ppopt):
    """Solves AC optimal power flow using IPOPT.

    Inputs are an OPF model object and a PYPOWER options vector.

    Outputs are a C{results} dict, C{success} flag and C{raw} output dict.

    C{results} is a PYPOWER case dict (ppc) with the usual C{baseMVA}, C{bus}
    C{branch}, C{gen}, C{gencost} fields, along with the following additional
    fields:
        - C{order}      see 'help ext2int' for details of this field
        - C{x}          final value of optimization variables (internal order)
        - C{f}          final objective function value
        - C{mu}         shadow prices on ...
            - C{var}
                - C{l}  lower bounds on variables
                - C{u}  upper bounds on variables
            - C{nln}
                - C{l}  lower bounds on nonlinear constraints
                - C{u}  upper bounds on nonlinear constraints
            - C{lin}
                - C{l}  lower bounds on linear constraints
                - C{u}  upper bounds on linear constraints

    C{success} is C{True} if solver converged successfully, C{False} otherwise

    C{raw} is a raw output dict in form returned by MINOS
        - C{xr}     final value of optimization variables
        - C{pimul}  constraint multipliers
        - C{info}   solver specific termination code
        - C{output} solver specific output information

    @see: L{opf}, L{pips}

    """
    import pyipopt

    ## unpack data
    ppc = om.get_ppc()
    baseMVA, bus, gen, branch, gencost = \
        ppc['baseMVA'], ppc['bus'], ppc['gen'], ppc['branch'], ppc['gencost']
    vv, _, nn, _ = om.get_idx()

    ## problem dimensions
    nb = shape(bus)[0]          ## number of buses
    ng = shape(gen)[0]          ## number of gens
    nl = shape(branch)[0]       ## number of branches

    ## linear constraints
    A, l, u = om.linear_constraints()

    ## bounds on optimization vars
    _, xmin, xmax = om.getv()

    ## build admittance matrices
    Ybus, Yf, Yt = makeYbus(baseMVA, bus, branch)

    ## try to select an interior initial point
    ll = xmin.copy(); uu = xmax.copy()
    ll[xmin == -Inf] = -2e19   ## replace Inf with numerical proxies
    uu[xmax ==  Inf] =  2e19
    x0 = (ll + uu) / 2
    Varefs = bus[bus[:, BUS_TYPE] == REF, VA] * (pi / 180)
    x0[vv['i1']['Va']:vv['iN']['Va']] = Varefs[0]  ## angles set to first reference angle
    if ny > 0:
        ipwl = find(gencost[:, MODEL] == PW_LINEAR)