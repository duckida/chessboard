# matrix demo
# turns the LED of a square green if there's a piece on it

from time import sleep
from keypad_lib import Keypad
from machine import Pin
import neopixel

STRIP_LENGTH = 4
STRIP_PIN = 16
BRIGHTNESS = 1
strip = neoRing = neopixel.NeoPixel(Pin(STRIP_PIN), STRIP_LENGTH)

def set_brightness(color):
    r, g, b = color
    r = int(r * BRIGHTNESS)
    g = int(g * BRIGHTNESS)
    b = int(b * BRIGHTNESS)
    return (r, g, b)

ROW_GPIO_LIST = [Pin(1), Pin(0)]
COL_GPIO_LIST = [Pin(2), Pin(3)]

OFF_COLOR = set_brightness((255,255,255))
ON_COLOR = set_brightness((0,255,0))

keypad = Keypad(ROW_GPIO_LIST, COL_GPIO_LIST)

while True:
    key_list = keypad.read_keypad()
    print("----")
    for index, square in enumerate(key_list[0]):
        if square == 1:
            strip[index] = ON_COLOR
            print(index)
        else:
            strip[index] = OFF_COLOR

    for index, square in enumerate(key_list[1]):
        if square == 1:
            strip[STRIP_LENGTH - 1 -index] = ON_COLOR
        else:
            strip[STRIP_LENGTH - 1 - index] = OFF_COLOR

    print(key_list[0])
    print(key_list[1])

    strip.write()
    sleep(0.1)  # debounce and delay
