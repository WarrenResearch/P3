import conductivityMonitor
import PicoGPC
import DLS_handler_new
from PyQt5 import QtWidgets, QtCore

class analysisHub(QtWidgets.QWidget):
    def __init__(self, parent, main):
        super(analysisHub, self).__init__(parent)
    
        self.main = main

    ### Set widget master layout
        self._layout = QtWidgets.QGridLayout()
        self.setLayout(self._layout)

    ### Define monitoring devices
        self.conductivityMonitor = conductivityMonitor.ConductivityMonitor(self, conductivityName="Reactor 5", analysisHub=self)
        self.GPCMonitor = PicoGPC.PicoGPC(self, analysisHub=self)

    ### Create monitoring group-box and add devices
        self.monitoringBox = QtWidgets.QGroupBox("Process monitoring")
        self.monitoringBox.setMaximumHeight(1000)
        self.monitoringBox.setMaximumWidth(1000)
        self.monitoringLayout = QtWidgets.QGridLayout(self.monitoringBox)
        self._layout.addWidget(self.monitoringBox, 0, 0, QtCore.Qt.AlignLeft)

        self.monitoringLayout.addWidget(self.conductivityMonitor, 0, 0, QtCore.Qt.AlignTop)
        self.monitoringLayout.addWidget(self.GPCMonitor, 1, 0, QtCore.Qt.AlignTop)


    ### Define analytical instruments
        self.stoppedFlowDLS = DLS_handler_new.StoppedFlowDLS(self, main=self.main)

    ### Create analysis group-box and add instruments
        self.analysisBox = QtWidgets.QGroupBox("Product analysis")
        self.analysisLayout = QtWidgets.QGridLayout(self.analysisBox)
        self._layout.addWidget(self.analysisBox, 0, 1, QtCore.Qt.AlignLeft)

        self.analysisLayout.addWidget(self.stoppedFlowDLS, 0, 0, QtCore.Qt.AlignTop)
