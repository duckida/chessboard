# API reference

## LiChess
### Get the current status of the LiChess game
`curl http://127.0.0.1:5000/lichess-status`

### Start searching for a game 
`curl -X POST http://127.0.0.1:5000/search-and-join-game`

### Update the game (once found)
`curl -X POST http://127.0.0.1:5000/update-game`

### Make a move
`curl -X POST http://127.0.0.1:5000/make-move -H "Content-Type: application/json" -d '{"move": "e7e6"}'`
`curl -X POST http://127.0.0.1:5000/make-move -H "Content-Type: application/json" -d '{"move": "e2e4"}'`

### Reset game state (if aborted etc.)
`curl -X POST http://127.0.0.1:5000/reset-game`

## Stockfish
