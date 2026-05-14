
class Bullet():
    def __init__(self, position, direction, owner, speed = 500, lifetime = 5, age = 0):
            self.position = position
            self.direction = direction
            self.owner = owner
            self.speed = speed
            self.lifetime = lifetime
            self.age = age