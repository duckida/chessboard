"use client";
import { useRef, useState, useEffect } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

// backend calling functions
const BASE_URL = "http://127.0.0.1:5000";

function StockfishChessboard() {
  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;

  const [gameFen, setGameFen] = useState(chessGame.fen());

  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.get(`${BASE_URL}/stockfish-status`)
        .then(function (response) {
          setGameFen(response.data);
      });
    }, 300); // check every 300 ms

    return () => clearInterval(intervalId);
  }, [chessGame]);

  const chessboardOptions = {
        position: gameFen,
        id: 'stockfish-board'
  };

  return <Chessboard options={chessboardOptions}/>;
}

function undo() {
  axios.post(`${BASE_URL}/sf-undo`).catch((error) => {
    console.error(error);
  });
}

async function leave() {
  await fetch(`${BASE_URL}/reset-stockfish-game`, { method: 'POST' });
  window.location.href = '/';
}

export default function Page() {
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
      <StockfishChessboard />
      <Button onPointerDown={() => undo()} className="w-[160px] h-[80px] text-xl font-bold">
       ↩ Undo
      </Button>
    </div>
  );
}
