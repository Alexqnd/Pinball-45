from enum import auto
import pygame
from pygame.constants import (QUIT, K_ESCAPE, KEYDOWN, K_UP, K_RIGHT, K_DOWN, K_LEFT, K_w, K_d, K_s, K_a, K_KP_PLUS, K_KP_MINUS)
import os
import math

class Settings(object):
    window = {'width': 800, 'height': 800}
    fps = 240
    deltatime = 1.0 / fps
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

#Ball on the Pinball-table
class Ball(pygame.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self.width = 25
        self.height = 25
        self.image = pygame.image.load(Settings.imagepath("ball.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height)).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (Settings.window['width'] // 2, self.height // 2)
        self.pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        self.direction = (0, 0)
        self.gravity = 981

    def update(self) -> None:
        self.direction = (self.direction[0], self.direction[1] + self.gravity * Settings.deltatime)
        self.pos[0] = self.direction[0] * Settings.deltatime
        self.pos[1] = self.direction[1] * Settings.deltatime
        self.rect.centerx += round(self.pos[0])
        self.rect.centery += round(self.pos[1])

#Returns if a certain time has passed
class Timer(object):
    def __init__(self, duration, with_start = True):
        self.duration = duration
        if with_start:
            self.next = pygame.time.get_ticks()
        else:
            self.next = pygame.time.get_ticks() + self.duration

    def is_next_stop_reached(self) -> None:
        if pygame.time.get_ticks() > self.next:
            self.next = pygame.time.get_ticks() + self.duration
            return True
        return False

    def change_duration(self, delta=10):
        self.duration += delta
        if self.duration < 0:
            self.duration = 0

#Deployes the ball where it is in a given angle with a given force
class AutoDeploy360(pygame.sprite.Sprite):
    def __init__(self, ball, pos_x, pos_y, angle, force) -> None:
        super().__init__()
        self.ball = ball
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.angle = angle
        self.force = force
        self.width = 25
        self.height = 25
        self.image = pygame.image.load(Settings.imagepath("autodeploy360.png")).convert_alpha()
        self.image_template = pygame.transform.scale(self.image, (self.width, self.height)).convert_alpha()
        self.image = pygame.transform.rotate(self.image_template, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos_x, self.pos_y)

    def deploy(self) -> None:
        direction_x = - self.force * math.sin(math.radians(self.angle))
        direction_y = - self.force * math.cos(math.radians(self.angle))
        self.ball.sprite.direction = (direction_x, direction_y) 
        self.ball.sprite.rect.center = (self.pos_x, self.pos_y)

#Controls the deployer
    def rotate_left(self) -> None:
        self.angle += 22.5
        if self.angle >= 360:
            self.angle -= 360
        self.image = pygame.transform.rotate(self.image_template, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
    
    def rotate_right(self) -> None:
        self.angle -= 22.5
        if self.angle < 0:
            self.angle += 360
        self.image = pygame.transform.rotate(self.image_template, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def increase_force(self) -> None:
        self.force += 50
    
    def decrease_force(self) -> None:
        self.force -= 50

    def move_up(self) -> None:
        self.pos_y -= 20
        self.rect.center = (self.pos_x, self.pos_y)

    def move_right(self) -> None:
        self.pos_x += 20
        self.rect.center = (self.pos_x, self.pos_y)

    def move_down(self) -> None:
        self.pos_y += 20
        self.rect.center = (self.pos_x, self.pos_y)

    def move_left(self) -> None:
        self.pos_x -= 20
        self.rect.center = (self.pos_x, self.pos_y)

#For testing the ball-physics. Inherits from AutoDeploy. It redeploys the ball after a certain time
class ReDeploy360(AutoDeploy360):
    def __init__(self, ball, pos_x, pos_y, angle, force, time) -> None:
        super().__init__(ball, pos_x, pos_y, angle, force)
        self.timer = Timer(time)

    def redeploy(self) -> None:
        if self.timer.is_next_stop_reached():
            self.deploy()

    def increase_time(self) -> None:
        self.timer.duration += 200

    def decrease_time(self) -> None:
        self.timer.duration -= 200
#main class    
class Game(object):
    def __init__(self) -> None:
        super().__init__()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "10, 50"
        pygame.init()
        self.screen = pygame.display.set_mode(Settings.dim())
        pygame.display.set_caption(Settings.title)
        self.clock = pygame.time.Clock()
        self.ball = pygame.sprite.GroupSingle(Ball())
        self.redeploy = pygame.sprite.GroupSingle(ReDeploy360(self.ball, 500, 100, 45, 400, 2000)) 
        self.running = False

    def run(self) -> None:
        self.running = True
        while self.running:
            Settings.deltatime = self.clock.tick(Settings.fps) / 1000
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
                    
                #Controls the deployer
                elif event.key == K_LEFT:
                    self.redeploy.sprite.rotate_left()
                elif event.key == K_RIGHT:
                    self.redeploy.sprite.rotate_right()
                elif event.key == K_UP:
                    self.redeploy.sprite.increase_force()
                elif event.key == K_DOWN:
                    self.redeploy.sprite.decrease_force()
                elif event.key == K_w:
                    self.redeploy.sprite.move_up()
                elif event.key == K_d:
                    self.redeploy.sprite.move_right()
                elif event.key == K_s:
                    self.redeploy.sprite.move_down()
                elif event.key == K_a:
                    self.redeploy.sprite.move_left()
                elif  event.key == K_KP_PLUS:
                    self.redeploy.sprite.increase_time()
                elif  event.key == K_KP_MINUS:
                    self.redeploy.sprite.decrease_time()
                

    def update(self) -> None:
        self.redeploy.sprite.redeploy()
        self.ball.update()
    
    def draw(self) -> None:
        self.screen.fill((30, 30, 70))
        self.redeploy.draw(self.screen)
        self.ball.draw(self.screen)
        pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()
