from numpy import array, zeros, ones, exp, arange, r_, flatnonzero as find
from scipy.sparse import vstack, hstack, issparse, csr_matrix as sparse

from idx_gen import PG, QG
from idx_brch import F_BUS, T_BUS
from dSbr_dV import dSbr_dV
from d2AIbr_dV2 import d2AIbr_dV2
from d2Sbus_dV2 import d2Sbus_dV2
from dIbr_dV import dIbr_dV
from d2ASbr_dV2 import d2ASbr_dV2
from opf_costfcn import opf_costfcn
from opf_consfcn import opf_consfcn

def opf_hessfcn(x, lmbda, om, Ybus, Yf, Yt, ppopt, rh0, il=None):
    """Evaluates Hessian of Lagrangian for AC OPF.

    Hessian evaluation function for AC optimal power flow, suitable
    for use with L{pips}.

    Examples::
        Lxx = opf_hessfcn(x, lmbda, om, Ybus, Yf, Yt, ppopt)
        Lxx = opf_hessfcn(x, lmbda, om, Ybus, Yf, Yt, ppopt, il)
        Lxx = opf_hessfcn(x, lmbda, om, Ybus, Yf, Yt, ppopt, il, cost_mult)

    @param x: optimization vector
    @param lmbda: C{eqnonlin} - Lagrange multipliers on power balance
    equations. C{ineqnonlin} - Kuhn-Tucker multipliers on constrained
    branch flows.
    @param om: OPF model object
    @param Ybus: bus admittance matrix
    @param Yf: admittance matrix for "from" end of constrained branches
    @param Yt: admittance matrix for "to" end of constrained branches
    @param ppopt: PYPOWER options vector
    @param il: (optional) vector of branch indices corresponding to
    branches with flow limits (all others are assumed to be unconstrained).
    The default is C{range(nl)} (all branches). C{Yf} and C{Yt} contain
    only the rows corresponding to C{il}.
    @param cost_mult: (optional) Scale factor to be applied to the cost
    (default = 1).

    @return: Hessian of the Lagrangian.

    @see: L{opf_costfcn}, L{opf_consfcn}

    """

    ppc = om.get_ppc()
    baseMVA, bus, gen, branch = \
        ppc["baseMVA"], ppc["bus"], ppc["gen"], ppc["branch"]
    vv, _, _, _ = om.get_idx()

    ## unpack needed parameters
    nb = bus.shape[0]          ## number of buses
    nl = branch.shape[0]       ## number of branches
    ng = gen.shape[0]          ## number of dispatchable injections
    nxyz = len(x)              ## total number of control vars of all types

    ## set default constrained lines
    if il is None:
        il = arange(nl)            ## all lines have limits by default
    nl2 = len(il)           ## number of constrained lines

    ## grab Pg & Qg
    Pg = x[vv["i1"]["Pg"]:vv["iN"]["Pg"]]  ## active generation in p.u.
    Qg = x[vv["i1"]["Qg"]:vv["iN"]["Qg"]]  ## reactive generation in p.u.

    ## put Pg & Qg back in gen
    gen[:, PG] = Pg * baseMVA  ## active generation in MW
    gen[:, QG] = Qg * baseMVA  ## reactive generation in MVAr

    ## reconstruct V
    Va = x[vv["i1"]["Va"]:vv["iN"]["Va"]]
    Vm = x[vv["i1"]["Vm"]:vv["iN"]["Vm"]]
    V = Vm * exp(1j * Va)
    nxtra = nxyz - 2 * nb

    ## ----- evaluate d2f -----
    d2f_dv2 = sparse(rh0 * ones(2 * nb), (range(2 * nb), range(2 * nb), (2 * nb, nxyz)))
    blank_dv2 = sparse((2 * nb, 2 * ng))
    blank_dg2 = sparse((2 * ng, nxyz))
    # d2f = vstack([d2f_dv2, blank_dv2], "csr")
    d2f = hstack([d2f_dv2, blank_dg2], "csr")

    ##----- evaluate Hessian of power balance constraints -----
    nlam = int(len(lmbda["eqnonlin"]) / 2)
    lamP = lmbda["eqnonlin"][:nlam]
    lamQ = lmbda["eqnonlin"][nlam:nlam + nlam]
    Gpaa, Gpav, Gpva, Gpvv = d2Sbus_dV2(Ybus, V, lamP)
    Gqaa, Gqav, Gqva, Gqvv = d2Sbus_dV2(Ybus, V, lamQ)

    d2G = vstack([
            hstack([
                vstack([hstack([Gpaa, Gpav]),
                        hstack([Gpva, Gpvv])]).real +
                vstack([hstack([Gqaa, Gqav]),
                        hstack([Gqva, Gqvv])]).imag,
                sparse((2 * nb, nxtra))]),
            hstack([
                sparse((nxtra, 2 * nb)),
                sparse((nxtra, nxtra))
            ])
        ], "csr")

    ##----- evaluate Hessian of flow constraints -----
    nmu = int(len(lmbda["ineqnonlin"]) / 2)
    muF = lmbda["ineqnonlin"][:nmu]
    muT = lmbda["ineqnonlin"][nmu:nmu + nmu]
    if ppopt['OPF_FLOW_LIM'] == 2:       ## current
        dIf_dVa, dIf_dVm, dIt_dVa, dIt_dVm, If, It = dIbr_dV(branch, Yf, Yt, V)
        Hfaa, Hfav, Hfva, Hfvv = d2AIbr_dV2(dIf_dVa, dIf_dVm, If, Yf, V, muF)
        Htaa, Htav, Htva, Htvv = d2AIbr_dV2(dIt_dVa, dIt_dVm, It, Yt, V, muT)
    else:
        f = branch[il, F_BUS].astype(int)    ## list of "from" buses
        t = branch[il, T_BUS].astype(int)    ## list of "to" buses
        ## connection matrix for line & from buses
        Cf = sparse((ones(nl2), (arange(nl2), f)), (nl2, nb))
        ## connection matrix for line & to buses
        Ct = sparse((ones(nl2), (arange(nl2), t)), (nl2, nb))
        dSf_dVa, dSf_dVm, dSt_dVa, dSt_dVm, Sf, St = \
                dSbr_dV(branch[il,:], Yf, Yt, V)
        if ppopt['OPF_FLOW_LIM'] == 1:     ## real power
            Hfaa, Hfav, Hfva, Hfvv = d2ASbr_dV2(dSf_dVa.real, dSf_dVm.real,
                                                Sf.real, Cf, Yf, V, muF)
            Htaa, Htav, Htva, Htvv = d2ASbr_dV2(dSt_dVa.real, dSt_dVm.real,
                                                St.real, Ct, Yt, V, muT)
        else:                  ## apparent power
            Hfaa, Hfav, Hfva, Hfvv = \
                    d2ASbr_dV2(dSf_dVa, dSf_dVm, Sf, Cf, Yf, V, muF)
            Htaa, Htav, Htva, Htvv = \
                    d2ASbr_dV2(dSt_dVa, dSt_dVm, St, Ct, Yt, V, muT)

    d2H = vstack([
            hstack([
                vstack([hstack([Hfaa, Hfav]),
                        hstack([Hfva, Hfvv])]) +
                vstack([hstack([Htaa, Htav]),
                        hstack([Htva, Htvv])]),
                sparse((2 * nb, nxtra))
            ]),
            hstack([
                sparse((nxtra, 2 * nb)),
                sparse((nxtra, nxtra))
            ])
        ], "csr")

    ##-----  do numerical check using (central) finite differences  -----
    # if 0:
    #     nx = len(x)
    #     step = 1e-lamda10
    #
    #     num_d2G = sparse((nx, nx))
    #     num_d2H = sparse((nx, nx))
    #     for i in range(nx):
    #         xp = x
    #         xm = x
    #         xp[i] = x[i] + step / 2
    #         xm[i] = x[i] - step / 2
    #         # evaluate cost & gradients
    #         _, dfp = opf_costfcn(xp, om)
    #         _, dfm = opf_costfcn(xm, om)
    #         # evaluate constraints & gradients
    #         _, _, dHp, dGp = opf_consfcn(xp, om, Ybus, Yf, Yt, ppopt, il)
    #         _, _, dHm, dGm = opf_consfcn(xm, om, Ybus, Yf, Yt, ppopt, il)
    #
    #         num_d2G[:, i] = (dGp - dGm) * lmbda["eqnonlin"]   / step
    #         num_d2H[:, i] = (dHp - dHm) * lmbda["ineqnonlin"] / step
    #
    #     d2G_err = max(max(abs(d2G - num_d2G)))
    #     d2H_err = max(max(abs(d2H - num_d2H)))
    #
    #     if d2G_err > 1e-lamda10:
    #         print('Max difference in d2G: %g' % d2G_err)
    #     if d2H_err > 1e-6:
    #         print('Max difference in d2H: %g' % d2H_err)

    return d2f + d2G + d2H