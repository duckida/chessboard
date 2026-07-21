# backend

This is the folder that runs on the Raspberry Pi inside the chessboard, communicating with LiChess & the Stockfish chess engine. It also scans hardware inputs and manages the NeoPixel LEDs.

## backend API
The API routes that create and modify games and connect to different services are in `app.py`, which is a Flask API. 

Details about API routes can be found in [API.md](https://github.com/duckida/chessboard/blob/main/backend/API.md).

## backend deployment instructions
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` and restart your shell
2. Clone this repo and enter: `git clone https://github.com/duckida/chessboard && cd chessboard`
3. Enter the backend and install packages: `cd backend && uv sync`
4. 

## hardware interface

### enabling serial
1. Add the `pi` user to the Serial group `sudo usermod -a -G dialout pi`
2. Run `sudo raspi-config` go to Interfaces, click Serial and say no to login shell, yes to serial port hardware

## deployment
