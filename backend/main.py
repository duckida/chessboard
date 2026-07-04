import os

import berserk
from flask import Flask

app = Flask(__name__)

LICHESS_TOKEN = os.environ["LICHESS_TOKEN"]


class Opponent:
    def __init__(self, game_id, username, elo, color):
        self.game_id = game_id
        self.username = username
        self.elo = elo
        self.color = color


class Game:
    def __init__(self):
        self.session = berserk.TokenSession(LICHESS_TOKEN)
        self.client = berserk.Client(session=self.session)
        self.board = self.client.board
        self.playing = False

    def search(self, time, increment):  # time in mins, increment in seconds
        self.board.seek(time=time, increment=increment, color="random")

    def update_stream(self):
        for event in self.board.stream_incoming_events():
            if event["type"] == "gameStart":
                self.join(event)

    def join(self, data):
        print(data)
        game_data = data["game"]
        print(game_data)
        if not self.playing:  # not already in a game
            self.game_id = game_data["gameId"]
            self.playing = True
            self.color = game_data["color"]

            if game_data["color"] == "white":
                opponent_color = "black"
            else:
                opponent_color = "white"

            opponent_data = game_data["opponent"]
            self.opponent = Opponent(
                self.game_id,
                opponent_data["id"],
                opponent_data["rating"],
                opponent_color,
            )


@app.route("/")
def index_page():
    return "<p>Smart chessboard API</p>"


def test():
    game = Game()
    game.search(10, 0)
    game.update_stream()
    print(game.opponent.username)


if __name__ == "__main__":
    test()
    # app.run(debug=True)
