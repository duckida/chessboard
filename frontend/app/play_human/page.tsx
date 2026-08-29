"use client";
import { useRef, useState, useEffect } from "react";
import { Chess, Square } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

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

    }, 300); // check every 300 ms

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
  const router = useRouter();

  async function leave() {
    await fetch(`${BASE_URL}/reset-hvh-game`, { method: 'POST' });
    router.push('/');
  }

  return (
    <div className="w-[320px] flex flex-col">
        <Button variant="outline" className="w-[80px] h-[60px] text-l font-bold" onClick={() => leave()}>
        ← Back
        </Button>
        <HVHChessboard />
    </div>
  );
}
