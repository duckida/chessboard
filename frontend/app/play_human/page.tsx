"use client";
import { useRef, useState, useEffect } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios, { AxiosHeaders } from "axios";
import { Button } from "@/components/ui/button";

// backend calling functions
const BASE_URL = "http://127.0.0.1:5000";

function HVHChessboard() {
  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;

  const [gameFen, setGameFen] = useState(chessGame.fen());
  const [bestMove, setBestMove] = useState("")

  useEffect(() => {
    const intervalId = setInterval(() => {
      // Set the game FEN
      axios.get(`${BASE_URL}/hvh-status`)
        .then(function (response) {
          setGameFen(response.data);
        });

      // Get & display the best move
      axios.post(`${BASE_URL}/hvh-find-best-move`)
        .then(function (response) {
          setBestMove(response.data)
        });

    }, 1000); // check every 1000 ms

    return () => clearInterval(intervalId);
  }, [gameFen]);

  const chessboardOptions = {
        arrows: bestMove ? [{
          startSquare: bestMove.substring(0, 2) as Square,
          endSquare: bestMove.substring(2, 4) as Square,
          color: 'rgb(0, 128, 0)'
        }] : undefined,
        position: gameFen,
        id: 'hvh-board'
      };

  return <Chessboard options={chessboardOptions} />;
}

export default function Page() {
  return (
    <>
        <HVHChessboard />
    </>
  );
}
