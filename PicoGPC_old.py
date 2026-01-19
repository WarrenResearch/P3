from tc08usb import TC08USB, USBTC08_ERROR, USBTC08_UNITS, USBTC08_TC_TYPE
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
import threading
import datetime
import time
import pandas as pd

class PicoGPC(QtWidgets.QWidget):
    def __init__(self, parent, ):
        super().__init__(parent)


        RI_SignalGroupBox = QtWidgets.QGroupBox('RI_Signal measurements')
        RI_SignalGroupBox.setFixedSize(600, 250)

        self.connectButton = QtWidgets.QPushButton('Connect')
        self.connectButton.setFixedSize(75, 25)
        self.connectButton.setStyleSheet("background-color: rgb(210, 210, 210);" "color: black;" "border-radius:5px")

        self.measureButton = QtWidgets.QPushButton("Measure")
        self.measureButton.setFixedSize(75, 25)
        self.measureButton.setStyleSheet("background-color: rgb(210, 210, 210);" "color: black;" "border-radius:5px")

        self.stopMeasureButton = QtWidgets.QPushButton("Stop measure")
        self.stopMeasureButton.setFixedSize(75, 25)
        self.stopMeasureButton.setStyleSheet("background-color: rgb(210, 210, 210);" "color: black;" "border-radius:5px")

        self.resetGraphButton = QtWidgets.QPushButton("Reset graph")
        self.resetGraphButton.setFixedSize(75, 25)
        self.resetGraphButton.setStyleSheet("background-color: rgb(210, 210, 210);" "color: black;" "border-radius:5px")

        self.disconnectButton = QtWidgets.QPushButton("Disconnect")
        self.disconnectButton.setFixedSize(75, 25)
        self.disconnectButton.setStyleSheet("background-color: rgb(210, 210, 210);" "color: black;" "border-radius:5px")

        self.saveDataButton = QtWidgets.QPushButton("Save data")
        self.saveDataButton.setFixedSize(75, 25)
        self.saveDataButton.setStyleSheet("background-color: rgb(210, 210, 210);" "color: black;" "border-radius:5px")

        ################# Plot widget definition ##################
        self.dataFeed = pg.PlotWidget()
        self.dataFeed.setBackground('#F4F4F4')
        self.dataFeed.setTitle("RI_Signal", color='#000000')
        styles = {'color': '#000000', 'font-size': '14px'}
        self.dataFeed.setLabel('left', "RI_Signal [\u2103]", **styles)
        self.dataFeed.setLabel('bottom', 'Time [s]', **styles)
        self.dataFeed.addLegend(colCount=5, offset=15, pen=None, labelTextSize='7pt', labelTextColor='#000000')
        channel1 = np.array([])

        timeAxis = np.array([])
        self.channel1Line = self.dataFeed.plot(timeAxis, channel1, pen='r', name='R1')

        self.channel1Label = QtWidgets.QLabel("R1: ")
        self.channel1Value = QtWidgets.QLineEdit()

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)
        grid = QtWidgets.QGridLayout()
        innergrid10 = QtWidgets.QGridLayout()
        grid.addLayout(innergrid10, 1, 0, 5, 1)
        layout.addWidget(RI_SignalGroupBox)
        RI_SignalGroupBox.setLayout(grid)
        innergrid10.addWidget(self.connectButton, 0, 0)
        innergrid10.addWidget(self.measureButton, 1, 0)
        innergrid10.addWidget(self.stopMeasureButton, 2, 0)
        innergrid10.addWidget(self.resetGraphButton, 3, 0)
        innergrid10.addWidget(self.disconnectButton, 4, 0)
        innergrid10.addWidget(self.saveDataButton, 5, 0)
        grid.addWidget(self.dataFeed, 1, 1, 5, 1)
        grid.addWidget(self.channel1Label, 1, 2)
        grid.addWidget(self.channel1Value, 1, 3)

        grid.setContentsMargins(3, 3, 3, 3)

        self.connectButton.clicked.connect(self.connect)
        self.measureButton.clicked.connect(self.measure)
        self.stopMeasureButton.clicked.connect(self.stopMeasure)
        self.resetGraphButton.clicked.connect(self.resetGraph)
        self.disconnectButton.clicked.connect(self.disconnect)
        self.saveDataButton.clicked.connect(self.saveData)

    def connect(self):
        self.tc08usb = TC08USB()
        self.tc08usb.open_unit()
        self.tc08usb.set_mains(50)
        self.channels = [1]
        self.numChannels = len(self.channels)
        for i in self.channels:
            self.tc08usb.set_channel(i, USBTC08_TC_TYPE.X)
        self.tc08usbConnected = True
        print('TC-08 picologger connected')

    def measure(self): # Opens new thread for RI_Signal measurement  
        if self.tc08usbConnected:
            self.tc08usbRun = True
            self.readRI_SignalThread = threading.Thread(target = self.read_data)
            self.readRI_SignalThread.start()
            self.stopRI_SignalThread = False

    def read_data(self):
        self.RI_SignalData = np.array([])
        self.timeAxis = np.array([])
        self.channel1 = np.array([]) #initialise data array for voltage
        self.timeAxis = np.array([])
        self.startMeasurementTime = datetime.datetime.now()

        while self.tc08usbRun:
            self.tc08usb.get_single()
            self.experimentTime = (datetime.datetime.now() - self.startMeasurementTime).seconds
            self.timeAxis = np.append(self.timeAxis, self.experimentTime)
            newData = np.array([self.tc08usb[1]]) # gathers new RI_Signal values from TC-08
            self.channel1 = np.append(self.channel1, newData[0]) # appends new data for each channel to the old array
            self.channel1Value.setText(f"{newData[0]:.6f}")
            self.RI_SignalXRange = np.size(self.channel1)*1.2
            # self.RI_SignalYRange = max(self.channel1)*1.2
            # self.dataFeed.setXRange(0, self.RI_SignalXRange + 100, padding = 0)
            # self.dataFeed.setYRange(0, self.RI_SignalYRange + 20, padding = 0)
            self.update_plot_data()
            time.sleep(0.2)
            
            if self.stopRI_SignalThread:
                break

    def update_plot_data(self):
        self.x = self.timeAxis
        self.channel1Line.setData(self.x, self.channel1)
        self.RI_SignalXRange = len(self.channel1)*1.2
        self.RI_SignalYRange = max(self.channel1)*1.2
        self.dataFeed.setXRange(0, self.RI_SignalXRange + 100, padding = 0)
        self.dataFeed.setYRange(-0.7, 0.7, padding = 0)

    def stopMeasure(self):
        self.stopRI_SignalThread = True
        self.readRI_SignalThread.join()
        self.tc08usbRun = False
        print("Measurement stopped")

    def resetGraph(self):
        self.dataFeed.clear()
        self.channel1 = np.array([])
        self.timeAxis = np.array([])
        self.update_plot_data()
    
    def saveData(self):
        savePath = r"G:\My Drive\Coding\P3_SDL" + "\-GPC.csv"
        print(savePath)
        df = pd.DataFrame(data=[self.x, self.channel1]).T
        df.columns=['Time (s)',
        'Channel 1 Voltage'
        ]        
        pd.DataFrame(df).to_csv(savePath)

    def disconnect(self):
        self.tc08usb.close_unit()