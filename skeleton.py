import pygame as pg
from pygame.locals import *
import os


FPS = 60
TILE_SIZE = 64
MAP_SIZE = (11, 11)
WIN_SIZE = pg.Rect(0, 0, MAP_SIZE[0] * TILE_SIZE, 
                         MAP_SIZE[1] * TILE_SIZE)


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
    img = os.path.join(textures, 'none.png')
    def __init__(self, pos):
        super().__init__(Object.all_sprites)
        self.image = load_image(self.img, -1)
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(*pos)

    def update(self, *args):
        pass


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(WIN_SIZE.size)
        self.clock = pg.time.Clock()
        self.menu_running = True
        self.game_running = False
        self.camera = Camera()
        self.all_sprites = pg.sprite.Group()
        self.hard_blocks = pg.sprite.Group()
        self.player = pg.sprite.Group()
        self.objects = pg.sprite.Group()
        Tile.all_sprites = self.all_sprites
        Tile.hard_blocks = self.hard_blocks
        Player.player = self.player
        # когда появится класс предметов добавить в группу

    def menu_run(self):
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
                if event.key == K_SPACE:
                    self.game_run()

    def menu_update(self):
        self.clock.tick(FPS)

    def menu_render(self):
        self.screen.blit(self.menu_bg, (0, 0))
        pg.display.update()

    def game_run(self):
        self.game_running = True
        while self.game_running:
            self.game_events()
            self.game_update()
            self.game_render()

    def game_events(self):
        for event in pg.event.get():
            if event.type == QUIT:
                self.game_running = False
            if event.type == KEYUP:
                if event.key == K_ESCAPE:
                    self.game_running = False
                if event.key in [K_w, K_s, K_a, K_d]:
                    pass

    def game_update(self):
        pass

    def game_render(self):
        self.screen.fill((0, 0, 0))
        pg.display.update()


if __name__ == '__main__':
    Game().menu_run()