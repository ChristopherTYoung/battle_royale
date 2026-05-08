from typing import Optional, Tuple

import numpy as np

class Actor:
    def __init__(self, id: int = 0, position: Tuple[float, float] = (0, 0), health: int = 100, speed: float = 200):
        self.id = id
        self.position = np.array(position, dtype=np.float32)
        self.velocity = np.array([0, 0], dtype=np.float32)
        self.last_direction = np.array([1, 0], dtype=np.float32)  # Default facing right
        self.health = health
        self.speed = speed
        self.radius = 10  # For collision detection