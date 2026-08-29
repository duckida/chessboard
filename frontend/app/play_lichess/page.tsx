"use client";
import { useRef, useState, useEffect } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Play, Search, RotateCcw } from "lucide-react"
import { useRouter } from "next/navigation";

// backend calling functions
const BASE_URL = "http://chessboard.local:5000";

function searchGame() {
  axios.post(`${BASE_URL}/search-and-join-lichess-game`).catch((error) => {
    console.error(error);
  });
}

function startGame() {
  axios.post(`${BASE_URL}/update-lichess-game`).catch((error) => {
    console.error(error);
  });
}

function resetGame() {
  axios.post(`${BASE_URL}/reset-lichess-game`).catch((error) => {
    console.error(error);
  });
}

// custom ui components

function StatusText() {
  const [status, setStatus] = useState("No game active");

  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.get(`${BASE_URL}/lichess-status`).then(function (response) {
        setStatus(JSON.stringify(response.data));
      });
    }, 300); // check every 300 ms

    return () => clearInterval(intervalId);
  }, []);
  return <p className="text-xs">{status}</p>;
}

function PlayerData() {
  const [playerData, setPlayerData] = useState([{"username": "unknown", "elo": 0, "color": "black"}, {"username": "unknown", "elo": 0, "color": "white"}]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.get(`${BASE_URL}/lichess-players`).then(function (response) {
        setPlayerData(response.data);
      });
    }, 2000); // check every 2000 ms

    return () => clearInterval(intervalId);
  }, []);


  return (
    <div className="flex flex-row items-center justify-center p-2 gap-2">
      <div className='rounded-xl w-[150px] h-[60px] border-gray-200 border-solid border bg-white p-[5px]' style={{backgroundColor: playerData[0].color}}>
        <p className="font-bold text-lg" style={{color: playerData[0].color == "white" ? "black" : "white"}}>{playerData[0].username}</p>
        <p style={{color: playerData[0].color == "white" ? "black" : "white"}}>{playerData[0].elo}</p>
      </div>

      <div className='rounded-xl w-[150px] h-[60px] border-gray-200 border-solid border bg-white p-[5px]' style={{backgroundColor: playerData[1].color}}>
        <p className="font-bold text-lg" style={{color: playerData[1].color == "white" ? "black" : "white"}}>{playerData[1].username}</p>
        <p style={{color: playerData[1].color == "white" ? "black" : "white"}}>{playerData[1].elo}</p>
      </div>
    </div>
  )
}

function LiChessboard() {
  const chessGameRef = useRef(new Chess());
  const chessGame = chessGameRef.current;

  const [gameFen, setGameFen] = useState(chessGame.fen());
  const lastMoveRef = useRef("");

  useEffect(() => {
    const intervalId = setInterval(() => {
      axios.get(`${BASE_URL}/lichess-status`).then(function (response) {
        const status = response.data
        if (status.gamedata && status.gamedata.type == "gameState") {
          const splitMoves = status.gamedata.moves.split(" ")
          const mostRecentMove = splitMoves[splitMoves.length - 1]

          if (lastMoveRef.current != mostRecentMove) { // not the same / repeat move
            chessGame.move(mostRecentMove);
            setGameFen(chessGame.fen());
            lastMoveRef.current = mostRecentMove;
          }
        }
      });
    }, 500); // check every 500 ms

    return () => clearInterval(intervalId);
  }, [chessGame]);

  const chessboardOptions = {
    position: gameFen,
    id: "lichess-board",
  };

  return <Chessboard options={chessboardOptions} />;
}

export default function Page() {
  const router = useRouter();

  async function leave() {
    await fetch(`${BASE_URL}/reset-lichess-game`, { method: 'POST' });
    router.push('/')
  }

  return (
    <>
      <div className="w-[320px] flex flex-row">
          <Button variant="outline" className="w-[80px] h-[60px] text-l font-bold" onClick={() => leave()}>
            ← Back
          </Button>
          <Button className="h-[60px] aspect-square text-2xl" onClick={() => searchGame()}>
            <Search/>
          </Button>
          <Button className="h-[60px] aspect-square" onClick={() => startGame()}>
            <Play />
          </Button>
          <Button className="h-[60px] aspect-square" variant="outline" onClick={() => resetGame()}>
            <RotateCcw />
          </Button>
        </div>
      <StatusText />
      <div className="w-[320px]">
        <LiChessboard />
      </div>

      <div className="w-[320px]">
        <PlayerData />
      </div>

    </>
  );
}
