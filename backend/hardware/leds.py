from rpi_ws281x import PixelStrip, Color, ws
import time

class LEDStrip:
    PIXEL_SQUARE_MAPPING = {
        "a1": 56, "a2": 55, "a3": 40, "a4": 39, "a5": 24, "a6": 23, "a7": 8,  "a8": 7,
        "b1": 57, "b2": 54, "b3": 41, "b4": 38, "b5": 25, "b6": 22, "b7": 9,  "b8": 6,
        "c1": 58, "c2": 53, "c3": 42, "c4": 37, "c5": 26, "c6": 21, "c7": 10, "c8": 5,
        "d1": 59, "d2": 52, "d3": 43, "d4": 36, "d5": 27, "d6": 20, "d7": 11, "d8": 4,
        "e1": 60, "e2": 51, "e3": 44, "e4": 35, "e5": 28, "e6": 19, "e7": 12, "e8": 3,
        "f1": 61, "f2": 50, "f3": 45, "f4": 34, "f5": 29, "f6": 18, "f7": 13, "f8": 2,
        "g1": 62, "g2": 49, "g3": 46, "g4": 33, "g5": 30, "g6": 17, "g7": 14, "g8": 1,
        "h1": 63, "h2": 48, "h3": 47, "h4": 32, "h5": 31, "h6": 16, "h7": 15, "h8": 0,
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
