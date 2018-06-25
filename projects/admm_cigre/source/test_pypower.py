from pypower.api import *
from cigre_matrix import cigre_matrix
import pandapower.converter as pc

import pandapower.networks as pn

ppc = cigre_matrix()
# net = pn.create_cigre_network_mv(with_der="all")
# ppc = pc.to_ppc(net)
OPF_OPTIONS = ['opf_alg', 0, 'opf_violation', 5e-6,'opf_ignore_ang_lim', True]
# opt = ppoption(OPF_OPTIONS)
opt = ppoption(PF_ALG=2, PF_TOL=1e-4)
opt = ppoption(opt, OPF_ALG=565, VERBOSE=2, OPF_TOL=1e-4, OPF_IGNORE_ANG_LIM=True)
results = runpf(ppc, ppopt=opt)
results = runopf(ppc, ppopt=opt)
# help(runopf)
print results["x"]