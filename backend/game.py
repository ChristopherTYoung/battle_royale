import time
import threading

import numpy as np

from actor import Actor
from game_core import GameCore
from enemy import Enemy

class Game(GameCore):
    def __init__(self, tick_rate=60):
        super().__init__(tick_rate)
        self.enemy_ai_agents = []  # List to store Enemy AI objects
        self.tick_count = 0
    
    def add_enemies(self, count, health=100):
        for _ in range(count):
            position = np.array([np.random.randint(-960, 960), np.random.randint(-540, 540)], dtype=int)
            
            # Add enemy to game and get its id
            enemy_id = self.add_enemy(position, health)
            
            # Create Enemy AI agent for this enemy
            enemy_ai = Enemy(enemy_id, self)
            self.enemy_ai_agents.append(enemy_ai)
    
    def action(self, move_x, move_y, direction_x, direction_y, shooting=False):
        self.player_input = {
            'move_x': move_x,
            'move_y': move_y,
            'direction_x': direction_x,
            'direction_y': direction_y,
            'shooting': shooting
        }
        # Return current state without waiting for update
        return self.get_info()
    
    def _game_loop(self):
       while self.running:
           self.tick()
    
    def step(self, enemy_id, action):
        move_x, move_y, direction_x, direction_y, shoot = action
        
        # Update enemy with the action
        self.update_enemy(
            enemy_id,
            move_x,
            move_y,
            direction_x,
            direction_y,
            shoot=1 if shoot > 0.5 else 0
        )
        
        # Return current game state
        enemy = self.enemies[enemy_id]
        return {
            'player_pos': self.player.position,
            'player_health': self.player.health,
            'enemy_pos': enemy.position,
            'enemy_health': enemy.health,
            'distance': np.linalg.norm(self.player.position - enemy.position),
            'projectiles': [(p.position, p.direction) for p in self.projectiles]
        }

    def tick(self):
        self.tick_count += 1
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
           
        # Read player input (set by action() method)
        inp = self.player_input
           
        # Update player with current input
        self._update_player(np.array([inp['move_x'], inp['move_y']]), np.array([inp['direction_x'], inp['direction_y']]), dt)
           
        # Shoot if requested
        if inp['shooting']:
            self._player_shoot()
           
        # Update projectiles, check collisions
        self._update_projectiles(dt)
        self._check_collisions()
           
        # Sleep to maintain tick rate
        time.sleep(max(0, self.dt - (time.time() - current_time)))
