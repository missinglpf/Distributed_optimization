from pypower.api import *
from case6ww import case6ww

ppc = case6ww()
results = runopf(ppc)



