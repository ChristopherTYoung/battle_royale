import numpy as np
import time

from game import Game
import pytest

def test_no_input():
    game = Game()
    game.tick()
    
    assert np.linalg.norm(game.player.position) == 0

@pytest.mark.parametrize("direction_x, direction_y", [(1, 0), (0, 1), (-1, 0), (0, -1), (0.5, 0.5), (-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5)])
def test_all_positive_directions(direction_x, direction_y):
    game = Game()
    game.action(direction_x, direction_y, direction_x, direction_y, False)
    game.tick()
    
    assert np.linalg.norm(game.player.position) > 0

@pytest.mark.parametrize("direction_x, direction_y", [(1, 0), (0, 1), (-1, 0), (0, -1), (0.5, 0.5), (-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5)])
def test_shooting_creates_projectile(direction_x, direction_y):
    game = Game()
    initial_count = len(game.projectiles)
    game.action(direction_x, direction_y, direction_x, direction_y, shooting=True)
    game.tick()

    assert len(game.projectiles) > initial_count
    assert game.projectiles[0]['direction'][0] == direction_x
    assert game.projectiles[0]['direction'][1] == direction_y

def test_projectiles_disappear_after_expiration():
    game = Game()
    game.action(move_x=1, move_y=0, direction_x=1, direction_y=0, shooting=True)
    game.tick()
    game.action(move_x=1, move_y=0, direction_x=1, direction_y=0, shooting=False)
    
    assert len(game.projectiles) > 0
    
    time.sleep(5)
    assert len(game.projectiles) == 0
