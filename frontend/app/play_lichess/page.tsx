"use client";
import { useRef, useState, useEffect } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios from "axios";
import { Button } from "@/components/ui/button";
import Link from 'next/link';

// backend calling functions
const BASE_URL = "http://chessboard.local:5000";

function searchGame() {
  axios.post(`${BASE_URL}/search-and-join-lichess-game`).catch((error) => {
    console.error(error);
  });
}

function startGame() {
  axios.post(`${BASE_URL}/update-lichess-game`).catch((error) => {
    console.error(error);
  });
}

function resetGame() {
  axios.post(`${BASE_URL}/reset-lichess-game`).catch((error) => {
    console.error(error);
  });
}

// custom ui components

function StatusText() {
  const [status, setStatus] = useState("No game active");

  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.get(`${BASE_URL}/lichess-status`).then(function (response) {
        setStatus(JSON.stringify(response.data));
      });
    }, 300); // check every 300 ms

    return () => clearInterval(intervalId);
  }, []);
  return <h2>{status}</h2>;
}

function LiChessboard() {
  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;

  const [gameFen, setGameFen] = useState(chessGame.fen());
  const lastMoveRef = useRef("");

  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.get(`${BASE_URL}/lichess-status`).then(function (response) {
        const status = response.data
        if (status.gamedata && status.gamedata.type == "gameState") {
          const splitMoves = status.gamedata.moves.split(" ")
          const mostRecentMove = splitMoves[splitMoves.length - 1]

          if (lastMoveRef.current != mostRecentMove) { // not the same / repeat move
            chessGame.move(mostRecentMove);
            setGameFen(chessGame.fen());
            lastMoveRef.current = mostRecentMove;
          }
        }
      });
    }, 500); // check every 500 ms

    return () => clearInterval(intervalId);
  }, [chessGame]);

  const chessboardOptions = {
    position: gameFen,
    id: "lichess-board",
  };

  return <Chessboard options={chessboardOptions} />;
}

export default function Page() {
  return (
    <>
      <div className="w-[320px] flex flex-col">
          <Link href="/">
            <Button variant="outline" className="w-[80px] h-[60px] text-l font-bold">
             ← Back
            </Button>
          </Link>
          <Button onClick={() => searchGame()}>
            Search Game
          </Button>
          <Button onClick={() => startGame()}>
            Start Game (once found)
          </Button>
          <Button variant="outline" onClick={() => resetGame()}>
            Reset Game
          </Button>
        </div>
      <StatusText />
      <div className="w-[320px]">
        <LiChessboard />
      </div>
    </>
  );
}
