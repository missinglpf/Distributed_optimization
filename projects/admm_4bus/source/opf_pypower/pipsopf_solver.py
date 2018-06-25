"""Solves AC optimal power flow using PIPS.
"""

from numpy import ones, zeros, Inf, pi, exp, conj, r_
from numpy import flatnonzero as find

from idx_bus import BUS_TYPE, REF, VM, VA, MU_VMAX, MU_VMIN, LAM_P, LAM_Q
from idx_brch import F_BUS, T_BUS, RATE_A, PF, QF, PT, QT, MU_SF, MU_ST
from idx_gen import GEN_BUS, PG, QG, VG, MU_PMAX, MU_PMIN, MU_QMAX, MU_QMIN

from makeYbus import makeYbus
from opf_consfcn import opf_consfcn
from opf_costfcn import opf_costfcn
from opf_hessfcn import opf_hessfcn
from pips import pips

def pipsopf_solver(om, ppopt, z, nu, rho):
    """Solves AC optimal power flow using PIPS.

    Inputs are an OPF model object, a PYPOWER options vector and
    a dict containing keys (can be empty) for each of the desired
    optional output fields.

    outputs are a C{results} dict, C{success} flag and C{raw} output dict.

    C{results} is a PYPOWER case dict (ppc) with the usual baseMVA, bus
    branch, gen, gencost fields, along with the following additional
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
        - xr     final value of optimization variables
        - pimul  constraint multipliers
        - info   solver specific termination code
        - output solver specific output information

    @see: L{opf}, L{pips}
    """

    ##----- initialization -----

    ## options
    verbose = ppopt['VERBOSE']
    feastol = ppopt['PDIPM_FEASTOL']
    gradtol = ppopt['PDIPM_GRADTOL']
    comptol = ppopt['PDIPM_COMPTOL']
    costtol = ppopt['PDIPM_COSTTOL']
    max_it  = ppopt['PDIPM_MAX_IT']
    max_red = ppopt['SCPDIPM_RED_IT']
    step_control = (ppopt['OPF_ALG'] == 565)  ## OPF_ALG == 565, PIPS-sc
    if feastol == 0:
        feastol = ppopt['OPF_VIOLATION']
    opt = {  'feastol': feastol,
             'gradtol': gradtol,
             'comptol': comptol,
             'costtol': costtol,
             'max_it': max_it,
             'max_red': max_red,
             'step_control': step_control,
             'cost_mult': 1e-4,
             'verbose': verbose  }

    ## unpack data
    ppc = om.get_ppc()
    baseMVA, bus, gen, branch = \
        ppc["baseMVA"], ppc["bus"], ppc["gen"], ppc["branch"]
    vv, _, nn, _ = om.get_idx()

    ## problem dimensions
    nb = bus.shape[0]          ## number of buses
    nl = branch.shape[0]       ## number of branches

    ## linear constraints
    A, l, u = om.linear_constraints()

    ## bounds on optimization vars
    _, xmin, xmax = om.getv()

    ## build admittance matrices
    Ybus, Yf, Yt = makeYbus(baseMVA, bus, branch)

    ## try to select an interior initial point
    ll, uu = xmin.copy(), xmax.copy()
    ll[xmin == -Inf] = -1e10   ## replace Inf with numerical proxies
    uu[xmax ==  Inf] =  1e10
    x0 = (ll + uu) / 2
    Varefs = bus[bus[:, BUS_TYPE] == REF, VA] * (pi / 180)
    ## angles set to first reference angle
    # x0[vv["i1"]["Va"]:vv["iN"]["Va"]] = Varefs[0]

    ## find branches with flow limits
    il = find((branch[:, RATE_A] != 0) & (branch[:, RATE_A] < 1e10))
    nl2 = len(il)           ## number of constrained lines

    ##-----  run opf  -----
    f_fcn = lambda x, return_hessian=False: opf_costfcn(x, om, rho, nu, z, return_hessian)
    gh_fcn = lambda x: opf_consfcn(x, om, Ybus, Yf[il, :], Yt[il,:], ppopt, il)
    hess_fcn = lambda x, lmbda, cost_mult: opf_hessfcn(x, lmbda, om, Ybus, Yf[il, :], Yt[il, :], ppopt, rho, il)

    solution = pips(f_fcn, x0, A, l, u, xmin, xmax, gh_fcn, hess_fcn, opt)
    x, f, info, lmbda, output = solution["x"], solution["f"], \
            solution["eflag"], solution["lmbda"], solution["output"]

    success = (info > 0)

    ## update solution data
    Va = x[vv["i1"]["Va"]:vv["iN"]["Va"]]
    Vm = x[vv["i1"]["Vm"]:vv["iN"]["Vm"]]
    Pg = x[vv["i1"]["Pg"]:vv["iN"]["Pg"]]
    Qg = x[vv["i1"]["Qg"]:vv["iN"]["Qg"]]

    V = Vm * exp(1j * Va)

    ##-----  calculate return values  -----
    ## update voltages & generator outputs
    bus[:, VA] = Va * 180 / pi
    bus[:, VM] = Vm
    gen[:, PG] = Pg * baseMVA
    gen[:, QG] = Qg * baseMVA
    gen[:, VG] = Vm[ gen[:, GEN_BUS].astype(int) ]

    ## compute branch flows
    Sf = V[ branch[:, F_BUS].astype(int) ] * conj(Yf * V)  ## cplx pwr at "from" bus, p["u"].
    St = V[ branch[:, T_BUS].astype(int) ] * conj(Yt * V)  ## cplx pwr at "to" bus, p["u"].
    branch[:, PF] = Sf.real * baseMVA
    branch[:, QF] = Sf.imag * baseMVA
    branch[:, PT] = St.real * baseMVA
    branch[:, QT] = St.imag * baseMVA

    ## line constraint is actually on square of limit
    ## so we must fix multipliers
    muSf = zeros(nl)
    muSt = zeros(nl)
    if len(il) > 0:
        muSf[il] = \
            2 * lmbda["ineqnonlin"][:nl2] * branch[il, RATE_A] / baseMVA
        muSt[il] = \
            2 * lmbda["ineqnonlin"][nl2:nl2+nl2] * branch[il, RATE_A] / baseMVA

    ## update Lagrange multipliers
    bus[:, MU_VMAX]  = lmbda["upper"][vv["i1"]["Vm"]:vv["iN"]["Vm"]]
    bus[:, MU_VMIN]  = lmbda["lower"][vv["i1"]["Vm"]:vv["iN"]["Vm"]]
    gen[:, MU_PMAX]  = lmbda["upper"][vv["i1"]["Pg"]:vv["iN"]["Pg"]] / baseMVA
    gen[:, MU_PMIN]  = lmbda["lower"][vv["i1"]["Pg"]:vv["iN"]["Pg"]] / baseMVA
    gen[:, MU_QMAX]  = lmbda["upper"][vv["i1"]["Qg"]:vv["iN"]["Qg"]] / baseMVA
    gen[:, MU_QMIN]  = lmbda["lower"][vv["i1"]["Qg"]:vv["iN"]["Qg"]] / baseMVA

    bus[:, LAM_P] = \
        lmbda["eqnonlin"][nn["i1"]["Pmis"]:nn["iN"]["Pmis"]] / baseMVA
    bus[:, LAM_Q] = \
        lmbda["eqnonlin"][nn["i1"]["Qmis"]:nn["iN"]["Qmis"]] / baseMVA
    branch[:, MU_SF] = muSf / baseMVA
    branch[:, MU_ST] = muSt / baseMVA

    ## package up results
    nlnN = om.getN('nln')

    results = ppc
    results["bus"], results["branch"], results["gen"], \
        results["om"], results["x"], results["f"] = \
            bus, branch, gen, om, x, f

    return results, success