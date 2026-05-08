import time
import threading

import numpy as np

from actor import Actor
from game_core import GameCore

class Game(GameCore):
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

    def tick(self):
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
