import pandapower.converter as pc

import pandapower.networks as pn

net = pn.create_cigre_network_mv(with_der=False)
print net

# print ppc["bus"]
# print ppc["gen"]
# print ppc["branch"]
print ppc["basekV"]