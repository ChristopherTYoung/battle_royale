export interface PlayerInput {
  move_x: number;
  move_y: number;
  direction_x: number;
  direction_y: number;
  shooting: boolean;
}

export interface Actor {
  id: number;
  pos: [number, number];
  health: number;
}

export interface GameState {
  player: Actor;
  enemies: Actor[];
  projectiles: Array<{ pos: [number, number]; direction: [number, number] }>;
}

type GameStateCallback = (state: GameState) => void;
type ErrorCallback = (error: Error) => void;
type ConnectionCallback = () => void;

export class GameWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private clientId: string;
  private stateCallback: GameStateCallback | null = null;
  private errorCallback: ErrorCallback | null = null;
  private connectCallback: ConnectionCallback | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // ms

  constructor(url: string, clientId: string) {
    this.url = url;
    this.clientId = clientId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.url}/game/${this.clientId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log("Connected to game server");
          this.reconnectAttempts = 0;
          this.connectCallback?.();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const gameState = JSON.parse(event.data) as GameState;
            this.stateCallback?.(gameState);
          } catch (error) {
            console.error("Failed to parse game state:", error);
            this.errorCallback?.(new Error("Invalid game state format"));
          }
        };

        this.ws.onerror = () => {
          const error = new Error("WebSocket error occurred");
          console.error(error);
          this.errorCallback?.(error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log("Disconnected from game server");
          this.attemptReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );
      
      setTimeout(() => {
        this.connect().catch((error) => {
          console.error("Reconnection failed:", error);
        });
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      const error = new Error("Max reconnection attempts reached");
      this.errorCallback?.(error);
    }
  }

  sendInput(input: PlayerInput): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(input));
      } catch (error) {
        console.error("Failed to send input:", error);
        this.errorCallback?.(new Error("Failed to send input"));
      }
    } else {
      console.warn("WebSocket not connected");
    }
  }

  onGameStateUpdate(callback: GameStateCallback): void {
    this.stateCallback = callback;
  }

  onError(callback: ErrorCallback): void {
    this.errorCallback = callback;
  }

  onConnect(callback: ConnectionCallback): void {
    this.connectCallback = callback;
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export function createGameClient(
  serverUrl: string,
  clientId: string
): GameWebSocket {
  return new GameWebSocket(serverUrl, clientId);
}
