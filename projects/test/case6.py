# Copyright (c) 1996-2015 PSERC. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Power flow data for 6 bus, 3 gen case from Wood & Wollenberg.
"""

from numpy import array

def case6():
    """Power flow data for 6 bus, 3 gen case from Wood & Wollenberg.
    Please see L{caseformat} for details on the case file format.

    This is the 6 bus example from pp. 104, 112, 119, 123-124, 549 of
    I{"Power Generation, Operation, and Control, 2nd Edition"},
    by Allen. J. Wood and Bruce F. Wollenberg, John Wiley & Sons, NY, Jan 1996.

    @return: Power flow data for 6 bus, 3 gen case from Wood & Wollenberg.
    """
    ppc = {"version": '2'}

    ##-----  Power Flow Data  -----##
    ## system MVA base
    ppc["baseMVA"] = 100.0

    ## bus data
    # bus_i type Pd Qd Gs Bs area Vm Va baseKV zone Vmax Vmin
    ppc["bus"] = array([
        [1, 3,  0,  0, 0, 0, 1, 1.05, 0, 230, 1, 1.05, 1.05],
        [2, 2,  0,  0, 0, 0, 1, 1.05, 0, 230, 1, 1.05, 0.95],
        [4, 1, 70, 70, 0, 0, 1, 1,    0, 230, 1, 1.05, 0.95],
        [5, 1, 70, 70, 0, 0, 1, 1,    0, 230, 1, 1.05, 0.95],
    ])

    ## generator data
    # bus, Pg, Qg, Qmax, Qmin, Vg, mBase, status, Pmax, Pmin, Pc1, Pc2,
    # Qc1min, Qc1max, Qc2min, Qc2max, ramp_agc, ramp_10, ramp_30, ramp_q, apf
    ppc["gen"] = array([
        [1, 0,  0, 100, -100, 1.05, 100, 1, 200, 50,   0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ])

    ## branch data
    # fbus, tbus, r, x, b, rateA, rateB, rateC, ratio, angle, status, angmin, angmax
    ppc["branch"] = array([
        [1, 2, 0.1,  0.2,  0.04, 40, 40, 40, 0, 0, 1, -360, 360],
        [1, 4, 0.05, 0.2,  0.04, 60, 60, 60, 0, 0, 1, -360, 360],
        [1, 5, 0.08, 0.3,  0.06, 40, 40, 40, 0, 0, 1, -360, 360],
    ])

    ##-----  OPF Data  -----##
    ## generator cost data
    # 1 startup shutdown n x1 y1 ... xn yn
    # 2 startup shutdown n c(n-1) ... c0
    ppc["gencost"] = array([
        [2, 0, 0, 3, 0.00533, 11.669, 213.1],
    ])

    return ppc