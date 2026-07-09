# main.py for reed matrix scanning
# reads the switches and outputs a 2D list of rows/columns of switches to Serial

from time import sleep
from keypad_lib import Keypad
from machine import Pin

ROW_GPIO_LIST = [Pin(1), Pin(0)]
COL_GPIO_LIST = [Pin(2), Pin(3)]
keypad = Keypad(ROW_GPIO_LIST, COL_GPIO_LIST)

while True:
    key_list = keypad.read_keypad()
    print(key_list)
    sleep(0.05)  # debounce and delay
