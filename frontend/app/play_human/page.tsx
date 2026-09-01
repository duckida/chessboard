"use client";
import { useRef, useState, useEffect } from "react";
import { Chess, Square } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios from "axios";
import { Lightbulb } from "lucide-react"
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

// backend calling functions
const BASE_URL = "http://chessboard.local:5000";

function undo() {
  axios.post(`${BASE_URL}/hvh-undo`).catch((error) => {
    console.error(error);
  });
}

function HVHChessboard() {
  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;

  const [gameFen, setGameFen] = useState(chessGame.fen());
  const [bestMove, setBestMove] = useState("")

  // get the best move & display it
  function findBestMove() {
    axios.post(`${BASE_URL}/hvh-find-best-move`)
      .then(function (response) {
        setBestMove(response.data)
      });
  }

  useEffect(() => {
    const intervalId = setInterval(() => {
      // Set the game FEN
      axios.get(`${BASE_URL}/hvh-status`)
        .then(function (response) {
          setGameFen(response.data.fen);
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

  return (
    <>
      <Chessboard options={chessboardOptions} />
      <div className="flex flex-row">
        <Button onPointerDown={() => findBestMove()} className="w-[160px] h-[80px] text-xl font-bold">
          <Lightbulb/> Hint
        </Button>
        <Button onPointerDown={() => undo()} className="w-[160px] h-[80px] text-xl font-bold">
        ↩ Undo
        </Button>
      </div>
    </>
  );
}

export default function Page() {
  useEffect(() => {
      // Runs after the component mounts (i.e., on page load)
      fetch(`${BASE_URL}/hvh-start`, { method: 'POST' });
    }, []);

  const router = useRouter();

  async function leave() {
    await fetch(`${BASE_URL}/reset-hvh-game`, { method: 'POST' });
    router.push('/');
  }

  return (
    <div className="w-[320px] flex flex-col">
        <Button variant="outline" className="w-[80px] h-[60px] text-l font-bold" onPointerDown={() => leave()}>
        ← Back
        </Button>
        <HVHChessboard />
    </div>
  );
}
