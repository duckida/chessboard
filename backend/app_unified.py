from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import berserk
import chess.engine
import json
import copy
import os
import threading

app = Flask(__name__)
CORS(app)

load_dotenv()
LICHESS_TOKEN = os.environ["LICHESS_TOKEN"]


class StockfishEngine:
    limit = chess.engine.Limit(time=0.5)

    def __init__(self):
        self.stockfish = chess.engine.SimpleEngine.popen_uci("../stockfish")
        self.stockfish.configure({
            "Hash": 4,          # Use 4MB of hash table
            "Threads": 1,        # Use only 1 CPU thread
            "Use NNUE": False, # disable neural networks
        })

    def make_move(self, board):
        result = self.stockfish.play(board, self.limit)
        return result

    def find_best_move(self, board):
        best_move = self.stockfish.play(board, self.limit).move
        return best_move.uci()

stockfish_engine = StockfishEngine()

class Player:
    def __init__(self, username, elo, color):
        self.username = username
        self.elo = elo
        self.color = color
        self.seconds = 0

class LichessGame:
    def __init__(self):
        self.session = berserk.TokenSession(LICHESS_TOKEN)
        self.client = berserk.Client(session=self.session)
        self.board = self.client.board
        self.playing = False
        self.results = {"state": "idle"}
        self.my_player = None
        self.opponent_player = None
        self.update_thread = None

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
        for event in self.board.stream_game_state(self.game_id):
            if event["type"] == "gameFull":
                my_dict = event[self.color]
                self.my_player = Player(my_dict["name"], my_dict["rating"], self.color)

            self.results = {"state": "playing", "gamedata": event}

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
            self.opponent_player = Player(
                opponent_data["username"],
                opponent_data["rating"],
                opponent_color,
            )

            self.results = {"state": "found", "lichess_gameid": self.game_id}

            # start thread
            self.update_thread = threading.Thread(target=self.update, daemon=True)
            self.update_thread.start()

    def reset_game(self):
        self.playing = False
        self.update_thread = None
        self.game_id = ""
        self.my_player = None
        self.opponent_player = None
        self.results = {"state": "idle"}

    def make_user_move(self, move):
        self.board.make_move(self.game_id, move)

class HumanGame:
    def __init__(self):
        self.board = chess.Board()
        self.status = {"fen": self.board.fen(), "state": "idle"}

    def join(self):
        self.status = {"fen": self.board.fen(), "state": "playing"}

    def make_user_move(self, move):
        move_object = chess.Move.from_uci(move)
        self.board.push(move_object)
        self.status = {"fen": self.board.fen(), "state": "playing"}

    def hint(self):
        best_move = stockfish_engine.find_best_move(self.board)
        return best_move

    def undo(self):
        # undos last 1 move
        self.board.pop()
        self.status = {"fen": self.board.fen(), "state": "playing"}

class StockfishGame:
    def __init__(self):
        self.board = chess.Board()

    def make_opponent_move(self):
        result = stockfish_engine.make_move(self.board)
        self.board.push(result.move)
        return result.move.uci()

    def make_user_move(self, move):
        move_object = chess.Move.from_uci(move)
        self.board.push(move_object)

    def undo(self): # can only be called when both player have moved.
        # undos last 2 moves
        self.board.pop()
        self.board.pop()


# Unified API routes
status = {}
current_game = HumanGame()

## POST (actionable) routes
# make user move
@app.route("/make-user-move", methods=["POST"])
def make_user_move():
    move = request.json.get("move")
    try:
        current_game.make_move(move)
        return "200"
    except Exception as e:
        return str(e)

# make opponent move
@app.route("/make-opponent-move", methods=["POST"])
def make_opponent_move():
    try:
        current_game.make_opponent_move()
        return "200"
    except Exception as e:
        return str(e)

# join the game
@app.route("/join", methods=["POST"])
def join():
    global status
    try:
        game_type = current_game.join()
        status["game_type"] = game_type
        return "200"
    except Exception as e:
        return str(e)

# reset game
@app.route("/reset", methods=["POST"])
def reset():
    global current_game
    current_game = None
    return "200"

# undo (available in HVH and Stockfish only)
@app.route("/undo", methods=["POST"])
def undo():
    try:
        current_game.undo()
        return "200"
    except Exception as e:
        return str(e)

# hint (available in HVH only)
@app.route("/hint", methods=["POST"])
def hint():
    move = current_game.hint()
    try:
        return str(move)
    except Exception as e:
        return str(e)

# search (only available in LiChess)
TIME = 10
INCREMENT = 0
@app.route("/search", methods=["POST"])
def search():
    try:
        search_thread = threading.Thread(
            target=current_game.search, args=(TIME, INCREMENT), daemon=True
        )
        search_thread.start()
        return "200"
    except Exception as e:
        return str(e)

# shutdown the Pi
@app.route("/poweroff", methods=["POST"])
def poweroff():
    os.system("sudo poweroff")
    return "200"

## GET routes (information)
# get player details
@app.route("/players")
def return_players():
    return json.dumps([current_game.opponent_player.__dict__, current_game.user_player.__dict__])

# return fen
@app.route("/fen")
def return_fen():
    return current_game.fen()

def return_status():
    return status

@app.route("/lichess-status")
def return_status():
    results = copy.deepcopy(lichess_game.results)  # to avoid changing the original pointer
    print(results)

    if "gamedata" in results and results["gamedata"]["type"] == "gameState":
        for key in ["binc", "winc", "wtime", "btime"]:
            results["gamedata"][key] = results["gamedata"][key].total_seconds()

    return jsonify(results)



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", use_reloader=False, port=5000)
