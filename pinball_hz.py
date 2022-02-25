from enum import auto
import pygame
from pygame.constants import (QUIT, K_ESCAPE, KEYDOWN)
import os

class Settings(object):
    window = {'width': 800, 'height': 800}
    fps = 60
    title = "Pinball-Hz"
    path = {}
    path['file'] = os.path.dirname(os.path.abspath(__file__))
    path['image'] = os.path.join(path['file'], "images")

    @staticmethod
    def dim():
        return (Settings.window['width'], Settings.window['height'])

    @staticmethod
    def imagepath(name):
        return os.path.join(Settings.path['image'], name)

class Ball(pygame.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self.width = 25
        self.height = 25
        self.image = pygame.image.load(Settings.imagepath("ball.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height)).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (Settings.window['width'] // 2, self.height // 2)
        self.direction = (0, 0)

    def update(self) -> None:
        self.accelerate()
        self.rect.move_ip(self.direction)

    def accelerate(self) -> None:
        new_direction_x = self.direction[0]
        new_direction_y = self.direction[1]
        self.direction = (new_direction_x, new_direction_y)

class AutoDeploy360(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, angle, force) -> None:
        super().__init__()
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.angle = angle
        self.force = force

    def deploy(self) -> None:
        self.direction_x = 0
        self.direction_y = 1
        return (self.pos_x, self.pos_y, self.direction_x, self.direction_y)

    
class Game(object):
    def __init__(self):
        super().__init__()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "10, 50"
        pygame.init()
        self.screen = pygame.display.set_mode(Settings.dim())
        pygame.display.set_caption(Settings.title)
        self.clock = pygame.time.Clock()
        self.ball = pygame.sprite.GroupSingle(Ball())
        self.autoD = pygame.sprite.GroupSingle(AutoDeploy360(500, 100, 0, 1)) 
        self.running = False

    def run(self) -> None:
        self.running = True
        autoDvalues = self.autoD.sprite.deploy()
        print(self.ball.sprite.direction)
        self.ball.sprite.rect.center = (autoDvalues[0], autoDvalues[1])
        print(self.ball.sprite.rect.center)
        self.ball.sprite.direction = (autoDvalues[2], autoDvalues[3]) 
        while self.running:
            self.clock.tick(Settings.fps)
            self.watch_for_events()
            self.update()
            self.draw()
        pygame.quit()

    def watch_for_events(self) -> None:
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False

    def update(self) -> None:
        self.ball.update()
    
    def draw(self) -> None:
        self.screen.fill((30, 30, 70))
        self.ball.draw(self.screen)
        pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()
