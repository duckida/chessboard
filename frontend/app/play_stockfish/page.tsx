"use client";
import { useRef, useState, useEffect } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios, { AxiosHeaders } from "axios";
import { Button } from "@/components/ui/button";

// backend calling functions
const BASE_URL = "http://chessboard.local:5000";

function StockfishChessboard() {
  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;

  const [gameFen, setGameFen] = useState(chessGame.fen());
  const [bestMove, setBestMove] = useState("")

  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.post(`${BASE_URL}/sf-analyze-fen`, {'fen': gameFen})
        .then(function (response) {
          setBestMove(response.data)
          setGameFen(chessGame.fen());
      });
    }, 3000); // check every 1000 ms

    return () => clearInterval(intervalId);
  }, [chessGame]);

  const chessboardOptions = {
        arrows: bestMove ? [{
          startSquare: bestMove.substring(0, 2) as Square,
          endSquare: bestMove.substring(2, 4) as Square,
          color: 'rgb(0, 128, 0)'
        }] : undefined,
        position: gameFen,
        id: 'stockfish-board'
      };

  return <Chessboard options={chessboardOptions} />;
}

export default function Page() {
  return (
    <>
        <StockfishChessboard />
    </>
  );
}
