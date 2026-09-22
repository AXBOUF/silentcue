import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Clipboard,
  CornerDownRight,
  LogOut,
  Signal,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// have additional selection commands right now 
const COMMANDS = {
  presentation: [
    { name: "BACK", value: 0 },
    { name: "NEXT", value: 1 },
  ],
  film_shooting: [
    { name: "STOP", value: 0 },
    { name: "START", value: 1 },
  ],
  YES_NO: [
    { name: "NO", value: 0 },
    { name: "YES", value: 1 },
  ]
};

const MODE_LABELS = {
  presentation: "Presentation",
  film_shooting: "Film shooting",
  YES_NO: "Yes / no",
  custom: "Custom",
};

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-9 place-items-center border border-foreground bg-primary text-primary-foreground">
      </span>
      <span className="text-xl font-black uppercase tracking-normal">Silentcue</span>
    </div>
  );
}

export function RelayApp() {
  const [screen, setScreen] = useState("home");
  const [roomCode, setRoomCode] = useState("");
  const [controllerToken, setControllerToken] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [role, setRole] = useState("controller");
  const [connected, setConnected] = useState(false);
  const [deviceCount, setDeviceCount] = useState(1);
  const [lastSignal, setLastSignal] = useState(null);
  const [signalCount, setSignalCount] = useState(0);
  const [copied, setCopied] = useState(false);
  const [sessionWarning, setSessionWarning] = useState(null);
  const [mode, setMode] = useState("presentation");
  const [modeMenuOpen, setModeMenuOpen] = useState(false);
  const [customCommands, setCustomCommands] = useState([
    { name: "CUSTOM", value: 0 },
    { name: "CUSTOM", value: 1 },
  ]);
  const socketRef = useRef(null);

  const activeCommands = mode === "custom" ? customCommands : COMMANDS[mode];

  const receiveSignal = useCallback((signal) => {
    setLastSignal(signal);
    setSignalCount((count) => count + 1);
  }, []);

  useEffect(() => {
    if (screen !== "room" || !roomCode) return;
    setConnected(false);
    setDeviceCount(1);
    setSessionWarning(null);
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socketRole = role === "controller" ? "root" : "user";
    const tokenQuery = role === "controller" ? `&token=${encodeURIComponent(controllerToken)}` : "";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/chat/${roomCode}/?role=${socketRole}${tokenQuery}`);
    socketRef.current = socket;
    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "peer_status") {
          setConnected(Boolean(message.connected));
          setDeviceCount(message.connected ? 2 : 1);
        } else if (
          message.type === "signal" &&
          message.name &&
          (message.value === 0 || message.value === 1)
        ) {
          receiveSignal({ name: message.name, value: message.value });
        } else if (message.type === "session_warning") {
          setSessionWarning(message.remaining_seconds);
        } else if (message.type === "room_dismantled") {
          setSessionWarning(null);
          setScreen("home");
          setRoomCode("");
        }
      } catch {
        setConnected(false);
      }
    };
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    const heartbeat = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "heartbeat" }));
      }
    }, 30000);
    return () => {
      window.clearInterval(heartbeat);
      socket.close();
      socketRef.current = null;
    };
  }, [controllerToken, receiveSignal, role, roomCode, screen]);

  function enterRoom(code, nextRole = role, token = "") {
    setRoomCode(code.toUpperCase());
    setControllerToken(token);
    setRole(nextRole);
    setLastSignal(null);
    setSignalCount(0);
    setScreen("room");
  }

  async function createRoom() {
    const response = await fetch("/create_room/?format=json");
    if (!response.ok) throw new Error("Unable to create room");
    const data = await response.json();
    enterRoom(data.room_code, "controller", data.controller_token);
  }

  async function joinRoom(code) {
    const response = await fetch(`/join_room/${encodeURIComponent(code)}/?format=json`);
    if (!response.ok) throw new Error("Room not found or inactive");
    const data = await response.json();
    enterRoom(data.room_code, "receiver");
  }

  function sendSignal(signal) {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(signal));
    }
  }

  function updateCustomCommand(index, name) {
    const singleWord = name.trim().split(/\s+/)[0] || "";
    setCustomCommands((commands) => commands.map((command, commandIndex) => (
      commandIndex === index ? { ...command, name: singleWord.toUpperCase() || `CUSTOM ${command.value}` } : command
    )));
  }

  async function copyCode() {
    await navigator.clipboard.writeText(roomCode);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  function leaveRoom() {
    setScreen("home");
    setRoomCode("");
    setControllerToken("");
    setLastSignal(null);
  }

  if (screen === "home") {
    return (
      <main className="min-h-screen bg-primary text-foreground">
        <header className="flex h-20 items-center justify-between border-b border-foreground px-5 md:px-10">
          <Brand />
        </header>

        <section className="grid min-h-[calc(100dvh-5rem)] w-full grid-cols-1">

          <div className="grid w-full border-t border-foreground lg:border-t-0">
            <button
              type="button"
              className="group flex min-h-[clamp(280px,45dvh,620px)] cursor-pointer flex-col justify-between border-b border-foreground bg-[#dc5543] p-7 text-left text-white transition-colors hover:bg-[#c44738] md:p-10"
              onClick={() => createRoom().catch((error) => window.alert(error.message))}
            >
              <span className="flex items-end justify-between gap-4">
              <span className="text-[clamp(3rem,8vw,7rem)] font-black uppercase leading-none">
                Create<br />Room
              </span>
                <span className="grid size-16 shrink-0 place-items-center rounded-full border border-current transition-transform group-hover:rotate-[-45deg]">
                  <CornerDownRight className="size-7" />
                </span>
              </span>
            </button>

            <div className="flex min-h-72 flex-col justify-between bg-secondary p-7 md:p-10">
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  if (joinCode.length === 8) joinRoom(joinCode).catch((error) => window.alert(error.message));
                }}
              >
                <label htmlFor="room-code" className="text-5xl font-black uppercase leading-none md:text-7xl">Join <br /> room</label>
                <div className="flex border border-foreground bg-background">
                  <Input
                    id="room-code"
                    value={joinCode}
                    onChange={(event) => setJoinCode(event.target.value.replace(/[^a-z0-9]/gi, "").slice(0, 8).toUpperCase())}
                    placeholder="A4K7P2Q9"
                    maxLength={8}
                    autoComplete="off"
                    className="h-16 flex-1 rounded-none border-0 bg-transparent px-5 font-mono text-2xl font-bold uppercase tracking-[0.25em] shadow-none focus-visible:ring-0"
                  />
                  <Button
                    type="submit"
                    size="icon"
                    disabled={joinCode.length !== 8}
                    className="h-16 w-16 rounded-none border-l border-foreground shadow-none"
                    aria-label="Join room"
                  >
                    <ArrowRight className="size-6" />
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </section>
      </main>
    );
  }

  const receiverTextTone = ["receiver-signal-primary", "receiver-signal-forest", "receiver-signal-ochre"][signalCount % 3];

  return (
    <main className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-foreground px-4 py-3 md:px-8">
        <Brand />
        <div className="order-3 flex w-full items-center justify-between gap-5 border-t border-meter pt-3 md:order-2 md:w-auto md:border-0 md:pt-0">
          <div>
            <span className="block font-mono text-[10px] font-bold uppercase text-muted-foreground">Room code</span>
            <span className="font-mono text-2xl font-black tracking-[0.18em]">{roomCode}</span>
          </div>
          <Button variant="outline" className="h-10 rounded-none border-foreground bg-transparent shadow-none" onClick={copyCode}>
            {copied ? <Check /> : <Clipboard />} {copied ? "" : ""}
          </Button>
        </div>
        <div className="order-2 flex items-center gap-4 md:order-3">
          <div className="hidden text-right sm:block">
            <span className="block text-xs font-bold uppercase">{connected ? "Connected" : "Waiting for another device…"}</span>
            <span className="font-mono text-[10px] uppercase text-muted-foreground">{deviceCount} {deviceCount === 1 ? "device" : "devices"} · </span>
          </div>
          <span className={cn("size-3 rounded-full border border-foreground", connected ? "bg-status" : "animate-pulse bg-primary")} />
        </div>
      </header>

      <div className="grid flex-1 grid-cols-1 lg:grid-cols-[260px_1fr]">

        {sessionWarning !== null && (
          <div className="col-span-full border-b border-foreground bg-accent px-4 py-3 text-center font-mono text-xs font-bold uppercase">
            Room expires in {Math.max(1, Math.ceil(sessionWarning / 60))} minutes
          </div>
        )}

          <div className="hidden p-5 lg:block">
              <Button variant="ghost" onClick={leaveRoom} className="w-full justify-start rounded-none px-0 text-destructive hover:bg-transparent">
                <LogOut /> Leave room
              </Button>
          </div>
        {role === "controller" ? (
          <section className="flex min-h-[620px] flex-col p-4 md:p-8">
            <div className="relative z-20 mb-4 w-full max-w-sm">
              <button
                type="button"
                aria-expanded={modeMenuOpen}
                aria-haspopup="listbox"
                onClick={() => setModeMenuOpen((open) => !open)}
                className="flex w-full items-center justify-between border border-foreground bg-background px-3 py-2 text-left font-mono text-sm uppercase"
              >
                {MODE_LABELS[mode]}
                <ArrowRight className={cn("size-4 transition-transform", modeMenuOpen && "rotate-90")} />
              </button>
              {modeMenuOpen && (
                <div role="listbox" aria-label="Command mode" className="absolute left-0 top-full max-h-52 w-full overflow-y-auto border-x border-b border-foreground bg-background shadow-lg">
                  {Object.entries(MODE_LABELS).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      role="option"
                      aria-selected={mode === value}
                      onClick={() => {
                        setMode(value);
                        setModeMenuOpen(false);
                      }}
                      className={cn("block w-full px-3 py-3 text-left font-mono text-sm uppercase hover:bg-accent", mode === value && "bg-secondary")}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {mode === "custom" && (
              <div className="mb-4 grid gap-3 md:grid-cols-2">
                {customCommands.map((command, index) => (
                  <Input
                    key={command.value}
                    value={command.name}
                    maxLength={20}
                    aria-label={`Custom command ${command.value}`}
                    onChange={(event) => updateCustomCommand(index, event.target.value)}
                    className="rounded-none border-foreground bg-transparent font-mono uppercase"
                  />
                ))}
              </div>
            )}
            <div className="grid flex-1 gap-3 md:grid-cols-2">
              {activeCommands.map((command, index) => (
                <Button
                  key={command.value}
                  onClick={() => sendSignal(command)}
                  className={cn(
                    "group relative h-full min-h-44 overflow-hidden rounded-none border border-foreground bg-secondary p-6 text-foreground shadow-none hover:bg-accent",
                    index === COMMANDS.length - 1 && "bg-primary text-primary-foreground hover:bg-forest",
                  )}
                >
                  <span className="text-[clamp(3.5rem,8vw,8rem)] font-black leading-none tracking-normal">{command.name}</span>
                  {index === 0 ? <ArrowLeft className="absolute bottom-5 left-5 size-7" /> : <ArrowRight className="absolute bottom-5 right-5 size-7" />}
                </Button>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between font-mono text-[10px] font-bold uppercase text-muted-foreground">
              <span>Last sent: {lastSignal?.name ?? "—"}</span>
              <Button variant="ghost" onClick={leaveRoom} className="h-8 rounded-none px-2 text-destructive lg:hidden"><LogOut /> Leave</Button>
            </div>
          </section>
        ) : (
          <section className="relative flex min-h-[650px] flex-col justify-between bg-background p-5 text-foreground transition-colors duration-150 md:p-10">
            <div className="flex items-center justify-between font-mono text-xs font-bold uppercase">
            </div>
            <div className="flex flex-1 items-center justify-center overflow-hidden py-10">
              <span className={cn("max-w-full break-words text-center text-[clamp(7rem,24vw,22rem)] font-black uppercase leading-[0.75] tracking-normal", lastSignal && receiverTextTone)}>
                {lastSignal?.name ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-current pt-4 font-mono text-xs font-bold uppercase">
              <span>Signal {String(signalCount).padStart(3, "0")}</span>
            </div>
            <Button variant="outline" onClick={leaveRoom} className="absolute right-4 top-14 rounded-none border-current bg-transparent lg:hidden"><LogOut /> Leave</Button>
          </section>
        )}
      </div>
    </main>
  );
}
