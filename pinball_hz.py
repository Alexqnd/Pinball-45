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

class Game(object):
    def __init__(self):
        super().__init__()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "10, 50"
        pygame.init()
        self.screen = pygame.display.set_mode(Settings.dim())
        pygame.display.set_caption(Settings.title)
        self.clock = pygame.time.Clock()
        self.running = False

    def run(self) -> None:
        self.running = True
        while self.running:
            self.clock.tick(Settings.fps)
            self.watch_for_events()
            self.draw()
        pygame.quit()

    def watch_for_events(self) -> None:
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
    
    def draw(self) -> None:
        self.screen.fill((30, 30, 70))
        pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()
