# Simple serial reading object
# Reads the serial and outputs it as a list

import serial
import json

class ChessboardMatrix:
    def __init__(self):
        self.ser = serial.Serial('/dev/serial0', 115200, timeout=1)

    def get_state(self):
        # Throw away any backlog we only want the freshest reading
        self.ser.reset_input_buffer()

        while True:
            try:
                raw_bytes = self.ser.readline()
                matrix_string = raw_bytes.decode("utf-8", errors="ignore").strip()
                if not matrix_string:
                    continue
                matrix = json.loads(matrix_string)
                return matrix
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
