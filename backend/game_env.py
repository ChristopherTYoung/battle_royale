import random
import threading
import time

from actor import Actor
from game_core import GameCore
import gymnasium as gym
from gymnasium import spaces

import numpy as np

class GameEnv(GameCore, gym.Env):
    def __init__(self, tick_rate=60):
        super().__init__(tick_rate)
        self.previous_distance = 100
        self.position = [0, 100]
        self.previous_player_health = self.player.health
        self.previous_health = 100
        self.id = self.add_enemy(self.position, self.previous_health)
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(5,),
            dtype=np.float32
        )
        
    def _game_loop(self):
        pass
    
    def _snap_to_half(x):
        return np.round(x * 2) / 2
        
    def _get_obs(self):
        agent = self.enemies[self.id]
        
        return {
            'agent': agent.position, 
            'target': self.player.position, 
            'agent_health': agent.health,
            'target_health': self.player.health,
            'distance_to_player': np.linalg.norm([self.player.position, agent.position])
            }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.player = Actor()
        self.enemies = {}
        self.projectiles = []
        
        # Input buffer (updated by WebSocket, read by game loop)
        self.player_input = {'move_x': 0, 'move_y': 0, 'direction_x': 0, 'direction_y': 0, 'shooting': False}
        self.position = self.np_random.integers(-960, 960, size=2, dtype=int)
        self.previous_distance = np.linalg.norm([self.player.position, self.position])
        self.previous_health = 100
        self.previous_player_health = self.player.health
        self.id = self.add_enemy(self.position, self.previous_health)
        
        # Start game loop on separate thread
        self.running = True
        self.last_time = time.time()
        self.game_thread = threading.Thread(target=self._game_loop, daemon=True)
        self.game_thread.start()     
        
    def step(self, action):
        move_x, move_y, direction_x, direction_y, shoot = action
        self.update_enemy(self._snap_to_half(move_x), 
                          self._snap_to_half(move_y), 
                          self._snap_to_half(direction_x), 
                          self._snap_to_half(direction_y), 
                          shoot = 1 if np.abs(shoot) > 0.5 else 0)
        current_distance = np.linalg.norm([self.player.position, self.enemies])
        enemy = self.enemies[self.id]
        reward = 0

        # encourage survival
        reward += 0.01
        
        # encourage approaching player
        reward += self.previous_distance - current_distance
        
        # reward hits
        reward += 10 if self.player.health < self.previous_player_health else 0
        
        # reward kill
        reward += 100 if self.player.health <= 0 else 0
        
        # punish death
        reward -= 100 if enemy.health <= 0 else 0
        
        observation = self._get_obs()
        
        terminated = (
            self.player.health <= 0 or
            enemy.health <= 0
        )
        
        return observation, reward, terminated, False, observation["distance_to_player"]
