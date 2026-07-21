from hardware import matrix

m = matrix.ChessboardMatrix()

letters = "abcdefgh"

while True:
    x = "a"
    y = 1
    state = m.get_state()
    for y_index, y_value in enumerate(state):
       for x_index, x_value in enumerate(y_value):
           if x_value == 1:
               x = letters[x_index]
               y = y_index + 1
               print(f"{x}{y}")
