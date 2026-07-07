from time import sleep

import neopixel
from machine import Pin

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


while True:
    white_color = set_brightness((255, 255, 255))
    strip[0] = strip[2] = white_color

    black_color = set_brightness((139, 69, 19))

    strip[1] = strip[3] = black_color

    strip[2] = strip[3] = (0, 0, 0)

    strip.write()

    sleep(0.2)
