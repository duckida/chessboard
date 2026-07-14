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

## Stockfish (hints for human vs human)
### Analyze a given FEN and return the best move:
`curl -X POST http://chessboard.local:5000/sf-find-best-move -H "Content-Type: application/json" -d '{"fen": "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"}'`

## Stockfish (play against AI)
### Make a move
`curl -X POST http://127.0.0.1:5000/sf-make-human-move -H "Content-Type: application/json" -d '{"move": "e7e6"}'`
### Tell Stockfish to make a move
`curl -X POST http://127.0.0.1:5000/sf-play`
