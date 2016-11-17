import time
import io
import serial
import sys
import glob
from sample import Sampler

BAUD_RATE = 9600
STOP_BITS = serial.STOPBITS_ONE
BYTE_SIZE = serial.EIGHTBITS


# all of this code exists so that I can use a dumb terminal to talk to my code.
class SerialInterface:

    def __init__(self):
        existing_ports = SerialInterface.serial_ports()
        if len(existing_ports) > 1:
            print('WARN! more than one serial port is active on the computer.  Blindly using first one...')
        if len(existing_ports) is 0:
            print('ERR! no serial ports found on the computer! Exiting...')
            exit(-1)
        print('using port: ' + existing_ports[0])
        port_name = existing_ports[0]
        self.ser = serial.Serial(port=port_name, baudrate=9600, bytesize=BYTE_SIZE, parity=serial.PARITY_NONE,
                                 stopbits=STOP_BITS, write_timeout=10, timeout=10)
        self.sampler = Sampler()

    @staticmethod
    def serial_ports():
        if sys.platform.startswith('win'):  # windows COM port enumerations
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):  # linux and cygwin support
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):  # OSX support
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:  # for every possible port name
            try:
                s = serial.Serial(port)  # open it and close it
                s.close()
                result.append(port)  # if nothing went wrong, the port exists on the system
            except (OSError, serial.SerialException):  # if something went wrong, the port does not exist
                pass
        return result  # return the list of ports that currently actually exist on the system

    def respond_to_input_loop(self):
        sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser, 1), newline='\r', line_buffering=True)
        while True:
            time.sleep(5)  # pause
            self.ser.write(bytes([12]))  # clear the screen
            self.ser.write(b'>')  # provide a prompt
            query = sio.readline().lower().replace('\r', '\n')
            if not query:
                pass
            else:
                print('recieved query: ' + query)
                response = self.sampler.sample(prime_text=query, num_sample_symbols=(80*25))
                response = response.replace('\n', '\r').replace('\r\r', '\r').replace('\r', '\r\n')
                response = response[:140]
                print('responding with response: ' + response)
                response += '\a'
                self.ser.write(bytes([12]))
                self.ser.write(response.encode('ascii'))

    def __del__(self):
        self.ser.close()

if __name__ == "__main__":
    SerialInterface().respond_to_input_loop()
