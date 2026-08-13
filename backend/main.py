#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py -- Chessboard hardware loop
====================================

Runs on the Raspberry Pi inside the physical chessboard. It:

  1. Reads the 8x8 reed-switch matrix (JSON over serial from the Pico).
  2. Turns confirmed square-occupancy changes into legal chess moves.
  3. Talks to the local Flask API (``app.py``): Stockfish games, human-vs-
     human relay, or live Lichess games.
  4. Drives the 64 WS281x LEDs to confirm moves, prompt the player to move
     the engine's/opponent's pieces, and -- crucially -- to show *which
     pieces should be where* whenever the physical board and the logical
     game state disagree.

LED language
------------
  brown/black checkerboard   idle, everything is consistent
  WHITE from+to (brief)      your move was registered
  RED blink from + GREEN to  please move this piece here (engine / opponent)
  ORANGE blink               (during a move prompt) your king is in check
  YELLOW solid               a piece is MISSING from this square
  BLUE solid                 there is an UNEXPECTED piece on this square
  center-4 pulse             searching for a Lichess game
  full-board green/red/gold  you won / you lost / draw

The yellow/blue "guidance" markers appear whenever the physical occupancy
has disagreed with the logical position for more than GUIDANCE_DELAY
seconds and no move is currently being prompted. They resolve themselves
the instant the board is fixed. This is what makes every failure mode
recoverable: a rejected move, a Wi-Fi hiccup, a knocked-over piece or a
half-finished castle all end with the board itself telling the player
exactly what to move where.

After a game ends, physically resetting all pieces to the start position
(and leaving them still for ~2s) automatically starts the next game.

Configuration (environment variables, all optional)
---------------------------------------------------
  BASE_URL               API base URL               (default http://127.0.0.1:5000)
  CHESSBOARD_MODE        stockfish|hvh|lichess|auto (default auto)
  LED_BRIGHTNESS         0-255                      (default 150)
  POLL_INTERVAL          seconds between matrix reads (default 0.03)
  DEBOUNCE_READS         identical reads to confirm a square (default 3)
  GUIDANCE_DELAY         seconds of stable mismatch before yellow/blue
                         guidance LEDs appear       (default 4.0)
  PROMPT_BLINK_HZ        blink rate of move prompts (default 1.5)
  MODE_CHECK_INTERVAL    seconds between auto mode re-checks (default 2.0)
  ENGINE_TIMEOUT         max seconds to wait for Stockfish (default 30)
  AUTO_RESTART           "1"/"0": new game when pieces are reset (default 1)
  RESET_ON_START         "1"/"0": reset the server game on startup (default 1)
  BOARD_ORIENTATION      "standard" | "rotated_180" (default standard)
  SIMULATE               "1" to use mock hardware (no Pi required)
  LOG_LEVEL              DEBUG|INFO|WARNING         (default INFO)
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import signal
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import chess
import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is a soft dependency for this script
    pass

# --------------------------------------------------------------------------
# Hardware access, with a graceful software fallback so this file can be
# imported/run on a machine without the rpi_ws281x / pyserial hardware libs.
# --------------------------------------------------------------------------
try:
    from hardware import leds as hw_leds  # type: ignore
    from hardware import matrix as hw_matrix  # type: ignore

    _HARDWARE_IMPORT_ERROR: Optional[Exception] = None
except Exception as exc:  # pragma: no cover - only hit off-Pi / missing deps
    hw_leds = None
    hw_matrix = None
    _HARDWARE_IMPORT_ERROR = exc

LETTERS = "abcdefgh"
UCI_RE = re.compile(r"^[a-h][1-8][a-h][1-8][qrbn]?$")

# LED colours
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
DIM_RED = (60, 0, 0)
GREEN = (0, 255, 0)
DIM_GREEN = (0, 60, 0)
YELLOW = (255, 200, 0)
BLUE = (0, 80, 255)
ORANGE = (255, 120, 0)
GOLD = (200, 200, 0)

INITIAL_OCCUPANCY: Set[str] = {
    chess.square_name(sq) for sq in chess.SquareSet(chess.Board().occupied)
}

# --------------------------------------------------------------------------
# Matrix <-> chess-square coordinate mapping
# --------------------------------------------------------------------------
# The physical reed-switch matrix may be wired 180° from the standard
# algebraic orientation. BOARD_ORIENTATION controls this globally.
#   "standard"     a1 at matrix (0,0), h8 at (7,7)
#   "rotated_180"  h8 at matrix (0,0), a1 at (7,7)
BOARD_ORIENTATION: str = "standard"

def square_name(y_index: int, x_index: int) -> str:
    """state[y][x] -> chess square name, respecting BOARD_ORIENTATION."""
    if BOARD_ORIENTATION == "rotated_180":
        y_index = 7 - y_index
        x_index = 7 - x_index
    return f"{LETTERS[x_index]}{y_index + 1}"

def matrix_coords(square: str) -> Tuple[int, int]:
    """Inverse of square_name(): chess square name -> (y, x) matrix coords."""
    file_idx = LETTERS.index(square[0])
    rank_idx = int(square[1]) - 1
    if BOARD_ORIENTATION == "rotated_180":
        return 7 - rank_idx, 7 - file_idx
    return rank_idx, file_idx

def occupancy_of(board: chess.Board) -> Set[str]:
    """Names of all squares that should physically hold a piece."""
    return {chess.square_name(sq) for sq in chess.SquareSet(board.occupied)}

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
@dataclass
class Config:
    base_url: str = "http://127.0.0.1:5000"
    mode: str = "auto"  # stockfish | hvh | lichess | auto
    led_brightness: int = 150
    poll_interval: float = 0.03
    debounce_reads: int = 3
    simulate: bool = False
    reset_on_start: bool = True
    auto_restart: bool = True
    resync_interval: float = 8.0
    lichess_poll_interval: float = 0.6
    mode_check_interval: float = 2.0
    request_timeout: float = 5.0
    engine_timeout: float = 30.0
    retry_backoff: float = 0.6
    highlight_delay: float = 0.7  # how long the white "move registered" flash stays
    guidance_delay: float = 4.0  # stable-mismatch time before guidance LEDs
    prompt_blink_hz: float = 1.5
    board_orientation: str = "standard"
    log_level: str = "INFO"

def load_config() -> Config:
    def env_bool(name: str, default: bool) -> bool:
        val = os.environ.get(name)
        if val is None:
            return default
        return val.strip().lower() in ("1", "true", "yes", "on")

    def env_float(name: str, default: float) -> float:
        try:
            return float(os.environ.get(name, default))
        except (TypeError, ValueError):
            return default

    def env_int(name: str, default: int) -> int:
        try:
            return int(os.environ.get(name, default))
        except (TypeError, ValueError):
            return default

    return Config(
        base_url=os.environ.get("BASE_URL", "http://127.0.0.1:5000").rstrip("/"),
        mode=os.environ.get("CHESSBOARD_MODE", "auto").strip().lower(),
        led_brightness=env_int("LED_BRIGHTNESS", 150),
        poll_interval=env_float("POLL_INTERVAL", 0.03),
        debounce_reads=env_int("DEBOUNCE_READS", 3),
        simulate=env_bool("SIMULATE", False),
        reset_on_start=env_bool("RESET_ON_START", True),
        auto_restart=env_bool("AUTO_RESTART", True),
        guidance_delay=env_float("GUIDANCE_DELAY", 4.0),
        prompt_blink_hz=env_float("PROMPT_BLINK_HZ", 1.5),
        mode_check_interval=env_float("MODE_CHECK_INTERVAL", 2.0),
        engine_timeout=env_float("ENGINE_TIMEOUT", 30.0),
        board_orientation=os.environ.get("BOARD_ORIENTATION", "standard").strip().lower(),
        log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    )

def setup_logging(cfg: Config) -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, cfg.log_level, logging.INFO),
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("chessboard")

# --------------------------------------------------------------------------
# Hardware fallbacks (used automatically if the real libraries are missing,
# or explicitly via SIMULATE=1)
# --------------------------------------------------------------------------
class MockMatrix:
    """Stands in for hardware.matrix.ChessboardMatrix. Always reports an
    empty board unless poked programmatically (handy for tests)."""

    def __init__(self):
        self._state = [[0] * 8 for _ in range(8)]

    def get_state(self):
        return [row[:] for row in self._state]

    def set_state(self, state):
        self._state = [row[:] for row in state]

class MockLEDStrip:
    """Stands in for hardware.leds.LEDStrip. Remembers the last colour
    written to each square, useful for tests/logging."""

    def __init__(self, brightness=150):
        self.brightness = brightness
        self.pixels: Dict[str, Tuple[int, int, int]] = {}

    def set_square_rgb(self, square, rgb):
        self.pixels[square] = tuple(rgb)

    def set_all_rgb(self, rgb):
        for sq in list(self.pixels.keys()):
            self.pixels[sq] = tuple(rgb)

    def set_matrix_rgb(self, rgb_white, rgb_black):
        self.pixels["__base_white__"] = tuple(rgb_white)
        self.pixels["__base_black__"] = tuple(rgb_black)

    def update(self):
        pass

def create_matrix(cfg: Config, log: logging.Logger):
    if cfg.simulate:
        log.warning("SIMULATE=1: using mock matrix (no physical board reads)")
        return MockMatrix()
    if hw_matrix is None:
        log.warning(
            "hardware.matrix unavailable (%s); falling back to mock matrix",
            _HARDWARE_IMPORT_ERROR,
        )
        return MockMatrix()
    try:
        return hw_matrix.ChessboardMatrix()
    except Exception as exc:
        log.warning("failed to open serial matrix (%s); falling back to mock", exc)
        return MockMatrix()

def create_leds(cfg: Config, log: logging.Logger):
    if cfg.simulate:
        log.warning("SIMULATE=1: using mock LED strip (no physical LEDs)")
        return MockLEDStrip(cfg.led_brightness)
    if hw_leds is None:
        log.warning(
            "hardware.leds unavailable (%s); falling back to mock LEDs",
            _HARDWARE_IMPORT_ERROR,
        )
        return MockLEDStrip(cfg.led_brightness)
    try:
        return hw_leds.LEDStrip(cfg.led_brightness)
    except Exception as exc:
        log.warning("failed to init LED strip (%s); falling back to mock", exc)
        return MockLEDStrip(cfg.led_brightness)

# --------------------------------------------------------------------------
# LED rendering
# --------------------------------------------------------------------------
class LedView:
    """Thin, error-tolerant, de-duplicating renderer. The main loop calls
    ``render`` every tick with the set of overlay colours; hardware is only
    touched when the picture actually changes, so blink animations and
    guidance markers are essentially free."""

    def __init__(self, strip, log: logging.Logger):
        self.strip = strip
        self.log = log
        self._warned = False
        self._last_key = None

    def _safe(self, fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
        except Exception as exc:
            if not self._warned:
                self.log.warning("LED write failed (%s); continuing without LEDs", exc)
                self._warned = True

    def render(self, overlays: Dict[str, Tuple[int, int, int]]):
        """Redraw base checkerboard + per-square overlays, only if changed."""
        key = tuple(sorted(overlays.items()))
        if key == self._last_key:
            return
        self._last_key = key
        self._safe(self.strip.set_matrix_rgb, BROWN, BLACK)
        for sq, rgb in overlays.items():
            self._safe(self.strip.set_square_rgb, sq, rgb)
        self._safe(self.strip.update)

    def flash_all(self, rgb, times=2, delay=0.15):
        for _ in range(times):
            self._safe(self.strip.set_all_rgb, rgb)
            self._safe(self.strip.update)
            time.sleep(delay)
            self._safe(self.strip.set_matrix_rgb, BROWN, BLACK)
            self._safe(self.strip.update)
            time.sleep(delay)
        self._last_key = None  # force next render to rewrite

    def clear(self):
        self._last_key = None
        self.render({})

# --------------------------------------------------------------------------
# Move detection
# --------------------------------------------------------------------------
class DebouncedReader:
    """Wraps the raw matrix reader and only reports a square's state once
    it has been stable for `debounce_reads` consecutive polls."""

    def __init__(self, matrix, debounce_reads: int, log: logging.Logger):
        self.matrix = matrix
        self.debounce_reads = max(1, debounce_reads)
        self.log = log
        self.confirmed = [[0] * 8 for _ in range(8)]
        self._candidate = [[0] * 8 for _ in range(8)]
        self._streak = [[0] * 8 for _ in range(8)]
        self._primed = False

    def _read_raw(self) -> Optional[List[List[int]]]:
        try:
            raw = self.matrix.get_state()
        except Exception as exc:
            self.log.debug("matrix read failed: %s", exc)
            return None
        if (
            not isinstance(raw, list)
            or len(raw) != 8
            or any(not isinstance(r, list) or len(r) != 8 for r in raw)
        ):
            self.log.debug("matrix returned malformed state: %r", raw)
            return None
        return raw

    def poll(self) -> Set[str]:
        """Reads once and returns the set of squares whose *confirmed*
        state just changed."""
        raw = self._read_raw()
        if raw is None:
            return set()

        changed: Set[str] = set()
        for y in range(8):
            for x in range(8):
                val = 1 if raw[y][x] else 0
                if val == self._candidate[y][x]:
                    self._streak[y][x] += 1
                else:
                    self._candidate[y][x] = val
                    self._streak[y][x] = 1

                if self._streak[y][x] >= self.debounce_reads and self.confirmed[y][x] != val:
                    self.confirmed[y][x] = val
                    if self._primed:
                        changed.add(square_name(y, x))
        self._primed = True
        return changed

    def is_occupied(self, sq: str) -> bool:
        y, x = matrix_coords(sq)
        return bool(self.confirmed[y][x])

    def occupied_squares(self) -> Set[str]:
        out = set()
        for y in range(8):
            for x in range(8):
                if self.confirmed[y][x]:
                    out.add(square_name(y, x))
        return out

class MoveFinder:
    """Turns confirmed occupancy changes into legal chess moves, validated
    against a locally mirrored board.

    Handles normal moves, captures (either physical pick-up order),
    castling (including the "king onto the rook's square" style) and
    en passant, auto-promoting to queen when the player doesn't specify.
    """

    LIFT_TTL = 20.0  # seconds a "lifted" square stays eligible as a "from"

    def __init__(self):
        self.lifted: Dict[str, float] = {}

    def reset(self):
        self.lifted.clear()

    def on_lift(self, square: str, now: float):
        self.lifted[square] = now

    def on_place(self, square: str, now: float, board: chess.Board) -> Optional[str]:
        """A square just became occupied. Returns a UCI move string if this
        placement completes a legal move, else None."""
        self._expire(now)
        # A square that now holds a piece can no longer be a "from".
        self.lifted.pop(square, None)

        candidates = []
        for from_sq in list(self.lifted.keys()):
            uci = self._try_move(board, from_sq, square)
            if uci:
                candidates.append((from_sq, uci))

        if not candidates:
            return None

        if len(candidates) == 1:
            from_sq, uci = candidates[0]
        else:
            # Ambiguous (e.g. mid-castle): the most recently lifted square
            # is the most likely intended "from".
            candidates.sort(key=lambda c: -self.lifted.get(c[0], 0))
            from_sq, uci = candidates[0]

        self.lifted.pop(from_sq, None)
        return uci

    def _expire(self, now: float):
        expired = [sq for sq, t in self.lifted.items() if now - t > self.LIFT_TTL]
        for sq in expired:
            self.lifted.pop(sq, None)

    @staticmethod
    def _try_move(board: chess.Board, from_sq: str, to_sq: str) -> Optional[str]:
        # Direct move (with auto-promotion fallbacks).
        for suffix in ("", "q", "r", "b", "n"):
            try:
                move = chess.Move.from_uci(from_sq + to_sq + suffix)
            except ValueError:
                continue
            if move in board.legal_moves:
                return move.uci()
        # Castling performed as "king onto the rook's square".
        try:
            piece = board.piece_at(chess.parse_square(from_sq))
        except ValueError:
            piece = None
        if piece is not None and piece.piece_type == chess.KING:
            for move in board.legal_moves:
                if (
                    board.is_castling(move)
                    and chess.square_name(move.from_square) == from_sq
                    and MoveFinder._castle_rook_square(board, move) == to_sq
                ):
                    return move.uci()
        return None

    @staticmethod
    def _castle_rook_square(board: chess.Board, move: chess.Move) -> Optional[str]:
        king_from = chess.square_name(move.from_square)
        if board.is_kingside_castling(move):
            return "h1" if king_from == "e1" else "h8"
        if board.is_queenside_castling(move):
            return "a1" if king_from == "e1" else "a8"
        return None

def physical_equivalents(board: chess.Board, uci: str) -> Set[str]:
    """The set of physical from/to pairs (plain 4-char strings) that a
    player might produce while executing `uci` by hand."""
    equivalents = {uci[:4]}
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return equivalents
    if board.is_castling(move):
        rook_sq = MoveFinder._castle_rook_square(board, move)
        if rook_sq:
            equivalents.add(uci[:2] + rook_sq)
    return equivalents

# --------------------------------------------------------------------------
# API client
# --------------------------------------------------------------------------
class GameClient:
    """Wraps the Flask API with timeouts, retries and thread-local sessions
    (the Stockfish engine call runs on a worker thread)."""

    def __init__(self, cfg: Config, log: logging.Logger):
        self.cfg = cfg
        self.log = log
        self._tls = threading.local()

    @property
    def session(self) -> requests.Session:
        sess = getattr(self._tls, "session", None)
        if sess is None:
            sess = requests.Session()
            self._tls.session = sess
        return sess

    def _request(self, method: str, path: str, retries: int, **kwargs) -> Optional[requests.Response]:
        url = f"{self.cfg.base_url}{path}"
        kwargs.setdefault("timeout", self.cfg.request_timeout)
        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                return self.session.request(method, url, **kwargs)
            except requests.RequestException as exc:
                last_exc = exc
                self.log.debug("%s %s failed (attempt %d/%d): %s", method, path, attempt, retries, exc)
                if attempt < retries:
                    time.sleep(self.cfg.retry_backoff * attempt)
        self.log.warning("%s %s unreachable after %d attempts: %s", method, path, retries, last_exc)
        return None

    def get_text(self, path: str, retries: int = 2) -> Optional[str]:
        resp = self._request("GET", path, retries)
        if resp is None or resp.status_code >= 400:
            return None
        return resp.text.strip()

    def get_json(self, path: str, retries: int = 2) -> Optional[dict]:
        resp = self._request("GET", path, retries)
        if resp is None or resp.status_code >= 400:
            return None
        try:
            return resp.json()
        except ValueError:
            return None

    def post(self, path: str, json_body: Optional[dict] = None, retries: int = 1,
             timeout: Optional[float] = None) -> Optional[str]:
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        resp = self._request("POST", path, retries, json=json_body, **kwargs)
        if resp is None:
            return None
        return resp.text.strip()

    # ---- convenience wrappers -----------------------------------------
    def reset_stockfish(self) -> bool:
        return self.post("/reset-stockfish-game", retries=3) == "200"

    def reset_hvh(self) -> bool:
        return self.post("/reset-hvh-game", retries=3) == "200"

    def stockfish_fen(self) -> Optional[str]:
        return self.get_text("/stockfish-status")

    def hvh_fen(self) -> Optional[str]:
        return self.get_text("/hvh-status")

    def sf_make_human_move(self, uci: str) -> bool:
        return self.post("/sf-make-human-move", json_body={"move": uci}, retries=2) == "200"

    def sf_play(self) -> Optional[str]:
        body = self.post("/sf-play", retries=1, timeout=self.cfg.engine_timeout)
        if body and UCI_RE.match(body):
            return body
        if body:
            self.log.info("engine could not move (%s) -- likely game over", body)
        return None

    def hvh_make_move(self, uci: str) -> bool:
        return self.post("/hvh-make-move", json_body={"move": uci}, retries=2) == "200"

    def lichess_status(self) -> Optional[dict]:
        return self.get_json("/lichess-status", retries=1)

    def li_make_move(self, uci: str) -> bool:
        return self.post("/li-make-move", json_body={"move": uci}, retries=2) == "success"

# --------------------------------------------------------------------------
# Game loop
# --------------------------------------------------------------------------
class GameLoop:
    """Orchestrates matrix reads -> move detection -> API calls -> LEDs.

    States:
      awaiting_human     it is the (local) player's turn; watch for moves
      awaiting_engine    Stockfish is thinking on a worker thread
      pending_execution  engine/opponent move known; player must move a piece
      game_over          finished; waits for a physical full-board reset
    """

    def __init__(self, cfg: Config, matrix, leds: LedView, client: GameClient, log: logging.Logger):
        self.cfg = cfg
        self.matrix = matrix
        self.leds = leds
        self.client = client
        self.log = log

        self.reader = DebouncedReader(matrix, cfg.debounce_reads, log)
        self.finder = MoveFinder()
        self.board = chess.Board()

        self.mode: Optional[str] = None
        self.state = "awaiting_human"

        # pending (engine/opponent) move awaiting physical execution
        self.pending_move: Optional[str] = None
        self.pending_equivalents: Set[str] = set()
        self.pending_check_sq: Optional[str] = None
        self._gameover_after_pending: Optional[Tuple[Optional[bool], str]] = None

        # stockfish worker
        self._engine_event = threading.Event()
        self._engine_result: Optional[str] = None
        self._engine_started = 0.0

        # confirmation flash ("move registered")
        self._confirm_move: Optional[str] = None
        self._confirm_until = 0.0

        # guidance (physical != logical) tracking
        self._mismatch_since: Optional[float] = None
        self._missing: Set[str] = set()
        self._extra: Set[str] = set()

        # game-over auto-restart
        self._reset_candidate_since: Optional[float] = None

        # lichess bookkeeping
        self.human_color: Optional[bool] = chess.WHITE
        self.lichess_ply_count = 0
        self._li_moves: List[str] = []
        self._li_initial_fen: Optional[str] = None
        self._li_waiting = False

        self.last_resync = 0.0
        self.last_lichess_poll = 0.0
        self.last_mode_check = 0.0
        self.running = True

        signal.signal(signal.SIGINT, self._on_signal)
        signal.signal(signal.SIGTERM, self._on_signal)

    def _on_signal(self, signum, frame):
        self.log.info("received signal %s, shutting down...", signum)
        self.running = False

    # ---- mode selection --------------------------------------------------
    def _detect_mode(self) -> str:
        forced = self.cfg.mode
        if forced in ("stockfish", "hvh", "lichess"):
            return forced
        status = self.client.lichess_status()
        if status and status.get("state") in ("searching", "found", "playing"):
            return "lichess"
        return "stockfish"

    def _enter_mode(self, mode: str):
        self.log.info("entering mode: %s", mode)
        self.mode = mode
        self.finder.reset()
        self.state = "awaiting_human"
        self.pending_move = None
        self.pending_equivalents = set()
        self.pending_check_sq = None
        self._gameover_after_pending = None
        self._confirm_move = None
        self._mismatch_since = None
        self._missing = set()
        self._extra = set()
        self._reset_candidate_since = None
        self._engine_event.clear()

        if mode == "stockfish":
            if self.cfg.reset_on_start:
                self.client.reset_stockfish()
            self.board = chess.Board()
            self.human_color = chess.WHITE
        elif mode == "hvh":
            if self.cfg.reset_on_start:
                self.client.reset_hvh()
            self.board = chess.Board()
            self.human_color = None  # both sides are human
        elif mode == "lichess":
            self.board = chess.Board()
            self.lichess_ply_count = 0
            self._li_moves = []
            self._li_initial_fen = None
            self._li_waiting = False
            self.human_color = None  # inferred from the game (see _poll_lichess)

        self.leds.clear()

    # ---- main loop ---------------------------------------------------------
    def run(self):
        self.log.info("starting chessboard loop (base_url=%s, orientation=%s)",
                      self.cfg.base_url, BOARD_ORIENTATION)
        self._enter_mode(self._detect_mode())
        self.last_resync = time.time()

        while self.running:
            try:
                self._tick()
            except Exception:
                self.log.error("unexpected error in main loop:\n%s", traceback.format_exc())
                time.sleep(1.0)
            time.sleep(self.cfg.poll_interval)

        self.leds.clear()
        self.log.info("shutdown complete")

    def _tick(self):
        now = time.time()
        changed = self.reader.poll()

        # IMPORTANT: process all lifts before any places. A fast lift+place
        # can confirm within the same poll batch; if the place were handled
        # first, the lift wouldn't be registered yet and the move would be
        # silently lost.
        lifts = sorted(sq for sq in changed if not self.reader.is_occupied(sq))
        places = sorted(sq for sq in changed if self.reader.is_occupied(sq))

        for sq in lifts:
            if self.state in ("awaiting_human", "pending_execution"):
                self.finder.on_lift(sq, now)

        for sq in places:
            if self.state == "pending_execution":
                if self._check_pending_execution(sq):
                    self._execute_pending_move()
                # anything else while pending is noise; guidance will sort it
                continue
            if self.state != "awaiting_human":
                continue
            move = self.finder.on_place(sq, now, self.board)
            if move:
                self._handle_candidate_move(move)

        # stockfish engine worker
        if self.state == "awaiting_engine":
            self._consume_engine(now)

        # lichess polling
        if self.mode == "lichess" and now - self.last_lichess_poll >= self.cfg.lichess_poll_interval:
            self.last_lichess_poll = now
            self._poll_lichess()

        # periodic resync with the server (only when idle and it's our move)
        if self.state == "awaiting_human" and now - self.last_resync >= self.cfg.resync_interval:
            self.last_resync = now
            self._resync()

        # auto mode: check for a newly started Lichess game (throttled)
        if (
            self.mode != "lichess"
            and self.cfg.mode == "auto"
            and now - self.last_mode_check >= self.cfg.mode_check_interval
        ):
            self.last_mode_check = now
            if self._detect_mode() == "lichess":
                self._enter_mode("lichess")

        self._update_mismatch(now)
        if self.state == "game_over":
            self._check_auto_restart(now)
        self._render(now)

    # ---- physical-vs-logical guidance ---------------------------------------
    def _update_mismatch(self, now: float):
        """Compares physical occupancy to the logical board. When they
        disagree stably for GUIDANCE_DELAY seconds (and we're not prompting
        a move), the LEDs show exactly which squares need attention."""
        if self.state == "pending_execution":
            # mismatch is expected while the prompted move is being made
            self._mismatch_since = None
            self._missing = set()
            self._extra = set()
            return
        if self.state == "game_over":
            self._mismatch_since = None
            self._missing = set()
            self._extra = set()
            return

        expected = occupancy_of(self.board)
        physical = self.reader.occupied_squares()
        if expected == physical:
            if self._mismatch_since is not None:
                self.log.info("board is consistent again")
            self._mismatch_since = None
            self._missing = set()
            self._extra = set()
            return

        if self._mismatch_since is None:
            self._mismatch_since = now
        self._missing = expected - physical
        self._extra = physical - expected

    @property
    def guidance_visible(self) -> bool:
        return self._mismatch_since is not None and (
            time.time() - self._mismatch_since >= self.cfg.guidance_delay
        )

    # ---- rendering -----------------------------------------------------------
    def _render(self, now: float):
        overlays: Dict[str, Tuple[int, int, int]] = {}

        if self.state == "pending_execution" and self.pending_move:
            blink_on = int(now * self.cfg.prompt_blink_hz * 2) % 2 == 0
            frm, to = self.pending_move[:2], self.pending_move[2:4]
            overlays[to] = GREEN if blink_on else DIM_GREEN
            overlays[frm] = RED if blink_on else DIM_RED
            if self.pending_check_sq:
                overlays[self.pending_check_sq] = ORANGE if blink_on else DIM_RED
        elif self.guidance_visible:
            for sq in self._missing:
                overlays[sq] = YELLOW
            for sq in self._extra:
                overlays[sq] = BLUE
        elif self._li_waiting:
            pulse = int(now * 1.5) % 2 == 0
            for sq in ("d4", "e4", "d5", "e5"):
                overlays[sq] = WHITE if pulse else (40, 40, 40)
        elif self._confirm_move and now < self._confirm_until:
            overlays[self._confirm_move[:2]] = WHITE
            overlays[self._confirm_move[2:4]] = WHITE

        self.leds.render(overlays)

    def _flash_game_over(self, winner: Optional[bool]):
        if winner is None:
            self.leds.flash_all(GOLD, times=3)
        elif winner == self.human_color:
            self.leds.flash_all(GREEN, times=3)
        else:
            self.leds.flash_all(RED, times=3)
        self.leds.clear()

    # ---- pending move handling ------------------------------------------------
    def _set_pending_move(self, uci: str, pre_move_board: Optional[chess.Board] = None):
        """Record `uci` as a move the player still needs to perform.
        Equivalents must be derived from the position *before* the move."""
        board_before = pre_move_board if pre_move_board is not None else self.board
        self.pending_move = uci
        self.pending_equivalents = physical_equivalents(board_before, uci)
        self.state = "pending_execution"
        self._update_pending_check()

    def _update_pending_check(self):
        self.pending_check_sq = None
        if self.pending_move and self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                self.pending_check_sq = chess.square_name(king_sq)

    def _check_pending_execution(self, placed_sq: str) -> bool:
        """Direct match of a physical lift+place pair against the pending
        move's equivalents, bypassing legal-move validation (the pending
        move is already pushed onto self.board)."""
        if not self.pending_move:
            return False
        for from_sq in list(self.finder.lifted.keys()):
            if (from_sq + placed_sq) in self.pending_equivalents:
                self.finder.lifted.pop(from_sq, None)
                return True
        return False

    def _execute_pending_move(self):
        self.log.info("player executed pending move %s", self.pending_move)
        self.pending_move = None
        self.pending_equivalents = set()
        self.pending_check_sq = None
        self.leds.clear()

        deferred = self._gameover_after_pending
        self._gameover_after_pending = None
        if deferred is not None:
            winner, reason = deferred
            self.state = "game_over"
            self.log.info("game over (%s)", reason)
            self._flash_game_over(winner)
        else:
            self.state = "awaiting_human"
            self._check_game_over()

    # ---- game over -------------------------------------------------------------
    def _check_game_over(self) -> bool:
        if not self.board.is_game_over():
            return False
        winner = (not self.board.turn) if self.board.is_checkmate() else None
        self._declare_game_over(winner, self.board.result(claim_draw=True))
        return True

    def _declare_game_over(self, winner: Optional[bool], reason: str):
        if self.state == "pending_execution":
            # the mating/resigning move still has to be physically made
            self._gameover_after_pending = (winner, reason)
            return
        self.log.info("game over (%s)", reason)
        self.state = "game_over"
        self._flash_game_over(winner)

    def _check_auto_restart(self, now: float):
        """New game when the pieces have been physically reset and left
        stable for a moment."""
        if not self.cfg.auto_restart:
            return
        if self.reader.occupied_squares() == INITIAL_OCCUPANCY:
            if self._reset_candidate_since is None:
                self._reset_candidate_since = now
            elif now - self._reset_candidate_since >= 2.0:
                self.log.info("board physically reset -- starting a new game")
                self._enter_mode(self._detect_mode())
        else:
            self._reset_candidate_since = None

    # ---- resync -------------------------------------------------------------
    def _resync(self):
        fen = None
        if self.mode == "stockfish":
            fen = self.client.stockfish_fen()
        elif self.mode == "hvh":
            fen = self.client.hvh_fen()
        if not fen:
            return
        try:
            server_board = chess.Board(fen)
        except ValueError:
            self.log.warning("server returned invalid FEN: %s", fen)
            return
        if server_board.fen() != self.board.fen():
            self.log.info("resyncing local board with server state")
            self.board = server_board
            self.finder.reset()
            # guidance LEDs will now walk the player through fixing the
            # physical position if it doesn't match the server
            self._mismatch_since = None
            self._check_game_over()

    # ---- shared move handling -----------------------------------------------
    def _handle_candidate_move(self, uci: str):
        if self.state != "awaiting_human":
            self.log.debug("ignoring candidate %s in state %s", uci, self.state)
            return
        if self.mode == "stockfish":
            self._handle_stockfish_move(uci)
        elif self.mode == "hvh":
            self._handle_hvh_move(uci)
        elif self.mode == "lichess":
            self._handle_lichess_move(uci)

    def _confirm(self, uci: str):
        self._confirm_move = uci
        self._confirm_until = time.time() + self.cfg.highlight_delay

    # ---- Stockfish mode -------------------------------------------------------
    def _handle_stockfish_move(self, uci: str):
        piece = self.board.piece_at(chess.parse_square(uci[:2]))
        if piece is None or piece.color != chess.WHITE or self.board.turn != chess.WHITE:
            self.log.debug("ignoring %s: not the human's piece/turn", uci)
            return

        if not self.client.sf_make_human_move(uci):
            # Server rejected it: DON'T push locally. The physical move has
            # already been made, so guidance LEDs will show the player how
            # to put the piece back.
            self.log.warning("server rejected human move %s; resyncing", uci)
            self.leds.flash_all(DIM_RED, times=2)
            self._resync()
            return

        self.board.push(chess.Move.from_uci(uci))
        self.log.info("human played %s", uci)
        self._confirm(uci)

        if self._check_game_over():
            return

        self._start_engine_move()

    def _start_engine_move(self):
        """Stockfish can take many seconds; think on a worker thread so the
        matrix and Lichess keep being polled."""
        self.state = "awaiting_engine"
        self._engine_result = None
        self._engine_started = time.time()
        self._engine_event.clear()

        def work():
            try:
                result = self.client.sf_play()
            except Exception as exc:  # pragma: no cover - defensive
                self.log.warning("engine worker crashed: %s", exc)
                result = None
            self._engine_result = result
            self._engine_event.set()

        threading.Thread(target=work, daemon=True, name="stockfish-move").start()

    def _consume_engine(self, now: float):
        if self._engine_event.is_set():
            ai_move = self._engine_result
            self._engine_event.clear()
            if not ai_move:
                self.log.warning("engine returned no move; resyncing")
                self.leds.flash_all(DIM_RED, times=2)
                self.state = "awaiting_human"
                self._resync()
                return
            self._set_pending_move(ai_move)  # before push: needs pre-move board
            self.board.push(chess.Move.from_uci(ai_move))
            self._update_pending_check()
            self.log.info("engine plays %s", ai_move)
            self._check_game_over()  # deferred if pending (piece still needs moving)
        elif now - self._engine_started > self.cfg.engine_timeout + 5.0:
            self.log.warning("engine timed out; resyncing")
            self.leds.flash_all(DIM_RED, times=2)
            self.state = "awaiting_human"
            self._resync()

    # ---- Human vs human mode -----------------------------------------------
    def _handle_hvh_move(self, uci: str):
        if not self.client.hvh_make_move(uci):
            self.log.warning("server rejected hvh move %s; resyncing", uci)
            self.leds.flash_all(DIM_RED, times=2)
            self._resync()
            return

        self.board.push(chess.Move.from_uci(uci))
        self.log.info("hvh move played: %s", uci)
        self._confirm(uci)
        self._check_game_over()

    # ---- Lichess mode --------------------------------------------------------
    def _replay(self, moves: List[str]) -> Optional[chess.Board]:
        try:
            board = chess.Board(self._li_initial_fen) if self._li_initial_fen else chess.Board()
        except ValueError:
            board = chess.Board()
        for mv in moves:
            try:
                move = chess.Move.from_uci(mv)
            except ValueError:
                return None
            if move not in board.legal_moves:
                return None
            board.push(move)
        return board

    def _poll_lichess(self):
        status = self.client.lichess_status()
        if status is None:
            return  # transient failure; try again next poll
        state = status.get("state")

        if state in (None, "idle"):
            self._li_waiting = False
            if self.cfg.mode == "auto":
                self.log.info("lichess game ended/idle; leaving lichess mode")
                self._enter_mode("stockfish")
            return

        if state in ("searching", "found"):
            if not self._li_waiting:
                self.log.info("lichess: %s", state)
            self._li_waiting = True
            return

        self._li_waiting = False
        gamedata = status.get("gamedata") or {}
        if gamedata.get("type") == "gameFull":
            self._li_initial_fen = gamedata.get("initialFEN") or None
            color = gamedata.get("color") or status.get("color")
            if color in ("white", "black"):
                self.human_color = chess.WHITE if color == "white" else chess.BLACK
                self.log.info("lichess: we play %s", color)
            gamedata = gamedata.get("state") or {}

        moves_str = gamedata.get("moves") or ""
        moves = moves_str.split() if moves_str else []

        if moves != self._li_moves:
            self._apply_lichess_moves(moves)

        status_field = gamedata.get("status")
        if status_field and status_field not in ("started", "created"):
            winner = {"white": chess.WHITE, "black": chess.BLACK}.get(gamedata.get("winner"))
            self._declare_game_over(winner, f"lichess: {status_field}")

    def _apply_lichess_moves(self, moves: List[str]):
        """Brings the local board in line with the server's move list.
        Incremental when possible; full replay on takebacks/desync."""
        incremental = (
            len(moves) > self.lichess_ply_count
            and moves[: self.lichess_ply_count] == self._li_moves
        )
        if not incremental:
            self._li_full_resync(moves)
            return

        for mv in moves[self.lichess_ply_count :]:
            try:
                move = chess.Move.from_uci(mv)
            except ValueError:
                self.log.warning("lichess sent unparseable move %s; resyncing", mv)
                self._li_full_resync(moves)
                return
            if move not in self.board.legal_moves:
                self.log.warning("lichess move %s illegal locally; resyncing", mv)
                self._li_full_resync(moves)
                return

            mover = self.board.turn
            if self.human_color is None:
                # The first move we ever *receive* must be the opponent's
                # (our own moves are applied locally before they're echoed).
                self.human_color = not mover
                self.log.info("lichess: inferred we play %s",
                              "white" if self.human_color else "black")

            is_last = mv == moves[-1]
            if is_last and mover != self.human_color:
                # Opponent's move: prompt the player to mirror it, unless
                # they somehow already have.
                physical = self.reader.occupied_squares()
                after = self.board.copy(stack=False)
                after.push(move)
                if physical == occupancy_of(after):
                    pass  # already mirrored physically
                elif physical == occupancy_of(self.board):
                    self._set_pending_move(mv, self.board)  # pre-push board
                # else: board is in some other state; guidance will reconcile

            self.board.push(move)

        self.lichess_ply_count = len(moves)
        self._li_moves = list(moves)
        self._update_pending_check()

    def _li_full_resync(self, moves: List[str]):
        new_board = self._replay(moves)
        if new_board is None:
            self.log.warning("cannot replay lichess move list; keeping local state")
            return

        self.log.info("lichess full resync (%d half-moves)", len(moves))
        self.finder.reset()
        if self.state == "pending_execution":
            self.pending_move = None
            self.pending_equivalents = set()
            self.pending_check_sq = None
            self.state = "awaiting_human"

        if moves:
            before = self._replay(moves[:-1])
            if before is not None:
                mover = before.turn
                if self.human_color is None:
                    self.human_color = not mover
                    self.log.info("lichess: inferred we play %s",
                                  "white" if self.human_color else "black")
                if mover != self.human_color:
                    physical = self.reader.occupied_squares()
                    if physical == occupancy_of(new_board):
                        pass  # already mirrored
                    elif physical == occupancy_of(before):
                        # exactly one opponent move behind: prompt it
                        self._set_pending_move(moves[-1], before)
                    # else: more drift than one move; guidance LEDs will
                    # show exactly what goes where

        self.board = new_board
        self.lichess_ply_count = len(moves)
        self._li_moves = list(moves)
        self._update_pending_check()

    def _handle_lichess_move(self, uci: str):
        piece = self.board.piece_at(chess.parse_square(uci[:2]))
        if piece is None or piece.color != self.board.turn:
            self.log.debug("ignoring %s: not the side to move", uci)
            return

        if self.human_color is None:
            # First physical move of the game tells us our colour.
            self.human_color = piece.color
            self.log.info("lichess: physical move tells us we play %s",
                          "white" if self.human_color else "black")
        elif piece.color != self.human_color:
            self.log.debug("ignoring %s: that's the opponent's piece", uci)
            return

        if not self.client.li_make_move(uci):
            # Either a real rejection or a lost response. Don't push; the
            # next poll will either echo it back (if it actually landed) or
            # guidance will show the player to move the piece back.
            self.log.warning("lichess rejected move %s", uci)
            self.leds.flash_all(DIM_RED, times=2)
            return

        self.board.push(chess.Move.from_uci(uci))
        self._li_moves.append(uci)
        self.lichess_ply_count += 1
        self._confirm(uci)
        self.log.info("sent lichess move %s", uci)
        self._check_game_over()

# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chessboard hardware loop")
    parser.add_argument("--mode", choices=["auto", "stockfish", "hvh", "lichess"], default=None)
    parser.add_argument("--simulate", action="store_true", help="use mock hardware")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--no-reset", action="store_true",
                        help="don't reset the server-side game on startup")
    parser.add_argument("--board-orientation", default=None,
                        choices=["standard", "rotated_180"],
                        help="how the physical matrix maps to chess squares "
                             "(default: standard)")
    return parser.parse_args(argv)

def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = load_config()
    if args.mode:
        cfg.mode = args.mode
    if args.simulate:
        cfg.simulate = True
    if args.base_url:
        cfg.base_url = args.base_url.rstrip("/")
    if args.no_reset:
        cfg.reset_on_start = False
    if args.board_orientation:
        cfg.board_orientation = args.board_orientation

    global BOARD_ORIENTATION
    if cfg.board_orientation not in ("standard", "rotated_180"):
        cfg.board_orientation = "standard"
    BOARD_ORIENTATION = cfg.board_orientation

    log = setup_logging(cfg)
    log.info("chessboard main.py starting (mode=%s, simulate=%s, orientation=%s)",
             cfg.mode, cfg.simulate, BOARD_ORIENTATION)

    matrix = create_matrix(cfg, log)
    strip = create_leds(cfg, log)
    leds = LedView(strip, log)
    leds.clear()
    client = GameClient(cfg, log)

    while True:
        loop = GameLoop(cfg, matrix, leds, client, log)
        try:
            loop.run()
            break
        except Exception:
            log.error("fatal error, restarting loop in 5s:\n%s", traceback.format_exc())
            time.sleep(5.0)

    return 0

if __name__ == "__main__":
    sys.exit(main())
