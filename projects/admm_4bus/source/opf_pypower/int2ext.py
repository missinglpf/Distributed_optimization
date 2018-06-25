import sys

from copy import deepcopy

from idx_bus import BUS_I
from idx_gen import GEN_BUS
from idx_brch import F_BUS, T_BUS

def int2ext(ppc):
    ppc = deepcopy(ppc)
    o = ppc["order"]

    ## save data matrices with internal ordering & restore originals
    o["int"] = {}
    o["int"]["bus"] = ppc["bus"].copy()
    o["int"]["branch"] = ppc["branch"].copy()
    o["int"]["gen"] = ppc["gen"].copy()
    ppc["bus"] = o["ext"]["bus"].copy()
    ppc["branch"] = o["ext"]["branch"].copy()
    ppc["gen"] = o["ext"]["gen"].copy()

    ## update data (in bus, branch and gen only)
    ppc["bus"][o["bus"]["status"]["on"], :] = \
        o["int"]["bus"]
    ppc["branch"][o["branch"]["status"]["on"], :] = \
        o["int"]["branch"]
    ppc["gen"][o["gen"]["status"]["on"], :] = \
        o["int"]["gen"][o["gen"]["i2e"], :]

    ## revert to original bus numbers
    ppc["bus"][o["bus"]["status"]["on"], BUS_I] = \
        o["bus"]["i2e"] \
            [ppc["bus"][o["bus"]["status"]["on"], BUS_I].astype(int)]
    ppc["branch"][o["branch"]["status"]["on"], F_BUS] = \
        o["bus"]["i2e"][ppc["branch"] \
            [o["branch"]["status"]["on"], F_BUS].astype(int)]
    ppc["branch"][o["branch"]["status"]["on"], T_BUS] = \
        o["bus"]["i2e"][ppc["branch"] \
            [o["branch"]["status"]["on"], T_BUS].astype(int)]
    ppc["gen"][o["gen"]["status"]["on"], GEN_BUS] = \
        o["bus"]["i2e"][ppc["gen"] \
            [o["gen"]["status"]["on"], GEN_BUS].astype(int)]

    o["state"] = 'e'
    ppc["order"] = o

    return ppc

def int2ext1(i2e, bus, gen, branch):
    """Converts from the consecutive internal bus numbers back to the originals
    using the mapping provided by the I2E vector returned from C{ext2int}.

    @see: L{ext2int}
    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    bus[:, BUS_I]    = i2e[ bus[:, BUS_I].astype(int) ]
    gen[:, GEN_BUS]  = i2e[ gen[:, GEN_BUS].astype(int) ]
    branch[:, F_BUS] = i2e[ branch[:, F_BUS].astype(int) ]
    branch[:, T_BUS] = i2e[ branch[:, T_BUS].astype(int) ]

    return bus, gen, branch