"use client";
import { useRef, useState, useEffect } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios from "axios";
import { Button } from "@/components/ui/button";

// backend calling functions
const BASE_URL = "http://127.0.0.1:5000";

function searchGame() {
  axios.post(`${BASE_URL}/search-and-join-game`).catch((error) => {
    console.error(error);
  });
}

function startGame() {
  axios.post(`${BASE_URL}/update-game`).catch((error) => {
    console.error(error);
  });
}

function resetGame() {
  axios.post(`${BASE_URL}/reset-game`).catch((error) => {
    console.error(error);
  });
}

// custom ui components

function StatusText() {
  const [status, setStatus] = useState("No game active");

  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.get(`${BASE_URL}/status`).then(function (response) {
        setStatus(JSON.stringify(response.data));
      });
    }, 1000); // check every 1000 ms

    return () => clearInterval(intervalId);
  }, []);
  return <h2>{status}</h2>;
}

function LiChessboard() {
  const chessboardOptions = {
    // your config options here
  };

  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;
  const possibleMoves = chessGame.moves();

  console.log(possibleMoves);

  return <Chessboard options={chessboardOptions} />;
}

export default function Page() {
  return (
    <>
        <Button onClick={() => searchGame()}>
          Search Game
        </Button>
        <Button onClick={() => startGame()}>
          Start Game (once found)
        </Button>
        <Button variant="outline" onClick={() => resetGame()}>
          Reset Game
        </Button>
        <StatusText />
        <LiChessboard />
    </>
  );
}
