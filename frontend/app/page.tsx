"use client";
import { useRef, useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Power } from "lucide-react"

export default function Page() {
  return (
    <>
      <div className="flex flex-col gap-2 items-center p-5">

        <h1 className="font-mono font-bold text-2xl">Chessboard</h1>
        <Button className="w-[80vw] h-[20vh] bg-green-600 text-lg font-bold">
          Play Stockfish
        </Button>

        <Button className="w-[80vw] h-[20vh] bg-yellow-800 text-lg font-bold">
          Play LiChess
        </Button>

        <Button className="w-[80vw] h-[20vh] bg-sky-400 text-lg font-bold">
          Human Play
        </Button>
      </div>

      <div>
        <Button className="w-[40vw] h-[10vh] bg-red-500 font-bold">
          <Power className="stroke-[2.5]"/>Shutdown
        </Button>
      </div>
    </>
  );
}
