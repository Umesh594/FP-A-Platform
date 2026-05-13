import { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { type AgentConnectionStatus, useAppStore } from "@/stores/appStore";
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
  const setAgentConnectionStatus = useAppStore((state) => state.setAgentConnectionStatus);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const healthTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const offlineTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempt = useRef(0);

  const setConnectionState = useCallback(
    (status: AgentConnectionStatus) => {
      const isUsable = status === "connected" || status === "degraded";
      setConnected(isUsable);
      storeSetConnected(isUsable);
      setAgentConnectionStatus(status);
    },
    [setAgentConnectionStatus, storeSetConnected],
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

  const markOfflineAfterGrace = useCallback(() => {
    if (offlineTimer.current) clearTimeout(offlineTimer.current);
    offlineTimer.current = setTimeout(() => {
      if (ws.current?.readyState !== WebSocket.OPEN) {
        setConnectionState("offline");
      }
    }, 25000);
  }, [setConnectionState]);

  const connect = useCallback(() => {
    try {
      if (ws.current?.readyState === WebSocket.OPEN || ws.current?.readyState === WebSocket.CONNECTING) {
        return;
      }

      setConnectionState("connecting");
      const socket = new WebSocket(WS_URL);
      ws.current = socket;

      socket.onopen = () => {
        reconnectAttempt.current = 0;
        if (offlineTimer.current) clearTimeout(offlineTimer.current);
        setConnectionState("connected");
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
        setConnectionState("connecting");
        markOfflineAfterGrace();
        scheduleReconnect(connect);
      };
    } catch {
      setConnectionState("connecting");
      markOfflineAfterGrace();
      scheduleReconnect(connect);
    }
  }, [addAgentActivity, clearHeartbeat, markOfflineAfterGrace, scheduleReconnect, setConnectionState]);

  useEffect(() => {
    let cancelled = false;

    async function wakeBackendAndConnect() {
      setConnectionState("connecting");
      try {
        const health = await api.health();
        if (!cancelled && health.status === "ok") {
          setConnectionState("degraded");
        }
      } catch {
        markOfflineAfterGrace();
      } finally {
        if (!cancelled) connect();
      }
    }

    wakeBackendAndConnect();
    connect();
    healthTimer.current = setInterval(async () => {
      try {
        const health = await api.health();
        if (health.status === "ok" && ws.current?.readyState !== WebSocket.OPEN) {
          setConnectionState("degraded");
          connect();
        }
      } catch {
        if (ws.current?.readyState !== WebSocket.OPEN) {
          markOfflineAfterGrace();
        }
      }
    }, 15000);

    return () => {
      cancelled = true;
      clearHeartbeat();
      ws.current?.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (healthTimer.current) clearInterval(healthTimer.current);
      if (offlineTimer.current) clearTimeout(offlineTimer.current);
    };
  }, [clearHeartbeat, connect, markOfflineAfterGrace, setConnectionState]);

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
