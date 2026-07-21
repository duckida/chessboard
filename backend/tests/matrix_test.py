from hardware import matrix
from time import sleep
import copy

m = matrix.ChessboardMatrix()

letters = "abcdefgh"

old_state = copy.deepcopy(m.get_state())

while True:
    x = "a"
    y = 1
    state = m.get_state()

    for y_index, y_value in enumerate(state):
       for x_index, x_value in enumerate(y_value):
           if x_value != old_state[y_index][x_index]:
               pos = ""
               if x_value == 1:
                   pos = "down"# now there's a piece
               else: pos = "up"

               x = letters[x_index]
               y = y_index + 1
               print(f"{pos} {x}{y}")

    old_state = copy.deepcopy(state)
    sleep(0.05)
