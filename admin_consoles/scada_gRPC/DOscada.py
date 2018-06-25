#!/usr/bin/python
import sys
import re
import json
from concurrent import futures
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
import grpc
import admm_pb2
import admm_pb2_grpc
import admin_pb2
import admin_pb2_grpc

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

    scripts_folder_path = "/home/g2elab/devel/Distributed_Optimization/RPi_cluster/scripts/"
    projects_folder_path = "/home/g2elab/devel/Distributed_Optimization/RPi_cluster/projects/"
    current_project = ""
    data_folder_path = "/logs/"
    config_folder_path = "/config_files/"

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
        self.log_text('>> ' + cmd)
        self.processCommand(cmd)
        self._input.setText("")

    def list_folder_content(self, folder):
        data_folder = folder
        sd = os.listdir(data_folder)
        sd.sort(reverse=True)
        # sd = [data_folder + x for x in sd]
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

    def upload_project(self, project_name):
        if os.path.isdir(self.projects_folder_path + project_name):  # test if the project folder exists
            os.system("(cd " + self.scripts_folder_path + "; ./upload_project_to_cluster.sh " + project_name + ")")
            self.current_project = project_name
            self.log_text("Code uploaded to cluster. Active project: " + project_name)
            self._parent.set_window_title("Active project: " + project_name)
        else:
            self.log_text("error: the provided project folder does not exist")

    def set_scenario(self, scenario_name):
        if self.current_project == "":
            self.log_text("No active project selected")
        else:
            if os.path.isdir(self.projects_folder_path + self.current_project +
                                     self.config_folder_path + scenario_name):  # test if the configuration exists
                self._parent.admin.comm_scenario = scenario_name
                self._parent.set_window_title("Active project: " + self.current_project + " -- " +scenario_name)
                self.log_text("Active scenario: " + scenario_name)
                if "wired" in scenario_name:
                    self._parent.admin.set_communication("wired")
                if "wireless" in scenario_name:
                    self._parent.admin.set_communication("wireless")
            else:
                self.log_text('error: the provided configuration file does not exist')

    def processCommand(self, cmd):
        try:
            parts = shlex.split(cmd)
            if len(parts) > 0:
                if parts[0] == "def":
                    # TODO remove hardcoded default project and scenario names
                    self.upload_project("DGridAgentgRPC")
                    self.set_scenario("wired_default")
                elif parts[0] == "plot":
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
                elif parts[0] == "project":
                    self.upload_project(parts[1])
                elif parts[0] == "scenario":
                    self.set_scenario(parts[1])
                elif parts[0] == "stop":  # stops all the agents
                    self._parent.admin.say_to_all_agents("STOP")
                elif parts[0] == "agent":  # commands that target only one agent
                    if parts[2] == "start":
                        os.system("(cd " + scripts_folder_path + "; ./start_agent.sh " + self._parent.admin.comm_scenario +
                                  " " + parts[1] + ")")
                    if parts[2] == "stop":
                        self._parent.admin.say_to_agent(int(parts[1]), "STOP")
                    if parts[2] == "enable":
                        self._parent.admin.say_to_agent(int(parts[1]), "ENABLE")
                    if parts[2] == "merge":
                        self._parent.admin.merge_agent(int(parts[1]))
                elif parts[0] == "start":  # starts all the agents
                    os.system("(cd " + self.scripts_folder_path + "; ./start_agents.sh " + self.current_project + " " +
                              self._parent.admin.comm_scenario + ")")
                elif parts[0] == "killall":  # starts all the agents
                    os.system("(cd " + self.scripts_folder_path + "; ./killallagents.sh)")
                elif parts[0] == "enable":  # enables all the agents
                    self._parent.admin.say_to_all_agents("ENABLE")
                elif parts[0] == "collect":  # collects the data at the end of an experiment from both agents and OPAL
                    os.system("(cd " + self.scripts_folder_path + "; ./collect_agent_and_opal_data.sh" + " " +
                              self.current_project + ")")
                elif parts[0] == "clean":  # cleans the experiment data and logs from the agents
                    os.system("(cd " + self.scripts_folder_path + "; ./clean_agents_logs.sh" + " " +
                              self.current_project + ")")
                elif parts[0] == "load":     # loads one of the folders containing experiment data
                    self.load_data_folder(parts[1])
                elif parts[0] == "optimize":  # manually starts the ADMM algorithm
                    self._parent.admin.say_to_all_agents("START ADMM")
                elif parts[0] == "list":
                    if parts[1] == "projects":  # prints the list of folders containing experiment data
                        s = self.list_folder_content(self.projects_folder_path)
                        self.log_text(s)
                    if parts[1] == "data":  # prints the list of folders containing experiment data
                        if self.current_project == "":
                            self.log_text("No active project selected")
                        else:
                            s = self.list_folder_content(self.projects_folder_path + self.current_project + self.data_folder_path)
                            self.log_text(s)
                    elif parts[1] == "results":  # prints the results of the ADMM algorithm so that it can be copy-pasted in Matlab
                        s = self._parent.admin.print_results()
                        self.log_text(s)
                    elif parts[1] == "scenarios":  # prints the list of available configurations
                        if self.current_project == "":
                            self.log_text("No active project selected")
                        else:
                            s = self.list_folder_content(self.projects_folder_path + self.current_project + self.config_folder_path)
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
                    if "web_srv" in parts[1]:
                        self._parent.admin.set_measurement_webserver(parts[2], int(parts[3]))
                elif parts[0] == "help":  # prints the list of available commands
                    s = """List of available commands:
                        project <project_name> -> sets the active project. see the list command
                        scenario <scenario_name> -> sets the active scenario for the active project. see the list command
                        start                 -> starts the agents
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
                            web_srv <IP> <port>  -> sets the IP and port of the measurement webserver to be used by the agents
                        optimize              -> tell the agents to start the ADMM algorithm
                        list projects         -> lists the available projects
                             data             -> lists the available <data_folder>s for the current project
                             scenarios           -> lists the available <comm_scenario>s for the current project
                             results          -> prints the result of the ADMM algorithm so that it can be copy-pasted in Matlab
                        addplot <#idx> <#lbl> -> adds a plot tab at index <#idx> and with the label <#lbl>. see goto command
                        plot                  -> command for plotting. see plot --help for details
                        hold on/off           -> holds the current plot. similar to matlab
                        goto <#idx>           -> make the <#idx> the active plot. see addplot command
                        """
                    self.log_text(s)
                else:
                    self.log_text("Don't know how to process: '" + cmd)
        except Exception as exc:
            self.log_text("Error while processing command")
            self.log_text(exc.message)

    def log_text(self, message):
        self._log.insertPlainText(message + "\n")
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

    def set_window_title(self, title):
        self.setWindowTitle(title)

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


class RPCAdmin(admin_pb2_grpc.AdminServicer):

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

    agents_dummy = [[1, "169.254.35.100", 8001],
                    [2, "169.254.35.100", 8002]]

    def __init__(self, ex):
        # keep a reference to the gui
        self.ex = ex
        # the communication scenario to be used by default by the agents
        self.comm_scenario = "wired_default"
        self.set_communication("wired")

    def agent_online(self, request, context):
        try:
            self.ex.agent_connected(request.agent_id)
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    def agent_offline(self, request, context):
        try:
            self.ex.agent_disconnected(request.agent_id)
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    def agent_started_admm(self, request, context):
        try:
            self.ex.agent_running_admm(request.agent_id)
            self.v_opt = {}
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('FAILED'), message=exc.message)

    def agent_finished_admm(self, request, context):
        try:
            self.ex.agent_finished_admm(request.agent_id, request.avg_opt_time, request.avg_rpc_time,
                                        request.v_ref, request.p_ref )
            self.v_opt[ano] = [request.v_ref, request.p_ref]
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('FAILED'),
                                       message=exc.message)

    def print_results(self):
        s_keys = sorted(self.v_opt)
        volt = []
        power = []
        for key in s_keys:
            volt.append(self.v_opt[key][0])
            power.append(self.v_opt[key][1])
        return 'v_d = ' + str(volt) + "'; \n p_d = " + str(power) + "';"

    def agent_measurements(self, request, context):
        try:
            self.ex.agent_update_values(request.agent_id, request.avg_opal_time, request.v_meas,
                                        request.p_meas, request.trip)
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('FAILED'),
                                       message=exc.message)

    def agent_general_use_message(self, request, context):
        try:
            print("Agent " + str(request.agent_id) + ":" + request.text)
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('SUCCESS'))
        except Exception as exc:
            return admin_pb2.CommReply(status=admin_pb2.OperationStatus.Value('FAILED'),
                                       message=exc.message)

    def set_communication(self, comm_type):
        if "wired" in comm_type:
            self.agents = self.agents_wired
        else:
            self.agents = self.agents_wireless
            # initialize comm channels with the agents
        for a in self.agents:
            channel = grpc.insecure_channel(a[1] + ":" + str(a[2]))
            stub = dgrid_pb2_grpc.DGridAgentStub(channel)
            a += [stub]  # store the rpc stub in the self.agents collection

    def say_to_agent(self, id, s):
        try:
            for a in self.agents:
                if a[0] == id:
                    req = dgrid_pb2.EmptyRequest()
                    if s is "STOP":
                        a[-1].remote_shutdown(req)
                    if s is "ENABLE":
                        a[-1].enable(req)
        except Exception as exc:
            print("Cannot talk to agent " + str(a[0]))
            print(exc.message)

    def say_to_all_agents(self, s):
        try:
            for a in self.agents:
                req = dgrid_pb2.EmptyRequest()
                if s is "STOP":
                    a[-1].remote_shutdown(req)
                if s is "START ADMM":
                    a[-1].start_admm(req)
                if s is "ENABLE":
                    a[-1].enable(req)
        except Exception as exc:
                    print("Cannot talk to agent " + str(a[0]))
                    print(exc.message)

    def set_rho_in_all_agents(self, rho):
        try:
            for a in self.agents:
                req = dgrid_pb2.SetRhoRequest(value=rho)
                a[-1].set_admm_rho(req)
        except Exception as exc:
            print("Cannot talk to agent " + str(a[0]))
            print(exc.message)

    def set_max_iter_in_all_agents(self, max_iter):
        try:
            for a in self.agents:
                req = dgrid_pb2.SetMaxIterRequest(value=max_iter)
                a[-1].set_admm_max_iter(req)
        except Exception as exc:
            print("Cannot talk to agent " + str(a[0]))
            print(exc.message)

    def set_comm_link_between_agents(self, agenti, agentj, delay, loss):
        try:
            for a in self.agents:
                if a[0] == agenti:
                    req = dgrid_pb2.SetCommLinkRequest(neigh_id=agentj, delay=delay, loss=loss)
                    a[-1].set_comm_link_to_neigh(req)
                if a[0] == agentj:
                    req = dgrid_pb2.SetCommLinkRequest(neigh_id=agenti, delay=delay, loss=loss)
                    a[-1].set_comm_link_to_neigh(req)
        except Exception as exc:
            print("Cannot talk to agent " + str(a[0]))
            print(exc.message)

    def set_measurement_webserver(self, ip, port):
        try:
            for a in self.agents:
                print('Setting web_srv for agent ' + str(a[0]))
                req = dgrid_pb2.SetMeasServerRequest(server_ip=ip, server_port=port)
                result = a[-1].set_measurement_webserver(req)
                print('result: ' + result.message)
        except Exception as exc:
            print("Cannot talk to agent " + str(a[0]))
            print(exc.message)

    def merge_agent(self, id, connect_signal):
        try:
            for a in self.agents:
                if a[0] == id:
                    req = dgrid_pb2.MergeRequest(connect_switch=connect_signal)
                    a[-1].merge(req)
        except Exception as exc:
            print("Cannot talk to agent " + str(a[0]))
            print(exc.message)

    def disconnect(self):
        global server
        print("=====Shuting down RPC server")
        server.stop(0)


admin_ip = "169.254.35.100"
admin_port = 8000

app = QApplication(sys.argv)
ex = ScadaGui(redirect_sys_out=True)
ex.show()

# the grpc server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
admin = RPCAdmin(ex)
admin_pb2_grpc.add_AdminServicer_to_server(admin, server)
server.add_insecure_port(admin_ip + ":" + str(admin_port))
server.start()


ex.admin = admin
app.aboutToQuit.connect(admin.disconnect)
sys.exit(app.exec_())

