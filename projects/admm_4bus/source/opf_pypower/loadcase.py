import sys

from os.path import basename, splitext, exists

from copy import deepcopy

from numpy import array, zeros, ones, c_

from scipy.io import loadmat
from _compat import PY2
from case import case

if not PY2:
    basestring = str


def loadcase(casefile):
    rootname = casefile

    extension = '.py'
    fname = basename(rootname)
    try:
        if PY2:
            execfile(rootname + extension)
        else:
            exec(compile(open(rootname + extension).read(),
                                     rootname + extension, 'exec'))
        try:                      ## assume it returns an object
            s = eval(fname)()
        except ValueError as e:
            print(str(e))
        s = {}
        try:
            s['baseMVA'], s['bus'], s['gen'], s['branch'] = eval(fname)()
        except IOError as e:
            print(str(e))
    except IOError as e:
        print(str(e))
    ppc = deepcopy(s)

    return ppc

ppc=case

