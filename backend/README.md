# backend

This is the folder that runs on the Raspberry Pi inside the chessboard, communicating with LiChess & the Stockfish chess engine. It also scans hardware inputs and manages the NeoPixel LEDs.

## backend API
The API routes that create and modify games and connect to different services are in `app.py`, which is a Flask API. 

Details about API routes can be found in [API.md](https://github.com/duckida/chessboard/blob/main/backend/API.md).

The backend can be deployed using systemd

## hardware interface

### enabling serial
1. Add the `pi` user to the Serial group `sudo usermod -a -G dialout pi`
2. Run `sudo raspi-config` go to Interfaces, click Serial and say no to login shell, yes to serial port hardware

## deployment
