from rpi_ws281x import PixelStrip, Color, ws
import time

class LEDStrip:
    PIXEL_SQUARE_MAPPING = {
        "a1": 63, "a2": 48, "a3": 47, "a4": 32, "a5": 31, "a6": 16, "a7": 15, "a8": 0,
        "b1": 62, "b2": 49, "b3": 46, "b4": 33, "b5": 30, "b6": 17, "b7": 14, "b8": 1,
        "c1": 61, "c2": 50, "c3": 45, "c4": 34, "c5": 29, "c6": 18, "c7": 13, "c8": 2,
        "d1": 60, "d2": 51, "d3": 44, "d4": 35, "d5": 28, "d6": 19, "d7": 12, "d8": 3,
        "e1": 59, "e2": 52, "e3": 43, "e4": 36, "e5": 27, "e6": 20, "e7": 11, "e8": 4,
        "f1": 58, "f2": 53, "f3": 42, "f4": 37, "f5": 26, "f6": 21, "f7": 10, "f8": 5,
        "g1": 57, "g2": 54, "g3": 41, "g4": 38, "g5": 25, "g6": 22, "g7": 9,  "g8": 6,
        "h1": 56, "h2": 55, "h3": 40, "h4": 39, "h5": 24, "h6": 23, "h7": 8,  "h8": 7,
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
