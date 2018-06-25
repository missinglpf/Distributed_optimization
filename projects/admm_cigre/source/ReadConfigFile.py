import json
from numpy import *


class ReadConfiguration:

    def __init__(self, file_name):
        with open(file_name) as json_data:
            d = json.load(json_data)
            # id, ip and port of this agent
            self.me = d["me"]
            # id, ip, port, delay, and packet loss of communication partners
            self.partners = d["partners"]

            # all ids
            self.all_ids = [row[0] for row in (self.me + self.partners)]
            # self.all_ids.append(self.me[0])
            # self.all_ids.sort()
            print(self.all_ids)
            self.my_idx = self.all_ids.index(self.me[0][0])
            # time step for pooling opal rt
            self.ts_opal = d["ts_opal"]
            # the url for the opal websrv
            self.url_opal = d["url_opal"]
            # the ids of the variables that the agent gets from OPAL RT
            self.opal_get_ids = d["opal_get_ids"]
            # the ids of the variables that the agent sets in OPAL RT
            self.opal_set_ids = d["opal_set_ids"]
            # the default values to set in OPAL RT at the beginning of the session
            self.opal_default_set = d["opal_default_set"]

            # the base power for the system
            self.s_base = d["s_base"]

            # the base voltage for the system
            self.v_base = d["v_base"]
            # local variables of the agent:
            # conductantce matrix
            # this could be dynamically built based on information from the breakers by adding additional
            # variables in the opal web server. To take into consideration for next version.
            self.z_pk = array(d["z_pk"], float_)
            self.z_qk = array(d["z_qk"], float_)

            # self.P = zeros(self.G.shape)
            # self.P[self.my_idx, :] = self.G[self.my_idx, :] / 2
            # self.P[:, self.my_idx] = self.G[:, self.my_idx] / 2
            # self.P[self.my_idx, self.my_idx] *= 2
            # node type: 1 = load 2 = generator 3 = slack
            self.node_type = d["node_type"]
            # number of neighbors
            self.n = len(self.all_ids)
            # p load
            self.pd = d["p_d"]
            # q load
            self.qd = d["q_d"]
            # p gen max
            self.p_max = d["p_max"]
            # p gen min
            self.p_min = d["p_min"]
            # q gen max
            self.q_max = d["q_max"]
            # q gen min
            self.q_min = d["q_min"]
            # voltage constraints
            self.v_min = d["v_min"]
            self.v_max = d["v_max"]  # this can be dynamically built using the methods proposed in my thesis
            self.v_nom = d["v_nom"]
            # ADMM step
            self.rho = d["rho"]
            # maximum number of admm iterations
            self.max_iter = d["max_iter"]
            # number of constraints. Always an equality or an inequality constraint
            # self.m = 1
