import sys

from copy import deepcopy

from numpy import array, zeros, argsort, arange, concatenate
from numpy import flatnonzero as find
from scipy.sparse import issparse, vstack, hstack, csr_matrix as sparse

from idx_bus import PQ, PV, REF, NONE, BUS_I, BUS_TYPE
from idx_gen import GEN_BUS, GEN_STATUS
from idx_brch import F_BUS, T_BUS, BR_STATUS

def ext2int(ppc):
    ppc = deepcopy(ppc)
    o = {
        'ext': {
            'bus': None,
            'branch': None,
            'gen': None
        },
        'bus': {'e2i': None,
                'i2e': None,
                'status': {}},
        'gen': {'e2i': None,
                'i2e': None,
                'status': {}},
        'branch': {'status': {}}
    }
    nb = ppc["bus"].shape[0]
    ng = ppc["gen"].shape[0]
    ng0 = ng
    o["ext"]["bus"] = ppc["bus"].copy()
    o["ext"]["branch"] = ppc["branch"].copy()
    o["ext"]["gen"] = ppc["gen"].copy()

    ## check that all buses have a valid BUS_TYPE
    bt = ppc["bus"][:, BUS_TYPE]
    err = find(~((bt == PQ) | (bt == PV) | (bt == REF) | (bt == NONE)))
    if len(err) > 0:
        sys.stderr.write('ext2int: bus %d has an invalid BUS_TYPE\n' % err)

    ## determine which buses, branches, gens are connected and
    ## in-service
    n2i = sparse((range(nb), (ppc["bus"][:, BUS_I], zeros(nb))),
                 shape=(max(ppc["bus"][:, BUS_I]) + 1, 1))
    n2i = array(n2i.todense().flatten())[0, :]  # as 1D array
    bs = (bt != NONE)  ## bus status
    o["bus"]["status"]["on"] = find(bs)  ## connected
    o["bus"]["status"]["off"] = find(~bs)  ## isolated
    gs = ((ppc["gen"][:, GEN_STATUS] > 0) &  ## gen status
          bs[n2i[ppc["gen"][:, GEN_BUS].astype(int)]])
    o["gen"]["status"]["on"] = find(gs)  ## on and connected
    o["gen"]["status"]["off"] = find(~gs)  ## off or isolated
    brs = (ppc["branch"][:, BR_STATUS].astype(int) &  ## branch status
           bs[n2i[ppc["branch"][:, F_BUS].astype(int)]] &
           bs[n2i[ppc["branch"][:, T_BUS].astype(int)]]).astype(bool)
    o["branch"]["status"]["on"] = find(brs)  ## on and conn
    o["branch"]["status"]["off"] = find(~brs)

    ## delete stuff that is "out"
    if len(o["bus"]["status"]["off"]) > 0:
        #                ppc["bus"][o["bus"]["status"]["off"], :] = array([])
        ppc["bus"] = ppc["bus"][o["bus"]["status"]["on"], :]
    if len(o["branch"]["status"]["off"]) > 0:
        #                ppc["branch"][o["branch"]["status"]["off"], :] = array([])
        ppc["branch"] = ppc["branch"][o["branch"]["status"]["on"], :]
    if len(o["gen"]["status"]["off"]) > 0:
        #                ppc["gen"][o["gen"]["status"]["off"], :] = array([])
        ppc["gen"] = ppc["gen"][o["gen"]["status"]["on"], :]

    ## update size
    nb = ppc["bus"].shape[0]

    ## apply consecutive bus numbering
    o["bus"]["i2e"] = ppc["bus"][:, BUS_I].copy()
    o["bus"]["e2i"] = zeros(max(o["bus"]["i2e"]).astype(int) + 1)
    o["bus"]["e2i"][o["bus"]["i2e"].astype(int)] = arange(nb)
    ppc["bus"][:, BUS_I] = \
        o["bus"]["e2i"][ppc["bus"][:, BUS_I].astype(int)].copy()
    ppc["gen"][:, GEN_BUS] = \
        o["bus"]["e2i"][ppc["gen"][:, GEN_BUS].astype(int)].copy()
    ppc["branch"][:, F_BUS] = \
        o["bus"]["e2i"][ppc["branch"][:, F_BUS].astype(int)].copy()
    ppc["branch"][:, T_BUS] = \
        o["bus"]["e2i"][ppc["branch"][:, T_BUS].astype(int)].copy()

    ## reorder gens in order of increasing bus number
    o["gen"]["e2i"] = argsort(ppc["gen"][:, GEN_BUS])
    o["gen"]["i2e"] = argsort(o["gen"]["e2i"])

    ppc["gen"] = ppc["gen"][o["gen"]["e2i"].astype(int), :]

    if 'int' in o:
        del o['int']
    o["state"] = 'i'
    ppc["order"] = o

    return ppc

def ext2int1(bus, gen, branch):
    """Converts from (possibly non-consecutive) external bus numbers to
    consecutive internal bus numbers which start at 1. Changes are made
    to BUS, GEN, BRANCH and optionally AREAS matrices, which are returned
    along with a vector of indices I2E that can be passed to INT2EXT to
    perform the reverse conversion.

    @see: L{int2ext}
    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    i2e = bus[:, BUS_I].astype(int)
    e2i = zeros(max(i2e) + 1)
    e2i[i2e] = arange(bus.shape[0])

    bus[:, BUS_I]    = e2i[ bus[:, BUS_I].astype(int)    ]
    gen[:, GEN_BUS]  = e2i[ gen[:, GEN_BUS].astype(int)  ]
    branch[:, F_BUS] = e2i[ branch[:, F_BUS].astype(int) ]
    branch[:, T_BUS] = e2i[ branch[:, T_BUS].astype(int) ]

    return i2e, bus, gen, branch