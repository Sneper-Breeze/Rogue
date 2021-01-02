import os
import pygame as pg
from pygame.locals import *
from map import Generator
import random

current_dir = os.path.dirname(__file__)
textures = os.path.join(current_dir, 'data')
FPS = 60
TILE_SIZE = 32
WIN_SIZE = pg.Rect(0, 0, 1280, 800)
ST_SPEED = 1
TILES = {
    ' ': 'space.bmp', # Пустота
    '.': 'floor.bmp', # Пол
    '#': 'wall.bmp', # Стена
    '@': 'floor.bmp', # Игрок
    '%': 'image_path', # Враг 1
    ':': 'image_path' # Враг 2
}
HARD_TILES = ['#']

player = None


def load_image(img, colorkey=None):
    try:
        image = pg.image.load(img)
    except Exception:
        print('Картинка не нашлась')
        image = pg.Surface((64, 64))
        image.fill(pg.Color('red'))
        return image
    if colorkey == None:
        image.convert()
    else:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
        image.convert_alpha()
    return image



class Object(pg.sprite.Sprite):
    #all_sprites = None
    hard_blocks = None

    def __init__(self, pos, img=os.path.join(textures, 'none.png'), is_hard=False):
        super().__init__(Object.all_sprites)
        if is_hard:
            self.add(self.hard_blocks)
        self.image = load_image(os.path.join(textures, img))
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(*pos)

    def update(self, *args):
        pass


class Entity(Object):
	# Не уверен, что нужно делать all sprites для Entity, он же добавляется в all sprites у object
	# Поэтому пока что закоменчу эту группу
    # all_sprites = None
    entities = None
    def __init__(self, pos, hp, max_hp, damage, speed=ST_SPEED,
    	img=os.path.join(textures, 'none.png')):
        super().__init__(pos, img)
        # super(Object, self).__init__(Entity.entities)
        self.pos = pos
        self.max_hp = max_hp
        self.hp = hp
        self.speed = speed
        self.damage = damage
        # self.add(Entity.all_sprites)
        self.add(Entity.entities)

    def get_hit(self, damage):
        self.hp -= damage
        if self.hp == 0:
            self.death()

    def death(self):
        self.kill()

    def hit(self, other):
        other.get_hit(self.damage)

    # проверку можно ли походить на новые координаты я думаю лучше сделать в
    # игре когда она будет вызывать move, чтобы не передавать сюда level
    def move(self, x, y):
        new_pos = self.pos[0] + x, self.pos[1] + y
        if new_pos[0] != self.pos[0] and new_pos[1] != self.pos[1] or max(abs(new_pos[0] - self.pos[0]),
        	abs(new_pos[1] - self.pos[1])) > self.speed:
        	return False
        else:
        	self.pos = new_pos
        self.rect.topleft = self.pos


class Player(Entity):
    player_group = None
    def __init__(self, pos, hp, max_hp, damage, speed=ST_SPEED, img='player.bmp'):
        super().__init__(pos, hp, max_hp, damage, speed, img)

    def update(self):
        keys = pg.key.get_pressed()
        left = keys[K_a] or keys[K_LEFT]
        right = keys[K_d] or keys[K_RIGHT]
        up = keys[K_w] or keys[K_UP]
        down = keys[K_s] or keys[K_DOWN]

        if left == right:
            speed_x = 0
        elif left:
            speed_x = -self.speed
        else:
            speed_x = self.speed
        self.rect.x += speed_x
        if pg.sprite.spritecollideany(self, Object.hard_blocks):
            self.rect.x -= speed_x
        if up == down:
            speed_y = 0
        elif up:
            speed_y = -self.speed
        else:
            speed_y = self.speed
        self.rect.y += speed_y
        if pg.sprite.spritecollideany(self, Object.hard_blocks):
            self.rect.y -= speed_y


class Level:
    def __init__(self):
        generator = Generator(TILES)
        self.level, starting_point = generator.level, generator.starting_point
        self.width, self.height = generator.width, generator.height
        self.load_map()

    def load_map(self):
        global player
        for y, line in enumerate(self.level):
            for x, symbol in enumerate(line):
                if symbol in TILES.keys():
                    if symbol == '@':
                        player_pos = x * TILE_SIZE, y * TILE_SIZE
                    if symbol == ' ':
                        continue

                    Object((x * TILE_SIZE, y * TILE_SIZE), TILES[symbol], symbol in HARD_TILES)
        player = Player(player_pos, 100, 100, 1)


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WIN_SIZE.size)
        self.clock = pg.time.Clock()
        self.menu_running = True
        self.game_running = False
        # self.camera = Camera()
        self.all_sprites = pg.sprite.Group()
        self.hard_blocks = pg.sprite.Group()
        self.player = pg.sprite.Group()
        self.objects = pg.sprite.Group()
        self.entities = pg.sprite.Group()
        self.player_group = pg.sprite.Group()
        Object.all_sprites = self.all_sprites
        Object.hard_blocks = self.hard_blocks
        Entity.entities = self.entities
        Player.player_group = self.player_group
        # Player.player = self.player
        # когда появится класс предметов добавить в группу

    def menu_run(self):
        self.button = load_image(os.path.join(textures, 'Start1.png'))
        self.buttonrect = self.button.get_rect()
        self.buttonrect.center = (WIN_SIZE.w // 2, WIN_SIZE.h // 2)
        while self.menu_running:
            self.menu_events()
            self.menu_update()
            self.menu_render()

    def menu_events(self):
        for event in pg.event.get():
            if event.type == QUIT:
                self.menu_running = False
            if event.type == KEYUP:
                if event.key == K_ESCAPE:
                    self.menu_running = False
            if event.type == MOUSEBUTTONUP:
                if self.buttonrect.collidepoint(event.pos):
                    self.game_run()

    def menu_update(self):
        self.clock.tick(FPS)

    def menu_render(self):
        self.screen.fill('black')
        self.screen.blit(self.button, self.buttonrect)
        pg.display.update()

    def game_run(self):
        self.all_sprites.empty()
        self.game_running = True
        self.level = Level()
        while self.game_running:
            self.game_events()
            self.game_update()
            self.game_render()

    def game_events(self):
        for event in pg.event.get():
            if event.type == QUIT:
                self.game_running = False
                self.menu_running = False
            if event.type == KEYUP:
                if event.key == K_ESCAPE:
                    self.game_running = False
                if event.key in [K_w, K_s, K_a, K_d]:
                    pass
            #if event.type == KEYDOWN:
            #    if event.key == K_UP:
            #        player.move(0, -player.speed)
            #    elif event.key == K_DOWN:
            #        player.move(0, player.speed)
            #    elif event.key == K_RIGHT:
            #        player.move(player.speed, 0)
            #    elif event.key == K_LEFT:
            #        player.move(-player.speed, 0)


    def game_update(self):
        player.update()

    def game_render(self):
        self.screen.fill((0, 0, 0))
        self.all_sprites.draw(self.screen)
        self.player_group.draw(self.screen)
        pg.display.update()


if __name__ == '__main__':
    Game().menu_run()
