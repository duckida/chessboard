# main.py for reed matrix scanning
# reads the switches and outputs a 2D list of rows/columns of switches to UART Serial

from time import sleep
from keypad_lib import Keypad
from machine import Pin, UART

ROW_GPIO_LIST = [Pin(0), Pin(1), Pin(2), Pin(3), Pin(4), Pin(5), Pin(6), Pin(7)]
COL_GPIO_LIST = [Pin(8), Pin(9), Pin(10), Pin(11), Pin(12), Pin(13), Pin(14), Pin(15)]

keypad = Keypad(ROW_GPIO_LIST, COL_GPIO_LIST)
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

while True:
    key_list = keypad.read_keypad()
    uart.write(str(key_list).encode("utf-8") + b"\n")
    sleep(0.02)  # debounce and delay
