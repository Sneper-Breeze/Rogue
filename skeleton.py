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
    '.': ['floor1.bmp', 'floor2.bmp', 'floor3.bmp', 'floor4.bmp', 'floor5.bmp'], # Пол
    '#': 'wall.bmp', # Стена
    '@': ['floor1.bmp', 'floor2.bmp', 'floor3.bmp', 'floor4.bmp', 'floor5.bmp'], # Игрок
    '%': ['floor1.bmp', 'floor2.bmp', 'floor3.bmp', 'floor4.bmp', 'floor5.bmp'], # Враг 1
    ':': ['floor1.bmp', 'floor2.bmp', 'floor3.bmp', 'floor4.bmp', 'floor5.bmp'] # Враг 2
}
HARD_TILES = ['#']
ENEMY_HP = 100
ENEMY_DAMAGE = 20


PLAYER_HP = 100
PLAYER_SPEED = 300
ENEMY_SPEED = PLAYER_SPEED * 0.5

BULLET_SPEED = PLAYER_SPEED * 0.5

PLAYER_DAMAGE = 25


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
            # Создаём прозрачную поверхность
            image = pg.Surface((width, height), pg.SRCALPHA)
            rect = pg.Rect((width * col, height * row, width * col + width, height * row + height))
            # Отрисовываем на созданной поверхности кусочек большого изображения
            image.blit(full_image, (0, 0), rect)
            # Добавляем спрайт и его повёрнутую копию в список
            sprites.append((image, pg.transform.flip(image, True, False)))
    return sprites


def load_sounds(beginning, file_type):
    files = filter(lambda file: file.startswith(beginning) and file.endswith(f'.{file_type}'),
                   os.listdir(sounds_folder))
    sounds = list()
    # Пробегаемся по всем файлам с заданным расширением в папке со звуками
    for filename in files:
        sounds.append(pg.mixer.Sound(os.path.join(sounds_folder, filename)))
    return sounds


# отдельный класс иконки, так как это не объект и ему не нужны коллизии
class Icon(pg.sprite.Sprite):
    # icons = None
    def __init__(self, pos=(1, 1), img='None.png'):
        super().__init__(Icon.icons)
        self.img = img
        self.image = load_image(os.path.join(textures, img))
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(*pos)

    def update(self, img):
        # чтобы проще менять изображение
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

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Entity(Object):
    # класс сущности, от него наследуются все двигающиеся объекты
    entities = None
    def __init__(self, pos, hp, max_hp, damage, speed, img=os.path.join(textures, 'none.png')):
        super().__init__(pos, img)
        self.pos = pos
        self.hitted = False
        self.max_hp = max_hp
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.add(Entity.entities)

    def get_hit(self, damage):
        # hitted - чтобы враги не получали два удара за один дэш
        # и получали краткую неуязвимость после получения удара
        if not self.hitted:
            self.hp -= damage
            if self.hp <= 0:
                self.death()
            self.hitted = 1

    def death(self):
        self.kill()

    def hit(self, other):
        other.get_hit(self.damage)

    # метод движения, который мы в итоге не использовали
    #def move(self, x, y):
    #    new_pos = self.pos[0] + x, self.pos[1] + y
    #    if new_pos[0] != self.pos[0] and new_pos[1] != self.pos[1] or \
    #        max(abs(new_pos[0] - self.pos[0]),
    #        abs(new_pos[1] - self.pos[1])) > self.speed:
    #        return False
    #    self.pos = new_pos
    #    self.rect.topleft = self.pos
    #    return True


class Enemy(Entity):
    enemies = None
    def __init__(self, pos, hp=ENEMY_HP, damage=ENEMY_DAMAGE, img='enemy.bmp'):
        super().__init__(pos, hp, hp, damage, ENEMY_SPEED, img)
        # В каждом анимированном классе есть следующие аттрибуты для работы системы анимаций:
        #   images - словарь, в котором хранятся изображения, сгруппированные по действиям:
        #   (бег, idle анимация и т.д)
        #   anim_state - текущая анимация, один из ключей словаря images
        #   anim_index - текущий индекс анимации
        #   direction - текущее направление движения, 0 - вправо, 1 - влево
        #   anim_delay - промежуток времени, через который сменяется текущий кадр анимации
        #   anim_time - переменная, хранящая время после последней смены кадра
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
        # даёт неуязвимость после получения урона на 0.1 секунду(изначально hitted = 1)
        if self.hitted:
            if self.hitted >= 1.1:
                self.hitted = False
            else:
                self.hitted += ms / 1000
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
        for sprite in Object.hard_blocks:
            if sprite.rect.colliderect(view):
                sprites.append(sprite)

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
                target.hit(self)
            else:
                target.get_hit(self.damage)


class Turret(Enemy):
    def __init__(self, pos, hp=ENEMY_HP, damage=ENEMY_DAMAGE, img='turret.png'):
        super().__init__(pos, hp=hp, damage=damage, img=img)
        self.pos = pos
        self.seconds = 0
        # В каждом анимированном классе есть следующие аттрибуты для работы системы анимаций:
        #   images - словарь, в котором хранятся изображения, сгруппированные по действиям:
        #   (бег, idle анимация и т.д)
        #   anim_state - текущая анимация, один из ключей словаря images
        #   anim_index - текущий индекс анимации
        #   direction - текущее направление движения, 0 - вправо, 1 - влево
        #   anim_delay - промежуток времени, через который сменяется текущий кадр анимации
        #   anim_time - переменная, хранящая время после последней смены кадра
        self.images = {
            'idle': load_spritesheet(os.path.join(textures, 'turret_idle.png'), 1, 5)
        }
        self.anim_state = 'idle'
        self.anim_index = 0
        self.direction = 0
        self.anim_delay = 0.2
        self.anim_time = 0

    def update(self, target, ms):
        # print(self.damage)
        # print(self.hp)
        # даёт неуязвимость после получения урона на 0.1 секунду(изначально hitted = 1)
        if self.hitted:
            if self.hitted >= 1.1:
                self.hitted = False
            else:
                self.hitted += ms / 1000
        self.anim_time += ms / 1000
        self.image = self.images[self.anim_state][self.anim_index][self.direction]
        self.rect = self.image.get_rect().move(self.rect.topleft)

        if self.anim_time > self.anim_delay:
            self.anim_time = 0
            self.anim_index = (self.anim_index + 1) % len(self.images[self.anim_state])

        self.seconds += ms
        dist_x = abs(target.rect.centerx - self.rect.centerx)
        dist_y = abs(target.rect.centery - self.rect.centery)
        # если игрок достаточно быстро и прошло больше 4 секунд с последнего выстрела
        # то турель стреляет
        if dist_x <= 500 and dist_y <= 500:
            if self.seconds >= 1000:
                self.seconds = 0
                # print(self.pos, 't')
                Bullet(self.rect.center, target, self.damage * 1.5)
        if self.rect.colliderect(target):
            if target.is_dashing:
                target.hit(self)
            else:
                target.get_hit(self.damage)

    def death(self):
        self.kill()


class Bullet(Object):
    bullets = None
    def __init__(self, pos, target, damage, speed=BULLET_SPEED, img='Bullet.bmp', isboss=False):
        # self.add(Enemy.enemies)
        # print(pos)
        super().__init__(pos, img)
        # если пуля босса, то она меняется в размерах
        if isboss:
            self.image = pg.transform.scale(self.image, (15, 15))
        self.add(Bullet.bullets)
        self.seconds = 0
        self.isboss = isboss
        self.target = target
        self.damage = damage
        self.speed = speed
        # В каждом анимированном классе есть следующие аттрибуты для работы системы анимаций:
        #   images - словарь, в котором хранятся изображения, сгруппированные по действиям:
        #   (бег, idle анимация и т.д)
        #   anim_state - текущая анимация, один из ключей словаря images
        #   anim_index - текущий индекс анимации
        #   direction - текущее направление движения, 0 - вправо, 1 - влево
        #   anim_delay - промежуток времени, через который сменяется текущий кадр анимации
        #   anim_time - переменная, хранящая время после последней смены кадра
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
        else:
            self.rect.centerx = self.rect.centerx - self.speed * math.cos(self.angle) * ms / 1000
            self.rect.centery = self.rect.centery - self.speed * math.sin(self.angle) * ms / 1000
        # пули босса не исчезают после нанесения урона игроку и со временем, проходят сквозь стены
        if self.rect.colliderect(target):
            if not target.is_dashing:
                target.get_hit(self.damage)
                if not self.isboss:
                    self.kill()
            else:
                self.kill()
        if self.seconds >= 4000:
            if not self.isboss:
                self.kill()
        if pg.sprite.spritecollideany(self, Object.hard_blocks):
            if not self.isboss:
                self.kill()


class Boss(Enemy):
    def __init__(self, pos, hp=ENEMY_HP * 4, damage=ENEMY_DAMAGE * 1.2, img='boss.bmp'):
        super().__init__(pos, hp=hp, damage=damage, img=img)
        self.seconds = 0
        self.img = img
        # В каждом анимированном классе есть следующие аттрибуты для работы системы анимаций:
        #   images - словарь, в котором хранятся изображения, сгруппированные по действиям:
        #   (бег, idle анимация и т.д)
        #   anim_state - текущая анимация, один из ключей словаря images
        #   anim_index - текущий индекс анимации
        #   direction - текущее направление движения, 0 - вправо, 1 - влево
        #   anim_delay - промежуток времени, через который сменяется текущий кадр анимации
        #   anim_time - переменная, хранящая время после последней смены кадра
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
        # даёт неуязвимость после получения урона на 0.1 секунду(изначально hitted = 1)
        if self.hitted:
            if self.hitted >= 1.1:
                self.hitted = False
            else:
                self.hitted += ms / 1000

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
                self.get_hit(target.damage)
            else:
                target.get_hit(self.damage)
        dist_x = abs(target.rect.centerx - self.rect.centerx)
        dist_y = abs(target.rect.centery - self.rect.centery)
        # если игрок достаточно быстро и прошло больше 4 секунд с последнего выстрела
        # то босс стреляет
        if dist_x <= 500 and dist_y <= 500:
            if self.seconds >= 4000:
                self.seconds = 0
                Bullet(self.rect.center, target, 25, speed=300, isboss=True)


class Player(Entity):
    def __init__(self, pos, img='player.bmp'):
        super().__init__(pos, PLAYER_HP, PLAYER_HP, PLAYER_DAMAGE, PLAYER_SPEED, img)
        self.killed = False
        self.sounds = {
            'footsteps': load_sounds('footstep', 'ogg'),
            'dash': load_sounds('knifeSlice', 'ogg')
        }
        # В каждом анимированном классе есть следующие аттрибуты для работы системы анимаций:
        #   images - словарь, в котором хранятся изображения, сгруппированные по действиям:
        #   (бег, idle анимация и т.д)
        #   anim_state - текущая анимация, один из ключей словаря images
        #   anim_index - текущий индекс анимации
        #   direction - текущее направление движения, 0 - вправо, 1 - влево
        #   anim_delay - промежуток времени, через который сменяется текущий кадр анимации
        #   anim_time - переменная, хранящая время после последней смены кадра
        self.images = {
            'idle': load_spritesheet(os.path.join(textures, 'player_idle.png'), 1, 5),
            'move': load_spritesheet(os.path.join(textures, 'player_move.png'), 1, 6)
        }
        self.hp_bar = Icon((10, 50), img='hp_bar.bmp')
        self.image = self.images['idle'][0][0]
        self.direction = 0
        self.hitted = 0
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
        # если нразмер хп бара не равен хп игрока, то он меняется
        # сделал так для оптимизации
        if self.hp != self.hp_bar.image.get_size()[0] and self.hp >= 0:
            self.hp_bar.image = pg.transform.scale(self.hp_bar.image, 
                (int(self.hp / self.max_hp * 100), 10))
        # даёт неуязвимость после получения урона на 1.1 секунду(изначально hitted = 1)
        if self.hitted:
            if self.hitted >= 2.1:
                self.hitted = False
            else:
                self.hitted += ms / 1000
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
        if self.is_dashing and self.dash_directions['up'] or up:
            delta_y -= (4 if self.is_dashing else 1)  * self.speed * ms / 1000
        if self.is_dashing and self.dash_directions['down'] or down:
            delta_y += (4 if self.is_dashing else 1) * self.speed * ms / 1000
        
        if delta_x < 0:
            self.direction = 1
        elif delta_x > 0:
            self.direction = 0

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

        view = pg.Rect(x1, self.rect.y, x2 - x1, self.rect.height)
        sprites = []

        # находим твёрдые блоки в области
        # вроде работает. я не знаю как проверить это писец
        for sprite in Object.hard_blocks:
            if sprite.rect.colliderect(view):
                sprites.append(sprite)

        list_of_x = []
        # пересекается ли линии ходьбы с твёрдыми блоками
        for sprite in sprites:
            l1 = Line([view.x, view.y], [view.left, view.bottom])
            rect = sprite.rect
            if Intersection(l1, Line([rect.left, rect.top], [rect.right, rect.top])) or\
               Intersection(l1, Line([rect.left, rect.top], [rect.left, rect.bottom])) or\
               Intersection(l1, Line([rect.left, rect.bottom], [rect.right, rect.bottom])) or\
               Intersection(l1, Line([rect.right, rect.top], [rect.right, rect.bottom])):
                list_of_x.append(rect.x)
        if list_of_x:
            if delta_x < 0:
                self.rect.x = max(list_of_x) + TILE_SIZE
            if delta_x > 0:
                self.rect.right = min(list_of_x)
        else:
            self.rect.x += delta_x

        view = pg.Rect(self.rect.x, y1, self.rect.width, y2-y1)
        sprites = []

        # находим твёрдые блоки в области
        # вроде работает. я не знаю как проверить это писец
        for sprite in Object.hard_blocks:
            if sprite.rect.colliderect(view):
                sprites.append(sprite)

        list_of_y = []
        # пересекается ли линии ходьбы с твёрдыми блоками
        for sprite in sprites:
            l1 = Line([view.x, view.y], [view.left, view.bottom])
            rect = sprite.rect
            if Intersection(l1, Line([rect.left, rect.top], [rect.right, rect.top])) or\
               Intersection(l1, Line([rect.left, rect.top], [rect.left, rect.bottom])) or\
               Intersection(l1, Line([rect.left, rect.bottom], [rect.right, rect.bottom])) or\
               Intersection(l1, Line([rect.right, rect.top], [rect.right, rect.bottom])):
                list_of_y.append(rect.y)
        if list_of_y:
            if delta_y < 0:
                self.rect.y = min(self.rect.y, max(list_of_y) + TILE_SIZE)
            if delta_y > 0:
                self.rect.bottom = max(self.rect.y + self.rect.height, min(list_of_y))
        else:
            self.rect.y += delta_y

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
        # игрок не получает урон если не прошло достаточно времени с последнего получения урона
        if not self.hitted:
            if self.is_dashing:
                pass
            else:
                super().get_hit(damage)
                self.hitted = 1

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
    def __init__(self, k):
        self.k = k
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
                    if symbol == '.' or symbol == ':' or symbol == '%':
                        r = random.choice(TILES[symbol])
                        print(r)
                        Object((x * TILE_SIZE, y * TILE_SIZE), r, symbol in HARD_TILES)
                    else:
                        Object((x * TILE_SIZE, y * TILE_SIZE), TILES[symbol], symbol in HARD_TILES)
        for enemy in enemies_chars:
            if enemy[0] == 'e':
                Enemy(enemy[1], hp=ENEMY_HP * self.k, damage=ENEMY_DAMAGE * self.k)
            else:
                Turret(enemy[1], hp=ENEMY_HP * self.k // 3, damage=ENEMY_DAMAGE * self.k)


class Game:
    def __init__(self):
        pg.init()
        self.init_screen()
        self.clock = pg.time.Clock()
        self.boss_killed_time = False
        self.menu_running, self.game_running = True, False
        self.view = pg.Rect(-5, -5, WIN_SIZE.width + 10, WIN_SIZE.height + 10)
        self.init_groups()
        self.player = None
        self.camera = Camera()
        self.button = None
        self.buttonrect = None
        self.level = None

        self.k = 0

    def init_screen(self):
        self.screen = pg.display.set_mode(WIN_SIZE.size)
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
                    self.screen.fill('black')
                    download = load_image(os.path.join(textures, 'Zagruzka.bmp'))
                    self.screen.blit(download, download.get_rect().move(WIN_SIZE.center))
                    pg.display.flip()
                    self.game_run()

    def menu_update(self):
        # self.clock.tick(FPS)
        pass

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
        # коэффицент сложности к увеличивается на 1 если это первый запуск
        # и на четверть если не первый, передаётся в левел 
        # враги в левеле создаются с увеличиными в к раз статами, босс в гейме тоже
        if self.k == 0:
            self.k += 1
        else:
            self.k += 0.25
        if not self.game_running:
            self.game_running = True
        self.level = Level(self.k)
        if self.player is None:
            self.k = 1
            self.player = Player(self.level.starting_point)
        else:
            self.player.rect.topleft = self.level.starting_point
            if self.player.hp + 30 >= self.player.max_hp:
                self.player.hp = self.player.max_hp
            else:
                self.player.hp += 30
        if self.player.is_dashing:
            self.player.end_dash()
            self.player.dash_time = 1

    def game_run(self):
        self.new_level()
        while self.game_running:
            self.game_render()
            self.game_events()
            self.game_update()
        # если игрок умер, то к становится 1(чтобы сложность была изначальной)
        if not self.player.alive():
            self.k = 1
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
        if self.boss_killed_time >= 1:
            self.boss_killed_time += ms / 1000
        self.player.update(ms)
        for bullet in Bullet.bullets:
            bullet.update(self.player, ms=ms)
        if not self.player.alive():
            self.game_running = False
        self.camera.update(self.player)
        for enemy in Enemy.enemies:
            enemy.update(self.player, ms=ms)

        if not Enemy.enemies:
            if not self.boss:
                # босс создаётся за экраном, его статы увеличиваются на к и больше стандартных
                Boss((-200, -200), hp=ENEMY_HP * self.k * 4, damage=ENEMY_DAMAGE * self.k * 1.2)
            if self.boss or self.boss_killed_time:
                if not self.boss_killed_time:
                    self.boss_killed_time = 1
                elif self.boss_killed_time >= 3:
                    self.boss_killed_time = False
                    self.screen.fill('black')
                    download = load_image(os.path.join(textures, 'Zagruzka.bmp'))
                    self.screen.blit(download, download.get_rect().move(WIN_SIZE.center))
                    pg.display.flip()
                    self.new_level()
                    return
            # если self.boss == true, то босс не создаётся и осуществляется переход на следующий уровень
            self.boss = True

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
