import serial.tools.list_ports
import serial
import time

class rheodyneValve(object):
    
    def connect(self, COM):
        self.COMPort = COM
        self.valve = serial.Serial(port = self.COMPort, baudrate = 19200, timeout = 2)
        print("Switching valve connected on port " + self.COMPort)

    def switch(self, position):

        command = 'P{:02X}\r'.format(int(position))
        msg = command.encode('utf-8')
        self.valve.write(msg)