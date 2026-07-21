from rpi_ws281x import PixelStrip, Color, ws
import time

class LEDStrip:
    PIXEL_SQUARE_MAPPING = {
        "a1": 7,  "a2": 8,  "a3": 23, "a4": 24, "a5": 39, "a6": 40, "a7": 55, "a8": 56,
        "b1": 6,  "b2": 9,  "b3": 22, "b4": 25, "b5": 38, "b6": 41, "b7": 54, "b8": 57,
        "c1": 5,  "c2": 10, "c3": 21, "c4": 26, "c5": 37, "c6": 42, "c7": 53, "c8": 58,
        "d1": 4,  "d2": 11, "d3": 20, "d4": 27, "d5": 36, "d6": 43, "d7": 52, "d8": 59,
        "e1": 3,  "e2": 12, "e3": 19, "e4": 28, "e5": 35, "e6": 44, "e7": 51, "e8": 60,
        "f1": 2,  "f2": 13, "f3": 18, "f4": 29, "f5": 34, "f6": 45, "f7": 50, "f8": 61,
        "g1": 1,  "g2": 14, "g3": 17, "g4": 30, "g5": 33, "g6": 46, "g7": 49, "g8": 62,
        "h1": 0,  "h2": 15, "h3": 16, "h4": 31, "h5": 32, "h6": 47, "h7": 48, "h8": 63,
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
