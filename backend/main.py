from hardware import leds, matrix
import requests

BASE_URL = "http://127.0.0.1:5000"

led_strip = leds.LEDStrip(200)

while True:
    led_strip.set_matrix_rgb((139,69,19))
    led_strip.update()

    user_move = input("enter move")
    requests.post(f"{BASE_URL}/sf-make-human-move", f'{"move": move}') # make their move

    ai_move = requests.post(f"{BASE_URL}/sf-play").text # let the ai make it's move
    move_from = ai_move[0:1]
    move_to = ai_move[2:3]

    led_strip.set_square_rgb(move_from, (255,0,0))
    led_strip.set_square_rgb(move_to, (0,255,0))
    led_strip.update()
