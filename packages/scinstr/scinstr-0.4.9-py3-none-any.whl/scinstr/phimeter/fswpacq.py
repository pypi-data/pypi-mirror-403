#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""package fswp
author    Benoit Dubois
copyright FEMTO ENGINEERING
license   GPL v3.0+
brief     Acquire data trace from FSWP device.
"""

import sys
import os.path as path
import logging
import datetime
import socket
import struct
import signal
from pyqtgraph.parametertree import Parameter, ParameterTree
import pyqtgraph as pg
import numpy as np
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QDir, QFileInfo
from PyQt5.QtGui import QApplication, QMainWindow, QWidget, QVBoxLayout, \
    QHBoxLayout, QMessageBox, QFileDialog, QSplitter

# Ctrl-c closes the application
signal.signal(signal.SIGINT, signal.SIG_DFL)

CONSOLE_LOG_LEVEL = logging.DEBUG
FILE_LOG_LEVEL = logging.WARNING

IP = "172.16.120.200"
#PORT = 4880  # HiSLIP protocol port
PORT = 5025  # Raw socket port
APP_NAME = "FswpAcquire"


#===============================================================================
class FswpDev():

    def __init__(self, ip, port=PORT, timeout=1.0):
        """Constructor.
        :param ip: IP address of device (str)
        :param port: Ethernet port of device (int)
        :param timeout: Timeout on connection instance (float)
        :returns: None
        """
        self.ip = ip
        self.port = port
        self._timeout = timeout
        self._sock = None

    def connect(self):
        """Connect to device.
        """
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(self._timeout)
            self._sock.connect((self.ip, self.port))
        except ValueError as ex:
            logging.error("Connection parameters out of range: %r", ex)
            return False
        except socket.timeout:
            logging.error("Timeout on connection")
            return False
        except Exception as ex:
            logging.error("Unexpected exception during connection with " + \
                          "device: %r", ex)
            return False
        else:
            logging.debug("Connected to device")
            return True

    def write(self, data):
        """"Ethernet writing process.
        :param data: data writes to device (str)
        :returns: None
        """
        try:
            self._sock.send((data + '\n').encode('utf-8'))
        except socket.timeout:
            logging.error("Timeout")
        except Exception as ex:
            logging.error(ex)
        logging.debug("write " + data.strip('\n'))

    def read(self, length=100):
        """Read process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        try:
            retval = self._sock.recv(length).decode('utf-8').strip('\n')
        except socket.timeout:
            logging.error("Timeout")
            return ''
        except Exception as ex:
            logging.error(ex)
            raise ex
        logging.debug("read: " + retval)
        return retval

    def raw_read(self, length=512):
        """Raw read process.
        :param length: length of message to read (int)
        :returns: Message reads from device (bytes)
        """
        try:
            data = self._sock.recv(length)
        except socket.timeout:
            logging.error("Timeout")
            return bytes()
        except Exception as ex:
            logging.error(ex)
            raise ex
        return data

    def bin_read(self):
        """Read binary data then decode them to ascii.
        The reading process is specific to the transfert of binary data
        with these VNA devices: <header><data><EOT>, with:
        - <header>: #|lenght of bytes_count (one byte)|bytes_count
        - <data>: "REAL,32" (float32) binary data
        - <EOT>: '\n' character.
        Note: The data transfert format must be selected to "REAL,32"" before
        using this method
        """
        header_max_length = 11
        raw_data = self.raw_read(header_max_length)
        if raw_data.find(b'#') != 0:
            logging.error("Data header not valid")
            return
        byte_count_size = int(raw_data[1:2])
        byte_count = int(raw_data[2:2+byte_count_size])
        # Note : Read 'byte_count' bytes but only
        # 2 + byte_count_nb + byte_count - header_max_length
        # needs to be readen.
        # This tip can be used because EOF ('\n') is transmited at the end of
        # the message and thus stop reception of data.
        while len(raw_data) < byte_count:
            raw_data += self.raw_read(byte_count)
        nb_elem = int(byte_count / 4)
        data = np.asarray(struct.unpack("<{:d}f".format(nb_elem),
                                        raw_data[2+byte_count_size:-1]))
        return data

    def query(self, msg, length=100):
        """Basic query process: write query then read response.
        """
        self.write(msg)
        return self.read(length)

    def reset(self):
        """Reset device.
        """
        self.write("*RST")

    @property
    def id(self):
        """Return ID of device.
        """
        return self.query("*IDN?")

    def get_data_trace(self, trace=1, window=1):
        """Get a data trace.
        :param :
        :return: Array of measurement data.
        """
        self.write("FORM REAL, 32")
        self.write("TRAC{}? TRACE{}".format(window, trace))
        data = self.bin_read()
        datax = data[::2]
        datay = data[1::2]
        return np.asarray([datax, datay])

    def get_crossco_gain_indicator(self, window=1):
        """Get the data of the cross-correlation gain indicator (grey area).
        :param :
        :return: Array of the cross-correlation gain indicator data.
        """
        self.write("FORM REAL, 32")
        self.write("TRAC{}? XGINdicator".format(window))
        data = self.bin_read()
        datax = data[::2]
        datay = data[1::2]
        return np.asarray([datax, datay])
    


#===============================================================================
MAIN_PARAMS = [
    {'name': 'Load data', 'type': 'group', 'children': [
        {'name': 'From device', 'type': 'group', 'children': [
            {'name': 'IP', 'type': 'str', 'value': IP},
            {'name': 'Port', 'type': 'int', 'value': PORT},
            {'name': 'Trace', 'type': 'group', 'children': [
                {'name': 'Number', 'type': 'int', 'value': 1},
                {'name': 'Bench noise', 'type': 'bool', 'value': False},
            ]},
            
            {'name': 'Acquisition', 'type': 'action'},
        ]},
        {'name': 'From file', 'type': 'group', 'children': [
            {'name': 'Filename', 'type': 'str'},
            {'name': 'Open', 'type': 'action'},
        ]},
    ]},
    {'name': 'Plot', 'type': 'group', 'children': []},
]

CURVE_PARAMS = [
                {'name': 'Enable', 'type': 'bool', 'value': True},
                {'name': 'Scale', 'type': 'float', 'value': 1.0},
                {'name': 'Offset', 'type': 'float', 'value': 0.0},
                {'name': 'Color', 'type': 'color'},
        ]


class FswpUi(QMainWindow):
    """Ui of extract peak application.
    """

    def __init__(self):
        """Constructor.
        :returns: None
        """
        super().__init__()
        self.setWindowTitle("FSWP")
        self.setCentralWidget(self._central_widget())
        self.plot.showGrid(True, True, 0.5)
        self.plot.setLogMode(x=True, y=False)

    def _central_widget(self):
        """Generates central widget.
        :returns: central widget of UI (QWidget)
        """
        self.p = Parameter.create(name='params',
                                  type='group',
                                  children=MAIN_PARAMS)
        self.ptree = ParameterTree()
        self.ptree.setParameters(self.p, showTop=False)
        self.ptree.resizeColumnToContents(1)
        self.ptree.resizeColumnToContents(2)
        self.plot = pg.PlotWidget()
        splitter = QSplitter(self)
        splitter.addWidget(self.ptree)
        splitter.addWidget(self.plot)
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        return central_widget


#===============================================================================
class FswpApp(QApplication):
    """Fswp application.
    """

    # Emit data key value
    get_from_dev_done = pyqtSignal(str)
    get_from_file_done = pyqtSignal(str)

    def __init__(self, args):
        """Constructor.
        :returns: None
        """
        super().__init__(args)
        self._ui = FswpUi()
        self._data = {}
        self._ui.p.param(
            'Load data', 'From device', 'Acquisition').sigActivated.connect(
                self.get_data_from_device)
        self._ui.p.param(
            'Load data', 'From file', 'Open').sigActivated.connect(
                self.get_data_from_file)
        self.get_from_dev_done.connect(self.save_data)
        self.get_from_dev_done.connect(self.handle_acq_data)
        self.get_from_dev_done.connect(self.display_data)
        self.get_from_file_done.connect(self.handle_acq_data)
        self.get_from_file_done.connect(self.display_data)
        self._ui.p.param('Plot').sigTreeStateChanged.connect(
            self.display_data)
        self._ui.show()

    @pyqtSlot()
    def get_data_from_file(self):
        filename = QFileDialog(self._ui).getOpenFileName(
            parent=None,
            caption="Choose file to load",
            directory=QDir.currentPath(),
            filter="Any files (*)")[0]
        if filename == '':
            return
        try:
            data = np.loadtxt(filename)
        except Exception as ex:
            logging.error("Problem when reading file: %s", str(ex))
            QMessageBox.warning(self._ui, "Acquisition problem",
                                "Problem when reading file: {}".format(ex),
                                QMessageBox.Ok)
            return
        key = QFileInfo(filename).baseName()
        self._data[key] = data
        self.get_from_file_done.emit(key)

    @pyqtSlot()
    def get_data_from_device(self):
        """Acquire data process.
        :returns: None
        """
        ip = self._ui.p.param('Load data', 'From device', 'IP').value()
        port = self._ui.p.param('Load data', 'From device', 'Port').value()
        trace_nb = self._ui.p.param('Load data',
                                    'From device',
                                    'Trace',
                                    'Number').value()
        bench_noise = self._ui.p.param('Load data',
                                       'From device',
                                       'Trace',
                                       'Bench noise').value()
        # Acquisition itself
        dev = FswpDev(ip, port)
        if not dev.connect():
            logging.error("Connection error")
            return
        try:
            data = dev.get_data_trace(trace=trace_nb)
            if bench_noise is True:
                bnoise = [dev.get_crossco_gain_indicator()[0]]
                data = np.concatenate((data, bnoise))
        except Exception as ex:
            logging.error("Problem during acquisition: %r", ex)
            QMessageBox.warning(self._ui, "Acquisition problem",
                                "Problem during acquisition: {}".format(ex),
                                QMessageBox.Ok)
            return
        now = datetime.datetime.utcnow()
        key = now.strftime("%Y%m%d-%H%M%S")
        self._data[key] = data
        self.get_from_dev_done.emit(key)

    @pyqtSlot(str)
    def handle_acq_data(self, key):
        self._ui.p.param('Plot').addChild(
            Parameter.create(name=key,
                             type='group',
                             children=CURVE_PARAMS))
        # Get a new color for the new curve
        ##for child in self._ui.p.param('Plot').children():
        ##    color =  child.param('Color').value()

    @pyqtSlot(str)
    def save_data(self, key):
        np.savetxt("{}.dat".format(key), self._data[key])

    @pyqtSlot()
    def display_data(self):
        for pdi in self._ui.plot.getPlotItem().listDataItems():
            self._ui.plot.getPlotItem().removeItem(pdi)
        for child in self._ui.p.param('Plot').children():
            if child.param('Enable').value() is True:
                scale = child.param('Scale').value()
                offset = child.param('Offset').value()
                color =  child.param('Color').value()
                self._ui.plot.plot(
                    self._data[child.name()][0],
                    self._data[child.name()][1] * scale + offset,
                    pen=color)


#==============================================================================
def configure_logging():
    """Configures logs.
    """
    home = path.expanduser("~")
    log_file = "." + APP_NAME + ".log"
    abs_log_file = path.join(home, log_file)
    date_fmt = "%d/%m/%Y %H:%M:%S"
    log_format = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d): %(message)s"
    logging.basicConfig(level=FILE_LOG_LEVEL, \
                        datefmt=date_fmt, \
                        format=log_format, \
                        filename=abs_log_file, \
                        filemode='w')
    console = logging.StreamHandler()
    # define a Handler which writes messages to the sys.stderr
    console.setLevel(CONSOLE_LOG_LEVEL)
    # set a format which is simpler for console use
    console_format = '%(levelname) -8s %(filename)s (%(lineno)d): %(message)s'
    formatter = logging.Formatter(console_format)
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

#==============================================================================
def main():
    configure_logging()
    app = FswpApp(sys.argv)
    sys.exit(app.exec_())

#==============================================================================
if __name__ == '__main__':
    main()
