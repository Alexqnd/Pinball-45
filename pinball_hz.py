import pygame
from pygame.constants import (QUIT, K_ESCAPE, KEYDOWN, K_UP, K_RIGHT, K_DOWN, K_LEFT, K_w, K_d, K_s, K_a, K_r, K_SPACE)
import os
import math
from abc import ABC, abstractmethod


class Settings(object):
    window = {'width': 800, 'height': 800}
    fps = 120
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
        self.rect.center = (Settings.window['width'] // 2, 50)
        self.pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        self.direction = pygame.Vector2(0, 0)
        self.gravity = 981

    def update(self) -> None:
        self.direction[1] = self.direction[1] + self.gravity * Settings.deltatime
        self.pos[0] = self.direction[0] * Settings.deltatime
        self.pos[1] = self.direction[1] * Settings.deltatime
        self.rect.centerx += round(self.pos[0])
        self.rect.centery += round(self.pos[1])


#Walls of the table to keep the ball inside
class Wall(pygame.sprite.Sprite, ABC):
    def __init__(self, x, y, size) -> None:
        super().__init__()
        self.size = size
        self.width = 5
        self.pos_x = x
        self.pos_y = y

    def rect_from_image(self, angle) -> None:
        self.image = pygame.image.load(Settings.imagepath("wall.png")).convert_alpha()
        self.transform_image(angle)
        self.generate_rect()

    def transform_image(self, angle) -> None:
        self.image_template = pygame.transform.scale(self.image, (self.width, self.size)).convert_alpha()
        self.image = pygame.transform.rotate(self.image_template, angle)

    def generate_rect(self) -> None:
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.pos_x, self.pos_y)

    @abstractmethod
    def reflect(self, ball):
        pass

    @abstractmethod
    def ball_out_wall(self, ball):
        pass

class WallV(Wall):
    def __init__(self, pos_x, pos_y, size) -> None:
        super().__init__(pos_x, pos_y, size)
        self.rect_from_image(0)

    def reflect(self, ball):
        self.ball_out_wall(ball)
        ball.sprite.direction = ball.sprite.direction.reflect(pygame.Vector2(1, 0))

    def ball_out_wall(self, ball):
        if ball.sprite.direction[0] < 0:
            ball.sprite.rect.left = self.rect.right + 1
        else:
            ball.sprite.rect.right = self.rect.left - 1


class WallH(Wall):
    def __init__(self, pos_x, pos_y, size) -> None:
        super().__init__(pos_x, pos_y, size)
        self.rect_from_image(90)

    def reflect(self, ball):
        self.ball_out_wall(ball)
        ball.sprite.direction = ball.sprite.direction.reflect(pygame.Vector2(0, 1))

    def ball_out_wall(self, ball):
        if ball.sprite.direction[1] < 0:
            ball.sprite.rect.top = self.rect.bottom + 1
        else:
            ball.sprite.rect.bottom = self.rect.top - 1


class WallD(Wall, ABC):
    def __init__(self, pos_x, pos_y, size) -> None:    
        super().__init__(pos_x, pos_y, size)

    def ball_out_wall(self, ball):
        for i in range(1, 20):
            ball.sprite.rect.centerx += ball.sprite.direction[0] / 100
            ball.sprite.rect.centery += ball.sprite.direction[1] / 100
            if not pygame.sprite.collide_mask(self, ball.sprite):
                break


#Diagonal Wall top to bottom
class WallDTB(WallD):
    def __init__(self, pos_x, pos_y, size) -> None:    
        super().__init__(pos_x, pos_y, size)
        self.rect_from_image(45)

    def ball_out_wall(self, ball):
        super().ball_out_wall(ball)

    def reflect(self, ball):
        ball.sprite.direction = ball.sprite.direction.reflect(pygame.Vector2(-1, 1))
        self.ball_out_wall(ball)


#Diagonal Wall bottom to top
class WallDBT(WallD):
    def __init__(self, pos_x, pos_y, size) -> None:    
        super().__init__(pos_x, pos_y, size)
        self.rect_from_image(315)

    def ball_out_wall(self, ball):
        super().ball_out_wall(ball)

    def reflect(self, ball):
        ball.sprite.direction = ball.sprite.direction.reflect(pygame.Vector2(-1, -1))
        self.ball_out_wall(ball)


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


#Launches the ball where it is in a given angle with a given force
class Launcher(pygame.sprite.Sprite):
    def __init__(self, ball, pos_x, pos_y, force, angle = 0) -> None:
        super().__init__()
        self.ball = ball
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.angle = angle
        self.force = force
        self.width = 25
        self.height = 25

    def launch_ball(self) -> None:
        self.ball.sprite.direction[0] = - self.force * math.sin(math.radians(self.angle))
        self.ball.sprite.direction[1] = - self.force * math.cos(math.radians(self.angle))

    def position_ball_launch(self) -> None:
        self.ball.sprite.rect.center = (self.pos_x, self.pos_y)

    def generate_rect(self) -> None:
        self.image_template = pygame.transform.scale(self.image, (self.width, self.height)).convert_alpha()
        self.image = pygame.transform.rotate(self.image_template, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos_x, self.pos_y)

class ChargedLauncher(Launcher):
    def __init__(self, ball, pos_x, pos_y, force) -> None:
        super().__init__(ball, pos_x, pos_y, force)
        self.image = pygame.image.load(Settings.imagepath("chargedlauncher.png")).convert_alpha()
        self.generate_rect()
        self.charge = False

    def place_ball(self) -> None:
        self.ball.sprite.rect.center = (self.pos_x, self.pos_y - 100)

    def hold_ball(self) -> None:
        self.ball.sprite.direction[1] = 0
        self.ball.sprite.rect.centerx = self.pos_x
        self.ball.sprite.rect.bottom = self.pos_y

    def launch_ball(self) -> None:
        super().launch_ball()
        self.position_ball_launch()

    def position_ball_launch(self) -> None:
        self.ball.sprite.rect.bottom = self.rect.top - 1
        self.ball.sprite.rect.centerx = self.pos_x
        
        
#For testing the ball-physics. Inherits from Launcher. Ball can be launched again with the r-key
class DebugLauncher(Launcher):
    def __init__(self, ball, pos_x, pos_y, force, angle) -> None:
        super().__init__(ball, pos_x, pos_y, force, angle)
        self.image = pygame.image.load(Settings.imagepath("debuglauncher.png")).convert_alpha()
        self.generate_rect()

    def launch_ball(self) -> None:
        super().launch_ball()
        self.position_ball_launch()
    
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
        self.running = False
        self.place_objects()

    def place_objects(self) -> None:
        self.wall_margin = 100
        self.wallcreation()
        self.chargedlauncher = pygame.sprite.GroupSingle(ChargedLauncher(self.ball, Settings.window["width"] - self.wall_margin - 18, Settings.window["height"] - self.wall_margin - 40, 2000))
        self.chargedlauncher.sprite.place_ball()
        self.debuglauncher = pygame.sprite.GroupSingle(DebugLauncher(self.ball, 440, 120, 600, 0)) 

    def wallcreation(self) -> None:
        self.walls = pygame.sprite.Group()
        self.walls.add(WallV(self.wall_margin, self.wall_margin, Settings.window["height"] - self.wall_margin * 2))
        self.walls.add(WallV(Settings.window["width"] - self.wall_margin, self.wall_margin, Settings.window["height"] - self.wall_margin * 2))
        self.walls.add(WallV(Settings.window["width"] - self.wall_margin - 40, self.wall_margin + 40, Settings.window["height"] - self.wall_margin * 2 - 40))   
        self.walls.add(WallV(Settings.window["width"] - self.wall_margin, self.wall_margin, Settings.window["height"] - self.wall_margin * 2))
        self.walls.add(WallDTB(0, 0, Settings.window["height"] - self.wall_margin * 2))  
        self.walls.add(WallDBT(0, 0, Settings.window["height"] - self.wall_margin * 2))                  
        self.walls.add(WallH(self.wall_margin, self.wall_margin, Settings.window["width"] - self.wall_margin * 2))
        self.walls.add(WallH(self.wall_margin, Settings.window["height"] - self.wall_margin, (Settings.window["width"] - self.wall_margin * 2) / 2 - 25))
        self.walls.add(WallH(self.wall_margin + (Settings.window["width"] - self.wall_margin * 2) / 2 + 25, Settings.window["height"] - self.wall_margin, (Settings.window["width"] - self.wall_margin * 2) / 2 - 25))

    def run(self) -> None:
        self.running = True
        while self.running:
            Settings.deltatime = self.clock.tick(Settings.fps) / 1000
            self.watch_for_events()
            self.update()
            self.collision()
            self.draw()
        pygame.quit()

    def watch_for_events(self) -> None:
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_SPACE:
                    self.chargedlauncher.sprite.launch_ball()
                    
                #Controls the DebugLauncher
                elif event.key == K_LEFT:
                    self.debuglauncher.sprite.rotate_left()
                elif event.key == K_RIGHT:
                    self.debuglauncher.sprite.rotate_right()
                elif event.key == K_UP:
                    self.debuglauncher.sprite.increase_force()
                elif event.key == K_DOWN:
                    self.debuglauncher.sprite.decrease_force()
                elif event.key == K_w:
                    self.debuglauncher.sprite.move_up()
                elif event.key == K_d:
                    self.debuglauncher.sprite.move_right()
                elif event.key == K_s:
                    self.debuglauncher.sprite.move_down()
                elif event.key == K_a:
                    self.debuglauncher.sprite.move_left()
                elif event.key == K_r:
                    self.debuglauncher.sprite.launch_ball()

    def collision(self) -> None:
        collide = pygame.sprite.groupcollide(self.walls, self.ball, False, False, pygame.sprite.collide_mask)
        if pygame.sprite.groupcollide(self.chargedlauncher, self.ball, False, False, pygame.sprite.collide_mask):
            self.chargedlauncher.sprite.hold_ball()
        for wall in collide:
            wall.reflect(self.ball)

    def update(self) -> None:
        self.ball.update()
    
    def draw(self) -> None:
        self.screen.fill((30, 30, 70))
        self.debuglauncher.draw(self.screen)
        self.ball.draw(self.screen)
        self.chargedlauncher.draw(self.screen)
        self.walls.draw(self.screen)
        pygame.display.flip()

if __name__ == '__main__':
    game = Game()
    game.run()
