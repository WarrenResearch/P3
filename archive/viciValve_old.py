import serial.tools.list_ports
import serial
import time

class viciValve(object):

    def connect(self, COM):
        self.COMPort = COM
        self.valveObj = serial.Serial(port = self.COMPort, baudrate = 9600, timeout = 2, stopbits=1, parity='N', bytesize=8)
        print("Vici valve connected on port " + self.COMPort)
        
    def switch(self):
        command = 'TO'
        msg = command.encode('ASCII')
        print('Command sent: ' + str(msg))
        self.valveObj.write(msg)

    def positionA(self):
        command = 'CW\r\n'.encode('ASCII')
        self.valveObj.write(command)

    def positionB(self):
        command = 'CC\r\n'.encode('ASCII')
        self.valveObj.write(command)