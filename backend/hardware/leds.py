from rpi_ws281x import PixelStrip, Color, ws
import time

class LEDStrip:
    PIXEL_SQUARE_MAPPING = {
        "a1": 7,  "a2": 6,  "a3": 5,  "a4": 4,  "a5": 3,  "a6": 2,  "a7": 1,  "a8": 0,
        "b1": 8,  "b2": 9,  "b3": 10, "b4": 11, "b5": 12, "b6": 13, "b7": 14, "b8": 15,
        "c1": 23, "c2": 22, "c3": 21, "c4": 20, "c5": 19, "c6": 18, "c7": 17, "c8": 16,
        "d1": 24, "d2": 25, "d3": 26, "d4": 27, "d5": 28, "d6": 29, "d7": 30, "d8": 31,
        "e1": 39, "e2": 38, "e3": 37, "e4": 36, "e5": 35, "e6": 34, "e7": 33, "e8": 32,
        "f1": 40, "f2": 41, "f3": 42, "f4": 43, "f5": 44, "f6": 45, "f7": 46, "f8": 47,
        "g1": 55, "g2": 54, "g3": 53, "g4": 52, "g5": 51, "g6": 50, "g7": 49, "g8": 48,
        "h1": 56, "h2": 57, "h3": 58, "h4": 59, "h5": 60, "h6": 61, "h7": 62, "h8": 63,
    }

    LED_COUNT = 64
    LED_GPIO = 19
    LED_FREQ = 800000
    LED_DMA = 10
    LED_INVERT = False

    def __init__(self, brightness):
        self.brightness = brightness
        self.strip = PixelStrip(self.LED_COUNT, self.LED_GPIO, self.LED_FREQ, self.LED_DMA, self.LED_INVERT, brightness, channel=1, strip_type=ws.WS2811_STRIP_GRB)
        self.strip.begin()

    def set_square_rgb(self, square, rgb):
        pixel_num = self.PIXEL_SQUARE_MAPPING[square]
        self.strip.setPixelColor(pixel_num, Color(*rgb))

    def set_all_rgb(self, rgb):
        for pixel in range(self.LED_COUNT):
            self.strip.setPixelColor(pixel, Color(*rgb))

    def set_matrix_rgb(self, rgb_white, rgb_black):
        for pixel in range(0, self.LED_COUNT, 2):
            self.strip.setPixelColor(pixel, Color(*rgb_black))

        for pixel in range(1, self.LED_COUNT, 2):
            self.strip.setPixelColor(pixel, Color(*rgb_white))

    def update(self):
        self.strip.show()
