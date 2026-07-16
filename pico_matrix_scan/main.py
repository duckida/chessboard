# main.py for reed matrix scanning
# reads the switches and outputs a 2D list of rows/columns of switches to Serial

from time import sleep
from keypad_lib import Keypad
from machine import Pin

ROW_GPIO_LIST = [Pin(0), Pin(1), Pin(2), Pin(3), Pin(4), Pin(5), Pin(6), Pin(7)]
COL_GPIO_LIST = [Pin(8), Pin(9), Pin(10), Pin(11), Pin(12), Pin(13), Pin(14), Pin(15)]

keypad = Keypad(ROW_GPIO_LIST, COL_GPIO_LIST)

while True:
    key_list = keypad.read_keypad()
    print(key_list)
    sleep(0.1)  # debounce and delay
