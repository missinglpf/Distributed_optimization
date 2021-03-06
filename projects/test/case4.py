# Copyright (c) 1996-2015 PSERC. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Power flow data for 4 bus, 2 gen case from Grainger & Stevenson.
"""

from numpy import array

def case4():
    ppc = {"version": '2'}

    ##-----  Power Flow Data  -----##
    ## system MVA base
    ppc["baseMVA"] = 100.0

    ## bus data
    # bus_i type Pd Qd Gs Bs area Vm Va baseKV zone Vmax Vmin
    ppc["bus"] = array([

        [0, 3, 50,  30.99,  0, 0, 1, 1, 0, 230, 1, 1.0, 1.0, 0,0, 0, 0],
        [1, 1, 170, 105.35, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9, 0, 0, 0, 0],
        [2, 1, 200, 123.94, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9, 0,0, 0, 0],
        [3, 2, 80,  49.58,  0, 0, 1, 1, 0, 230, 1, 1.1, 0.9, 0,0, 0, 0]
    ])

    ## generator data
    # bus, Pg, Qg, Qmax, Qmin, Vg, mBase, status, Pmax, Pmin, Pc1, Pc2,
    # Qc1min, Qc1max, Qc2min, Qc2max, ramp_agc, ramp_10, ramp_30, ramp_q, apf
    ppc["gen"] = array([
        [0, 0, 0, 1000, -1000, 1, 100, 1, 800, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 1000, -1000, 1, 100, 1, 318, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    ])

    ## branch data
    #fbus, tbus, r, x, b, rateA, rateB, rateC, ratio, angle, status, angmin, angmax
    ppc["branch"] = array([

        [0, 1, 0.01008, 0.0504, 0.1025, 2500, 2500, 2500, 0, 0, 1, -360, 360, 0,0, 0, 0, 0,0, 0, 0],
        [0, 2, 0.00744, 0.0372, 0.0775, 2500, 2500, 2500, 0, 0, 1, -360, 360, 0,0, 0, 0, 0,0, 0, 0],
        [1, 3, 0.00744, 0.0372, 0.0775, 2500, 2500, 2500, 0, 0, 1, -360, 360, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 3, 0.01272, 0.0636, 0.1275, 2500, 2500, 2500, 0, 0, 1, -360, 360, 0,0, 0, 0, 0,0, 0, 0]
    ])

    ppc["gencost"] = array([
        [2, 0, 0, 3, 0.00533, 11.669, 213.1],
        [2, 0, 0, 3, 0.00533, 11.669, 213.1],
    ])
    return ppc
