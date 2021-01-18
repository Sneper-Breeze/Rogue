import random
import os
import math
import pygame as pg
from map import Generator

current_dir = os.path.dirname(__file__)
textures = os.path.join(current_dir, 'data')
sounds_folder = os.path.join(textures, 'sounds')
FPS = 60
TILE_SIZE = 32
WIN_SIZE = pg.Rect(0, 0, 1024, 720)
TILES = {
    ' ': 'space.bmp', # Пустота
    '.': 'floor.bmp', # Пол
    '#': 'wall.bmp', # Стена
    '@': 'floor.bmp', # Игрок
    '%': 'floor.bmp', # Враг 1
    ':': 'floor.bmp' # Враг 2
}
HARD_TILES = ['#']
ENEMY_HP = 100
ENEMY_DAMAGE = 1

PLAYER_HP = 100
PLAYER_SPEED = 300
ENEMY_SPEED = PLAYER_SPEED * 0.5

BULLET_SPEED = PLAYER_SPEED * 0.5

PLAYER_DAMAGE = 1


def Line(p1, p2):
    A = (p1[1] - p2[1])
    B = (p2[0] - p1[0])
    C = (p1[0]*p2[1] - p2[0]*p1[1])
    return A, B, -C


def Intersection(L1, L2):
    D  = L1[0] * L2[1] - L1[1] * L2[0]
    if D != 0:
        return True
    else:
        return False


def load_image(img, colorkey=None):
    try:
        image = pg.image.load(img)
    except FileNotFoundError:
        print('Картинка не нашлась')
        image = pg.Surface((32, 32))
        image.fill(pg.Color('red'))
        return image
    if colorkey is None:
        image.convert()
    else:
        image.convert_alpha()
    return image


def load_spritesheet(img, rows, cols, colorkey=-1):
    sprites = list()
    full_image = pg.image.load(img)
    full_image.convert_alpha()
    full_rect = full_image.get_rect()
    width, height = full_rect.w / cols, full_rect.h / rows
    for row in range(rows):
        for col in range(cols):
            image = pg.Surface((width, height), pg.SRCALPHA)
            rect = pg.Rect((width * col, height * row, width * col + width, height * row + height))
            image.blit(full_image, (0, 0), rect)
            sprites.append((image, pg.transform.flip(image, True, False)))
    return sprites


def load_spritesheet(img, rows, cols, colorkey=-1):
    sprites = list()
    full_image = pg.image.load(img)
    full_image.convert_alpha()
    full_rect = full_image.get_rect()
    width, height = full_rect.w / cols, full_rect.h / rows
    for row in range(rows):
        for col in range(cols):
            image = pg.Surface((width, height), pg.SRCALPHA)
            rect = pg.Rect((width * col, height * row, width * col + width, height * row + height))
            image.blit(full_image, (0, 0), rect)
            sprites.append((image, pg.transform.flip(image, True, False)))
    return sprites


def load_sounds(beginning, file_type):
    files = filter(lambda file: file.startswith(beginning) and file.endswith(f'.{file_type}'),
                   os.listdir(sounds_folder))
    sounds = list()
    for filename in files:
        sounds.append(pg.mixer.Sound(os.path.join(sounds_folder, filename)))
    return sounds


class Icon(pg.sprite.Sprite):
    # icons = None
    def __init__(self, pos=(1, 1), img='None.png'):
        super().__init__(Icon.icons)
        self.img = img
        self.image = load_image(os.path.join(textures, img))
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(*pos)

    def update(self, img):
        self.img = img
        self.image = load_image(os.path.join(textures, img))


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
        self.images = None
        self.current_animation = None
        self.time_to_change = 1

    def update(self, target, ms):
        pass


class Entity(Object):
    # Не уверен, что нужно делать all sprites для Entity, он же добавляется в all sprites у object
    # Поэтому пока что закоменчу эту группу
    # all_sprites = None
    entities = None
    def __init__(self, pos, hp, max_hp, damage, speed, img=os.path.join(textures, 'none.png')):
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
        if self.hp <= 0:
            self.death()

    def death(self):
        self.kill()

    def hit(self, other):
        other.get_hit(self.damage)

    # проверку можно ли походить на новые координаты я думаю лучше сделать в
    # игре когда она будет вызывать move, чтобы не передавать сюда level
    def move(self, x, y):
        new_pos = self.pos[0] + x, self.pos[1] + y
        if new_pos[0] != self.pos[0] and new_pos[1] != self.pos[1] or \
            max(abs(new_pos[0] - self.pos[0]),
            abs(new_pos[1] - self.pos[1])) > self.speed:
            return False

        self.pos = new_pos
        self.rect.topleft = self.pos
        return True


class Enemy(Entity):
    enemies = None
    def __init__(self, pos, img='enemy.bmp', hp=ENEMY_HP):
        super().__init__(pos, ENEMY_HP, ENEMY_HP, ENEMY_DAMAGE, ENEMY_SPEED, img)
        self.images = {
            'idle/movement': load_spritesheet(os.path.join(textures, 'slime_idle_movement.png'), 1, 8)
        }
        self.anim_state = 'idle/movement'
        self.anim_time = 0
        self.anim_delay = 0.1
        self.anim_index = 0
        self.direction = 0
        self.add(Enemy.enemies)

    def update(self, target, ms):
        self.anim_time += ms / 1000
        self.image = self.images[self.anim_state][self.anim_index][self.direction]
        self.rect = self.image.get_rect().move(self.rect.topleft)

        if self.anim_time > self.anim_delay:
            self.anim_index = (self.anim_index + 1) % len(self.images[self.anim_state])
            self.anim_time = 0

        delta_x = delta_y = 0
        if target.rect.centerx < self.rect.centerx:
            delta_x -= self.speed * ms / 1000
        elif target.rect.centerx > self.rect.centerx:
            delta_x += self.speed * ms / 1000

        if delta_x > 0:
            self.direction = 0
        elif delta_x < 0:
            self.direction = 1

        if target.rect.centery < self.rect.centery:
            delta_y -= self.speed * ms / 1000
        elif target.rect.centery > self.rect.centery:
            delta_y += self.speed * ms / 1000

        # находим область в которой мы смотрим твёрдые блоки
        # работает исправно
        if delta_x < 0:
            x1 = self.rect.left - abs(delta_x)
            x2 = self.rect.right
        else:
            x1 = self.rect.left 
            x2 = self.rect.right + delta_x
        if delta_y < 0:
            y1 = self.rect.top - abs(delta_y)
            y2 = self.rect.bottom
        else:
            y1 = self.rect.top
            y2 = self.rect.bottom + delta_y
        view = pg.Rect(x1, y1, x2 - x1, y2 - y1)
        sprites = []

        # находим твёрдые блоки в области
        # вроде работает. я не знаю как проверить это писец
        for sprite in Object.hard_blocks:
            if sprite.rect.colliderect(view):
                sprites.append(sprite)

        # пересекается ли линии ходьбы с твёрдыми блоками. я вообще в ах@@э
        for sprite in sprites:
            l1 = Line([x1, y1], [x2, y2])
            rect = sprite.rect
            if Intersection(l1, Line([rect.left, rect.top], [rect.right, rect.top])) or\
               Intersection(l1, Line([rect.left, rect.top], [rect.left, rect.bottom])) or\
               Intersection(l1, Line([rect.left, rect.bottom], [rect.right, rect.bottom])) or\
               Intersection(l1, Line([rect.right, rect.top], [rect.right, rect.bottom])):
                break
        else:
            self.rect.x += delta_x
            self.rect.y += delta_y


        if self.rect.colliderect(target):
            if target.is_dashing:
                self.death()
            else:
                target.death()


class Turret(Enemy):
    def __init__(self, pos, img='turret.png'):
        super().__init__(pos, img)
        self.pos = pos
        self.seconds = 0
        self.images = {
            'idle': load_spritesheet(os.path.join(textures, 'turret_idle.png'), 1, 5)
        }
        self.anim_state = 'idle'
        self.anim_index = 0
        self.direction = 0
        self.anim_delay = 0.2
        self.anim_time = 0

    def update(self, target, ms):
        self.anim_time += ms / 1000
        self.image = self.images[self.anim_state][self.anim_index][self.direction]
        self.rect = self.image.get_rect().move(self.rect.topleft)

        if self.anim_time > self.anim_delay:
            self.anim_time = 0
            self.anim_index = (self.anim_index + 1) % len(self.images[self.anim_state])

        self.seconds += ms
        dist_x = abs(target.rect.centerx - self.rect.centerx)
        dist_y = abs(target.rect.centery - self.rect.centery)
        if dist_x <= 500 and dist_y <= 500:
            if self.seconds >= 1000:
                self.seconds = 0
                # print(self.pos, 't')
                Bullet(self.rect.center, target, self.damage)
        if self.rect.colliderect(target):
            if target.is_dashing:
                self.death()
            else:
                target.kill()

    def death(self):
        self.kill()


class Bullet(Object):
    bullets = None
    def __init__(self, pos, target, damage, speed=BULLET_SPEED, img='Bullet.bmp', isboss=False):
        # self.add(Enemy.enemies)
        # print(pos)
        super().__init__(pos, img)
        if isboss:
            self.image = pg.transform.scale(self.image, (15, 15))
        self.add(Bullet.bullets)
        self.seconds = 0
        self.isboss = isboss
        self.target = target
        self.damage = damage
        self.speed = speed
        self.images = {
            'idle': load_spritesheet(os.path.join(textures, 'bullet.png'), 1, 6)
        }
        self.anim_state = 'idle'
        self.anim_index = 0
        self.direction = 0
        self.anim_delay = 0.7
        self.anim_time = 0
        delta_x = pos[0] - target.rect.centerx
        delta_y = pos[1] - target.rect.centery
        rads = math.atan2(delta_y, delta_x)
        rads %= 2 * math.pi
        self.angle = rads # Угол хранится в радианах, чтобы не переводить его каждый раз

    def update(self, target, ms):
        self.anim_time += ms / 1000
        self.image = self.images[self.anim_state][self.anim_index][self.direction]
        self.rect = self.image.get_rect().move(self.rect.topleft)

        if self.anim_time > self.anim_delay:
            self.anim_time = 0
            self.anim_index = (self.anim_index + 1) % len(self.images[self.anim_state])

        self.seconds += ms
        if self.isboss:
            delta_x = delta_y = 0

            if target.rect.centerx < self.rect.centerx:
                delta_x -= self.speed * ms / 1000
            elif target.rect.centerx > self.rect.centerx:
                delta_x += self.speed * ms / 1000
            self.rect.x += delta_x
    
            if target.rect.centery < self.rect.centery:
                delta_y -= self.speed * ms / 1000
            elif target.rect.centery > self.rect.centery:
                delta_y += self.speed * ms / 1000
            self.rect.y += delta_y
    
        self.rect.centerx = self.rect.centerx - self.speed * math.cos(self.angle) * ms / 1000
        self.rect.centery = self.rect.centery - self.speed * math.sin(self.angle) * ms / 1000
        if self.rect.colliderect(target):
            if not target.is_dashing:
                target.kill()
            self.kill()
        if self.seconds >= 4000:
            if not self.isboss:
                self.kill()
        if pg.sprite.spritecollideany(self, Object.hard_blocks):
            if not self.isboss:
                self.kill()


class Boss(Enemy):
    def __init__(self, pos, img='boss.bmp'):
        super().__init__(pos, img=img, hp=ENEMY_HP * 15)
        self.seconds = 0
        self.img = img
        self.images = {
            'idle': load_spritesheet(os.path.join(textures, 'boss_idle.png'), 1, 8)
        }
        self.anim_state = 'idle'
        self.anim_index = 0
        self.direction = 0
        self.anim_delay = 0.5
        self.anim_time = 0

    def update(self, target, ms):
        self.image = self.images[self.anim_state][self.anim_index][self.direction]
        self.rect = self.image.get_rect().move(self.rect.topleft)

        self.seconds += ms
        self.anim_time += ms

        if self.anim_time > self.anim_delay:
            self.anim_index = (self.anim_index + 1) % len(self.images[self.anim_state][self.anim_index])
            self.anim_time = 0

        delta_x = delta_y = 0

        if target.rect.centerx < self.rect.centerx:
            delta_x -= self.speed * ms / 1000
        elif target.rect.centerx > self.rect.centerx:
            delta_x += self.speed * ms / 1000
        self.rect.x += delta_x

        if target.rect.centery < self.rect.centery:
            delta_y -= self.speed * ms / 1000
        elif target.rect.centery > self.rect.centery:
            delta_y += self.speed * ms / 1000
        self.rect.y += delta_y

        if self.rect.colliderect(target):
            if target.is_dashing:
                self.kill()
            else:
                target.kill()
        dist_x = abs(target.rect.centerx - self.rect.centerx)
        dist_y = abs(target.rect.centery - self.rect.centery)
        if dist_x <= 500 and dist_y <= 500:
            if self.seconds >= 5000:
                self.seconds = 0
                # print(self.pos, 't')
                Bullet(self.rect.center, target, 0.1, speed=200, isboss=True)
        if self.rect.colliderect(target):
            if target.is_dashing:
                self.death()
            else:
                target.kill()


class Player(Entity):
    def __init__(self, pos, img='player.bmp'):
        super().__init__(pos, PLAYER_HP, PLAYER_HP, PLAYER_DAMAGE, PLAYER_SPEED, img)
        self.killed = False
        self.sounds = {
            'footsteps': load_sounds('footstep', 'ogg'),
            'dash': load_sounds('knifeSlice', 'ogg')
        }
        self.images = {
            'idle': load_spritesheet(os.path.join(textures, 'player_idle.png'), 1, 5),
            'move': load_spritesheet(os.path.join(textures, 'player_move.png'), 1, 6)
        }
        self.image = self.images['idle'][0][0]
        self.direction = 0
        self.anim_state = 'idle'
        self.anim_time = 0
        self.anim_index = 0
        self.anim_delay = 0.5
        self.rect = self.image.get_rect().move(self.pos)
        self.is_dashing = False
        self.dash_time = None
        self.dash_icon = Icon(pos=(10, 10), img='dash.bmp')
        self.dash_directions = None

    def update(self, ms):
        self.anim_time += ms / 1000
        self.image = self.images[self.anim_state][self.anim_index][self.direction]
        self.rect = self.image.get_rect().move(self.rect.topleft)

        if self.anim_time > self.anim_delay:
            self.anim_time = 0
            self.anim_index = (self.anim_index + 1) % len(self.images[self.anim_state])

        if self not in Object.all_sprites and not self.killed:
            self.add(Object.all_sprites)

        if self.dash_time is not None:
            self.dash_time += ms / 1000
        if self.dash_time:
            if self.dash_time > 1 and self.dash_icon.img != 'dash.bmp':
                self.dash_icon.update('dash.bmp')

        delta_x, delta_y = 0, 0
        keys = pg.key.get_pressed()
        left = keys[pg.K_a] or keys[pg.K_LEFT]
        right = keys[pg.K_d] or keys[pg.K_RIGHT]
        up = keys[pg.K_w] or keys[pg.K_UP]
        down = keys[pg.K_s] or keys[pg.K_DOWN]

        if self.is_dashing and self.dash_directions['left'] or left:
            delta_x -= (4 if self.is_dashing else 1) * self.speed * ms / 1000
        if self.is_dashing and self.dash_directions['right'] or right:
            delta_x += (4 if self.is_dashing else 1) * self.speed * ms / 1000
        
        if delta_x < 0:
            self.direction = 1
        elif delta_x > 0:
            self.direction = 0


        self.rect.x += delta_x

        sprite = pg.sprite.spritecollideany(self, Object.hard_blocks)
        if sprite:
            if self.is_dashing:
                self.end_dash()

            if delta_x > 0:
                self.rect.right = sprite.rect.left
            elif delta_x < 0:
                self.rect.left = sprite.rect.right

        if self.is_dashing and self.dash_directions['up'] or up:
            delta_y -= (4 if self.is_dashing else 1)  * self.speed * ms / 1000
        if self.is_dashing and self.dash_directions['down'] or down:
            delta_y += (4 if self.is_dashing else 1) * self.speed * ms / 1000
        self.rect.y += delta_y

        sprite = pg.sprite.spritecollideany(self, Object.hard_blocks)
        if sprite:
            if self.is_dashing:
                self.end_dash()

            if delta_y > 0:
                self.rect.bottom = sprite.rect.top
            elif delta_y < 0:
                self.rect.top = sprite.rect.bottom

        if delta_x or delta_y:
            if self.anim_state != 'move':
                self.anim_index = 0
                self.anim_time = 0
                self.anim_delay = 0.1
            self.anim_state = 'move'
            if not pg.mixer.get_busy():
                sound = random.choice(self.sounds['footsteps'])
                sound.play()
        else:
            if self.anim_state != 'idle':
                self.anim_index = 0
                self.anim_time = 0
                self.anim_delay = 0.5
            self.anim_state = 'idle'
            if pg.mixer.get_busy():
                pg.mixer.stop()

        if self.is_dashing and self.dash_time > 0.3:
            self.end_dash()

    def start_dash(self):
        if self.dash_time is not None and self.dash_time < 1:
            return

        random.choice(self.sounds['dash']).play()

        self.is_dashing = True
        self.dash_time = 0
        keys = pg.key.get_pressed()
        left = keys[pg.K_a] or keys[pg.K_LEFT]
        right = keys[pg.K_d] or keys[pg.K_RIGHT]
        up = keys[pg.K_w] or keys[pg.K_UP]
        down = keys[pg.K_s] or keys[pg.K_DOWN]
        self.dash_directions = {
            'left': left,
            'right': right,
            'up': up,
            'down': down
        }

    def end_dash(self):
        self.dash_icon.update('no_dash.bmp')
        self.is_dashing = False
        self.dash_directions = None

    def get_hit(self, damage):
        if self.is_dashing:
            pass
        else:
            super().get_hit(damage)

    def death(self):
        self.killed = True
        self.kill()


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
                    if symbol == ':':
                        enemies_chars.append(('e', (x * TILE_SIZE, y * TILE_SIZE)))
                    if symbol == '%':
                        enemies_chars.append(('t', (x * TILE_SIZE, y * TILE_SIZE)))
                    if symbol == ' ':
                        continue

                    Object((x * TILE_SIZE, y * TILE_SIZE), TILES[symbol], symbol in HARD_TILES)

        for enemy in enemies_chars:
            if enemy[0] == 'e':
                Enemy(enemy[1])
            else:
                Turret(enemy[1])


class Game:
    def __init__(self):
        pg.init()
        self.init_screen()
        self.clock = pg.time.Clock()
        self.menu_running, self.game_running = True, False
        self.init_groups()
        self.player = None
        self.camera = Camera()
        self.button = None
        self.buttonrect = None
        self.level = None

    def init_screen(self):
        self.screen = pg.display.set_mode(WIN_SIZE.size, vsync=True)
        pg.display.set_caption('Rogue')

    def init_groups(self):
        self.players = pg.sprite.Group()
        self.icons = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group()
        self.hard_blocks = pg.sprite.Group()
        self.objects = pg.sprite.Group()
        self.entities = pg.sprite.Group()
        self.bullets = pg.sprite.Group()
        self.enemies = pg.sprite.Group()

        Bullet.bullets = self.bullets
        Object.all_sprites = self.all_sprites
        Object.hard_blocks = self.hard_blocks
        Entity.entities = self.entities
        Enemy.enemies = self.enemies
        Icon.icons = self.icons
        # Player.players = self.players

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
            if event.type == pg.QUIT:
                self.menu_running = False
            if event.type == pg.KEYUP:
                if event.key == pg.K_ESCAPE:
                    self.menu_running = False
            if event.type == pg.MOUSEBUTTONUP:
                if self.buttonrect.collidepoint(event.pos):
                    self.game_run()

    def menu_update(self):
        self.clock.tick(FPS)

    def menu_render(self):
        self.screen.fill('black')
        self.screen.blit(self.button, self.buttonrect)
        pg.display.update()

    def new_level(self):
        self.boss = False
        self.all_sprites.empty()
        self.hard_blocks.empty()
        self.objects.empty()
        self.entities.empty()
        self.enemies.empty()
        self.bullets.empty()
        if not self.game_running:
            self.game_running = True
        self.level = Level()
        if self.player is None:
            self.player = Player(self.level.starting_point)
        else:
            self.player.rect.topleft = self.level.starting_point
        if self.player.is_dashing:
            self.player.end_dash()
            self.player.dash_time = 1

    def game_run(self):
        self.new_level()
        while self.game_running:
            self.game_render()
            self.game_events()
            self.game_update()

        if not self.player.alive():
            self.player = None

    def game_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.game_running = False
                self.menu_running = False
            elif event.type == pg.KEYUP:
                if event.key == pg.K_ESCAPE:
                    self.game_running = False
                    self.player.death()
                elif event.key in [pg.K_w, pg.K_s, pg.K_a, pg.K_d]:
                    pass
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 3:
                    if self.player:
                        self.player.start_dash()

    def game_update(self):
        ms = self.clock.tick(FPS)
        self.player.update(ms)
        for bullet in Bullet.bullets:
            bullet.update(self.player, ms=ms)
        if not self.player.alive():
            self.game_running = False
        self.camera.update(self.player)
        for enemy in Enemy.enemies:
            enemy.update(self.player, ms=ms)

        if not Enemy.enemies:
            Boss((-200, -200))
            if self.boss:
                self.new_level()
                return
            self.boss = True

        # for enemy in self.level.enemies:
        #     if enemy.update(self.player, ms):
        #         self.level.enemies.remove(enemy)

        # обновляем положение всех спрайтов
        for sprite in self.all_sprites:
            self.camera.apply(sprite)

    def game_render(self):
        self.screen.fill((0, 0, 0))
        self.all_sprites.draw(self.screen)
        self.icons.draw(self.screen)
        self.display_fps()
        pg.display.update()

    def display_fps(self):
        font = pg.font.Font(None, 30)
        text = font.render(str(int(self.clock.get_fps())), 1, pg.Color('white'))
        self.screen.blit(text, text.get_rect(topleft=(5, 5)))


if __name__ == '__main__':
    Game().menu_run()
