"use client";
import { useRef, useState } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";

export default function Page() {
  const chessboardOptions = {
    // your config options here
  };

  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;
  const possibleMoves = chessGame.moves();

  console.log(possibleMoves);

  return (
    <>
      <h1>Hello, Next.js!</h1>
      <Chessboard options={chessboardOptions} />
    </>
  );
}
