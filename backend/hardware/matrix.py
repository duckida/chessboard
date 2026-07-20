# Simple serial reading object
# Reads the serial and outputs it as a list

import serial
import json

class ChessboardMatrix:
    def __init__(self.):
        self.ser = serial.Serial('/dev/serial0', 115200, timeout=1)

    def get_state(self):
        matrix_string = self.ser.readline().decode().strip()
        matrix = json.loads(matrix_string)
        return matrix
