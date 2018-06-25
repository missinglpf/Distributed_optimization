from sys import stdout, stderr

from numpy import array, any, delete, unique, arange, nonzero, pi, \
    r_, ones, Inf
from numpy import flatnonzero as find

from scipy.sparse import hstack, csr_matrix as sparse

from opf_model import opf_model
from opf_args import opf_args
from idx_bus import BUS_TYPE, REF, VA, VM, PD, GS, VMAX, VMIN
from idx_gen import GEN_BUS, VG, PG, QG, PMAX, PMIN, QMAX, QMIN
from idx_brch import RATE_A

def opf_setup(ppc, ppopt):
    ## options



    ## data dimensions
    nb = ppc['bus'].shape[0]    ## number of buses
    nl = ppc['branch'].shape[0] ## number of branches
    ng = ppc['gen'].shape[0]    ## number of dispatchable injections

    ## create (read-only) copies of individual fields for convenience
    baseMVA, bus, gen, branch, ppopt = opf_args(ppc)

    ## warn if there is more than one reference bus
    refs = find(bus[:, BUS_TYPE] == REF)
    if len(refs) > 1:
        errstr = '\nopf_setup: Warning: Multiple reference buses.\n' + \
            '           For a system with islands, a reference bus in each island\n' + \
            '           may help convergence, but in a fully connected system such\n' + \
            '           a situation is probably not reasonable.\n\n'
        stdout.write(errstr)

    ## set up initial variables and bounds
    gbus = gen[:, GEN_BUS].astype(int)
    Va   = bus[:, VA] * (pi / 180.0)
    Vm   = bus[:, VM].copy()
    Vm[gbus] = gen[:, VG]   ## buses with gens, init Vm from gen data
    Pg   = gen[:, PG] / baseMVA
    Qg   = gen[:, QG] / baseMVA
    Pmin = gen[:, PMIN] / baseMVA
    Pmax = gen[:, PMAX] / baseMVA
    Qmin = gen[:, QMIN] / baseMVA
    Qmax = gen[:, QMAX] / baseMVA

    ## more problem dimensions
    nv    = nb           ## number of voltage magnitude vars
    nq    = ng           ## number of Qg vars

    user_vars = ['Va', 'Vm', 'Pg', 'Qg']
    ycon_vars = ['Pg', 'Qg', 'y']

    ## voltage angle reference constraints
    Vau = Inf * ones(nb)
    Val = -Vau
    Vau[refs] = Va[refs]
    Val[refs] = Va[refs]

    ## more problem dimensions
    nx = nb+nv + ng+nq;  ## number of standard OPF control variables

    ## construct OPF model object
    om = opf_model(ppc)

    om.add_vars('Va', nb, Va, Val, Vau)
    om.add_vars('Vm', nb, Vm, bus[:, VMIN], bus[:, VMAX])
    om.add_vars('Pg', ng, Pg, Pmin, Pmax)
    om.add_vars('Qg', ng, Qg, Qmin, Qmax)
    om.add_constraints('Pmis', nb, 'nonlinear')
    om.add_constraints('Qmis', nb, 'nonlinear')
    om.add_constraints('Sf', nl, 'nonlinear')
    om.add_constraints('St', nl, 'nonlinear')

    return om