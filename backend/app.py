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
        print("joined lichess game")
        game_data = data["game"]
        if not self.playing:  # not already in a lichess_game
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

            self.results = {"state": "found", "lichess_gameid": self.game_id}

    def reset_game(self):
        self.playing = False
        self.game_id = ""
        self.opponent = None
        self.results = {"state": "idle"}

    def make_move(self, move):
        self.board.make_move(self.game_id, move)

class HumanGame:
    stockfish = chess.engine.SimpleEngine.popen_uci("../stockfish")
    stockfish.configure({
        "Hash": 4,          # Use 4MB of hash table
        "Threads": 1,        # Use only 1 CPU thread
    })
    limit = chess.engine.Limit(time=0.5)

    def __init__(self):
        self.board = chess.Board()

    def make_move(self, move):
        move_object = chess.Move.from_uci(move)
        self.board.push(move_object)

    def find_best_move(self):
        best_move = self.stockfish.play(self.board, self.limit).move
        return best_move

    def get_fen(self):
        return self.board.fen()

class StockfishGame:
    limit = chess.engine.Limit(time=0.5)
    stockfish = chess.engine.SimpleEngine.popen_uci("../stockfish")
    stockfish.configure({
        "Hash": 4,          # Use 4MB of hash table
        "Threads": 1,        # Use only 1 CPU thread
    })

    def __init__(self):
        self.board = chess.Board()

    def make_stockfish_move(self):
        result = self.stockfish.play(self.board, self.limit)
        self.board.push(result)

    def make_human_move(self, move):
        move_object = chess.Move.from_uci(move)
        self.board.push(move_object)

    def get_fen(self):
        return self.board.fen()

# Human vs human routes
hvh_game = HumanGame()

@app.route("/hvh-find-best-move", methods=["POST"])
def hvh_best_move():
    fen = request.json.get("fen")
    move = hvh_game.find_best_move()
    return str(move)

@app.route("/hvh-make-move", methods=["POST"]):
def hvh_make_move():
    move = request.json.get("move")
    try:
        hvh_game.make_move(move)
        return "200"
    except Exception as e:
        return str(e)

@app.route("/hvh-status") # returns FEN of current hvh game board
def hvh_status():
    return hvh_game.board.fen()

@app.route("/reset-hvh-game", methods=["POST"])
def reset_hvh_game():
    hvh_game = StockfishGame()
    return "200"




# Stockfish routes
stockfish_game = StockfishGame()

@app.route("/sf-play", methods=["POST"])
def sf_play():
    try:
        stockfish_game.make_stockfish_move()
        return "200"
    except Exception as e:
        return str(e)

@app.route("/sf-make-human-move", methods=["POST"])
def sf_make_human_move():
    move = request.json.get("move")
    try:
        stockfish_game.make_human_move(move)
        return "200"
    except Exception as e:
        return str(e)

@app.route("/stockfish-status") # returns FEN of current stockfish game board
def stockfish_status():
    return stockfish_game.board.fen()

@app.route("/reset-stockfish-game", methods=["POST"])
def reset_stockfish_game():
    stockfish_game = StockfishGame()
    return "200"






# LiChess routes
lichess_game = LichessGame()
TIME = 10
INCREMENT = 0

@app.route("/search-and-join-lichess-lichess_game", methods=["POST"])
def search_and_join_lichess_game():
    search_thread = threading.Thread(
        target=lichess_game.search, args=(TIME, INCREMENT), daemon=True
    )
    search_thread.start()
    return "success"


@app.route("/reset-lichess-game", methods=["POST"])
def reset_lichess_game():
    lichess_game.reset_game()
    return "success"


@app.route("/update-lichess-game", methods=["POST"])
def update_lichess_game():
    lichess_game_thread = threading.Thread(target=lichess_game.update, daemon=True)
    lichess_game_thread.start()
    return "success"


@app.route("/li-make-move", methods=["POST"])
def li_make_human_move():
    move = request.json.get("move")

    try:
        lichess_game.make_move(move)
        return "success"
    except Exception as e:
        return f"error {e}"


@app.route("/lichess-status")
def return_status():
    results = copy.deepcopy(lichess_game.results)  # to avoid changing the original pointer
    print(results)

    if "gamedata" in results and results["gamedata"]["type"] == "gameState":
        for key in ["binc", "winc", "wtime", "btime"]:
            results["gamedata"][key] = results["gamedata"][key].total_seconds()

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
