# API reference

## LiChess
### Get the current status of the LiChess game
`curl http://127.0.0.1:5000/lichess-status`

### Start searching for a game 
`curl -X POST http://127.0.0.1:5000/search-and-join-lichess-game`

### Update the game (once found)
`curl -X POST http://127.0.0.1:5000/update-lichess-game`

### Make a move
`curl -X POST http://127.0.0.1:5000/li-make-move -H "Content-Type: application/json" -d '{"move": "e7e6"}'`
`curl -X POST http://127.0.0.1:5000/li-make-move -H "Content-Type: application/json" -d '{"move": "e2e4"}'`

### Reset game state (if aborted etc.)
`curl -X POST http://127.0.0.1:5000/reset-lichess-game`

## Human vs Human
### Make a move
`curl -X POST http://127.0.0.1:5000/hvh-make-move -H "Content-Type: application/json" -d '{"move": "e7e6"}'`
### Find best move
`curl -X POST http://chessboard.local:5000/hvh-find-best-move`
### Get game FEN
`curl http://127.0.0.1:5000/hvh-status`
### Reset game
`curl -X POST http://127.0.0.1:5000/reset-hvh-game`

## Stockfish (play against AI)
### Make a move
`curl -X POST http://127.0.0.1:5000/sf-make-human-move -H "Content-Type: application/json" -d '{"move": "e7e6"}'`
### Tell Stockfish to make a move
`curl -X POST http://127.0.0.1:5000/sf-play`
### Get game FEN
`curl http://127.0.0.1:5000/stockfish-status`
### Reset game state
`curl -X POST http://127.0.0.1:5000/reset-stockfish-game`
