import os
import pygame as pg
from pygame.locals import *
from map import Generator

current_dir = os.path.dirname(__file__)
textures = os.path.join(current_dir, 'data')
FPS = 60
TILE_SIZE = 32
WIN_SIZE = pg.Rect(0, 0, 1280, 800)

TILES = {
    ' ': 'space.bmp', # Пустота
    '.': 'floor.bmp', # Пол
    '#': 'wall.bmp', # Стена
    '@': 'player.bmp', # Игрок
    '%': 'image_path', # Враг 1
    ':': 'image_path' # Враг 2
}


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
    all_sprites = None
    hard_blocks = None

    def __init__(self, pos, img=os.path.join(textures, 'none.png'), is_hard=False):
        super().__init__(Object.all_sprites)
        self.image = load_image(os.path.join(textures, img))
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(*pos)

    def update(self, *args):
        pass


class Level:
    def __init__(self):
        generator = Generator(TILES)
        self.level, starting_point = generator.level, generator.starting_point
        self.width, self.height = generator.width, generator.height
        print(generator.room_list)
        self.load_map()

    def load_map(self):
        for y, line in enumerate(self.level):
            for x, symbol in enumerate(line):
                if symbol in TILES.keys():
                    if symbol == ' ':
                        continue
                    Object((x * TILE_SIZE, y * TILE_SIZE), TILES[symbol])


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
        Object.all_sprites = self.all_sprites
        Object.hard_blocks = self.hard_blocks
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

    def game_update(self):
        pass

    def game_render(self):
        self.screen.fill((0, 0, 0))
        self.all_sprites.draw(self.screen)
        pg.display.update()


if __name__ == '__main__':
    Game().menu_run()
