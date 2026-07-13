import copy
import os
import threading

import berserk
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import chess.engine

app = Flask(__name__)
CORS(app)

load_dotenv()
LICHESS_TOKEN = os.environ["LICHESS_TOKEN"]


class Opponent:
    def __init__(self, game_id, username, elo, color):
        self.game_id = game_id
        self.username = username
        self.elo = elo
        self.color = color


class LichessGame:
    def __init__(self):
        self.session = berserk.TokenSession(LICHESS_TOKEN)
        self.client = berserk.Client(session=self.session)
        self.board = self.client.board
        self.playing = False
        self.results = {"state": "idle"}

    def search(self, time, increment):  # time in mins, increment in seconds
        if self.results["state"] == "found":  # already found
            return  # leave

        self.results = {"state": "searching", "gameid": ""}
        self.board.seek(time=time, increment=increment, color="random")
        for event in self.board.stream_incoming_events():
            if event["type"] == "gameStart":
                self.join(event)
                return

    def update(self):
        for state in self.board.stream_game_state(self.game_id):
            self.results = {"state": "playing", "gamedata": state}

    def join(self, data):
        print("joined game")
        game_data = data["game"]
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

            self.results = {"state": "found", "gameid": self.game_id}

    def reset_game(self):
        self.playing = False
        self.game_id = ""
        self.opponent = None
        self.results = {"state": "idle"}

    def make_move(self, move):
        self.board.make_move(self.game_id, move)

class StockfishGame:
    limit = chess.engine.Limit(time=0.5)
    def __init__(self):
        self.board = chess.Board()

    def make_stockfish_move(self):
        result = stockfish.play(self.board, self.limit)
        self.board.push(result)

    def make_human_move(self, move):
        move_object = chess.Move.from_uci(move)
        self.board.push(move_object)

    def get_fen(self):
        return self.board.fen()

# Stockfish routes
stockfish = chess.engine.SimpleEngine.popen_uci("../stockfish")
stockfish.configure({
    "Hash": 4,          # Use 4MB of hash table
    "Threads": 1,        # Use only 1 CPU thread
})

# this is for playing against human, suggesting next best move
@app.route("/sf-analyze-fen", methods=["POST"])
def sf_analyze_fen():
    fen = request.json.get("fen")
    board = chess.Board(fen)
    limit = chess.engine.Limit(time=0.5)
    move = stockfish.play(board, limit).move

    return str(move)

# these are for playing against stockfish
stockfishGame = StockfishGame()

@app.route("/sf-play", methods=["POST"])
def sf_play():
    stockfishGame.make_stockfish_move()

@app.route("/sf-make-human-move", methods=["POST"])
def sf_make_human_move():
    move = request.json.get("move")
    stockfishGame.make_human_move(move)

# LiChess routes
game = LichessGame()
TIME = 10
INCREMENT = 0

@app.route("/search-and-join-game", methods=["POST"])
def search_and_join_game():
    search_thread = threading.Thread(
        target=game.search, args=(TIME, INCREMENT), daemon=True
    )
    search_thread.start()
    return "success"


@app.route("/reset-game", methods=["POST"])
def reset_game():
    game.reset_game()
    return "success"


@app.route("/update-game", methods=["POST"])
def update_game():
    game_thread = threading.Thread(target=game.update, daemon=True)
    game_thread.start()
    return "success"


@app.route("/make-move", methods=["POST"])
def li_make_human_move():
    move = request.json.get("move")

    try:
        game.make_move(move)
        return "success"
    except Exception as e:
        return f"error {e}"


@app.route("/lichess-status")
def return_status():
    results = copy.deepcopy(game.results)  # to avoid changing the original pointer
    print(results)

    if "gamedata" in results and results["gamedata"]["type"] == "gameState":
        for key in ["binc", "winc", "wtime", "btime"]:
            results["gamedata"][key] = results["gamedata"][key].total_seconds()

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
