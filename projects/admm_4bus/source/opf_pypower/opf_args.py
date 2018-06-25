# Copyright (c) 1996-2015 PSERC. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

"""Parses and initializes OPF input arguments.
"""

from sys import stderr

from numpy import array
from scipy.sparse import issparse

from _compat import PY2
from ppoption import ppoption
from loadcase import loadcase


if not PY2:
    basestring = str


def opf_args(casefile):
    """Parses and initializes OPF input arguments.

    Returns the full set of initialized OPF input arguments, filling in
    default values for missing arguments. See Examples below for the
    possible calling syntax options.

    Input arguments options::

        opf_args(ppc)
        opf_args(ppc, ppopt)
        opf_args(ppc, userfcn, ppopt)
        opf_args(ppc, A, l, u)
        opf_args(ppc, A, l, u, ppopt)
        opf_args(ppc, A, l, u, ppopt, N, fparm, H, Cw)
        opf_args(ppc, A, l, u, ppopt, N, fparm, H, Cw, z0, zl, zu)

        opf_args(baseMVA, bus, gen, branch, areas, gencost)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, ppopt)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, userfcn, ppopt)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, A, l, u)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, A, l, u, ppopt)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, A, l, u, ...
                                    ppopt, N, fparm, H, Cw)
        opf_args(baseMVA, bus, gen, branch, areas, gencost, A, l, u, ...
                                    ppopt, N, fparm, H, Cw, z0, zl, zu)

    The data for the problem can be specified in one of three ways:
      1. a string (ppc) containing the file name of a PYPOWER case
      which defines the data matrices baseMVA, bus, gen, branch, and
      gencost (areas is not used at all, it is only included for
      backward compatibility of the API).
      2. a dict (ppc) containing the data matrices as fields.
      3. the individual data matrices themselves.

    The optional user parameters for user constraints (C{A, l, u}), user costs
    (C{N, fparm, H, Cw}), user variable initializer (z0), and user variable
    limits (C{zl, zu}) can also be specified as fields in a case dict,
    either passed in directly or defined in a case file referenced by name.

    When specified, C{A, l, u} represent additional linear constraints on the
    optimization variables, C{l <= A*[x z] <= u}. If the user specifies an C{A}
    matrix that has more columns than the number of "C{x}" (OPF) variables,
    then there are extra linearly constrained "C{z}" variables. For an
    explanation of the formulation used and instructions for forming the
    C{A} matrix, see the MATPOWER manual.

    A generalized cost on all variables can be applied if input arguments
    C{N}, C{fparm}, C{H} and C{Cw} are specified.  First, a linear
    transformation of the optimization variables is defined by means of
    C{r = N * [x z]}. Then, to each element of r a function is applied as
    encoded in the C{fparm} matrix (see Matpower manual). If the resulting
    vector is named C{w}, then C{H} and C{Cw} define a quadratic cost on
    C{w}: C{(1/2)*w'*H*w + Cw * w}.
    C{H} and C{N} should be sparse matrices and C{H} should also be symmetric.

    The optional C{ppopt} vector specifies PYPOWER options. See L{ppoption}
    for details and default values.

    @author: Ray Zimmerman (PSERC Cornell)
    @author: Carlos E. Murillo-Sanchez (PSERC Cornell & Universidad
    Autonoma de Manizales)
    """
#    nargin = len([arg for arg in [baseMVA, bus, gen, branch, areas, gencost,
#                                  Au, lbu, ubu, ppopt, N, fparm, H, Cw,
#                                  z0, zl, zu] if arg is not None])



    ## passing filename or dict

    if isinstance(casefile, dict):
        zu    = array([])
        zl    = array([])
        z0    = array([])
        Cw    = array([])
        H     = None
        fparm = array([])
        N     = None
        ppopt = ppoption()
        ubu   = array([])
        lbu   = array([])
        Au    = None


        ppc = casefile
        baseMVA, bus, gen, branch = \
            ppc['baseMVA'], ppc['bus'], ppc['gen'], ppc['branch']
        return baseMVA, bus, gen, branch, ppopt
    else:
        stderr.write('opf_args: Incorrect input arg order, number or type\n')
        return array([]), array([]), array([]), array([]), array([])

def opf_args2(casefile):
    """Parses and initializes OPF input arguments.
    """
    baseMVA, bus, gen, branch, ppopt = opf_args(casefile)

    ppc = {}

    ppc['baseMVA'] = baseMVA
    ppc['bus'] = bus
    ppc['gen'] = gen
    ppc['branch'] = branch

    return ppc, ppopt
