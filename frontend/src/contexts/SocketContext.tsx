import { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { useAppStore } from "@/stores/appStore";
import { getWsUrl } from "@/lib/api";

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

  const connect = useCallback(() => {
    try {
      const socket = new WebSocket(WS_URL);
      ws.current = socket;

      socket.onopen = () => {
        setConnected(true);
        storeSetConnected(true);
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
        setConnected(false);
        storeSetConnected(false);
      };

      socket.onclose = () => {
        setConnected(false);
        storeSetConnected(false);
        // Reconnect after 5 s
        reconnectTimer.current = setTimeout(connect, 5000);
      };
    } catch {
      reconnectTimer.current = setTimeout(connect, 5000);
    }
  }, [storeSetConnected, addAgentActivity]);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connect]);

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
