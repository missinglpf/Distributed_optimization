#!/usr/bin/python
import sys
import re
import json
from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, \
    QHBoxLayout, QTableWidget, QTextEdit, QLineEdit, QTabWidget, QTableWidgetItem
import matplotlib
import os
import datetime
import csv


# Make sure that we are using QT5
matplotlib.use('Qt5Agg')
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
# from CustomStanzas import ADMMStepOverview
# from sleekxmpp import Iq, jid
# from sleekxmpp.xmlstream import register_stanza_plugin
# from sleekxmpp.xmlstream.handler import Callback
# from sleekxmpp.xmlstream.matcher import StanzaPath
# import sleekxmpp
import scipy.io
import argparse
import shlex
import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import SocketServer
import xmlrpclib
from socket import error as socket_error


import numpy as np


class OutputWindow(QTextEdit):
    def write(self, txt):
        self.insertPlainText(str(txt))
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


class ArgumentParserError(Exception): pass


class CommandParser(argparse.ArgumentParser):
    def __init__(self, custom_cmd, description):
        super(CommandParser, self).__init__(prog=custom_cmd, description=description)

    def error(self, message):
        raise ArgumentParserError(message)

    def exit(self):
        return


class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2 * pi * t)
        self.axes.plot(t, s)

    def update_figure(self, x, y, marker, label):
        self.axes.plot(x, y, marker, label=label)
        self.draw()

    def plot_hold(self, holdon):
        self.axes.hold(holdon)


class ScadaShell(QWidget):
    def __init__(self, parent):
        super(ScadaShell, self).__init__(parent)
        self._parent = parent
        self._log = OutputWindow(parent)
        self._log.setMinimumSize(500, 200)
        self._log.setReadOnly(True)
        # if parent.redirect_sys_out:
        #     print("aaaaa")
        #     sys.stdout = self._log
        #     sys.stderr = self._log
        self._input = QLineEdit(parent)
        self._input.returnPressed.connect(self.onReturnPressed)
        layout = QVBoxLayout()
        layout.addWidget(self._log)
        layout.addWidget(self._input)
        self.setLayout(layout)


    def setFocus(self):
        self._input.setFocus()

    def onReturnPressed(self, key=None):
        cmd = self._input.text()
        self.log_text('>> ' + cmd + '\n')
        self.processCommand(cmd)
        self._input.setText("")

    def list_folder_content(self, folder):
        data_folder = folder
        sd = os.listdir(data_folder)
        sd.sort(reverse=True)
        sd = [data_folder + x for x in sd]
        return '\n'.join(sd)

    def load_data_folder(self, log_folder):
        data_folder = log_folder + "/data/"
        mat_file = log_folder + "/DCNetwork27Nodes.mat"
        # extract and decompose the mat file
        mat = scipy.io.loadmat(mat_file)
        net_data = mat['opvar']
        self.net_bus = range(1, 5) + [6, 7, 8, 10] + range(12, 31)
        self.net_gen = [1, 2, 13, 22, 23, 27]
        self.net_load = [b for b in self.net_bus if b not in self.net_gen]
        self.mat_data = {}
        self.mat_data['Sim_Time'] = net_data[0, :]  # simuation time
        self.mat_data['Net_Time'] = [datetime.datetime.fromtimestamp(p / 1000) for p in net_data[1, :]]  # wall clock time
        self.mat_data['V_net'] = net_data[2:29, :]  # voltage measurements
        self.mat_data['P_net'] = net_data[29:56, :]  # power measurements
        # extract and decompose the agent's log files
        self.agent_data = {}
        for b in self.net_bus:
            with open(data_folder + 'data_A_' + str(b) + '.csv', 'rb') as f:
                reader = csv.reader(f)
                headers = reader.next()
                column = {}
                for h in headers:
                    column[h] = []
                for row in reader:
                    for h, v in zip(headers, row):
                        if h == "Id" or h == 'ADMM_ON' == h is 'ADMM_IT':
                            column[h].append(int(v))
                        elif h == "Time":
                            column[h].append(datetime.datetime.fromtimestamp(float(v)))
                        else:
                            column[h].append(float(v))
                self.agent_data[b] = column

    def processCommand(self, cmd):
        parts = shlex.split(cmd)
        if len(parts) > 0:
            if parts[0] == "plot":
                plot_parser = CommandParser(description='The plot command', custom_cmd='plot')
                plot_parser.add_argument("-a", "--agent", help="id of agents to be ploted. 0 for all", type=int)
                plot_parser.add_argument("-v", "--vars", help="names of variables to be plotted", nargs='*')
                plot_parser.add_argument("-ym", "--y_min", help="min y limits for the plots", nargs='*', type=float,
                                         default=0)
                plot_parser.add_argument("-yM", "--y_max", help="max y limits for the plots", nargs='*', type=float,
                                         default=1)

                try:
                    args = plot_parser.parse_args(parts[1:])
                    if args.agent == 0:
                        for b in self.net_bus:
                            for v in args.vars:
                                if v in self.agent_data[b]:
                                    x = self.agent_data[b]['Time']
                                    y = self.agent_data[b][v]
                                    self._parent.plot_data(x, y, '.', label=v + '-' + str(b))
                    else:
                        b = args.agent
                        for v in args.vars:  # plot the variables
                            if v in self.agent_data[b]:
                                x = self.agent_data[b]['Time']
                                y = self.agent_data[b][v]
                                self._parent.plot_data(x, y, '.', label=v + '-' + str(b))
                except ArgumentParserError as ape:
                    self.log_text('error: %s\n' % ape.message)
                except Exception as ex:
                    self.log_text('error: %s\n' % ex.message)
            elif parts[0] == "stop":  # stops all the agents
                self._parent.admin.say_to_all_agents("STOP")
            elif parts[0] == "agent":  # commands that target only one agent
                if parts[2] == "start":
                    os.system(
                        "(cd /home/g2elab/devel/Distributed_Optimization/RPi_cluster/scripts/; ./start_agent.sh "
                        + self._parent.admin.comm_scenario + " " + parts[1] + ")")
                if parts[2] == "stop":
                    self._parent.admin.say_to_agent(int(parts[1]), "STOP")
                if parts[2] == "enable":
                    self._parent.admin.enable_agent(int(parts[1]))
                if parts[2] == "merge":
                    self._parent.admin.merge_agent(int(parts[1]))
            elif parts[0] == "start":  # starts all the agents
                os.system(
                    "(cd /home/g2elab/devel/Distributed_Optimization/RPi_cluster/scripts/; ./start_agents.sh "
                    + self._parent.admin.comm_scenario + ")")
            elif parts[0] == "killall":  # starts all the agents
                os.system(
                    "(cd /home/g2elab/devel/Distributed_Optimization/RPi_cluster/scripts/; ./killallagents.sh)")
            elif parts[0] == "enable":  # enables all the agents
                self._parent.admin.enable_all_agents()
            elif parts[0] == "collect":  # collects the data at the end of an experiment from both agents and OPAL
                os.system("(cd /home/g2elab/devel/Distributed_Optimization/RPi_cluster/scripts/; ./collect_agent_and_opal_data.sh)")
            elif parts[0] == "clean":  # cleans the experiment data and logs from the agents
                os.system("(cd /home/g2elab/devel/Distributed_Optimization/RPi_cluster/scripts/; ./clean_agents_logs.sh)")
            elif parts[0] == "load":     # loads one of the folders containing experiment data
                self.load_data_folder(parts[1])
            elif parts[0] == "optimize":  # manually starts the ADMM algorithm
                self._parent.admin.say_to_all_agents("START ADMM")
            elif parts[0] == "engage":  # manually changes the power and voltage reference of the agents to the default
                                        # values
                self._parent.admin.say_to_all_agents("ENGAGE")
            elif parts[0] == "list":
                if parts[1] == "data":  # prints the list of folders containing experiment data
                    s = self.list_folder_content("../data/")
                    self.log_text(s)
                elif parts[1] == "results":  # prints the results of the ADMM algorithm so that it can be copy-pasted in Matlab
                    s = self._parent.admin.print_results()
                    self.log_text(s)
                elif parts[1] == "config":  # prints the list of available configurations
                    s = self.list_folder_content("../config_files/")
                    self.log_text(s)
            elif parts[0] == "hold":  # hold on and hold off for the current plot
                if parts[1] == "on":
                    self._parent.plot_hold(True)
                elif parts[1] == "off":
                    self._parent.plot_hold(False)
            elif parts[0] == "addplot":  # opens a new plot-tab in order to plot the data
                self._parent.add_plot_tab(int(parts[1]), parts[2])
            elif parts[0] == "goto":  # select the current plot
                self._parent.set_current_plot(int(parts[1]))
            elif parts[0] == "set":
                if "rho" in parts[1]:
                    self._parent.admin.set_rho_in_all_agents(float(parts[2]))
                if "max_iter" in parts[1]:
                    self._parent.admin.set_max_iter_in_all_agents(int(parts[2]))
                if "comm" in parts[1]:
                    self._parent.admin.set_comm_link_between_agents(int(parts[2]), int(parts[3]), float(parts[4]),
                                                                    float(parts[5]))
                if "scenario" in parts[1]:
                    if os.path.isdir("../config_files/" + parts[2]):  # test if the configuration exists
                        self._parent.admin.comm_scenario = parts[2]
                        if "wired" in parts[2]:
                            self._parent.admin.set_communication("wired")
                        if "wireless" in parts[2]:
                            self._parent.admin.set_communication("wireless")
                    else:
                        self.log_text('error: the provided configuration file does not exist \n')

                if "web_srv" in parts[1]:
                    self._parent.admin.set_measurement_webserver(parts[2], parts[3])
            elif parts[0] == "help":  # prints the list of available commands
                s = """List of available commands:
                    start <comm_scenario> -> starts the agents and enables the communication scenario. see the list command
                    enable                -> enables all the agents
                    stop                  -> stops all the agents
                    killall               -> kills all the agents
                    agent <#nr> start <comm_scenario> -> tell agent <#nr> to start and enable the communication scenario
                                            stop      -> stop agent <#nr>
                                            enable    -> enable agent <#nr>
                                            merge     -> merge agent <#nr> with the rest of the grid
                    collect               -> collects the experiment data from the agents and the opal
                    clean                 -> cleans the experiment data and logs from the agents
                    load <data_folder>    -> loads experiment data. see list command
                    set rho               -> sets the rho ADMM parameter for all the agents
                        max_iter          -> sets the max_iter ADMM parameter for all the agents
                        comm <i> <j> <d> <l> -> sets the comm. link from node i to node j with delay <d>[sec] and loss <l>[%]
                        comm_scenario     -> sets the communication scenario
                        web_srv <IP> <port>  -> sets the IP and port of the measurement webserver to be used by the agents
                    optimize              -> tell the agents to start the ADMM algorithm
                    engage                -> tell the agents to send their power references to the OPAL-RT
                    list data             -> lists the available <data_folder>s
                         config           -> lists the available <comm_scenario>s
                         results          -> prints the result of the ADMM algorithm so that it can be copy-pasted in Matlab
                    addplot <#idx> <#lbl> -> adds a plot tab at index <#idx> and with the label <#lbl>. see goto command
                    plot                  -> command for plotting. see plot --help for details
                    hold on/off           -> holds the current plot. similar to matlab
                    goto <#idx>           -> make the <#idx> the active plot. see addplot command
                    """
                self.log_text(s + "'\n")
            else:
                self.log_text("Don't know how to process: '" + cmd + "'\n")

    def log_text(self, message):
        self._log.insertPlainText(message)
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())


class ScadaGui(QWidget):
    def __init__(self, redirect_sys_out=True):
        self.redirect_sys_out = redirect_sys_out
        super(ScadaGui, self).__init__()
        self.initUI()

    def initUI(self):
        # creating widgets
        self._dgridPage = QWidget()
        self._networkPage = QWidget()
        # self._plotPage[0] = QWidget()
        self._plotPage = {}
        # create tabs
        self._tabs = QTabWidget(self)
        self._tabs.addTab(self._dgridPage, "dgrid")
        self._tabs.addTab(self._networkPage, "network")
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested[int].connect(self.tabClosedRequested)
        # self._tabs.addTab(self._plotPage, "plots")

        # create the network image display
        self._networkDisp = QtSvg.QSvgWidget('IEEE_30BusDC.svg')
        self._networkDisp.setMaximumSize(600, 500)

        # create the table for the measurements
        self._dgridValues = QTableWidget(10, 31, self._dgridPage)
        self._configure_table()

        # create the plot
        # self._plotCanvas = MyMplCanvas(self._plotPage, width=lamda10, height=4, dpi=100)
        # self._plotToolbar = NavigationToolbar(self._plotCanvas, self._plotPage)
        self._plotCanvas = {}
        self._plotToolbar = {}
        # create the shell
        self._scadaShell = ScadaShell(self)

        # setting the layout of the first tab, i.e., dgrid
        dgridLayout = QVBoxLayout(self._dgridPage)
        dgridLayout.addWidget(self._dgridValues)
        # setting the layout of the second tab, i.e., network
        networkLayout = QVBoxLayout(self._networkPage)
        networkLayout.addWidget(self._networkDisp)
        # setting the layout of the third tab, i.e., plots
        # plotLayout = QVBoxLayout(self._plotPage)
        # plotLayout.addWidget(self._plotCanvas)
        # plotLayout.addWidget(self._plotToolbar)

        # setting the layout of the main page
        self._mainLayout = QVBoxLayout()
        self._mainLayout.addWidget(self._tabs)
        self._mainLayout.addWidget(self._scadaShell)
        self.setLayout(self._mainLayout)
        self.setWindowTitle("Distributed Optimization SCADA")
        self.setMinimumSize(1100, 600)
        self.setWindowIcon(QtGui.QIcon('DOscada.png'))
        self._scadaShell.setFocus()

    def tabClosedRequested(self, tab_index):
        if tab_index >= 2:
            self._tabs.removeTab(tab_index)
            self._current_plot = -1

    def _configure_table(self):
        # configure the row header for the table
        self._dgridValues.setVerticalHeaderItem(0, QTableWidgetItem("ON"))
        self._dgridValues.setVerticalHeaderItem(1, QTableWidgetItem("A2O[ms]"))
        self._dgridValues.setVerticalHeaderItem(2, QTableWidgetItem("V[pu]"))
        self._dgridValues.setVerticalHeaderItem(3, QTableWidgetItem("P[pu]"))
        self._dgridValues.setVerticalHeaderItem(4, QTableWidgetItem("Trip"))
        self._dgridValues.setVerticalHeaderItem(5, QTableWidgetItem("ADMM"))
        self._dgridValues.setVerticalHeaderItem(6, QTableWidgetItem("Opt [ms]"))
        self._dgridValues.setVerticalHeaderItem(7, QTableWidgetItem("RPC [ms]"))
        self._dgridValues.setVerticalHeaderItem(8, QTableWidgetItem("V* [pu]"))
        self._dgridValues.setVerticalHeaderItem(9, QTableWidgetItem("P* [pu]"))
        # configure the column header of the table
        for i in range(0, 31):
            self._dgridValues.setHorizontalHeaderItem(i, QTableWidgetItem(str(i + 1)))
            self._dgridValues.horizontalHeaderItem(i).setForeground(QtGui.QColor(255, 0, 0, 255))
        # set the font-color for the generators columns in green
        self._dgridValues.horizontalHeaderItem(0).setForeground(QtGui.QColor(13, 148, 22, 255))
        self._dgridValues.horizontalHeaderItem(1).setForeground(QtGui.QColor(13, 148, 22, 255))
        self._dgridValues.horizontalHeaderItem(12).setForeground(QtGui.QColor(13, 148, 22, 255))
        self._dgridValues.horizontalHeaderItem(21).setForeground(QtGui.QColor(13, 148, 22, 255))
        self._dgridValues.horizontalHeaderItem(22).setForeground(QtGui.QColor(13, 148, 22, 255))
        self._dgridValues.horizontalHeaderItem(26).setForeground(QtGui.QColor(13, 148, 22, 255))
        font = self._dgridValues.horizontalHeader().font()
        font.setBold(True)
        self._dgridValues.horizontalHeader().setFont(font)
        # hide columns that don't have a coresponding network node
        self._dgridValues.setColumnHidden(4, True)
        self._dgridValues.setColumnHidden(8, True)
        self._dgridValues.setColumnHidden(10, True)
        # populate the table with empty cells
        for col in range(0, 31):
            for row in range(0, 10):
                self._dgridValues.setItem(row, col, QTableWidgetItem("     "))
                font = self._dgridValues.item(row, col).font()
                font.setPixelSize(8)
                self._dgridValues.item(row, col).setFont(font)
        self._dgridValues.resizeColumnsToContents()
        self._dgridValues.resizeRowsToContents()

    def set_current_plot(self, plot_no):
        self._current_plot = plot_no

    def add_plot_tab(self, plot_no, plot_name):
        self._current_plot = plot_no
        self._plotPage[plot_no] = QWidget()
        self._tabs.addTab(self._plotPage[plot_no], str(plot_no) + " - " + plot_name)
        # create the plot
        self._plotCanvas[plot_no] = MyMplCanvas(self._plotPage[plot_no], width=5, height=4, dpi=100)
        self._plotToolbar[plot_no] = NavigationToolbar(self._plotCanvas[plot_no], self._plotPage[plot_no])

        # setting the layout of the third tab, i.e., plots
        plotLayout = QVBoxLayout(self._plotPage[plot_no])
        plotLayout.addWidget(self._plotCanvas[plot_no])
        plotLayout.addWidget(self._plotToolbar[plot_no])

    def agent_connected(self, ano):
        self._dgridValues.item(0, ano - 1).setText("ON")
        self._dgridValues.resizeRowsToContents()
        self._dgridValues.viewport().update()

    def agent_running_admm(self, ano):
        self._dgridValues.item(5, ano - 1).setText("ON")
        self._dgridValues.resizeRowsToContents()
        self._dgridValues.viewport().update()

    def agent_disconnected(self, ano):
        self._dgridValues.item(0, ano - 1).setText("OFF")
        self._dgridValues.resizeRowsToContents()
        self._dgridValues.viewport().update()

    def agent_update_values(self, ano, dt_opal, v_meas, p_meas, trip):
        self._dgridValues.item(1, ano - 1).setText('{:4.3f}'.format(dt_opal))
        self._dgridValues.item(2, ano - 1).setText('{:4.3f}'.format(v_meas))
        self._dgridValues.item(3, ano - 1).setText('{:4.3f}'.format(p_meas))
        self._dgridValues.item(4, ano - 1).setText('{:4.3f}'.format(trip))
        self._dgridValues.resizeColumnsToContents()
        self._dgridValues.viewport().update()

    def agent_finished_admm(self, ano, dt_opt, dt_rpc, v_ref, p_ref):
        self._dgridValues.item(5, ano - 1).setText('OFF')
        self._dgridValues.item(6, ano - 1).setText('{:4.3f}'.format(dt_opt))
        self._dgridValues.item(7, ano - 1).setText('{:4.3f}'.format(dt_rpc))
        self._dgridValues.item(8, ano - 1).setText('{:4.3f}'.format(v_ref))
        self._dgridValues.item(9, ano - 1).setText('{:4.3f}'.format(p_ref))
        self._dgridValues.resizeColumnsToContents()
        self._dgridValues.viewport().update()

    def plot_data(self, x, y, marker, label):
        if self._current_plot == -1:
            self._scadaShell.log_text("No plot selected!")
        else:
            self._plotCanvas[self._current_plot].update_figure(x, y, marker, label)

    def plot_hold(self, holdon):
        if self._current_plot == -1:
            self._scadaShell.log_text("No plot selected!")
        else:
            self._plotCanvas[self._current_plot].plot_hold(holdon)


# class XmppAdmin:
#     # template for the xmpp username
#     xmpp_jid = 'admin@dgrid.net/self'
#     xmpp_pwd = 'admin'
#     xmpp_srv = '192.168.1.100'
#     # xmpp_srv = '127.0.0.1'
#     xmpp_nick = 'admin'
#     xmpp_port = 5222
#     # The administration console is conceived as a chat room joined by all the agents as well as the administrator
#     xmpp_room = 'admin_console@conference.dgrid.net'
#     stopRunning = 0
#     connected_agents = {}
#     data_buffer = {}
#
#     def __init__(self, ex):
#         # keep a reference to the gui
#         self.ex = ex
#         # create the xmpp client used for communicating
#         self.xmpp = sleekxmpp.ClientXMPP(self.xmpp_jid, self.xmpp_pwd)
#
#         # register custom handlers
#         self.xmpp.register_handler(Callback('ADMM Step Overview set iq',
#                                             StanzaPath('iq@type=set/admm_step_overview'),
#                                             self._raise_set_admm_step_event))
#
#         # register threaded event handlers for dealing with custom stanzas
#         self.xmpp.add_event_handler('set_admm_step_event',
#                                     self._handle_set_admm_step_event,
#                                     threaded=True)
#
#         # register handler for the beginning of the communication session
#         self.xmpp.add_event_handler("session_start", self._handle_xmpp_connected)
#
#         # register threaded event handlers for groupchat messages from the administration console
#         self.xmpp.add_event_handler("groupchat_message", self._handle_groupchat_message, threaded=True)
#
#         # register threaded event handlers for users going in and out of the group chat room
#         self.xmpp.add_event_handler("muc::%s::got_online" % self.xmpp_room, self._handle_muc_online, threaded=True)
#
#         self.xmpp.add_event_handler("muc::%s::got_offline" % self.xmpp_room, self._handle_muc_offline, threaded=True)
#
#         # register custom stanzas
#         register_stanza_plugin(Iq, ADMMStepOverview)
#
#     def _raise_set_admm_step_event(self, iq):
#         self.xmpp.event('set_admm_step_event', iq)
#
#     def connect(self):
#         self.xmpp.connect((self.xmpp_srv, self.xmpp_port))
#         self.xmpp.process(threaded=True)
#
#     def _handle_set_admm_step_event(self, iq):
#         if "error" not in iq['type']:
#             agent = iq["from"].bare
#             it = np.array([int(iq["admm_step_overview"]["iteration"])])
#             delta_opt = iq["admm_step_overview"]["opt_time"]
#             delta_wait = iq["admm_step_overview"]["wait_time"]
#
#             # x_opt = np.array(json.loads(iq['admm_step_overview']['x_opt']))
#             # beta = np.array(json.loads(iq['admm_step_overview']['beta']))
#             # nu = np.array(json.loads(iq['admm_step_overview']['nu']))
#             # z = np.array(json.loads(iq['admm_step_overview']['z']))
#             # if agent not in self.data_buffer:
#             # 	agent_data = [it, x_opt, beta, nu, z]
#             # 	self.data_buffer[agent] = agent_data
#             #
#             # else:
#             # 	agent_data = self.data_buffer[agent]
#             # 	agent_data[0] = np.concatenate((agent_data[0], it), axis=0)
#             # 	agent_data[1] = np.concatenate((agent_data[1], x_opt), axis=0)
#             # 	agent_data[2] = np.concatenate((agent_data[2], beta), axis=0)
#             # 	agent_data[3] = np.concatenate((agent_data[3], nu), axis=0)
#             # 	agent_data[4] = np.concatenate((agent_data[4], z), axis=0)
#             # 	self.data_buffer[agent] = agent_data
#             ano = int(re.search(r'\d+', agent).group())  # get the id of the agent
#             self.ex.agent_update_opt_step(ano, it[0], delta_opt, delta_wait)
#
#     def _handle_muc_online(self, presence):
#         agent = presence['muc']['nick']
#         if agent != self.xmpp_nick:  # test that the agent connecting is not the administrator
#             if agent not in self.connected_agents:
#                 self.connected_agents[agent] = 1
#                 ano = int(re.search(r'\d+', agent).group())  # get the id of the connected agent
#                 self.ex.agent_connected(ano)
#
#     def _handle_muc_offline(self, presence):
#         agent = presence['muc']['nick']
#         if agent != self.xmpp_nick:
#             self.connected_agents[agent] = 0
#             ano = int(re.search(r'\d+', agent).group())  # get the id of the connected agent
#             self.ex.agent_disconnected(ano)
#
#     def _handle_xmpp_connected(self, event):
#         # send the presence
#         self.xmpp.sendPresence()
#
#         # join the administration console chat room
#         self.xmpp.plugin['xep_0045'].joinMUC(self.xmpp_room, self.xmpp_nick, wait=True)
#
#     # handle communication messages received into the administration console
#     # there are two types of messages that we receive: non permanent and permanent
#     def _handle_groupchat_message(self, msg):
#         agent = msg['mucnick']
#         if self.xmpp_nick != agent:
#             s = msg['body']
#             if 'np' in s:  # non permanent values are being sent in the form:  np|value|value...
#                 ano = int(re.search(r'\d+', agent).group())  # get the id of the agent
#                 parts = s.split('|')
#                 self.ex.agent_update_values(ano, parts[1:])
#             else:
#                 print(agent + ":" + s)
#
#     def say_to_all_agents(self, message):
#         self.xmpp.sendMessage(mto=self.xmpp_room, mbody=message, mtype='groupchat')
#
#     def get_data_buffer_info(self):
#         i = 0
#         info = ""
#         for ad in self.data_buffer:
#             agent_data = self.data_buffer[ad]
#             dim1 = agent_data[0].shape
#             dim2 = agent_data[1].shape
#             info += ad + ": " + str(dim1) + " rec. for each " + str(dim2) + " x_opt beta nu z \t"
#             i += 1
#             if i % 3 == 0:
#                 info += "\n"
#         return info
#
#     def get_agent_data(self, ag, var, idx):
#         agent_data = self.data_buffer[ag]
#         it = agent_data[0]
#         y = agent_data[var]
#         x_data = it[:, 0]
#         y_data = y[:, idx]
#         return x_data, y_data


class RPCAdmin:
    # Threaded mix-in
    class AsyncXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer):
        pass

    admin_ip = "169.254.35.100"
    admin_port = 8000

    agents_wired = [[1, "169.254.35.101", 8000],
                  [2, "169.254.35.102", 8000],
                  [3, "169.254.35.103", 8000],
                  [4, "169.254.35.104", 8000],
                  [6, "169.254.35.105", 8000],
                  [7, "169.254.35.106", 8000],
                  [8, "169.254.35.107", 8000],
                  [10, "169.254.35.108", 8000],
                  [12, "169.254.35.109", 8000],
                  [13, "169.254.35.110", 8000],
                  [14, "169.254.35.101", 8001],
                  [15, "169.254.35.102", 8001],
                  [16, "169.254.35.103", 8001],
                  [17, "169.254.35.104", 8001],
                  [18, "169.254.35.105", 8001],
                  [19, "169.254.35.106", 8001],
                  [20, "169.254.35.107", 8001],
                  [21, "169.254.35.109", 8001],
                  [22, "169.254.35.110", 8001],
                  [23, "169.254.35.108", 8001],
                  [24, "169.254.35.101", 8002],
                  [25, "169.254.35.102", 8002],
                  [26, "169.254.35.103", 8002],
                  [27, "169.254.35.104", 8002],
                  [28, "169.254.35.106", 8002],
                  [29, "169.254.35.105", 8002],
                  [30, "169.254.35.107", 8002],
                  [31, "169.254.35.110", 8002]
                    ]
    #

    agents_wireless = [[1, "192.168.1.101", 8000],
                      [2, "192.168.1.102", 8000],
                      [3, "192.168.1.103", 8000],
                      [4, "192.168.1.104", 8000],
                      [6, "192.168.1.105", 8000],
                      [7, "192.168.1.106", 8000],
                      [8, "192.168.1.107", 8000],
                      [10, "192.168.1.108", 8000],
                      [12, "192.168.1.109", 8000],
                      [13, "192.168.1.110", 8000],
                      [14, "192.168.1.101", 8001],
                      [15, "192.168.1.102", 8001],
                      [16, "192.168.1.103", 8001],
                      [17, "192.168.1.104", 8001],
                      [18, "192.168.1.105", 8001],
                      [19, "192.168.1.106", 8001],
                      [20, "192.168.1.107", 8001],
                      [21, "192.168.1.109", 8001],
                      [22, "192.168.1.110", 8001],
                      [23, "192.168.1.108", 8001],
                      [24, "192.168.1.101", 8002],
                      [25, "192.168.1.102", 8002],
                      [26, "192.168.1.103", 8002],
                      [27, "192.168.1.104", 8002],
                      [28, "192.168.1.106", 8002],
                      [29, "192.168.1.105", 8002],
                      [30, "192.168.1.107", 8002],
                      [31, "192.168.1.110", 8002]]
    #

    def __init__(self, ex):
        # keep a reference to the gui
        self.ex = ex

        # Create the RPC server for the admin
        # self.server = self.AsyncXMLRPCServer((self.admin_ip, self.admin_port), SimpleXMLRPCRequestHandler,
        #                                     logRequests=False)
        self.server = SimpleXMLRPCServer((self.admin_ip, self.admin_port), SimpleXMLRPCRequestHandler,
                                            logRequests=False)
        self.server.register_introspection_functions()
        # register the functions that can be called remotely
        self.server.register_function(self.agent_online, 'agent_online')
        self.server.register_function(self.agent_offline, 'agent_offline')
        self.server.register_function(self.agent_started_admm, 'agent_started_admm')
        self.server.register_function(self.agent_finished_admm, 'agent_finished_admm')
        self.server.register_function(self.agent_measurements, 'agent_measurements')
        self.server.register_function(self.agent_general_use_message, 'agent_general_use_message')
        # start the RPC server
        t = threading.Thread(target=self.server.serve_forever)
        t.start()
        # the communication scenario to be used by default by the agents
        self.comm_scenario = "wired_default"
        self.agents = self.agents_wired

    def agent_online(self, a_id):
        self.ex.agent_connected(a_id)
        return 1

    def agent_offline(self, a_id):
        self.ex.agent_disconnected(a_id)
        return 1

    def agent_started_admm(self, a_id):
        self.ex.agent_running_admm(a_id)
        self.v_opt = {}
        return 1

    def agent_finished_admm(self, ano, dt_opt, dt_rpc, v_ref, p_ref):
        self.ex.agent_finished_admm(ano, dt_opt, dt_rpc, v_ref, p_ref)
        self.v_opt[ano] = [v_ref, p_ref]
        return 1

    def print_results(self):
        s_keys = sorted(self.v_opt)
        volt = []
        power = []
        for key in s_keys:
            volt.append(self.v_opt[key][0])
            power.append(self.v_opt[key][1])
        return 'v_d = ' + str(volt) + "'; \n p_d = " + str(power) + "';"

    def agent_measurements(self, ano, dt_opal, v_meas, p_meas, trip):
        self.ex.agent_update_values(ano, dt_opal, v_meas, p_meas, trip)
        return 1

    def agent_general_use_message(self, ano, message):
        print("Agent " + str(ano) + ":" + message)
        return 1

    def disconnect(self):
        print("=====Shuting down RPC server")
        self.server.shutdown()

    def set_communication(self, comm_type):
        if "wired" in comm_type:
            self.agents = self.agents_wired
        else:
            self.agents = self.agents_wireless

    def say_to_agent(self, id, s):
        if s is "STOP":
            for a in self.agents:
                if a[0] == id:
                    srv_addr = "http://" + a[1] + ":" + str(a[2])
                    print ("asking agent " + str(id) + " to shut down at " + srv_addr)
                    agent = xmlrpclib.ServerProxy(srv_addr)
                    try:
                        agent.remote_shutdown()
                    except Exception as exc:
                        print("Cannot talk to agent " + str(id))

    def say_to_all_agents(self, s):
        if s is "STOP":
            for a in self.agents:
                srv_addr = "http://" + a[1] + ":" + str(a[2])
                agent = xmlrpclib.ServerProxy(srv_addr)
                try:
                    agent.remote_shutdown()
                except (socket_error, xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError), exc:
                    print("Cannot talk to agent " + str(a[0]))
        elif s is "START ADMM":
            # for a in self.agents:
            #     srv_addr = "http://" + a[1] + ":" + str(a[2])
            #     agent = xmlrpclib.ServerProxy(srv_addr)
            #     agent.start_admm()
            srv_addr = "http://" + self.agents[0][1] + ":" + str(self.agents[0][2])
            agent = xmlrpclib.ServerProxy(srv_addr)
            agent.start_admm()
        elif s is "ENGAGE":
            for a in self.agents:
                srv_addr = "http://" + a[1] + ":" + str(a[2])
                agent = xmlrpclib.ServerProxy(srv_addr)
                try:
                    agent.engage()
                except (socket_error, xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError), exc:
                    print("Cannot talk to agent " + str(a[0]))

    def set_rho_in_all_agents(self, rho):
        for a in self.agents:
            srv_addr = "http://" + a[1] + ":" + str(a[2])
            agent = xmlrpclib.ServerProxy(srv_addr)
            try:
                agent.set_admm_rho(rho)
            except (socket_error, xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError), exc:
                print("Cannot talk to agent " + str(a[0]))

    def set_max_iter_in_all_agents(self, max_iter):
        for a in self.agents:
            srv_addr = "http://" + a[1] + ":" + str(a[2])
            agent = xmlrpclib.ServerProxy(srv_addr)
            try:
                agent.set_admm_max_iter(max_iter)
            except (socket_error, xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError), exc:
                print("Cannot talk to agent " + str(a[0]))

    def set_comm_link_between_agents(self, agenti, agentj, delay, loss):
        for a in self.agents:
            if a[0] == agenti:
                srv_addr = "http://" + a[1] + ":" + str(a[2])
                agent = xmlrpclib.ServerProxy(srv_addr)
                try:
                    agent.set_comm_link_to_neigh(agentj, delay, loss)
                except (socket_error, xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError), exc:
                    print("Cannot talk to agent " + str(a[0]))
            if a[0] == agentj:
                srv_addr = "http://" + a[1] + ":" + str(a[2])
                agent = xmlrpclib.ServerProxy(srv_addr)
                try:
                    agent.set_comm_link_to_neigh(agenti, delay, loss)
                except (socket_error, xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError), exc:
                    print("Cannot talk to agent " + str(a[0]))

    def set_measurement_webserver(self, ip, port):
        for a in self.agents:
            srv_addr = "http://" + a[1] + ":" + str(a[2])
            agent = xmlrpclib.ServerProxy(srv_addr)
            try:
                agent.set_measurement_webserver(ip, port)
            except (socket_error, xmlrpclib.Fault, xmlrpclib.ProtocolError, xmlrpclib.ResponseError), exc:
                print("Cannot talk to agent " + str(a[0]))

    def enable_all_agents(self):
        for a in self.agents:
            srv_addr = "http://" + a[1] + ":" + str(a[2])
            agent = xmlrpclib.ServerProxy(srv_addr)
            try:
                agent.enable()
            except Exception as exc:
                print("Cannot talk to agent " + str(a[0]))

    def enable_agent(self, id):
        for a in self.agents:
            if a[0] == id:
                srv_addr = "http://" + a[1] + ":" + str(a[2])
                agent = xmlrpclib.ServerProxy(srv_addr)
                agent.enable()

    def merge_agent(self, id):
        for a in self.agents:
            if a[0] == id:
                srv_addr = "http://" + a[1] + ":" + str(a[2])
                agent = xmlrpclib.ServerProxy(srv_addr)
                agent.merge()



def main():
    app = QApplication(sys.argv)
    ex = ScadaGui(redirect_sys_out=True)
    ex.show()
    # admin = XmppAdmin(ex)
    # admin.xmpp.register_plugin('xep_0045')  # Multi user chat used for the admin console
    # admin.xmpp.register_plugin('xep_0030')  # Service Discovery
    # admin.xmpp.register_plugin('xep_0199')  # XMPP Ping
    # admin.connect()
    # app.aboutToQuit.connect(admin.xmpp.disconnect)
    admin = RPCAdmin(ex)
    ex.admin = admin
    app.aboutToQuit.connect(admin.disconnect)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
