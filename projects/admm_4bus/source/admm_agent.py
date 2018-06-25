import threading

import time
from concurrent import futures
import grpc
import admm_pb2
import admm_pb2_grpc
import admin_pb2
import admin_pb2_grpc
import json
from optparse import OptionParser
from acopf_nlopt_agent_run import ACopf_nlopt
from acopf_pips_agent import ACopf_pips
import os
import sys
import logging
import csv
import datetime
import re
from numpy import *
from ReadConfigFile import ReadConfiguration
import datetime
import urllib2
# sys.path.append('D:/phd/These_asys/source/nlopt_test/admm/opf_pypower')

# admm events
start_event = threading.Event()
all_beta_event = threading.Event()
all_z_event = threading.Event()
# prim_ctrl_finished_event = threading.Event()
# system events
agent_enabled_event = threading.Event()
# reconfiguration_event = threading.Event()

# system locks
measurement_lock = threading.Lock()  # manages the access to the measurement signals
references_lock = threading.Lock()  # manages the access to the reference signals
beta_lock = threading.Lock()  # manages the access to the beta & beta_received variables
z_lock = threading.Lock()  # manages the access to the z & z_received variables
x0_lock = threading.Lock()  # manages the access to the x0 variable

# the grpc server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))

# flag for stopping the agent
running = True

# variables for timing the performance of the agent
rpc_counter = 0
rpc_total_time = 0
opal_total_time = 0
opal_counter = 0
opt_total_time = 0
opt_counter = 0
trigger_counter = 0

# measurement signals of the agent
v_real_meas = 0.0
v_imag_meas = 0.0
p_meas = 0.0
q_meas = 0.0

# reference signals of the agent computed by the secondary control
p_ref = 0.0
q_ref = 0.0

# in case the communication with OPAL will have some errors, count them
opal_com_error_count = 0

# admin_ip = "169.254.35.100"
# admin_port = 8000
# MAX_ADMIN_COMM_RETRY = lamda10  # number of communication retries, in case of failing to contact the admin
# MAX_OPAL_COMM_RETRY = lamda10  # number of communication retries, in case of failing to contact OPAL-RT
# MEASUREMENTS_TO_ADMIN_DOWNSAMPLE = 500  # send to the admin each 500th measurement taken from OPAL-RT
# MEASUREMENTS_TO_NEIGH_DOWNSAMPLE = 20  # send to the neighbours each 20th measurement taken from OPAL-RT
# TRIGGER_SAMPLES = 50  # number of samples that have to meet a condition before taking any decision
# NON_TRIVIAL_DV = 0.001  # voltage deviation that is considered serious and that should trigger a system wide
#                         recalculation of set-points
# RAMP_TIME_OF_PRIMARY = 15.0  # apply the reference from the secondary control as a ramp lasting 15 seconds
DATA_LOG_PERIOD = 1  # write a line to the data_log_file every second

# global variables and price vectors for the ADMM algorithm. we keep the history of all the iterations
# for debugging reasons
admm_it = 0
admm_running = False
x = {}
beta = {}
z = {}
nu = {}
z_received = {}
beta_received = {}
x0 = []
lb = []
ub = []

class AgentServer(admm_pb2_grpc.ADMMAgentServicer):
    # ========================== Functions for the RPC server that can be called remotely
    # starts the admm algorithm
    def start_admm(self, request, context):
        try:
            # start_event.set()
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)
            # sets a beta value in the beta vector

    # function called by the neighbours to set their corresponding beta value in the beta vector
    def set_beta_element(self, request, context):
        try:
            set_local_beta_element(request.value_real, request.value_imag, request.agent_id, request.admm_it)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    # function called by the neighbours to set their corresponding z value in the z vector
    def set_z_element(self, request, context):
        try:
            set_local_z_element(request.value_real, request.value_imag, request.agent_id, request.admm_it)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    # set a x0 value in the x0 vector
    def set_x0_element(self, request, context):
        try:
            set_local_x0_element(request.value_real, request.value_imag, request.agent_id)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    # sets the step size for the admm algorithm
    def set_admm_rho(self, request, context):
        global config
        try:
            config.rho = request.value
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    # sets the number of iterations for the admm algorithm
    def set_admm_max_iter(self, request, context):
        global config
        try:
            config.max_iter = request.value
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    # function called by the administrator to set the configuration of the communication links
    def set_comm_link_to_neigh(self, request, context):
        try:
            # set_local_comm_link_to_neigh(request.neigh_id, request.delay, request.loss)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    def set_measurement_webserver(self, request, context):
        try:
            config.url_opal = "http://" + request.server_ip + ":" + str(request.server_port) + "/asyncsrv/"
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    # shuts down the agent remotely
    def remote_shutdown(self, request, context):
        global running
        try:
            running = False
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            logging.critical(exc.message)
            return admm_pb2.CommReply(status=admm_pb2.OperationStatus.Value('FAILED'), message=exc.message)

# def configure_comm_links():
#     if config.running_on_wireless:
#         device = "wlan0"
#     else:
#         device = "eth0"
#     config_script = "sudo tc qdisc del dev " + device + " root;" \
#                     "sudo tc qdisc add dev " + device + " handle 1: root htb;" \
#                     "sudo tc class add dev " + device + " parent 1: classid 1:1 htb rate 100Mbps;"
#     for p in config.partners:
#         tmpl = "sudo tc class add dev " + device + " parent 1:1 classid 1:1{0} htb rate 100Mbps;" \
#                "sudo tc qdisc add dev " + device + " parent 1:1{0} handle lamda10{0}: netem delay {3}s loss {4}%;" \
#                "sudo tc filter add dev " + device + " protocol ip parent 1:0 prio 3 u32 match ip dport {2} 0xffff match ip dst {1} flowid 1:1{0};"
#                                     # id, ip, port, delay, loss
#         config_script += tmpl.format(p[0], p[1], p[2], p[3], p[4])
#     #print(config_script)
#     os.system(config_script)

# def set_local_comm_link_to_neigh(neighbour, delay, loss):
#     if config.running_on_wireless:
#         device = "wlan0"
#     else:
#         device = "eth0"
#     for p in config.partners:
#         if p[0] == neighbour:
#             command = "sudo tc qdisc change dev " + device + " handle lamda10{0}: netem delay {1}s loss {2}%;".format(p[0], delay, loss)
#             os.system(command)

def pool_opal(agent_enabled_event):
    if not agent_enabled_event.isSet():
        logging.info("Waiting for the agent to be enabled")
    agent_enabled_event.wait()  # blocking call until the enable event is detected
    global opal_com_error_count
    global t_meas, v_meas, p_meas  # measurement signals
    # make access to shared resources thread safe
    key_p = "valout" + str(config.opal_get_ids["P"])
    key_q = "valout" + str(config.opal_get_ids["Q"])
    key_v = "valout" + str(config.opal_get_ids["V"])
    # compose the URL for the webserver
    get_url = config.url_opal + 'get?' + 'name0=' + key_p + '&' + 'name1=' + key_q + \
              '&' + 'name2=' + key_v

    req = urllib2.Request(url=get_url)
    try:
        tic = datetime.datetime.now()
        f = urllib2.urlopen(req, timeout=1)
        toc = datetime.datetime.now()
        response = f.read()
        delta = (toc - tic).total_seconds()
        get_opal_statistics(delta)
        d = json.loads(response)
        with measurement_lock:   # measurements are accessed from several threads, therefore they need to be protected
            p_meas = float(d[key_p])
            q_meas = float(d[key_q])
            v_meas = float(d[key_v])
            # test_if_secondary_control_should_start()
    except Exception as exc:
        opal_com_error_count += 1
        # if opal_com_error_count >= MAX_OPAL_COMM_RETRY:
            # notify_administrator("There seems to be a problem with the WEB-SERVER")
            # notify_administrator(exc.message)
            # opal_com_error_count = 0
        logging.critical(exc.message)

    # reschedule the function to start again
    t = threading.Timer(config.ts_opal, pool_opal, args=(agent_enabled_event,))
    t.name = "measurement-thread"
    t.daemon = True
    if running:
        t.start()

# set the initial voltage and power values in OPAL's web server
# ATTENTION! remember the sign change for the power reference. in opal the load power is with positive sign while in
# the optimization problem is with a negative sign
def init_opal():
    # set_url = config.url_opal + 'set?valin' + \
    #       str(config.opal_set_ids["P"]) + '=' + str(-config.opal_default_set["P"]) + \
    #       '&valin' + str(config.opal_set_ids["Q"]) + '=' + str(-config.opal_default_set["Q"])
    global p_ref, q_ref
    with references_lock:
        p_ref = config.opal_default_set["P"]
        q_ref = config.opal_default_set["Q"]
    # req = urllib2.Request(url=set_url)
    # f = urllib2.urlopen(req)
    # response = f.read()
    # if 'Ok' not in response:
    #     notify_administrator("Cannot set initial voltage & power references in OPAL-RT")

def get_optimization_statistics(delta):
    global opt_total_time, opt_counter
    opt_total_time += delta
    opt_counter += 1


def get_rpc_statistics(delta):
    global rpc_total_time, rpc_counter
    rpc_total_time += delta
    rpc_counter += 1

def get_opal_statistics(delta):
    global opal_total_time, opal_counter
    opal_total_time += delta
    opal_counter += 1
    # if opal_counter % MEASUREMENTS_TO_ADMIN_DOWNSAMPLE == 0:
    #     notify_administrator("measurements")

# ========================== ADMM Algorithm
def opf(all_beta_event, all_z_event):
    global admm_it, x, nu, x, z, admm_running, x0, config, lb, ub, v_gent, q_gen
    # while running:
    logging.debug('Waiting for admm_start event')
    # start_event.wait()  # blocking wait call until the event is detected
    admm_running = True
    # notify_administrator("admm_started")
    admm_it = 0
    for i in range(1, config.max_iter+1):
        # set the iteration number
        # admm step 1 - update the local variables
        # run the local optimization and compute the local variables
        logging.info(
            "Agent " + str(config.me[0][0]) + "========Solving ADMM iteration " + str(admm_it))
        # =========================non-linear approach=======================
        problem = ACopf_nlopt(x0, config.z_pk, config.z_qk, lb, ub, config.pd, config.qd,
                                 config.p_max, config.p_min, config.q_max, config.q_min, config.node_type,
                                 config.n, z[admm_it], nu[admm_it], config.rho)
        # ====================================================================
        # print(nu[admm_it],z[admm_it])
        # problem = ACopf_pips(x0, config.z_pk, config.z_qk, lb, ub, config.pd, config.qd,
        #                          config.p_max, config.p_min, config.q_max, config.q_min, config.node_type,
        #                          config.n, z[admm_it], nu[admm_it], config.rho)
        # ====================================================================
        tic = datetime.datetime.now()
        results = problem.solve_opf()
        toc = datetime.datetime.now()
        delta = (toc - tic).total_seconds()
        # print(delta)
        get_optimization_statistics(delta)
        xopt = results[0]
        logging.info(
            "Agent " + str(config.me[0][0]) + "========ADMM iteration " + str(admm_it) + " solved in " + str(delta)
            + " [s]")
        # save the local results of the optimization
        admm_it += 1
        x[admm_it] = xopt
        # compute the beta variable that is shared with the neighbours
        beta2distr = (1 / config.rho) * nu[admm_it-1] + xopt
        # admm step 2 - update the global variables
        # distribute the beta values to the neighbours
        distribute_beta(beta2distr)
        # wait to receive all the betas from the neighbours
        logging.info(" Waiting to receive all betas")
        all_beta_event.wait()
        # compute the z value corresponding to this agent
        z_real2distr = float(sum(beta[admm_it][0:config.n]) / float(config.n))
        z_imag2distr = float(sum(beta[admm_it][config.n:(2*config.n)]) / float(config.n))
        # distirbute the z value to the neighbours
        distribute_z(z_real2distr, z_imag2distr)
        # wait to receive all the z values from the neighbours
        logging.info(" Waiting to receive all z's")
        all_z_event.wait()
        # admm step 3 - update the lagrange multipliers
        nu[admm_it] = nu[admm_it - 1] + config.rho * (x[admm_it] - z[admm_it])
        data_snapshot_to_file(include_admm_data=True)
        all_beta_event.clear()
        all_z_event.clear()
    print(opt_total_time * 1000 / opt_counter)

    logging.info("Agent " + str(config.me[0][0]) + ": algorithm finished " + str(config.max_iter) + " iterations")
    admm_running = False
    idx = config.all_ids.index(config.me[0][0])
    x1 = asmatrix(x[admm_it])
    p = x1 * config.z_pk * x1.T + config.pd
    q = x1 * config.z_qk * x1.T + config.qd
    p_ref = float(p[idx])
    q_ref = float(q[idx])
    # notify_administrator("admm_finished")
    logging.info("Agent " + str(config.me[0][0]) + ": waiting for the primary to finish")
    # send_references_to_opal()
    # prim_ctrl_finished_event.wait()
    # re-initialize the buffers
    init_admm_buffers()
    start_event.clear()
    all_beta_event.clear()
    all_z_event.clear()
    # running = False

def set_local_beta_element(value_real, value_imag, agent_id, admm_it):
    idx = config.all_ids.index(agent_id)  # get the position in the vector where this value should go
    with beta_lock:
        try:
            if admm_it not in beta:
                beta[admm_it] = zeros(2*config.n, dtype=float_)
                beta_received[admm_it] = zeros(config.n, dtype=float_)
            beta[admm_it][idx] = value_real
            beta[admm_it][idx + config.n] = value_imag
            beta_received[admm_it][idx] = 1.0

            logging.debug("Agent " + str(config.me[0][0]) + ": Beta[" + str(admm_it) + "]=" + str(beta[admm_it]) +
                          "-> from Agent " + str(agent_id))
            # received all the information
            if sum(beta_received[admm_it]) == config.n:
                logging.info("Agent " + str(config.me[0][0]) + ": Received all beta info for iteration " +
                             str(admm_it) + ". Updating z.")
                all_beta_event.set()
        except KeyError as exc:
            logging.critical(
                "Agent " + str(config.me[0][0]) + ": WTFFF!!! Iteration:" + str(admm_it) + " Beta:" + str(beta))
            logging.critical(exc.message)

def distribute_beta(beta2distr):
    # distribute the beta variable
    # first locally
    # idx = config.all_ids.index(config.me[0])
    value_real = float(beta2distr[0])
    value_imag = float(beta2distr[config.n])
    set_local_beta_element(value_real, value_imag, config.me[0][0], admm_it)
    logging.info(" finish set local beta")
    # and then to the neighbours
    for p in config.partners:
        idx = config.all_ids.index(p[0])  # get the index of the neighbour
        value_real = float(beta2distr[idx])  # get the value of beta to be sent
        value_imag = float(beta2distr[idx + config.n])  # get the value of beta to be sent
        try:
            req = admm_pb2.SetBetaRequest(value_real=value_real, value_imag=value_imag, agent_id=config.me[0][0], admm_it=admm_it)
            tic = datetime.datetime.now()
            p[-1].set_beta_element(req)  # call RPC for each neighbour
            toc = datetime.datetime.now()
            delta = (toc - tic).total_seconds()
            get_rpc_statistics(delta)
        except Exception as exc:
            logging.critical(
                "Agent " + str(config.me[0][0]) + ": Can't contact agent " + str(p[0]) + " for setting beta = ")

            logging.exception(exc.message)
    logging.info("Agent " + str(config.me[0][0]) + ": I finished distributing all betas")

def distribute_z(z_real2distr, z_imag2distr):
    global rpc_total_time, rpc_counter
    # distribute the z variable
    # first locally
    set_local_z_element(z_real2distr, z_imag2distr, config.me[0][0], admm_it)
    # and then to the neighbours
    for p in config.partners:
        try:
            req = admm_pb2.SetZRequest(value_real=z_real2distr, value_imag=z_imag2distr, agent_id=config.me[0][0], admm_it=admm_it)
            tic = datetime.datetime.now()
            p[-1].set_z_element(req)
            toc = datetime.datetime.now()
            delta = (toc - tic).total_seconds()
            get_rpc_statistics(delta)
        except Exception as exc:
            logging.critical(
                "Agent " + str(config.me[0][0]) + ": can't contact agent " + str(p[0]) + " for setting z = ")
            logging.exception(exc.message)


def set_local_z_element(z_value_real, z_value_imag, agent_id, admm_it):
    try:
        idx = config.all_ids.index(agent_id)  # get the position in the vector where this value should go
        # access the z variable in a thread safe manner
        with z_lock:
            if admm_it not in z:
                z[admm_it] = zeros(2*config.n, dtype=float_)
                z_received[admm_it] = zeros(config.n, dtype=float_)
            z[admm_it][idx] = z_value_real
            z[admm_it][idx + config.n] = z_value_imag
            z_received[admm_it][idx] = 1.0
            logging.debug("Agent " + str(config.me[0][0]) + ": Z[" + str(admm_it) + "]=" + str(z[admm_it]))
            # received all the information
            if sum(z_received[admm_it]) == config.n:
                logging.info("Agent " + str(config.me[0][0]) + ": Received all z info for iteration " + str(
                        admm_it) + ". Updating nu.")
                all_z_event.set()
    except KeyError as exc:
        logging.critical(
            "Agent " + str(config.me[0][0]) + ": WTFFF!!! Iteration:" + str(admm_it) + " Z:" + str(z))
        logging.critical(exc.message)

def set_local_x0_element(x0_value, agent_id):
    global x0
    idx = config.all_ids.index(agent_id)
    with x0_lock:
        x0[idx] = x0_value
    logging.debug("Agent " + str(config.me[0][0]) + ": X0 = " + str(x0))


def init_admm_buffers():
    global admm_it, z, nu, x, beta, beta_received, z_received, x0, lb, ub

    if admm_it == 0:  # cold start of the ADMM
        logging.info("Agent " + str(config.me[0][0]) +
                     " initialized the ADMM buffers. First run. Populating first iteration with a cold start.")
        # global variables and price vectors for the ADMM algorithm. we keep the history of all the iterations
        # for debugging reasons
        z = {}
        nu = {}
        z[admm_it] = ones(2*config.n, dtype=float_) * 1.1
        nu[admm_it] = zeros(2*config.n, dtype=float_)
    else:  # warm start of the ADMM. Using the last values for nu and z
        logging.info("Agent " + str(config.me[0][0]) +
                     " re-initialized the ADMM buffers. Populating first iteration with a warm start")
        z_in = z[admm_it]
        nu_in = nu[admm_it]
        admm_it = 0
        z = {}
        nu = {}
        z[admm_it] = z_in
        nu[admm_it] = nu_in
    x = {}
    beta = {}
    z_received = {}
    beta_received = {}
    beta[admm_it] = zeros(2*config.n, dtype=float_)
    beta_received[admm_it] = zeros(config.n, dtype=float_)
    z_received[admm_it] = zeros(2*config.n, dtype=float_)
    x0 = ones(2*config.n, dtype=float_)
    x0[config.n:(2*config.n)] = zeros(config.n, dtype=float)
    lb = ones(2*config.n, dtype=float_) * (-1.1)
    ub = ones(2*config.n, dtype=float_) * 1.1
    if config.node_type == 3:
        lb[0] = 1.0
        ub [0] = 1.0 + 1e-5
        lb[config.n] = 0.0
        ub[config.n] = 0.0 + 1e-5

def data_snapshot_to_file(include_admm_data):
    global x, nu, z, admm_it, config
    try:
        if not os.path.isfile(dataFile):
            header = ['Id', 'Time', 'ADMM_IT']
            header += ['X_real']
            header += ['X_imag']
            header += ['Nu_real']
            header += ['Nu_imag']
            header += ['Z_real']
            header += ['Z_imag']
            header += ['P']
            header += ['Q']
            with open(dataFile, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(header)

        fields = []
        if include_admm_data:
            fields += [admm_it]
            # print(fields)
            fields += [x[admm_it][0]]
            # print(fields)
            fields += [x[admm_it][config.n]]
            fields += [nu[admm_it][0]]
            fields += [nu[admm_it][config.n]]
            fields += [z[admm_it][0]]
            fields += [z[admm_it][config.n]]
            # print('b')
            # P = V.*(G*V)
            # pz = np.multiply(z[admm_it], np.dot(config.G, z[admm_it]))
            x1 = asmatrix(x[admm_it])
            p = x1 * config.z_pk * x1.T + config.pd
            q = x1 * config.z_qk * x1.T + config.qd
            # print(p)
            # print(p[0,0])
            fields += [p[0,0]]
            fields += [q[0,0]]
            # print(fields)

        else:
            fields += [0] * 9  # add zeros to the file in order to create a consistent .csv table
        with open(dataFile, 'a') as f:
            writer = csv.writer(f)
            time_stamp = time.time()
            line = [config.me[0][0], time_stamp]
            line += ['{:3.4f}'.format(xval) for xval in fields]
            writer.writerow(line)
    except Exception as ex:
        print(ex.message)

def log_experiment_data_loop():
    # if not admm_running:
    #     data_snapshot_to_file(include_admm_data=False)
    t = threading.Timer(DATA_LOG_PERIOD, log_experiment_data_loop)
    t.daemon = True
    t.name = "log-thread"
    # logging.info("log thread")
    if running:
        t.start()

# def send_references_to_opal():
#     global p_ref, q_ref, z
#     # change the references only if you are a generator. don't forget about the sign change for the power
#     if config.node_type > 1:
#         set_url = config.url_opal + 'set?valin' + \
#                   str(config.opal_set_ids["P"]) + '=' + str(-p_ref) + '&valin' + \
#                   str(config.opal_set_ids["Q"]) + '=' + str(-q_ref)
#         req = urllib2.Request(url=set_url)
#         f = urllib2.urlopen(req)
#         response = f.read()
        # if 'Ok' not in response:
        #     notify_administrator("Cannot send the new references to the OPAL-RT")
    # notify the secondary when the primary is finished ramping towards the new reference
    # time.sleep(RAMP_TIME_OF_PRIMARY)  # just wait the amount of time required by the primary
                                      # in a real system the primary would notify the secondary when done
    # prim_ctrl_finished_event.set()  # notify the secondary

# ========================== Functions for communicating with the administrator and data logging
# handles the communication with the administrator
# def notify_administrator(topic):
#     comm_error_count = 0
#     while comm_error_count < MAX_ADMIN_COMM_RETRY:
#         try:
#             if topic is "online":
#                 req = admin_pb2.AgentRequest(agent_id=config.me[0])
#                 admin_stub.agent_online(req)
#             elif topic is "offline":
#                 req = admin_pb2.AgentRequest(agent_id=config.me[0])
#                 admin_stub.agent_offline(req)
#             elif topic is "admm_started":
#                 req = admin_pb2.AgentRequest(agent_id=config.me[0])
#                 admin_stub.agent_started_admm(req)
#             elif topic is "admm_finished":
#                 req = admin_pb2.ADMMResults(agent_id=config.me[0], avg_opt_time = opt_total_time * 1000 / opt_counter,
#                                             avg_rpc_time=rpc_total_time * 1000 / rpc_counter, v_ref=v_ref, p_ref = p_ref)
#                 admin_stub.agent_finished_admm(req)
#             elif topic is "measurements":
#                 req = admin_pb2.Measurements(agent_id=config.me[0], avg_opal_time=opal_total_time * 1000 / opal_counter,
#                                              v_meas=v_meas, p_meas=p_meas, trip=t_meas)
#                 admin_stub.agent_measurements(req)
#             else:  # if topic not in list send a general message to the admin
#                 req = admin_pb2.GenericMessage(agent_id=config.me[0], text=topic)
#                 admin_stub.agent_general_use_message(req)
#             break
#         except Exception as exc:
#             logging.error("Agent " + str(config.me[0]) + ": Can't contact the administrator for sending data")
#             comm_error_count += 1
#             if comm_error_count >= MAX_ADMIN_COMM_RETRY:
#                 logging.critical("Agent " + str(config.me[0]) + ": Something is definetly wrong. ABORTING!")
#                 logging.exception(exc.message)
#             else:
#                 logging.info(
#                     "Agent " + str(config.me[0]) + ": The communication might be busy. I will retry in lamda10 ms!")
#                 time.sleep(0.01)


# def data_snapshot_to_file(include_admm_data):
#     global x, nu, z, admm_it
#     try:
#         if not os.path.isfile(dataFile):
#             header = ['Id', 'Time', 'P_meas', 'V_meas', 'P_ref', 'V_ref', 'ADMM_IT']
#             header += ['X_' + str(el) for el in config.all_ids]
#             header += ['Nu_' + str(el) for el in config.all_ids]
#             header += ['Z_' + str(el) for el in config.all_ids]
#             header += ['Pz_' + str(el) for el in config.all_ids]
#             with open(dataFile, 'w') as f:
#                 writer = csv.writer(f)
#                 writer.writerow(header)
#
#         fields = [p_meas, v_meas, p_ref, q_ref]
#         if include_admm_data:
#             fields += [admm_it]
#             fields += x[admm_it].tolist()
#             fields += nu[admm_it].tolist()
#             fields += z[admm_it].tolist()
#             # P = V.*(G*V)
#             pz = np.multiply(z[admm_it], np.dot(config.G, z[admm_it]))
#             fields += [pz_i * (-1) for pz_i in pz.tolist()]
#         else:
#             fields += [0] * (
#                 1 + 4 * config.n)  # add zeros to the file in order to create a consistent .csv table
#         with open(dataFile, 'a') as f:
#             writer = csv.writer(f)
#             time_stamp = time.time()
#             line = [config.me[0], time_stamp]
#             line += ['{:3.4f}'.format(xval) for xval in fields]
#             writer.writerow(line)
#     except Exception as ex:
#         # notify_administrator(ex.message)
#         pass


def log_experiment_data_loop():
    # if not agent_enabled_event.isSet():
    #     logging.info("Waiting for the agent to be enabled")
    # agent_enabled_event.wait()
    if not admm_running:
        data_snapshot_to_file(include_admm_data=False)
    t = threading.Timer(DATA_LOG_PERIOD, log_experiment_data_loop)
    t.daemon = True
    t.name = "log-thread"
    if running:
        t.start()

optp = OptionParser()
optp.add_option("-f", "--filename", dest="jsonFile",
                help="json file containing the configuration of the agent")
opts, args = optp.parse_args()
if opts.jsonFile is None:
    opts.jsonFile = raw_input("Name of the json file containing the configuration of the agent:")

log = "../logs/sixbus/log_A_" + re.search(r'\d+', opts.jsonFile).group() + ".txt"
print log
dataFile = "../data/sixbus/lamda30/data_A_" + re.search(r'\d+', opts.jsonFile).group() + ".csv"
print dataFile
# log to file
print log
logging.basicConfig(level=logging.DEBUG,  filename=log, filemode="w",
                    format='%(asctime)s (%(threadName)-9s) %(levelname)s: %(message)s')

logging.info("Reading the configuration file")
# read the configuration of the agent
# print(opts.jsonFile)
config = ReadConfiguration(opts.jsonFile)

logging.info("Setting the initial values in OPAL-RT")
# set the voltage in the opal
# init_opal()

logging.info("Configuring the communication links")
# configure the communication links
# configure_comm_links()

logging.info("Initializing the ADMM buffers")
# initialize the ADMM buffers
init_admm_buffers()

logging.info("Opening communication channels to neighbours")
# open communication channels towards the neighbours
for p in config.partners:
    channel = grpc.insecure_channel(p[1] + ":" + str(p[2]))
    stub = admm_pb2_grpc.ADMMAgentStub(channel)
    p += [stub]  # store the rpc stub in the config.partners collection

# logging.info("Opening the communication channels to the admin")
# open the communication channel to the admin
# admin_channel = grpc.insecure_channel(admin_ip + ":" + str(admin_port))
# admin_stub = admin_pb2_grpc.AdminStub(channel=admin_channel)

# logging.info("Starting the measurement thread")
# configure and start the program threads
# meas_thread = threading.Thread(name='measurement-thread', target=pool_opal, args=(agent_enabled_event,))
# meas_thread.daemon = True
# meas_thread.start()  # start the measurement thread

logging.info("Starting the data loging thread")
log_thread = threading.Thread(name='log-thread', target=log_experiment_data_loop)
log_thread.daemon = True
log_thread.start()  # start the log thread

logging.info("Starting the opf thread")
admm_ctrl_thread = threading.Thread(name='opf-thread', target=opf,
                               args=(all_beta_event, all_z_event))
admm_ctrl_thread.daemon = True
admm_ctrl_thread.start()  # start the admm thread

# create the RPC server for the agent
logging.info("Starting the agent's RPC server")
admm_pb2_grpc.add_ADMMAgentServicer_to_server(AgentServer(), server)
server.add_insecure_port(config.me[0][1] + ":" + str(config.me[0][2]))
server.start()
logging.info("Agent " + str(config.me[0][0]) + " starting at:" + config.me[0][1] + ":" + str(config.me[0][2]))

# notify the administrator that I am online
# notify_administrator("online")
# time.sleep(lamda10)

while running:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        running = False

# notify_administrator("offline")
server.stop(0)