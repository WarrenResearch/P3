from tc08usb import TC08USB, USBTC08_ERROR, USBTC08_UNITS, USBTC08_TC_TYPE
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
import threading
import datetime
import time
import pandas as pd

class PicoThermocouples(QtWidgets.QWidget):
    def __init__(self, parent, analysisHub):
        super().__init__(parent)

        self.analysisHub = analysisHub

        temperatureGroupBox = QtWidgets.QGroupBox('Temperature measurements')
        temperatureGroupBox.setFixedSize(600, 250)

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
        self.dataFeed.setTitle("Reactor temperatures [\u2103]", color='#000000')
        styles = {'color': '#000000', 'font-size': '14px'}
        self.dataFeed.setLabel('left', "Temperature [\u2103]", **styles)
        self.dataFeed.setLabel('bottom', 'Time [s]', **styles)
        self.dataFeed.addLegend(colCount=5, offset=15, pen=None, labelTextSize='7pt', labelTextColor='#000000')
        channel1 = np.array([])
        channel2 = np.array([])
        channel3 = np.array([])
        channel4 = np.array([])
        channel5 = np.array([])
        timeAxis = np.array([])
        self.channel1Line = self.dataFeed.plot(timeAxis, channel1, pen='r', name='R1')
        self.channel2Line = self.dataFeed.plot(timeAxis, channel2, pen='#36B43D', name='R2')
        self.channel3Line = self.dataFeed.plot(timeAxis, channel3, pen='#001DE4', name='R3')
        self.channel4Line = self.dataFeed.plot(timeAxis, channel4, pen='#E4C500', name='R4')
        self.channel5Line = self.dataFeed.plot(timeAxis, channel5, pen='#D718C3', name='R5')

        self.channel1Label = QtWidgets.QLabel("R1: ")
        self.channel1Value = QtWidgets.QLineEdit()
        self.channel2Label = QtWidgets.QLabel("R2: ")
        self.channel2Value = QtWidgets.QLineEdit()
        self.channel3Label = QtWidgets.QLabel("R3: ")
        self.channel3Value = QtWidgets.QLineEdit()
        self.channel4Label = QtWidgets.QLabel("R4: ")
        self.channel4Value = QtWidgets.QLineEdit()
        self.channel5Label = QtWidgets.QLabel("R5: ")
        self.channel5Value = QtWidgets.QLineEdit()

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)
        grid = QtWidgets.QGridLayout()
        innergrid10 = QtWidgets.QGridLayout()
        grid.addLayout(innergrid10, 1, 0, 5, 1)
        layout.addWidget(temperatureGroupBox)
        temperatureGroupBox.setLayout(grid)
        innergrid10.addWidget(self.connectButton, 0, 0)
        innergrid10.addWidget(self.measureButton, 1, 0)
        innergrid10.addWidget(self.stopMeasureButton, 2, 0)
        innergrid10.addWidget(self.resetGraphButton, 3, 0)
        innergrid10.addWidget(self.disconnectButton, 4, 0)
        innergrid10.addWidget(self.saveDataButton, 5, 0)
        grid.addWidget(self.dataFeed, 1, 1, 5, 1)
        grid.addWidget(self.channel1Label, 1, 2)
        grid.addWidget(self.channel1Value, 1, 3)
        grid.addWidget(self.channel2Label, 2, 2)
        grid.addWidget(self.channel2Value, 2, 3)
        grid.addWidget(self.channel3Label, 3, 2)
        grid.addWidget(self.channel3Value, 3, 3)
        grid.addWidget(self.channel4Label, 4, 2)
        grid.addWidget(self.channel4Value, 4, 3)
        grid.addWidget(self.channel5Label, 5, 2)
        grid.addWidget(self.channel5Value, 5, 3)
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
        self.channels = [1, 2, 3, 4, 5]
        self.numChannels = len(self.channels)
        for i in self.channels:
            self.tc08usb.set_channel(i, USBTC08_TC_TYPE.K)
        self.tc08usbConnected = True
        print('TC-08 picologger connected')

    def measure(self): # Opens new thread for temperature measurement  
        global tc08usbRun, readTemperatureThread, stopTemperatureThread
        if self.tc08usbConnected:
            tc08usbRun = True
            readTemperatureThread = threading.Thread(target = self.read_data)
            readTemperatureThread.start()
            stopTemperatureThread = False

    def read_data(self):
        self.temperatureData = np.array([])
        self.timeAxis = np.array([])
        self.channel1 = np.array([]) #initialise data arrays for each thermocouple
        self.channel2 = np.array([])
        self.channel3 = np.array([])
        self.channel4 = np.array([])
        self.channel5 = np.array([])
        self.timeAxis = np.array([])
        self.startMeasurementTime = datetime.datetime.now()

        while tc08usbRun:
            self.tc08usb.get_single()
            self.experimentTime = (datetime.datetime.now() - self.startMeasurementTime).seconds
            self.timeAxis = np.append(self.timeAxis, self.experimentTime)
            newData = np.array([self.tc08usb[1], self.tc08usb[2], self.tc08usb[3], self.tc08usb[4], self.tc08usb[5]]) # gathers new temperature values from TC-08
            self.channel1 = np.append(self.channel1, newData[0]) # appends new data for each channel to the old array
            self.channel1Value.setText(str(newData[0]))
            self.channel2 = np.append(self.channel2, newData[1])
            self.channel2Value.setText(str(newData[1]))
            self.channel3 = np.append(self.channel3, newData[2])
            self.channel3Value.setText(str(newData[2]))
            self.channel4 = np.append(self.channel4, newData[3])
            self.channel4Value.setText(str(newData[3]))
            self.channel5 = np.append(self.channel5, newData[4])
            self.channel5Value.setText(str(newData[4]))
            self.temperatureXRange = np.size(self.channel1)*1.2
            # self.temperatureYRange = max(self.channel1)*1.2
            # self.dataFeed.setXRange(0, self.temperatureXRange + 100, padding = 0)
            # self.dataFeed.setYRange(0, self.temperatureYRange + 20, padding = 0)
            self.update_plot_data()
            time.sleep(5)
            
            if stopTemperatureThread:
                break

    def update_plot_data(self):
        self.x = self.timeAxis
        self.channel1Line.setData(self.x, self.channel1)
        self.channel2Line.setData(self.x, self.channel2)
        self.channel3Line.setData(self.x, self.channel3)
        self.channel4Line.setData(self.x, self.channel4)
        self.channel5Line.setData(self.x, self.channel5)
        self.temperatureXRange = len(self.channel1)*1.2
        self.temperatureYRange = max(self.channel1)*1.2
        self.dataFeed.setXRange(0, self.temperatureXRange + 100, padding = 0)
        self.dataFeed.setYRange(0, self.temperatureYRange + 20, padding = 0)

    def stopMeasure(self):
        global tc08usbRun, stopTemperatureThread, readTemperatureThread
        stopTemperatureThread = True
        readTemperatureThread.join()
        tc08usbRun = False
        print("Measurement stopped")

    def resetGraph(self):
        self.dataFeed.clear()
        self.channel1 = np.array([])
        self.channel2 = np.array([])
        self.channel3 = np.array([])
        self.channel4 = np.array([])
        self.channel5 = np.array([])
        self.timeAxis = np.array([])
        self.update_plot_data()
    
    def saveData(self):
        savePath = (self.analysisHub.methodHandler.savePath + '-temperature.csv')
        print(savePath)
        df = pd.DataFrame(data=[self.x, self.channel1, self.channel2, self.channel3, self.channel4, self.channel5]).T
        df.columns=['Time (s)',
        'Channel 1 temperature ([\u2103])',
        'Channel 2 temperature ([\u2103])',
        'Channel 3 temperature ([\u2103])',
        'Channel 4 temperature ([\u2103])',
        'Channel 5 temperature ([\u2103])'
        ]        
        pd.DataFrame(df).to_csv(savePath)

    def disconnect(self):
        self.tc08usb.close_unit()
