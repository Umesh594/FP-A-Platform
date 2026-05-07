import { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { useAppStore } from "@/stores/appStore";
import { api, getWsUrl } from "@/lib/api";

const WS_URL = import.meta.env.VITE_WS_URL || getWsUrl();

interface WsMessage {
  agent?: string;
  kpis?: unknown[];
  scenarios?: unknown;
  variance?: number;
  percentage?: number;
  explanation?: string;
  [key: string]: unknown;
}

interface SocketContextValue {
  connected: boolean;
  lastMessage: WsMessage | null;
  send: (msg: unknown) => void;
}

const SocketContext = createContext<SocketContextValue>({
  connected: false,
  lastMessage: null,
  send: () => {},
});

export const useSocket = () => useContext(SocketContext);

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const { setConnected: storeSetConnected, addAgentActivity } = useAppStore();
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const healthTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectAttempt = useRef(0);

  const setConnectionState = useCallback(
    (value: boolean) => {
      setConnected(value);
      storeSetConnected(value);
    },
    [storeSetConnected],
  );

  const clearHeartbeat = useCallback(() => {
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
  }, []);

  const scheduleReconnect = useCallback(
    (fn: () => void) => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      reconnectAttempt.current += 1;
      const delay = Math.min(30000, 2000 * reconnectAttempt.current);
      reconnectTimer.current = setTimeout(fn, delay);
    },
    [],
  );

  const connect = useCallback(() => {
    try {
      if (ws.current?.readyState === WebSocket.OPEN || ws.current?.readyState === WebSocket.CONNECTING) {
        return;
      }

      const socket = new WebSocket(WS_URL);
      ws.current = socket;

      socket.onopen = () => {
        reconnectAttempt.current = 0;
        setConnectionState(true);
        clearHeartbeat();
        heartbeatTimer.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "ping", ts: Date.now() }));
          }
        }, 25000);
      };

      socket.onmessage = (event) => {
        try {
          const data: WsMessage = JSON.parse(event.data);
          setLastMessage(data);

          // Push live agent activity into store
          if (data.agent) {
            addAgentActivity({
              id: `ws-${Date.now()}`,
              agentName: data.agent,
              action: data.explanation
                ? `Variance analysis: ${(data.percentage as number * 100).toFixed(1)}%`
                : data.kpis
                ? `KPI update received`
                : `Agent update received`,
              timestamp: new Date(),
              status: "completed",
              detail: data.explanation ? String(data.explanation).slice(0, 120) : undefined,
            });
          }
        } catch {
          // non-JSON frame — ignore
        }
      };

      socket.onerror = () => {
        clearHeartbeat();
      };

      socket.onclose = () => {
        clearHeartbeat();
        setConnectionState(false);
        scheduleReconnect(connect);
      };
    } catch {
      setConnectionState(false);
      scheduleReconnect(connect);
    }
  }, [addAgentActivity, clearHeartbeat, scheduleReconnect, setConnectionState]);

  useEffect(() => {
    connect();
    healthTimer.current = setInterval(async () => {
      try {
        const health = await api.health();
        if (health.status === "ok" && ws.current?.readyState !== WebSocket.OPEN) {
          setConnectionState(true);
          connect();
        }
      } catch {
        if (ws.current?.readyState !== WebSocket.OPEN) {
          setConnectionState(false);
        }
      }
    }, 15000);

    return () => {
      clearHeartbeat();
      ws.current?.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (healthTimer.current) clearInterval(healthTimer.current);
    };
  }, [clearHeartbeat, connect, setConnectionState]);

  const send = useCallback((msg: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(msg));
    }
  }, []);

  return (
    <SocketContext.Provider value={{ connected, lastMessage, send }}>
      {children}
    </SocketContext.Provider>
  );
}
