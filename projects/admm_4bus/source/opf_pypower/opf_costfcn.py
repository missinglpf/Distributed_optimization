from numpy import sum, array, ones, zeros, arange, r_, dot, flatnonzero as find, hstack, linalg, exp, vstack, hstack
from scipy.sparse import issparse, csr_matrix as sparse, lil_matrix
from idx_gen import GEN_BUS

def opf_costfcn(x, om, rho, nu, z, return_hessian=False):
    ##----- initialize -----

    ## unpack data
    ppc = om.get_ppc()
    baseMVA, bus, gen, branch = \
        ppc["baseMVA"], ppc["bus"], ppc["gen"], ppc["branch"]
    vv, _, _, _ = om.get_idx()

    ## problem dimensions
    nb = bus.shape[0]          ## number of buses
    nl = branch.shape[0]       ## number of branches
    ng = gen.shape[0]          ## number of dispatchable injections
    nxyz = len(x)              ## total number of control vars of all types

    Pg = x[vv["i1"]["Pg"]:vv["iN"]["Pg"]]
    Va = x[vv["i1"]["Va"]:vv["iN"]["Va"]]
    Vm = x[vv["i1"]["Vm"]:vv["iN"]["Vm"]]
    x = r_[Va, Vm]
    V = Vm * exp(1j * Va)
    f = sum(Pg) + float(dot(nu, x)) + float((rho/2) * (linalg.norm(x - z)**2))
    df_dv = nu + rho * (x - z)
    df_dg = ones(ng)
    blank = zeros(ng)
    df = r_[df_dv, df_dg, blank]

    if not return_hessian:
        return f, df
    d2f_dv2 = sparse(rho*ones(2*nb),(range(2*nb),range(2*nb), (2*nb, nxyz)))
    blank_dv2 = sparse((2*nb, 2*ng))
    blank_dg2 = sparse((2*ng, nxyz))
    # d2f = vstack([d2f_dv2, blank_dv2], "csr")
    d2f = hstack([d2f_dv2, blank_dg2], "csr")

    # d2f = sparse((nxyz,nxyz))

    return f, df, d2f

