class DashingBuff:

    def __init__(self, character):
        self.name = 'DashingBuff'
        self.speed = 30
        self.character = character
        self.direction = character.facing
        self.duration = 9

    def update(self):
        if self.duration > 0:
            self.duration -= 1

            if self.direction == 'left':
                self.character.dx = -self.speed
            else:
                self.character.dx = self.speed
            self.character.gravity = 0
            self.speed *= 0.9
