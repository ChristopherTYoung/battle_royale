import type { PlayerInput } from "./websocket";

export class InputHandler {
  private keys: Set<string> = new Set();
  private mousePosition: { x: number; y: number } = { x: 0, y: 0 };
  private shooting: boolean = false;

  constructor() {
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    document.addEventListener("keydown", (e) => this.onKeyDown(e));
    document.addEventListener("keyup", (e) => this.onKeyUp(e));
    document.addEventListener("mousemove", (e) => this.onMouseMove(e));
    document.addEventListener("mousedown", () => (this.shooting = true));
    document.addEventListener("mouseup", () => (this.shooting = false));
  }

  private onKeyDown(event: KeyboardEvent): void {
    this.keys.add(event.key.toLowerCase());
  }

  private onKeyUp(event: KeyboardEvent): void {
    this.keys.delete(event.key.toLowerCase());
  }

  private onMouseMove(event: MouseEvent): void {
    this.mousePosition = { x: event.clientX, y: event.clientY };
  }

  getInput(playerPos: [number, number]): PlayerInput {
    // Calculate movement from WASD keys
    let move_x = 0;
    let move_y = 0;

    if (this.keys.has("w")) move_y -= 1;
    if (this.keys.has("s")) move_y += 1;
    if (this.keys.has("a")) move_x -= 1;
    if (this.keys.has("d")) move_x += 1;

    // Normalize diagonal movement to prevent faster diagonal movement
    const moveLength = Math.sqrt(move_x * move_x + move_y * move_y);
    if (moveLength > 0) {
      move_x /= moveLength;
      move_y /= moveLength;
    }

    // Calculate direction from player to mouse
    const dx = this.mousePosition.x - playerPos[0];
    const dy = this.mousePosition.y - playerPos[1];
    const dirLength = Math.sqrt(dx * dx + dy * dy);

    const direction_x = dirLength > 0 ? dx / dirLength : 0;
    const direction_y = dirLength > 0 ? dy / dirLength : 0;

    return {
      move_x,
      move_y,
      direction_x,
      direction_y,
      shooting: this.shooting,
    };
  }

  isKeyPressed(key: string): boolean {
    return this.keys.has(key.toLowerCase());
  }

  getMousePosition(): { x: number; y: number } {
    return { ...this.mousePosition };
  }

  dispose(): void {
    document.removeEventListener("keydown", (e) => this.onKeyDown(e));
    document.removeEventListener("keyup", (e) => this.onKeyUp(e));
    document.removeEventListener("mousemove", (e) => this.onMouseMove(e));
  }
}

export function createInputHandler(): InputHandler {
  return new InputHandler();
}
