# Simple serial reading object
# Reads the serial and outputs it as a list

import serial
import json

class ChessboardMatrix:
    def __init__(self):
        self.ser = serial.Serial('/dev/serial0', 115200, timeout=1)

    def get_state(self): # this function was written by Gemini AI
        while True:
            try:
                # Read a full line from the hardware
                raw_bytes = self.ser.readline()

                # Decode to string, ignoring tiny byte anomalies at the split
                matrix_string = raw_bytes.decode("utf-8", errors="ignore").strip()

                # If it's a blank line, skip it and keep reading
                if not matrix_string:
                    continue

                # Parse the valid JSON list and hand it directly back to your test loop
                matrix = json.loads(matrix_string)
                return matrix

            except (UnicodeDecodeError, json.JSONDecodeError):
                # If we caught a corrupted line mid-stream on startup,
                # silently drop it and try the next read immediately.
                continue
