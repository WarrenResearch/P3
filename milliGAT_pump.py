import serial

class Milligat:

    def __init__(self, name, ser):
        """ Creates a controller for the MilliGat pumps

        Args:
            name: The name of the pump being controlled. This should be either 'A', 'B' or 'C'.
            ser: The serial connection used to communicate with the pump. See pyserial for more information.
        """
        self.name = name
        self.ser = ser
        try:
          ser.open()
        except:pass
    
    def set_flow_rate(self, flow_rate, pump_type=str):
        """"
        The flow rate is given in mL/min. 
        The pump type should be either 'HF': High flow or 'LF': low flow
        as the conversion to mL/min depends on the type of Milligat
        """
        if pump_type == 'LF':
            flow_rate_corrected = int(round(40533*flow_rate, 0))
        else:
            flow_rate_corrected = int(round(6454*flow_rate, 0))

        msg = f'{self.name}SL = {flow_rate_corrected}\r\n'.encode()
        self.ser.write(msg)

    def stop_pump(self):
        self.set_flow_rate(flow_rate=0)

    def aspirate(self, flow_rate, volume, pump_type=str):

        if pump_type == 'LF':
            flow_rate_corrected = int(round(81067*flow_rate, 0))
        else:
            flow_rate_corrected = int(round(13398*flow_rate, 0))
        
        msg1 = f'{self.name}VM = {flow_rate_corrected}\r\n'.encode()
        print(msg1)

        msg2 = f'{self.name}MR = {volume*-1}\r\n'.encode()
        print(msg2)

        self.ser.write(msg1)
        self.ser.write(msg2)

    def dispense(self, flow_rate, volume, pump_type=str):

        if pump_type == 'LF':
            flow_rate_corrected = int(round(81067*flow_rate, 0))
        else:
            flow_rate_corrected = int(round(13398*flow_rate, 0))
        
        msg1 = f'{self.name}VM = {flow_rate_corrected}\r\n'.encode()
        print(msg1)

        msg2 = f'{self.name}MR = {volume*1}\r\n'.encode()
        print(msg2)
        
        self.ser.write(msg1)
        self.ser.write(msg2)
