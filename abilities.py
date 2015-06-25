class DashAbility:
        def __init__(self):
                self.name = 'DashAbility'
                self.speed = 28
                self.cooldown = 0
                self.maxcooldown = 120
        def use(self):
                self.cooldown = self.maxcooldown
class PounceAbility:
        def __init__(self):
                self.name = 'PounceAbility'
                self.xspeed = 12
                self.yspeed = -18
                self.cooldown = 0
                self.maxcooldown = 300
        def use(self):
                self.cooldown = self.maxcooldown
        def update(self, character, direction):
                if direction == 'left':
                        character.dx = -self.xspeed
                elif direction == 'right':
                        character.dx = self.xspeed
                character.dy = self.yspeed

class ThrowKnifeAbility:
        def __init__(self):
                self.name = 'ThrowKnifeAbility'
                self.cooldown = 0
                self.maxcooldown = 180
        def use(self):
                self.cooldown = self.maxcooldown
