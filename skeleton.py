import os
import pygame as pg
from pygame.locals import *
from map import Generator
import random

current_dir = os.path.dirname(__file__)
textures = os.path.join(current_dir, 'data')
FPS = 60
TILE_SIZE = 32
WIN_SIZE = pg.Rect(0, 0, 1024, 720)
ST_SPEED = 250
TILES = {
    ' ': 'space.bmp', # Пустота
    '.': 'floor.bmp', # Пол
    '#': 'wall.bmp', # Стена
    '@': 'floor.bmp', # Игрок
    '%': 'floor.bmp', # Враг 1
    ':': 'floor.bmp' # Враг 2
}
HARD_TILES = ['#']


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
    def __init__(self, pos, hp, max_hp, damage, speed=ST_SPEED * 0.75, img='enemy.bmp'):
        super().__init__(pos, hp, max_hp, damage, speed, img)
        self.add(Enemy.enemies)

    def update(self, target, ms):
        delta_x = delta_y = 0

        if target.rect.centerx == self.rect.centerx:
            delta_x = 0
        elif target.rect.centerx < self.rect.centerx:
            delta_x = -self.speed * ms / 1000
        else:
            delta_x = self.speed * ms / 1000
        self.rect.x += delta_x

        object = pg.sprite.spritecollideany(self, Object.hard_blocks)
        if object:
            if delta_x > 0:
                self.rect.right = object.rect.left
            elif delta_x < 0:
                self.rect.left = object.rect.right

        if target.rect.centery == self.rect.centery:
            delta_y = 0
        elif target.rect.centery < self.rect.centery:
            delta_y = -self.speed * ms / 1000
        else:
            delta_y = self.speed * ms / 1000
        self.rect.y += delta_y

        object = pg.sprite.spritecollideany(self, Object.hard_blocks)
        if object:
            if delta_y > 0:
                self.rect.bottom = object.rect.top
            elif delta_y < 0:
                self.rect.top = object.rect.bottom

        if self.rect.colliderect(target):
            self.hit(target)


class Player(Entity):
    player_group = None
    def __init__(self, pos, hp, max_hp, damage, speed=ST_SPEED, img='player.bmp'):
        super().__init__(pos, hp, max_hp, damage, speed, img)
        self.image = pg.transform.scale(self.image, (20, 20))
        self.rect = self.image.get_rect().move(self.pos)
        self.is_dashing = False
        self.dash_start_time = None
        self.dash_directions = None

    def update(self, ms):
        delta_x, delta_y = 0, 0
        if self.is_dashing and self.dash_directions and self.dash_start_time:
            if self.dash_directions['right']:
                delta_x += self.speed * 4 * ms / 1000
            if self.dash_directions['left']:
                delta_x -= self.speed * 4 * ms / 1000

            self.rect.x += delta_x
            object = pg.sprite.spritecollideany(self, Object.hard_blocks)
            if object:
                self.end_dash()
                if delta_x > 0:
                    self.rect.right = object.rect.left
                elif delta_x < 0:
                    self.rect.left = object.rect.right
                return

            if self.dash_directions['up']:
                delta_y -= self.speed * 4 * ms / 1000
            if self.dash_directions['down']:
                delta_y += self.speed * 4 * ms / 1000

            self.rect.y += delta_y
            object = pg.sprite.spritecollideany(self, Object.hard_blocks)
            if object:
                self.end_dash()
                if delta_y > 0:
                    self.rect.bottom = object.rect.top
                elif delta_y < 0:
                    self.rect.top = object.rect.bottom
                return

            if pg.time.get_ticks() - self.dash_start_time > 240:
                self.end_dash()
            return

        keys = pg.key.get_pressed()
        left = keys[K_a] or keys[K_LEFT]
        right = keys[K_d] or keys[K_RIGHT]
        up = keys[K_w] or keys[K_UP]
        down = keys[K_s] or keys[K_DOWN]

        if left:
            delta_x -= self.speed * ms / 1000
        if right:
            delta_x += self.speed * ms / 1000
        self.rect.x += delta_x
        object = pg.sprite.spritecollideany(self, Object.hard_blocks)
        if object:
            if delta_x > 0:
                self.rect.right = object.rect.left
            elif delta_x < 0:
                self.rect.left = object.rect.right

        if up:
            delta_y -= self.speed * ms / 1000
        if down:
            delta_y += self.speed * ms / 1000
        self.rect.y += delta_y
        object = pg.sprite.spritecollideany(self, Object.hard_blocks)
        if object:
            if delta_y > 0:
                self.rect.bottom = object.rect.top
            elif delta_y < 0:
                self.rect.top = object.rect.bottom

    def start_dash(self):
        self.is_dashing = True
        self.dash_start_time = pg.time.get_ticks()
        keys = pg.key.get_pressed()
        left = keys[K_a] or keys[K_LEFT]
        right = keys[K_d] or keys[K_RIGHT]
        up = keys[K_w] or keys[K_UP]
        down = keys[K_s] or keys[K_DOWN]
        self.dash_directions = {
            'left': left,
            'right': right,
            'up': up,
            'down': down
        }

    def end_dash(self):
        self.is_dashing = False
        self.dash_start_time = None
        self.dash_directions = None


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
        self.enemies = list()
        generator = Generator(TILES)
        self.level, self.starting_point = generator.level, generator.starting_point
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


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WIN_SIZE.size, vsync=True)
        self.clock = pg.time.Clock()
        self.menu_running = True
        self.game_running = False
        # self.camera = Camera()
        self.all_sprites = pg.sprite.Group()
        self.hard_blocks = pg.sprite.Group()
        self.objects = pg.sprite.Group()
        self.entities = pg.sprite.Group()
        self.player = None
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
        self.entities.empty()
        self.game_running = True
        self.level = Level()

        if self.player is None:
            self.player = Player(self.level.starting_point, 100, 100, 1)
        else:
            self.player.rect.topleft = self.level.starting_point

        while self.game_running:
            self.game_render()
            self.game_events()
            self.game_update()
        if not self.player.alive():
            self.player = None

    def game_events(self):
        for event in pg.event.get():
            if event.type == QUIT:
                self.game_running = False
                self.menu_running = False
            elif event.type == KEYUP:
                if event.key == K_ESCAPE:
                    self.game_running = False
                    self.player.death()
                elif event.key in [K_w, K_s, K_a, K_d]:
                    pass
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 3:
                    if self.player:
                        self.player.start_dash()

    def game_update(self):

        ms = self.clock.tick(FPS)
        self.player.update(ms)
        if not self.player.alive():
            self.game_running = False
        self.camera.update(self.player)
        for enemy in self.level.enemies:
            enemy.update(self.player, ms)

        # обновляем положение всех спрайтов
        for sprite in self.all_sprites:
            self.camera.apply(sprite)

    def game_render(self):
        self.screen.fill((0, 0, 0))
        self.all_sprites.draw(self.screen)
        self.display_fps()
        pg.display.update()

    def display_fps(self):
        font = pg.font.Font(None, 30)
        text = font.render(str(int(self.clock.get_fps())), 1, pg.Color('white'))
        self.screen.blit(text, text.get_rect(topleft=(5, 5)))


if __name__ == '__main__':
    Game().menu_run()
