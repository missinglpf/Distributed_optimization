# Copyright (c) 1996-2015 PSERC. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Power flow data for 6 bus, 3 gen case from Wood & Wollenberg.
"""

from numpy import array

def case6ww():
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
    ppc["basekV"] = 230.0

    ## bus data
    # bus_i type Pd Qd Gs Bs area Vm Va baseKV zone Vmax Vmin
    ppc["bus"] = array([
        [0, 3,  0,  0, 0, 0, 1, 1, 0, 230, 1, 1.0, 1.0],
        [1, 2,  0,  0, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [2, 2,  0,  0, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [3, 1, 70, 70, 0, 0, 1, 1,    0, 230, 1, 1.1, 0.9],
        [4, 1, 70, 70, 0, 0, 1, 1,    0, 230, 1, 1.1, 0.9],
        [5, 1, 70, 70, 0, 0, 1, 1,    0, 230, 1, 1.1, 0.9]
    ])

    ## generator data
    # bus, Pg, Qg, Qmax, Qmin, Vg, mBase, status, Pmax, Pmin, Pc1, Pc2,
    # Qc1min, Qc1max, Qc2min, Qc2max, ramp_agc, ramp_10, ramp_30, ramp_q, apf
    ppc["gen"] = array([
        [0, 0,  0, 10000, -10000, 1.0, 100, 1, 20000, 50,   0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 62.74, 34.35, 10000, -10000, 1.0, 100, 1, 15000, 37.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 100.44, 108.49, 10000, -10000, 1.0, 100, 1, 18000, 45,   0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ])

    ## branch data
    # fbus, tbus, r, x, b, rateA, rateB, rateC, ratio, angle, status, angmin, angmax
    ppc["branch"] = array([
        [0, 3, 0.05, 0.2,  0.04, 1000, 1000, 1000, 0, 0, 1, -360, 360],
        [0, 4, 0.08, 0.3,  0.06, 4000, 4000, 4000, 0, 0, 1, -360, 360],
        [1, 3, 0.05, 0.1,  0.02, 1000, 1000, 1000, 0, 0, 1, -360, 360],
        [1, 4, 0.1,  0.3,  0.04, 1000, 1000, 1000, 0, 0, 1, -360, 360],
        [2, 4, 0.12, 0.26, 0.05, 1000, 1000, 1000, 0, 0, 1, -360, 360],
        [2, 5, 0.02, 0.1,  0.02, 1000, 1000, 1000, 0, 0, 1, -360, 360],
        [4, 5, 0.1,  0.3,  0.06, 4000, 4000, 4000, 0, 0, 1, -360, 360]
    ])

    ##-----  OPF Data  -----##
    ## generator cost data
    # 1 startup shutdown n x1 y1 ... xn yn
    # 2 startup shutdown n c(n-1) ... c0
    ppc["gencost"] = array([
        [2, 0, 0, 3, 0.00533, 11.669, 213.1],
        [2, 0, 0, 3, 0.00533, 11.669, 213.1],
        [2, 0, 0, 3, 0.00533, 11.669, 213.1]
    ])

    return ppc
