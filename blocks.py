from pygame import Rect


class Block:

    def __init__(self, pos):
        self.name = 'Block'

        self.pos = pos
        size = 8, 8
        self.rect = Rect(pos, size)


class Platform:

    def __init__(self, pos):
        self.name = 'Platform'

        self.pos = pos
        size = 8, 8
        self.rect = Rect(pos, size)


class Step:

    def __init__(self, pos):
        self.name = 'Step'

        self.pos = pos
        size = 8, 8
        self.rect = Rect(pos, size)
