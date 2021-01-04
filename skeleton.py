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
    '%': 'floor.bmp', # Враг 1
    ':': 'floor.bmp' # Враг 2
}
HARD_TILES = ['#']
enemieslist = []
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


class Enemy(Entity):
    enemies = None
    global enemieslist
    def __init__(self, pos, hp, max_hp, damage, speed=ST_SPEED, img='enemy.bmp'):
        super().__init__(pos, hp, max_hp, damage, speed, img)
        enemieslist.append(self)
        self.add(Enemy.enemies)

    def update(self, target):
        # print('f')
        #enemieslist.append(self)
        if target.rect.centerx == self.rect.centerx:
            speed_x = 0
        elif target.rect.centerx < self.rect.centerx:
            speed_x = -self.speed
        else:
            speed_x = self.speed
        self.rect.x += speed_x
        if pg.sprite.spritecollideany(self, Object.hard_blocks):
            self.rect.x -= speed_x
        if target.rect.centery == self.rect.centery:
            speed_y = 0
        elif target.rect.centery < self.rect.centery:
            speed_y = -self.speed
        else:
            speed_y = self.speed
        self.rect.y += speed_y
        if pg.sprite.spritecollideany(self, Object.hard_blocks):
            self.rect.y -= speed_y



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


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0
        
    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy
    
    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = -(target.rect.centerx - WIN_SIZE.centerx)
        self.dy = -(target.rect.centery - WIN_SIZE.centery)


class Level:
    def __init__(self):
        self.enemies = []
        self.player = None
        generator = Generator(TILES)
        self.level, starting_point = generator.level, generator.starting_point
        self.width, self.height = generator.width, generator.height
        self.load_map()

    def load_map(self):
        enemies_chars = []
        for y, line in enumerate(self.level):
            for x, symbol in enumerate(line):
                if symbol in TILES.keys():
                    if symbol == '@':
                        player_pos = x * TILE_SIZE, y * TILE_SIZE
                    if symbol == ':' or symbol == '%':
                        enemies_chars.append(((x * TILE_SIZE, y * TILE_SIZE), 100, 100, 1))
                    if symbol == ' ':
                        continue

                    Object((x * TILE_SIZE, y * TILE_SIZE), TILES[symbol], symbol in HARD_TILES)
        for enemy in enemies_chars:
            self.enemies.append(Enemy(*enemy))
        self.player = Player(player_pos, 100, 100, 1)


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
        self.player_group = pg.sprite.Group()
        self.objects = pg.sprite.Group()
        self.entities = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        Object.all_sprites = self.all_sprites
        Object.hard_blocks = self.hard_blocks
        Entity.entities = self.entities
        Enemy.enemies = self.enemies
        self.camera = Camera()
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
        self.hard_blocks.empty()
        self.objects.empty()
        self.player_group.empty()
        self.entities.empty()
        self.game_running = True
        self.level = Level()
        # self.enemy = Enemy((200, 200), 50, 50, 5)
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

    def game_update(self):
        self.level.player.update()
        for enemy in self.level.enemies:
            enemy.update(self.level.player)
        self.camera.update(self.level.player) 
        # обновляем положение всех спрайтов
        for sprite in self.all_sprites:
                self.camera.apply(sprite)

    def game_render(self):
        self.screen.fill((0, 0, 0))
        self.all_sprites.draw(self.screen)
        pg.display.update()


if __name__ == '__main__':
    Game().menu_run()