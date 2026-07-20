from hardware import leds

strip = leds.LEDStrip(200)
strip.set_matrix_rgb((139,69,19))
strip.update()
