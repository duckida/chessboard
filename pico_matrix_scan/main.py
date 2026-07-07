from time import sleep

from machine import Pin

chessboard = [[1] * 8 for _ in range(8)]  # 1 is no piece, 0 is piece

switch = Pin(0, Pin.IN, Pin.PULL_UP)

while True:
    print(switch.value())
    sleep(0.1)
