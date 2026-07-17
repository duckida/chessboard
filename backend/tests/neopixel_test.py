from rpi_ws281x import PixelStrip, Color, ws
import time

LED_COUNT = 64       # Number of LEDs
LED_GPIO = 19
LED_FREQ = 800000
LED_DMA = 5
LED_INVERT = False
LED_BRIGHTNESS = 50

strip = PixelStrip(LED_COUNT, LED_GPIO, LED_FREQ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, channel=1, strip_type=ws.WS2811_STRIP_GRB)
strip.begin()

for i in range(strip.numPixels()):
    strip.setPixelColor(i, Color(139,69,19))

strip.show()
