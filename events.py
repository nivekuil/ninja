class Event(object):

    """Base abstract class for events used by Listeners to communicate."""
    attributes = ()
    to_log = True  # Set to False in subclasses to avoid flooding the log.

    def __init__(self, *args):
        """Create a new event.

        The arguments must correspond to the `attribute` class variable.

        """
        object.__init__(self)
        if len(self.attributes) != len(args):
            msg = ("Incorrect number of arguments: %i needed, %i provided "
                   "(attributes list: %r)." %
                   (len(self.attributes), len(args), self.attributes))
            raise TypeError(msg)
        pairs = zip(self.attributes, args)
        for name, value in pairs:
            setattr(self, name, value)

    def __repr__(self):
        pieces = []
        for attr_name in self.attributes:
            piece = "%s=%r" % (attr_name, getattr(self, attr_name))
            if len(piece) > 50:
                piece = piece[:50] + "..."
            pieces.append(piece)
        params = ', '.join(pieces)
        return "%s(%s)" % (self.__class__.__name__, params)

    def __str__(self):
        lines = [self.__class__.__name__]
        for attribute in self.attributes:
            lines.append("    %s = %r" % (attribute, getattr(self, attribute)))
        return '\n'.join(lines)


class TickEvent(Event):

    def __init__(self, fps=0):
        self.name = 'TickEvent'
        self.fps = fps


class DrawEvent(Event):

    def __init__(self):
        self.name = 'DrawEvent'


class GameStartEvent(Event):

    def __init__(self):
        self.name = "GameStartEvent"


class GamePauseEvent(Event):

    def __init__(self):
        self.name = "GamePauseEvent"


class GamePausedEvent(Event):

    def __init__(self):
        self.name = "GamePausedEvent"


class GameRunningEvent(Event):

    def __init__(self):
        self.name = "GameRunningEvent"


class PlayerUpdateEvent(Event):

    def __init__(self):
        self.name = "PlayerUpdateEvent"


class PlayerJoinRequest(Event):

    def __init__(self, playerData):
        self.name = "PlayerJoinRequest"
        self.playerData = playerData


class PlayerJoinEvent(Event):

    def __init__(self, player):
        self.name = "PlayerJoinEvent"
        self.player = player


class CharacterAddRequest(Event):

    def __init__(self, pos):
        self.name = "CharacterAddRequest"
        self.pos = pos


class CharacterAddEvent(Event):

    def __init__(self):
        self.name = "CharacterAddEvent"


class CharacterUpdateRequest(Event):

    def __init__(self):
        self.name = "CharacterUpdateRequest"


class CharacterUpdateEvent(Event):

    def __init__(self, rect):
        self.name = "CharacterUpdateEvent"
        self.rect = rect


class CharacterWalkRequest(Event):

    def __init__(self, direction):
        self.name = "CharacterWalkRequest"
        self.direction = direction


class CharacterSetImage(Event):

    def __init__(self, frame, action):
        self.name = "CharacterSetImage"
        self.frame = frame
        self.action = action


class CharacterJumpRequest(Event):

    def __init__(self):
        self.name = "CharacterJumpRequest"


class CharacterDropEvent(Event):

    def __init__(self):
        self.name = "CharacterDropEvent"


class CharacterPunchRequest(Event):

    def __init__(self):
        self.name = "CharacterPunchRequest"


class CharacterCollideRequest(Event):

    def __init__(self, direction):
        self.name = "CharacterCollideRequest"
        self.direction = direction


class CharacterCollideEvent(Event):

    def __init__(self, direction, entities):
        self.name = "CharacterCollideEvent"
        self.direction = direction
        self.entities = entities


class ProjectileAddEvent(Event):

    def __init__(self, projectile):
        self.name = "ProjectileAddEvent"
        self.projectile = projectile


class SpritemodelAddEvent(Event):

    def __init__(self, model, pos):
        self.name = "SpritemodelAddEvent"
        self.model = model
        self.pos = pos


class SpriteAddEvent(Event):

    def __init__(self, sprite, pos):
        self.name = "SpriteAddEvent"
        self.sprite = sprite
        self.pos = pos


class SpriteKillEvent(Event):

    def __init__(self, model, pos):
        self.name = "SpriteKillEvent"
        self.model = model
        self.pos = pos


class ProjectileUpdateEvent(Event):

    def __init__(self, projectile):
        self.name = "ProjectileUpdateEvent"
        self.projectile = projectile


class AbilityUseEvent(Event):

    def __init__(self, ability):
        self.name = "AbilityUseEvent"
        self.ability = ability


class AbilityDashEvent(Event):

    def __init__(self, direction):
        self.name = "AbilityDashEvent"
        self.direction = direction


class BuffAddEvent(Event):

    def __init__(self, buff):
        self.name = 'BuffAddEvent'
        self.buff = buff


class CharacterKillEvent(Event):

    def __init__(self):
        self.name = "CharacterKillEvent"


class LevelBuildRequest(Event):

    def __init__(self, layout, backgrounds):
        self.name = "LevelBuildRequest"
        self.layout = layout
        self.backgrounds = backgrounds


class LevelBuildEvent(Event):

    def __init__(self, layout, backgrounds):
        self.name = "LevelBuildEvent"
        self.layout = layout
        self.backgrounds = backgrounds


class CameraMoveEvent(Event):

    def __init__(self, topleft):
        self.name = "CameraMoveEvent"
        self.topleft = topleft


class CameraCenterRequest(Event):

    def __init__(self, pos, xscroll=True, yscroll=True):
        self.name = "CameraCenterRequest"
        self.pos = pos
        self.xscroll = xscroll
        self.yscroll = yscroll
