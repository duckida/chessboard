from hardware import leds, matrix
import requests
from time import sleep
import copy

BASE_URL = "http://127.0.0.1:5000"

# matrix setup
m = matrix.ChessboardMatrix()
LETTERS = "abcdefgh"
old_state = copy.deepcopy(m.get_state())

led_strip = leds.LEDStrip(150)

# initialize with a chessboard pattern
led_strip.set_matrix_rgb((139,69,19), (0,0,0))
led_strip.update()

down_value = ""
up_value = ""

previous_ai_move = ""

requests.post(f"{BASE_URL}/reset-stockfish-game", timeout=1)
print("Ready")

while True:
    while up_value == "" or down_value == "": # no piece has been moved yet
        state = m.get_state() # read the matrix

        for y_index, y_value in enumerate(state): # for each row
            for x_index, x_value in enumerate(y_value): # check each switch in it
                if x_value != old_state[y_index][x_index]: # ooh something's changed!
                    x = LETTERS[x_index]
                    y = y_index + 1

                    if x_value == 1: # a piece is here now
                        down_value = f"{x}{y}"
                        print(f"DOWN {down_value}")
                        sleep(0.2)
                    elif x_value == 0:
                        up_value = f"{x}{y}"
                        print(f"UP {up_value}")
                        sleep(0.2)

        old_state = copy.deepcopy(state)
        sleep(0.05)

    user_move = f"{up_value}{down_value}"
    up_value = down_value = "" # reset for next time
    print(user_move)

    if user_move != previous_ai_move: # it's not just them moveing the AI pieces
        move_from = user_move[0:2]
        move_to = user_move[2:4]

        led_strip.set_matrix_rgb((139,69,19), (0,0,0))

        led_strip.set_square_rgb(move_from, (255,255,255))
        led_strip.set_square_rgb(move_to, (255,255,255))
        led_strip.update()
        sleep(0.5)

        requests.post(f"{BASE_URL}/sf-make-human-move", json={"move": user_move}, timeout=5) # make their move

        ai_move_req = requests.post(f"{BASE_URL}/sf-play", timeout=5) # let the ai make it's move
        ai_move = ai_move_req.text
        previous_ai_move = ai_move

        print(f"AI move: {ai_move}") # print

        move_from = ai_move[0:2]
        move_to = ai_move[2:4]

        led_strip.set_square_rgb(move_from, (255,0,0))
        led_strip.set_square_rgb(move_to, (0,255,0))
        led_strip.update()
        sleep(0.5)
