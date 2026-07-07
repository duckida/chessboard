import neopixel
from machine import Pin

STRIP_LENGTH = 4
STRIP_PIN = 16
BRIGHTNESS = 0.2
strip = neoRing = neopixel.NeoPixel(Pin(STRIP_PIN), STRIP_LENGTH)


def set_brightness(color):
    r, g, b = color
    r = int(r * BRIGHTNESS)
    g = int(g * BRIGHTNESS)
    b = int(b * BRIGHTNESS)
    return (r, g, b)


while True:
    white_color = set_brightness((0, 255, 0))
    strip[0] = strip[2] = white_color

    black_color = set_brightness((0, 0, 255))
    strip[1] = strip[3] = black_color

    strip.write()

    time.sleep_ms(200)
