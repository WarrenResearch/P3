from msilib.schema import PublishComponent
import serial

######################################################################
# TELEDYNE PUMP COMMANDS #
######################################################################

class teledynePump(object):
    # def __init__(self, COM, flowrate):
    #     self.COMPort = COM
    #     self.flowRate = flowrate
    #     flowrate = 0

    def connect(self, COMPort):
        self.COMPort = COMPort
        self.pump =  serial.Serial(port = self.COMPort, baudrate = 9600)
        print("Device connected on port " + self.COMPort)

    def setFlowrate(self, flowrate):   
        pump_flowrate = float(flowrate)
        if float(pump_flowrate) == 10:
                flowrate_comm_temp = str(9999)
        elif 1 <= float(pump_flowrate) < 10:
                flowrate_comm_temp = str(int(pump_flowrate*100))
        elif float(pump_flowrate) < 1:
                flowrate_comm_temp = '0' + str(int(pump_flowrate*100))
        elif float(pump_flowrate) < 0.1:
                flowrate_comm_temp = '00' + str(int(pump_flowrate*100))
        elif float(pump_flowrate) > 10:
                flowrate_comm_temp = str(9999)
                err = "Max flow rate is 10 mL/min"
                print(err)
        command_str = 'Fl' + flowrate_comm_temp
        self.pump.write(bytes(command_str, 'utf-8'))

    def start(self):
        # pump = serial.Serial(port = 'COM' + self.COMPort, baudrate = 9600)
        self.pump.write(bytes('RU', 'utf-8'))

    def stop(self):
        # pump = serial.Serial(port = 'COM' + self.COMPort, baudrate = 9600)
        self.pump.write(bytes('ST', 'utf-8'))