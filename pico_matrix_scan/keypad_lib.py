# based on https://github.com/PerfecXX/MicroPython-SimpleKeypad/blob/main/keypad.py

from machine import Pin
from time import sleep


class KeypadException(Exception):
    """
    Exception class for keypad-related errors.
    """
    pass

class Keypad:
    def __init__(self, row_pins, column_pins):
        """
        Initialize the keypad object.

        Args:
            row_pins (list): List of row pins.
            column_pins (list): List of column pins.

        Raises:
            KeypadException: If pins or keys are not properly defined.
        """
        if not all(isinstance(pin, Pin) for pin in row_pins):
            raise KeypadException("Row pins must be instances of Pin.")

        if not all(isinstance(pin, Pin) for pin in column_pins):
            raise KeypadException("Column pins must be instances of Pin.")


        self.row_pins = row_pins
        self.column_pins = column_pins

        for pin in self.row_pins:
            pin.init(Pin.IN, Pin.PULL_UP)

        for pin in self.column_pins:
            pin.init(Pin.OUT)

    def read_keypad(self):
        """
        Read the keypad and return 2D array of row/columns of key states.
        [
        [0, 1],
        [1, 0]
        ]

        Raises:
            KeypadException: If pins or keys are not properly defined.
        """
        if not self.column_pins:
            raise KeypadException("No column pins defined.")

        if not self.row_pins:
            raise KeypadException("No row pins defined.")

        keys_array = [[0] * len(self.column_pins) for _ in range(len(self.row_pins))]

        # new logic

        for column_index, column_pin in enumerate(self.column_pins):
            column_pin.value(0)  # Set column pin to LOW

            for row_index, row_pin in enumerate(self.row_pins):
                if not row_pin.value(): # pressed
                    keys_array[row_index][column_index] = 1

            column_pin.value(1)  # Set column pin back to HIGH

        return keys_array
