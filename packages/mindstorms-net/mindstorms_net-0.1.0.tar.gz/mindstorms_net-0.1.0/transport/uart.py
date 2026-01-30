from machine import UART
from mindstorms_net.protocol import pack, unpack

class UARTTransport:
    def __init__(self, tx=None, rx=None, baud=115200, serial_port=None):
        if serial_port:
            import serial
            self.uart = serial.Serial(serial_port, baud)
        else:
            self.uart = UART(1, tx=tx, rx=rx, baudrate=baud)

    def send(self, msg):
        self.uart.write(msg.encode('utf-8') + b"\n")

    def receive(self):
        if hasattr(self.uart, "in_waiting"):
            buf = []
            while self.uart.in_waiting:
                buf.append(self.uart.readline().decode().strip())
            return buf
        else:
            lines = []
            while self.uart.any():
                line = self.uart.readline()
                if line:
                    lines.append(line.decode().strip())
            return lines
