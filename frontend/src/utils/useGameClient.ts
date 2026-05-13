import { useEffect, useState, useCallback, useRef } from "react";
import {
  GameWebSocket,
  type GameState,
  type PlayerInput,
  createGameClient,
} from "./websocket";

export interface UseGameClientOptions {
  serverUrl: string;
  clientId: string;
  autoConnect?: boolean;
}

export function useGameClient(options: UseGameClientOptions) {
  const { serverUrl, clientId, autoConnect = true } = options;
  const clientRef = useRef<GameWebSocket | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(autoConnect);

  // Initialize client
  useEffect(() => {
    clientRef.current = createGameClient(serverUrl, clientId);

    clientRef.current.onGameStateUpdate((state) => {
      setGameState(state);
    });

    clientRef.current.onError((err) => {
      setError(err);
    });

    clientRef.current.onConnect(() => {
      setIsConnected(true);
      setIsLoading(false);
    });

    if (autoConnect) {
      clientRef.current.connect().catch((err) => {
        setError(err);
        setIsLoading(false);
      });
    }

    return () => {
      clientRef.current?.disconnect();
    };
  }, [serverUrl, clientId, autoConnect]);

  const connect = useCallback(async () => {
    if (!clientRef.current) return;
    setIsLoading(true);
    try {
      await clientRef.current.connect();
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Connection failed"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
    setIsConnected(false);
  }, []);

  const sendInput = useCallback((input: PlayerInput) => {
    clientRef.current?.sendInput(input);
  }, []);

  return {
    gameState,
    isConnected,
    isLoading,
    error,
    connect,
    disconnect,
    sendInput,
  };
}
