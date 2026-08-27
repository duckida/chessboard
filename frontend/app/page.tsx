"use client";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Power } from "lucide-react"

const BASE_URL = "http://127.0.0.1:5000";

function shutdown() {
  axios.post(`${BASE_URL}/poweroff`).catch((error) => {
    console.error(error);
  });
}

export default function Page() {
  return (
    <>
      <div className="flex flex-col gap-4 items-center p-5 w-[320px]">
        <h1 className="font-mono font-bold text-3xl">Chessboard</h1>

        <Button className="w-[300px] h-[100px] bg-green-600 text-2xl font-bold" onClick={() => window.location.href = "/play_stockfish"}>
          Play Stockfish
        </Button>

        <Button className="w-[300px] h-[100px] bg-yellow-800 text-2xl font-bold" onClick={() => window.location.href = "/play_lichess"}>
          Play LiChess
        </Button>

        <Button className="w-[300px] h-[100px] bg-sky-400 text-2xl font-bold" onClick={() => window.location.href = "/play_human"}>
          Human Play
        </Button>
      </div>

      <div>
        <Button className="w-[100px] h-[50px] bg-red-500 font-bold" onClick={()=>shutdown()}>
          <Power className="stroke-[2.5]"/>Shutdown
        </Button>
      </div>
    </>
  );
}
