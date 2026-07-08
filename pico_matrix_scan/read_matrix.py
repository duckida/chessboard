# Reads and prints keypad keys

from time import sleep
from keypad_lib import Keypad
from machine import Pin

chessboard = [[1] * 8 for _ in range(8)]  # 1 is no piece, 0 is piece

ROW_GPIO_LIST = [Pin(1), Pin(0)]
COL_GPIO_LIST = [Pin(2), Pin(3)]

keypad = Keypad(ROW_GPIO_LIST, COL_GPIO_LIST)

while True:
    list = keypad.read_keypad()
    print("----")
    print(list[0])
    print(list[1])
    sleep(0.1)  # debounce and delay
