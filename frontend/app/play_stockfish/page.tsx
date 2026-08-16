"use client";
import { useRef, useState, useEffect } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios, { AxiosHeaders } from "axios";
import { Button } from "@/components/ui/button";
import Link from "next/link";

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

export default function Page() {
  return (
    <div className="w-[320px] flex flex-col">
      <Link href="/">
        <Button variant="outline">
         ← Back
        </Button>
      </Link>
      <StockfishChessboard/>
    </div>
  );
}
