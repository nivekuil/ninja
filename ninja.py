#!/usr/bin/env python
from __future__ import division

import pygame
import rabbyt
import os
import sys
import fonts

from events import *
from abilities import *
from buffs import *

from OpenGL.GL import *


class EventManager:

    def __init__(self):
        from weakref import WeakKeyDictionary
        self.listeners = WeakKeyDictionary()
        self.eventQueue = []
        self.listenersToAdd = []
        self.listenersToRemove = []

    def RegisterListener(self, listener):
        self.listenersToAdd.append(listener)

    def UnregisterListener(self, listener):
        self.listenersToRemove.append(listener)

    def ActuallyUpdateListeners(self):
        for listener in self.listenersToAdd:
            self.listeners[listener] = 1
        for listener in self.listenersToRemove:
            if listener in self.listeners:
                del self.listeners[listener]

    def ConsumeEventQueue(self):
        i = 0
        while i < len(self.eventQueue):
            event = self.eventQueue[i]
            for listener in self.listeners:
                # Note: a side effect of notifying the listener
                # could be that more events are put on the queue
                # or listeners could Register / Unregister
                old = len(self.eventQueue)
                listener.Notify(event)
            i += 1
            if self.listenersToAdd:
                self.ActuallyUpdateListeners()
        # all code paths that could possibly add more events to
        # the eventQueue have been exhausted at this point, so
        # it's safe to empty the queue
        self.eventQueue = []

    def Post(self, event):
        self.eventQueue.append(event)
        if event.name == 'TickEvent':
            self.ActuallyUpdateListeners()
            self.ConsumeEventQueue()


def endProgram():
    pygame.quit()
    sys.exit()


class GameController:

    def __init__(self, evManager, playerName=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.drawCounter = 0
        self.drawCountTo = 1

        self.activePlayer = None
        self.playerName = playerName
        self.players = []

    def onGameRunning(self):
        event = None
        key = pygame.key.get_pressed()

        if key[pygame.K_LEFT]:
            direction = 'left'
            event = CharacterWalkRequest(direction)
            self.evManager.Post(event)

        elif key[pygame.K_RIGHT]:
            direction = 'right'
            event = CharacterWalkRequest(direction)
            self.evManager.Post(event)

        for e in pygame.event.get():
            ev = None
            if e.type == pygame.QUIT:
                endProgram()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_p:
                    ev = GamePauseEvent()
                elif e.key == pygame.K_COMMA:
                    if self.playerName:
                        name = self.playerName
                    else:
                        name = 'player%s' % str(len(self.players))
                    playerData = {'name': name}
                    ev = PlayerJoinRequest(playerData)
                elif e.key == pygame.K_PERIOD:
                    pos = 600, 32
                    ev = CharacterAddRequest(pos)
                elif e.key == pygame.K_SPACE:
                    ev = CharacterJumpRequest()
                elif e.key == pygame.K_DOWN:
                    ev = CharacterDropEvent()
                elif e.key == pygame.K_a:
                    ev = CharacterPunchRequest()
                elif e.key == pygame.K_d:
                    ev = AbilityUseEvent('DashAbility')
                elif e.key == pygame.K_s:
                    ev = AbilityUseEvent('ThrowKnifeAbility')
                elif e.key == pygame.K_v:
                    ev = AbilityUseEvent('PounceAbility')

            if ev:
                self.evManager.Post(ev)

    def onGamePaused(self):
        for e in pygame.event.get():
            ev = None
            if e.type == pygame.QUIT:
                endProgram()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    ev = GameStartEvent()
                if e.key == pygame.K_p:
                    ev = GamePauseEvent()
            if ev:
                self.evManager.Post(ev)

    def Notify(self, event):
        if event.name == 'TickEvent':
            self.drawCounter += 1
            if self.drawCounter == self.drawCountTo:
                self.drawCounter = 0

                event = DrawEvent()
                self.evManager.Post(event)
        elif event.name == 'PlayerJoinEvent':
            self.players.append(event.player)
            if event.player.name == self.playerName:
                self.activePlayer = event.player
            if not self.playerName and not self.activePlayer:
                self.activePlayer = event.player

        elif event.name == 'GamePausedEvent':
            self.onGamePaused()
        elif event.name == 'GameRunningEvent':
            self.onGameRunning()


class TickController:

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.running = 1
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.showFps = False

    def run(self):
        while self.running:
            self.clock.tick(self.fps)
            event = TickEvent()

            if self.showFps:
                event = TickEvent(self.clock.get_fps())

            self.evManager.Post(event)

    def Notify(self, event):
        pass


class Sprite(rabbyt.Sprite):

    def __init__(self, *args, **kwargs):
        rabbyt.Sprite.__init__(self, *args, **kwargs)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)


class CharacterSprite:

    def __init__(self):

        self.idleRight = [((0, 64, 32, 0), (0, 1, 1 / 8, 3 / 4))]
        self.idleLeft = [((0, 64, 32, 0), (1 / 8, 1, 0, 3 / 4))]

        self.walkRight = [((0, 64, 48, 0), (0, 3 / 4, 3 / 16, 1 / 2)),
                          ((0, 64, 48, 0), (3 / 16, 3 / 4, 6 / 16, 1 / 2)),
                          ((0, 64, 48, 0), (6 / 16, 3 / 4, 9 / 16, 1 / 2)),
                          ((0, 64, 48, 0), (9 / 16, 3 / 4, 12 / 16, 1 / 2)),
                          ((0, 64, 48, 0), (12 / 16, 3 / 4, 15 / 16, 1 / 2))]

        self.walkLeft = [((0, 64, 48, 0), (3 / 16, 3 / 4, 0, 1 / 2)),
                         ((0, 64, 48, 0), (6 / 16, 3 / 4, 3 / 16, 1 / 2)),
                         ((0, 64, 48, 0), (9 / 16, 3 / 4, 6 / 16, 1 / 2)),
                         ((0, 64, 48, 0), (12 / 16, 3 / 4, 9 / 16, 1 / 2)),
                         ((0, 64, 48, 0), (15 / 16, 3 / 4, 12 / 16, 1 / 2))]

        self.jumpRight = [((0, 64, 48, 0), (0, 1 / 2, 3 / 16, 1 / 4))]
        self.jumpLeft = [((0, 64, 48, 0), (3 / 16, 1 / 2, 0, 1 / 4))]

        self.punchRight = [((0, 64, 48, 0), (0, 1 / 4, 3 / 16, 0))]
        self.punchLeft = [((0, 64, 48, 0), (3 / 16, 1 / 4, 0, 0))]

        self.dashRight = [((0, 64, 48, 0), (196 / 256, 1, 1, 208 / 256))]
        self.dashLeft = [((0, 64, 48, 0), (1, 1, 196 / 256, 208 / 256))]

        self.onwallRight = [((0, 64, 48, 0), (3 / 16, 1 / 2, 0, 1 / 4))]
        self.onwallLeft = [((0, 64, 48, 0), (0, 1 / 2, 3 / 16, 1 / 4))]

        self.name = 'CharacterSprite'

        self.image = Sprite('ninja.png')
        self.image.shape = (0, 0, 0, 0)

    def set_cell(self, frame, action):
        if action == 'idleRight':
            shapes = self.idleRight[frame]
        elif action == 'idleLeft':
            shapes = self.idleLeft[frame]
        elif action == 'walkRight':
            shapes = self.walkRight[frame]
        elif action == 'walkLeft':
            shapes = self.walkLeft[frame]
        elif action == 'jumpRight':
            shapes = self.jumpRight[frame]
        elif action == 'jumpLeft':
            shapes = self.jumpLeft[frame]
        elif action == 'punchRight':
            shapes = self.punchRight[frame]
        elif action == 'punchLeft':
            shapes = self.punchLeft[frame]
        elif action == 'dashRight':
            shapes = self.dashRight[frame]
        elif action == 'dashLeft':
            shapes = self.dashLeft[frame]
        elif action == 'onwallLeft':
            shapes = self.onwallLeft[frame]
        elif action == 'onwallRight':
            shapes = self.onwallRight[frame]

        self.image.shape, self.image.tex_shape = shapes


class View:

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.camera = Camera(evManager)

        self.windowSize = 1280, 720

        if pygame.display.Info().current_h > 768:
            os.environ['SDL_VIDEO_CENTERED'] = '1'
        else:
            offset_left = int(
                (pygame.display.Info().current_w - self.windowSize[0]) / 2)
            window_pos = str(offset_left) + ',' + '6'
            os.environ['SDL_VIDEO_WINDOW_POS'] = window_pos

        self.window = rabbyt.init_display(self.windowSize)

        self.sprites = []

    def addSprite(self, sprite):
        self.sprites.append(sprite())

    def getCharacter(self):
        for s in self.sprites:
            if s.name == 'CharacterSprite':
                return s

    def moveSprite(self, sprite, pos):
        window_y = self.windowSize[1] / 2
        window_x = self.windowSize[0] / 2
        halfSpriteHeight = sprite.shape[1][1] / 2
        halfSpriteWidth = sprite.shape[1][0] / 2
        camera = self.camera.rect

        top = window_y + camera.top - pos[1] + halfSpriteHeight
        left = window_x + camera.left - pos[0] + halfSpriteWidth
        sprite.top, sprite.left = top, -left

    def moveBackground(self, sprite, pos, xparallax, yparallax):
        window_y = self.windowSize[1] / 2
        window_x = self.windowSize[0] / 2
        camera = self.camera.rect

        top = window_y - pos[1]
        left = window_x - pos[0]
        if xparallax:
            left += camera.left / xparallax
        if yparallax:
            top += camera.top / yparallax
        sprite.top, sprite.left = top, -left

    def killCharacterSprite(self):
        character = self.getCharacter()
        if character:
            self.sprites.remove(character)

    def buildLevel(self, backgrounds):
        for b in backgrounds:
            background = BackgroundSprite(
                b.pos, b.image, b.xparallax, b.yparallax)
            self.sprites.append(background)

    def Notify(self, event):
        if event.name == 'DrawEvent':
            pass

        elif event.name == 'TickEvent':
            rect = self.camera.rect
            for i in self.sprites:
                sprite = i.image
                if i.name == 'BackgroundSprite':
                    self.moveBackground(
                        sprite, (0, 0), i.xparallax, i.yparallax)
                sprite.render()

            if event.fps:

                fps = int(event.fps)
                string = str(fps)
                pgFont = pygame.font.Font(None, 20)
                rabbytFont = fonts.Font(pgFont)
                fontSprite = fonts.FontSprite(rabbytFont, string)
                fontSprite.render()
            pygame.display.flip()

        elif event.name == 'SpriteAddEvent':
            self.sprites.append(event.sprite)

        elif event.name == 'SpritemodelAddEvent':
            self.sprites.append(event.model.sprite)

        elif event.name == 'ProjectileUpdateEvent':
            projectile = event.projectile
            for sprite in self.sprites:
                if projectile.sprite == sprite:
                    if projectile.isAlive:
                        self.moveSprite(sprite.image, projectile.rect.center)
                    else:
                        self.sprites.remove(sprite)

        elif event.name == 'SpriteKillEvent':
            for i in self.sprites:
                if event.model.sprite == i:
                    self.sprites.remove(i)

        elif event.name == 'CharacterAddEvent':
            self.addSprite(CharacterSprite)

        elif event.name == 'CharacterKillEvent':
            self.killCharacterSprite()

        elif event.name == 'CharacterUpdateEvent':
            character = self.getCharacter()
            self.moveSprite(character.image, event.rect.center)

        elif event.name == 'CharacterSetImage':
            character = self.getCharacter()
            character.set_cell(event.frame, event.action)

        elif event.name == 'LevelBuildEvent':
            backgrounds = event.backgrounds
            self.buildLevel(backgrounds)
            if event.layout.get_width() * 8 < self.windowSize[0]:
                self.camera.xscroll = False
            if event.layout.get_height() * 8 < self.windowSize[1]:
                self.camera.yscroll = False


class Game:
    STATE_RUNNING = 'running'
    STATE_PAUSED = 'paused'

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.state = Game.STATE_PAUSED

        self.level = Level(evManager)
        self.players = []
        self.entities = []

    def start(self):
        self.state = Game.STATE_RUNNING

        self.level.build()

    def add_player(self, player):
        self.players.append(player)
        event = PlayerJoinEvent(player)
        self.evManager.Post(event)
        for player in self.players:
            print player.name

    def pause(self):
        if self.state == 'paused':
            self.state = Game.STATE_RUNNING
        elif self.state == 'running':
            self.state = Game.STATE_PAUSED

    def getEntities(self):
        characters = [
            player.character for player in self.players if player.character]
        blocks = self.level.blocks
        projectiles = [projectile for projectile in self.level.projectiles]

        self.entities = characters + blocks + projectiles

    def update(self):
        for player in self.players:
            player.update()
        self.level.update()

    def Notify(self, event):
        if event.name == 'TickEvent':
            if self.state == Game.STATE_PAUSED:
                event = GamePausedEvent()

            elif self.state == Game.STATE_RUNNING:
                self.update()
                event = GameRunningEvent()
            self.evManager.Post(event)

        elif event.name == 'PlayerJoinRequest':
            player = Player(self.evManager)
            player.set_data(event.playerData)
            self.add_player(player)

        elif event.name == 'CharacterAddEvent':
            self.getEntities()
        elif event.name == 'LevelBuildEvent':
            self.getEntities()
        elif event.name == 'ProjectileAddEvent':
            self.getEntities()

        elif event.name == 'CharacterCollideRequest':
            event = CharacterCollideEvent(event.direction, self.entities)
            self.evManager.Post(event)

        elif event.name == 'GameStartEvent':
            self.start()
            print 'start'

        elif event.name == 'GamePauseEvent':
            self.pause()


class Camera:

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.rect = pygame.Rect(0, 0, 1280, 720)
        self.maxOffset = 100
        self.xbound = self.ybound = 0
        self.xscroll = self.yscroll = True

    def centerOn(self, pos):

        rect = self.rect
        if self.yscroll:
            ydist = rect.centery - pos[1]

            if ydist == 1 or ydist == -1:
                ydist = 0
            if ydist < 0:
                rect.centery += 2

                if ydist < -10:
                    rect.centery += 2
                if ydist < -20:
                    rect.centery += 4
                if ydist < -self.maxOffset:
                    rect.centery = pos[1] - self.maxOffset

            elif ydist > 0:
                rect.centery -= 2

                if ydist > 10:
                    rect.centery -= 2
                if ydist > 20:
                    rect.centery -= 5
                if ydist > self.maxOffset:
                    rect.centery = pos[1] + self.maxOffset
            if rect.top < 0:
                rect.top = 0
            elif rect.bottom > self.ybound:
                rect.bottom = self.ybound
        if self.xscroll:
            rect.centerx = pos[0]

            if rect.left < 0:
                rect.left = 0
            elif rect.right > self.xbound:
                rect.right = self.xbound

        event = CameraMoveEvent(self.rect.topleft)
        self.evManager.Post(event)

    def Notify(self, event):
        if event.name == 'CameraCenterRequest':
            self.centerOn(event.pos)
        elif event.name == 'LevelBuildEvent':
            self.xbound = event.layout.get_width() * 8
            self.ybound = event.layout.get_height() * 8


class Level:

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.projectiles = []

    def build(self):
        #layout = load_image('level1layout.png')
        #level = Background((0,0), 'level1.png', 1, 1)
        #background = Background((0,0), 'background1.png', 15, 15)
        #layout = load_image('henesyslayout.png')
        #level = Background((0,0), 'henesys.png', 1,1)
        #layout = load_image('citylevellayout.png')
        #level = Background((0,0), 'citylevel.png',1, 1)
        layout = load_image('level3layout.png')
        level = Background((0, 0), 'level3.png', 1, 1)
        background = Background((0, 0), 'background3.png', 20, 20)

        self.backgrounds = [background, level]

        width, height = layout.get_size()

        self.blocks = []
        from blocks import Block, Platform, Step

        for y in xrange(height):
            for x in xrange(width):
                pos = x * 8, y * 8

                if layout.get_at((x, y)) == (0, 0, 0, 255):
                    self.blocks.append(Block(pos))

                elif layout.get_at((x, y)) == (0, 0, 255, 255):
                    self.blocks.append(Platform(pos))

                elif layout.get_at((x, y)) == (255, 0, 0, 255):
                    self.blocks.append(Step(pos))

        event = LevelBuildEvent(layout, self.backgrounds)
        self.evManager.Post(event)

    def update(self):
        for p in self.projectiles:
            p.update()
            for b in self.blocks:
                if b.name == 'Block' or b.name == 'Step':
                    if p.rect.colliderect(b.rect):
                        p.response()
                        break
            if not p.isAlive:
                self.projectiles.remove(p)
            event = ProjectileUpdateEvent(p)
            self.evManager.Post(event)

    def Notify(self, event):
        if event.name == 'LevelBuildRequest':
            self.build(event.layout, event.backgrounds)

        elif event.name == 'ProjectileAddEvent':
            self.projectiles.append(event.projectile)

            event = SpritemodelAddEvent(event.projectile, event.projectile.pos)
            self.evManager.Post(event)


class Background:

    def __init__(self, pos, image, xparallax=0, yparallax=0):
        self.pos = pos
        self.image = image
        self.xparallax = xparallax
        self.yparallax = yparallax


class BackgroundSprite:

    def __init__(self, pos, image, xparallax=0, yparallax=0):
        self.name = 'BackgroundSprite'

        self.xparallax = xparallax
        self.yparallax = yparallax
        self.image = Sprite(image)


class ButtonCooldownSprite:

    def __init__(self, pos, image, decreaseby):
        self.name = 'ButtonCooldownSprite'
        self.image = Sprite(image)
        self.pos = pos
        self.image.top, self.image.left = pos[0] - 32, pos[1] - 32
        self.image.shape = (0, 0, 0, 0)
        self.height = 64
        self.decreaseby = decreaseby

    def update(self):
        self.height -= self.decreaseby
        self.image.shape = (0, self.height, 64, 0)
        self.image.tex_shape = (0, self.height / 64, 1, 0)


class SkillButtonSprite:

    def __init__(self, pos, image, shape=None):
        self.name = 'SkillButtonSprite'
        self.pos = pos
        self.image = Sprite(image)
        self.image.top, self.image.left = pos
        if shape:
            self.image.shape = shape


class Player:

    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.character = None
        self.name = ''

    def set_data(self, playerDict):
        self.name = playerDict['name']

    def addCharacter(self, pos):
        self.buffs = []

        if self.character:
            self.character.kill()

        name = 'Ninja'
        if name == 'Ninja':
            self.abilities = [
                ThrowKnifeAbility(), DashAbility(), PounceAbility()]
            self.buttons = [SkillButtonSprite((-250, -600), 'button_throwknife.png'),
                            SkillButtonSprite((-250, -520), 'button_dash.png'),
                            SkillButtonSprite((-250, -440), 'button_dash.png')]

            self.cooldownbuttons = [ButtonCooldownSprite(self.buttons[0].pos, 'button_throwknifecd.png',
                                                         64 / self.abilities[0].maxcooldown),
                                    ButtonCooldownSprite(self.buttons[1].pos, 'button_dashcd.png',
                                                         64 / self.abilities[1].maxcooldown),
                                    ButtonCooldownSprite(self.buttons[2].pos, 'button_dashcd.png',
                                                         64 / self.abilities[2].maxcooldown)]

            for i in self.buttons:
                event = SpriteAddEvent(i, i.pos)
                self.evManager.Post(event)
            for i in self.cooldownbuttons:
                event = SpriteAddEvent(i, i.pos)
                self.evManager.Post(event)

            self.character = Ninja(self.evManager, pos)

        event = CharacterAddEvent()
        self.evManager.Post(event)

    def update(self):
        if self.character:
            for i in self.abilities:
                if i.cooldown > 0:
                    i.cooldown -= 1
                    button = self.cooldownbuttons[self.abilities.index(i)]
                    button.update()
                    if i.cooldown == 0:
                        button.height = 64
            self.character.update()

    def ninjaAbilities(self, abilityname):
        ability = next(
            (a for a in self.abilities if a.name == abilityname), None)
        if not ability.cooldown:
            character = self.character
            if abilityname == 'DashAbility':
                if character.state == 'pouncing':
                    return
                character.useDash()
            elif abilityname == 'ThrowKnifeAbility':
                character.useThrowKnife()
            elif abilityname == 'PounceAbility':
                if character.inAir:
                    if character.state != 'on_wall':
                        return
                if character.state == 'jumping' or character.state == 'dashing':
                    return
                character.usePounce()
            ability.use()

    def Notify(self, event):
        if event.name == 'CharacterAddRequest':
            self.addCharacter(event.pos)

        elif event.name == 'AbilityUseEvent' and self.character:
            if self.character.name == 'Ninja':
                self.ninjaAbilities(event.ability)


class Character:
    STATE_IDLE = 'idle'
    STATE_WALKING = 'walking'
    STATE_JUMPING = 'jumping'
    STATE_ONWALL = 'on_wall'
    STATE_PUNCHING = 'punching'
    STATE_DASHING = 'dashing'
    STATE_POUNCING = 'pouncing'

    def __init__(self, evManager, pos):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.name = 'Character'

        self.inAir = False

        self.isAlive = 1
        self.pos = pos

        size = 32, 60
        self.rect = pygame.Rect(pos, size)

        self.maxSpeed = 6.0
        self.accel = 1.0
        self.speed = 0.0

        self.jumpForce = 15.0
        self.jumpFallVel = 0.0
        self.jumpFallAccel = 1.0

        self.gravity = 0
        self.state = Character.STATE_IDLE

        self.facing = 'right'

        self.dx = 0
        self.dy = 0

        self.walk_frame = 0
        self.walk_animFrame = 0

        self.punch_frame = 0

        self.dash_frame = 0
        self.pounce_frame = 0

        self.buffs = []

    def kill(self):
        self.isAlive = 0
        self.evManager.UnregisterListener(self)

        event = CharacterKillEvent()
        self.evManager.Post(event)

    def reverseDirection(self):
        if self.facing == 'right':
            self.facing = 'left'
        else:
            self.facing = 'right'

    def whenIdle(self):
        if self.facing == 'right':
            event = CharacterSetImage(0, 'idleRight')
        else:
            event = CharacterSetImage(0, 'idleLeft')
        self.evManager.Post(event)

    def whenWalking(self):
        if self.facing == 'right':
            event = CharacterSetImage(self.walk_animFrame, 'walkRight')
        else:
            event = CharacterSetImage(self.walk_animFrame, 'walkLeft')
        self.evManager.Post(event)

        if self.walk_frame % 5 == 0:
            self.walk_animFrame += 1
            if self.walk_animFrame > 4:
                self.walk_animFrame = 0
        self.walk_frame += 1

    def whenJumping(self):
        self.dy = self.jumpFallVel - self.jumpForce
        if self.jumpFallVel < self.jumpForce:
            self.jumpFallVel += self.jumpFallAccel
        else:
            self.jumpFallVel += self.jumpFallAccel - 0.3

        self.dx = self.speed
        if self.speed == self.maxSpeed or self.speed == -self.maxSpeed:
            self.speed *= 0.5
        if self.speed > 0.0:
            self.speed -= 0.1
        elif self.speed < 0.0:
            self.speed += 0.1
        if -0.1 < self.speed < 0.1:
            self.speed = 0

    def update(self):
        for i in self.buffs:
            i.update()
            if i.duration < 0:
                self.buffs.remove(i)

        if self.state == 'idle':
            self.whenIdle()

        if self.state == 'walking':
            if self.inAir:
                self.whenIdle()
            else:
                self.whenWalking()
        else:
            self.walk_frame = 0
            self.walk_animFrame = -1
        if self.state == 'jumping':
            if self.facing == 'right':
                event = CharacterSetImage(0, 'jumpRight')
            else:
                event = CharacterSetImage(0, 'jumpLeft')
            self.evManager.Post(event)

        if self.state == 'punching' or self.punch_frame:
            self.whenPunching()

        if self.state == 'dashing' or self.dash_frame:
            self.whenDashing()
        if self.state == 'pouncing' or self.pounce_frame:
            self.whenPouncing()
        if self.state == 'on_wall':
            self.whenOnWall()

        self.updateMovement()

        self.rect.topleft = self.pos

        event = CameraCenterRequest(self.rect.center)
        self.evManager.Post(event)

        event = CharacterUpdateEvent(self.rect)
        self.evManager.Post(event)

    def updateMovement(self):
        if self.state == 'idle':
            self.speed = 0

        if self.state == 'jumping':
            self.whenJumping()

        else:
            self.applyGravity()

        if self.dy > 15.0:
            self.dy = 15.0

        if self.dy < 0.0:
            event = CharacterCollideRequest('up')
            self.evManager.Post(event)
        else:
            event = CharacterCollideRequest('down')
            self.evManager.Post(event)

        if self.dx < 0.0:
            event = CharacterCollideRequest('left')
            self.evManager.Post(event)
        else:
            event = CharacterCollideRequest('right')
            self.evManager.Post(event)

        if self.pos[0] < 0:
            self.pos = 0, self.pos[1]

    def jump(self):
        if not self.inAir and self.state != 'jumping':
            self.state = Character.STATE_JUMPING
            self.jumpSpeed = self.jumpForce

            self.jumpFallVel = 0
            self.gravity = 0

    def walk(self, direction):
        if self.state == 'dashing' or self.dash_frame:
            return
        if self.state == 'pouncing' or self.pounce_frame:
            return

        accel = self.accel

        if direction == 'left':
            self.speed -= accel
            maxSpeed = -self.maxSpeed
            if self.speed < maxSpeed:
                self.speed = maxSpeed
            self.facing = 'left'

        elif direction == 'right':
            self.speed += accel
            if self.speed > self.maxSpeed:
                self.speed = self.maxSpeed
            self.facing = 'right'

        if self.state == 'punching' or self.punch_frame:
            return

        self.dx = self.speed

        if self.state == 'jumping':
            return
        if self.state == 'on_wall':
            return

        self.state = Character.STATE_WALKING

    def applyGravity(self):
        if self.gravity < 4:
            # always move atleast 1 pixel on first frame for collision
            # detection purposes
            self.gravity += 1
        elif self.gravity < 10:
            self.gravity += 0.4
        else:
            self.gravity += 0.2

        self.dy += self.gravity

    def checkCollideX(self, direction, entities):
        self.pos = self.pos[0] + self.dx, self.pos[1]

        rect = self.rect
        rect.topleft = self.pos

        colliderect = rect.colliderect
        collided = [e for e in entities if colliderect(e.rect)]

        collidedBlocks = []
        collidedSteps = []

        for c in collided:
            if c.name == 'Block':
                collidedBlocks.append(c.rect)
            elif c.name == 'Step':
                collidedSteps.append(c.rect)

        collideLeft = collideRight = False
        if collidedBlocks:
            collideRect = collidedBlocks[0]
            for ix in xrange(len(collidedBlocks)):
                collideRect = collideRect.union(collidedBlocks[ix])

            if direction == 'left':
                self.pos = collideRect.right, self.pos[1]
                collideLeft = True

            elif direction == 'right':
                self.pos = collideRect.left - rect.width, self.pos[1]
                collideRight = True

        if collideLeft or collideRight:
            self.speed = 0
            if self.state == 'dashing' or self.dash_frame:
                self.state = Character.STATE_IDLE
                self.dash_frame = 0
            if self.state == 'walking':
                self.state = Character.STATE_IDLE
            if self.state == 'pouncing':
                self.state = Character.STATE_IDLE
                self.pounce_frame = 0
                self.gravity = 0

            if self.inAir or self.state == 'jumping':
                if self.dy > 0:
                    self.state = Character.STATE_ONWALL
        else:
            if self.state == 'on_wall':
                self.state = Character.STATE_IDLE

        self.dx = self.dy = 0

    def checkCollideY(self, direction, entities):
        self.pos = self.pos[0], self.pos[1] + self.dy

        rect = self.rect
        rect.topleft = self.pos

        if self.dy < 8:
            footheight = self.dy
        else:
            footheight = 9
        footrect = pygame.Rect(
            rect.left, rect.bottom - footheight - 1, rect.width, footheight)

        colliderect = rect.colliderect
        collided = [e for e in entities if colliderect(e.rect)]

        collidedBlocks = []
        collidedPlatforms = []
        collidedSteps = []

        for c in collided:
            if c.name == 'Block':
                collidedBlocks.append(c.rect)
            elif c.name == 'Platform':
                if footrect.colliderect(c.rect):
                    collidedPlatforms.append(c.rect)
            elif c.name == 'Step':
                collidedSteps.append(c.rect)

        collideUp = collideDown = False
        if collidedBlocks:
            collideRect = collidedBlocks[0]
            for ix in xrange(len(collidedBlocks)):
                collideRect = collideRect.union(collidedBlocks[ix])

            if direction == 'up':
                self.pos = self.pos[0], collideRect.bottom
                if self.state == 'jumping':
                    self.jumpFallVel = self.jumpForce

                collideUp = True

            elif direction == 'down':
                self.pos = self.pos[0], collideRect.top - rect.height
                self.state = Character.STATE_IDLE
                self.inAir = False
                self.gravity = 0

                collideDown = True
        if collidedPlatforms and direction == 'down':
            heights = [platform.top for platform in collidedPlatforms]
            index = heights.index(min(heights))

            collideRect = collidedPlatforms[index]

            self.pos = self.pos[0], collideRect.bottom - rect.height
            self.state = Character.STATE_IDLE
            self.inAir = False
            self.gravity = 0

            collideDown = True

        if collidedSteps and direction == 'down':
            heights = [step.top for step in collidedSteps]
            index = heights.index(min(heights))

            collideRect = collidedSteps[index]

            self.pos = self.pos[0], collideRect.bottom - rect.height
            self.state = Character.STATE_IDLE
            self.inAir = False
            self.gravity = 0

            collideDown = True

        if collideUp:
            if self.state == 'pouncing':
                self.gravity += 1.5
                self.state = Character.STATE_IDLE

        if collideDown:
            self.pounce_frame = 0
            self.state = Character.STATE_IDLE
        else:
            if self.state != 'jumping':
                self.inAir = True

    def Notify(self, event):
        if not self.isAlive:  # if dead, stop listening for events here
            return
        if event.name == 'BuffAddEvent':
            self.buffs.append(event.buff)

        elif event.name == 'CharacterWalkRequest':
            if event.direction == 'left':
                self.walk('left')
            elif event.direction == 'right':
                self.walk('right')

        elif event.name == 'CharacterCollideEvent':
            if event.direction == 'left' or event.direction == 'right':
                self.checkCollideX(event.direction, event.entities)
            else:
                self.checkCollideY(event.direction, event.entities)

        elif event.name == 'CharacterJumpRequest':
            self.jump()
        elif event.name == 'CharacterDropEvent':
            if self.state == 'idle' or self.state == 'walking':
                self.dy = 9


class Ninja(Character):

    def __init__(self, evManager, pos):
        Character.__init__(self, evManager, pos)
        self.name = 'Ninja'

    def applyGravity(self):
        self.jumps = 2
        if self.dy < 0:
            self.gravity += 0.7
        else:
            if self.gravity < 2:
                self.gravity += 1
            elif self.gravity < 4:
                self.gravity += 0.8
            elif self.gravity < 8:
                self.gravity += 0.5
            else:
                self.gravity += 0.2

            if self.state == 'on_wall' and self.gravity > 4:
                self.gravity = 4.0

        self.dy += self.gravity

    def whenOnWall(self):
        self.state = Character.STATE_ONWALL
        if self.facing == 'right':
            event = CharacterSetImage(0, 'onwallRight')
        else:
            event = CharacterSetImage(0, 'onwallLeft')
        self.evManager.Post(event)

    def jump(self):
        if self.state == 'pouncing':
            return
        if self.jumps:
            if self.inAir:
                self.jumps -= 1
            self.jumps -= 1
            self.state = Character.STATE_JUMPING
            self.gravity = 0
            self.jumpFallVel = 0
            self.jumpSpeed = self.jumpForce

    def punch(self):
        if self.state == 'idle' or self.state == 'walking':
            self.state = Character.STATE_PUNCHING

    def whenPunching(self):
        self.state = Character.STATE_PUNCHING
        self.punch_frame += 1

        if self.facing == 'right':
            event = CharacterSetImage(0, 'punchRight')
        else:
            event = CharacterSetImage(0, 'punchLeft')
        self.evManager.Post(event)

        if self.punch_frame > 6:
            self.punch_frame = 0
            self.state = Character.STATE_IDLE

    def useDash(self):
        if self.state == 'on_wall':
            self.reverseDirection()

        self.state = Character.STATE_DASHING

        event = BuffAddEvent(DashingBuff(self))
        self.evManager.Post(event)

    def whenDashing(self):
        self.state = Character.STATE_DASHING
        self.dash_frame += 1

        if self.facing == 'right':
            event = CharacterSetImage(0, 'dashRight')
        else:
            event = CharacterSetImage(0, 'dashLeft')
        self.evManager.Post(event)

        if self.dash_frame > 10:
            self.dash_frame = 0
            self.state = Character.STATE_IDLE

    def whenPouncing(self):
        self.state = Character.STATE_POUNCING
        self.pounce_frame += 1

        PounceAbility().update(self, self.facing)
        if self.facing == 'right':
            event = CharacterSetImage(0, 'dashRight')
        else:
            event = CharacterSetImage(0, 'dashLeft')
        self.evManager.Post(event)
        if self.pounce_frame > 100:
            self.pounce_frame = 0
            self.state = Character.STATE_IDLE

    def useThrowKnife(self):
        if self.state == 'on_wall':
            self.reverseDirection()
        if self.facing == 'right':
            event = ProjectileAddEvent(
                ThrowKnife((self.rect.centerx, self.rect.top + 12), self.facing))
        else:
            event = ProjectileAddEvent(ThrowKnife((self.rect.centerx - 12, self.rect.top + 12),
                                                  self.facing))
        self.evManager.Post(event)

    def usePounce(self):
        self.gravity = 0
        if self.state == 'on_wall':
            self.reverseDirection()
        self.state = Character.STATE_POUNCING

    def Notify(self, event):
        if not self.isAlive:
            return
        Character.Notify(self, event)

        if event.name == 'CharacterPunchRequest':
            self.punch()


class ThrowKnife:

    def __init__(self, pos, direction):
        self.name = 'ThrowKnife'

        self.pos = pos

        size = 16, 6
        self.rect = pygame.Rect(pos, size)

        self.damage = 10
        if direction == 'right':
            self.dx = 16
        else:
            self.dx = -16

        self.sprite = ThrowKnifeSprite()
        self.isAlive = 30

        self.dy = -0.6
        self.gravity = 0.08

    def update(self):
        self.pos = self.pos[0] + self.dx, self.pos[1] + self.dy
        self.dy += self.gravity
        self.rect.topleft = self.pos

        self.sprite.update(self.dx)

        self.isAlive -= 1

        if self.isAlive < 3:
            self.sprite.image.alpha -= 0.2

    def response(self):
        self.isAlive = 0


class ThrowKnifeSprite:

    def __init__(self):
        self.name = 'ThrowKnifeSprite'
        self.frames = [((0, 6, 16, 0), (0, 1, 1, 5 / 8)),
                       ((0, 4, 16, 0), (0, 3 / 4, 1, 0))]
        self.leftFrames = [((0, 6, 16, 0), (1, 1, 0, 5 / 8)),
                           ((0, 4, 16, 0), (1, 3 / 4, 0, 0))]
        self.image = Sprite('throwknife.png')
        self.image.shape = (0, 0, 0, 0)

        self.frame = 0

    def update(self, direction):
        frame = self.frame
        if direction > 0:
            shapes = self.frames[frame]
        else:
            shapes = self.leftFrames[frame]

        self.image.shape, self.image.tex_shape = shapes


def load_image(filename, xflip=0, yflip=0):
    image = pygame.image.load(filename).convert_alpha()
    image = pygame.transform.flip(image, xflip, yflip)
    return image


def main():
    pygame.init()

    evManager = EventManager()
    tickController = TickController(evManager)
    gameController = GameController(evManager)
    view = View(evManager)
    game = Game(evManager)
    tickController.run()

if __name__ == "__main__":
    main()
