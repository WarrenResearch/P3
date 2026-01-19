import serial
import time

class selectionValve(object):

    def connect(self, COM):
        self.valve = serial.Serial(port = COM, baudrate = 9600, timeout = .1)
        print("Switching valve connected on port " + COM)
    
    def switch(self, COM=any, valvePort=int):
        command = '<p' + str(valvePort) + '>'
        self.valve.write(bytes(command, 'utf-8'))
        time.sleep(2)

    def home(self):
        self.valve.write(bytes('<p1>', 'utf-8'))
        time.sleep(2)

    def p2(self):
        self.valve.write(bytes('<p2>', 'utf-8'))
        time.sleep(2)
        
    def p3(self):
        self.valve.write(bytes('<p3>', 'utf-8'))
        time.sleep(2) 
        
    def p4(self):
        self.valve.write(bytes('<p4>', 'utf-8'))
        time.sleep(2)

    def p5(self):
        self.valve.write(bytes('<p5>', 'utf-8'))
        time.sleep(2)

    def p6(self):
        self.valve.write(bytes('<p6>', 'utf-8'))
        time.sleep(2)

    def p7(self):
        self.valve.write(bytes('<p7>', 'utf-8'))
        time.sleep(2) 

    def p8(self):
        self.valve.write(bytes('<p8>', 'utf-8'))
        time.sleep(2)