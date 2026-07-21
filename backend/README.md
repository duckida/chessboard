# backend

This is the folder that runs on the Raspberry Pi inside the chessboard, communicating with LiChess & the Stockfish chess engine. It also scans hardware inputs and manages the NeoPixel LEDs.

## backend API
The API routes that create and modify games and connect to different services are in `app.py`, which is a Flask API. 

Details about API routes can be found in [API.md](https://github.com/duckida/chessboard/blob/main/backend/API.md).

## hardware interface
The backend folder also contains 2 hardware modules, `leds.py` which exposes a simple control interface for WS2812B strips used in the chessboard (this needs root) and `matrix.py` which reads the matrix over UART serial.

## backend deployment instructions
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh` and restart your shell
2. Clone this repo and enter: `git clone https://github.com/duckida/chessboard && cd chessboard`
3. Enter the backend and install packages: `cd backend && uv sync`
4. Download Stockfish 14 and compile it, and put this compiled binary at `/home/pi/chessboard/stockfish`
5. Get a LiChess API token and put it in `.env` (example: `LICHESS_TOKEN="lip..."
`)
4. In one terminal tab, run the backend API: `uv run app.py`
5. In another tab, run the hardware scanner / main loop: `sudo -E $(which uv) run main.py` (sudo is needed for LED interfacing and serial reading)

### systemd service - API
1. `sudo systemctl edit --full api.service --force`
2. Paste this in:
```
[Unit]
Description=Chessboard API Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/chessboard/backend
ExecStart=/home/pi/.local/bin/uv run /home/pi/chessboard/backend/app.py

[Install]
WantedBy=network.target
```
3. `sudo systemctl daemon-reload`
4. `sudo systemctl enable api.service`
5. Reboot the Pi: `sudo reboot`

### systemd service - main hardware loop
> This runs as root, run at your own risk!

1. `sudo systemctl edit --full main.service --force`
2. Paste this in:
```
[Unit]
Description=Chessboard main loop Service
After=network.target api.service 
Wants=api.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/chessboard/backend
ExecStart=/home/pi/.local/bin/uv run /home/pi/chessboard/backend/main.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=network.target
```
3. `sudo systemctl daemon-reload`
4. `sudo systemctl enable main.service`
5. Reboot the Pi: `sudo reboot`
