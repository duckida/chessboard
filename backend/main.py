from hardware import leds, matrix
import requests
from time import sleep

BASE_URL = "http://127.0.0.1:5000"

led_strip = leds.LEDStrip(200)
led_strip.set_matrix_rgb((139,69,19))
led_strip.update()

while True:
    user_move = input("enter move: ")

    move_from = user_move[0:2]
    move_to = user_move[2:4]

    led_strip.set_matrix_rgb((139,69,19))

    led_strip.set_square_rgb(move_from, (255,255,255))
    led_strip.set_square_rgb(move_to, (255,255,255))
    led_strip.update()
    sleep(0.5)

    requests.post(f"{BASE_URL}/sf-make-human-move", json={"move": user_move}, timeout=5) # make their move

    ai_move_req = requests.post(f"{BASE_URL}/sf-play", timeout=5) # let the ai make it's move
    ai_move = ai_move_req.text

    print(f"AI MOVE: {ai_move}")

    move_from = ai_move[0:2]
    move_to = ai_move[2:4]

    led_strip.set_square_rgb(move_from, (255,0,0))
    led_strip.set_square_rgb(move_to, (0,255,0))
    led_strip.update()
    sleep(0.5)
