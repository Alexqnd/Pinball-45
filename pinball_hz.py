import pygame
from pygame.constants import (QUIT, K_ESCAPE, KEYDOWN, K_UP, K_RIGHT, K_DOWN, K_LEFT, K_w, K_d, K_s, K_a, K_r, K_t, K_g, K_SPACE)
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
        self.preserved_energy = 0.9

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
    def reflect(self, ball) -> None:
        ball.sprite.direction[0] = ball.sprite.direction[0] * self.preserved_energy
        ball.sprite.direction[1] = ball.sprite.direction[1] * self.preserved_energy

    @abstractmethod
    def ball_out_wall(self, ball) -> None:
        pass


#Vertical Wall
class WallV(Wall):
    def __init__(self, pos_x, pos_y, size) -> None:
        super().__init__(pos_x, pos_y, size)
        self.rect_from_image(0)

    def reflect(self, ball) -> None:
        super(WallV, self).reflect(ball)
        self.ball_out_wall(ball)
        ball.sprite.direction = ball.sprite.direction.reflect(pygame.Vector2(1, 0))

    def ball_out_wall(self, ball) -> None:
        if ball.sprite.direction[0] < 0:
            ball.sprite.rect.left = self.rect.right + 1
        else:
            ball.sprite.rect.right = self.rect.left - 1


#Horizontal Wall
class WallH(Wall):
    def __init__(self, pos_x, pos_y, size) -> None:
        super().__init__(pos_x, pos_y, size)
        self.rect_from_image(90)

    def reflect(self, ball) -> None:
        super(WallH, self).reflect(ball)
        self.ball_out_wall(ball)
        ball.sprite.direction = ball.sprite.direction.reflect(pygame.Vector2(0, 1))

    def ball_out_wall(self, ball) -> None:
        if ball.sprite.direction[1] < 0:
            ball.sprite.rect.top = self.rect.bottom + 1
        else:
            ball.sprite.rect.bottom = self.rect.top - 1


#Diagonal Wall top to bottom
class WallDTB(Wall):
    def __init__(self, pos_x, pos_y, size) -> None:    
        super().__init__(pos_x, pos_y, size)
        self.rect_from_image(45)

    def reflect(self, ball) -> None:
        super(WallDTB, self).reflect(ball)
        ball.sprite.direction = ball.sprite.direction.reflect(pygame.Vector2(-1, 1))
        self.ball_out_wall(ball)

    def ball_out_wall(self, ball) -> None:
        y = (ball.sprite.rect.centery - self.rect.centery) - (ball.sprite.rect.centerx - self.rect.centerx)
        ball.sprite.rect.centery += y


#Diagonal Wall bottom to top
class WallDBT(Wall):
    def __init__(self, pos_x, pos_y, size) -> None:    
        super().__init__(pos_x, pos_y, size)
        self.rect_from_image(315)

    def reflect(self, ball) -> None:
        super(WallDBT, self).reflect(ball)
        ball.sprite.direction = ball.sprite.direction.reflect(pygame.Vector2(-1, -1))
        self.ball_out_wall(ball)

    def ball_out_wall(self, ball) -> None:
        y = (ball.sprite.rect.centery - self.rect.centery) + (ball.sprite.rect.centerx - self.rect.centerx)
        ball.sprite.rect.centery += y

    def generate_rect(self) -> None:
        self.rect = self.image.get_rect()
        self.rect.topright = (self.pos_x, self.pos_y)

    def transform_image(self, angle) -> None:
        self.image_template = pygame.transform.scale(self.image, (self.width, self.size)).convert_alpha()
        self.image = pygame.transform.rotate(self.image_template, angle)


#Returns if a certain time has passed
class Timer(object):
    def __init__(self, duration, with_start = True) -> None:
        self.duration = duration
        if with_start:
            self.next = pygame.time.get_ticks()
        else:
            self.next = pygame.time.get_ticks() + self.duration

    def is_next_stop_reached(self):
        if pygame.time.get_ticks() > self.next:
            self.next = pygame.time.get_ticks() + self.duration
            return True
        return False

    def change_duration(self, delta=10) -> None:
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


#Launcher which will later charge when pressing space. Right now it launches with 100%
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
        self.grit = 1
        self.generate_rect()

    #increase grit for finetunin the DebugLauncher
    def increase_grit(self) -> None:
        self.grit += 1
        print(self.grit, "grit")

    def decrease_grit(self) -> None:
        if self.grit > 1:
            self.grit -= 1
        print(self.grit, "grit")

    def launch_ball(self) -> None:
        super().launch_ball()
        self.position_ball_launch()
    
    def rotate_left(self) -> None:
        self.angle += 22.5 / self.grit
        if self.angle >= 360:
            self.angle -= 360
        self.image = pygame.transform.rotate(self.image_template, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
    
    def rotate_right(self) -> None:
        self.angle -= 22.5 / self.grit
        if self.angle < 0:
            self.angle += 360
        self.image = pygame.transform.rotate(self.image_template, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def increase_force(self) -> None:
        self.force += 50 / self.grit
    
    def decrease_force(self) -> None:
        self.force -= 50 / self.grit

    def move_up(self) -> None:
        self.pos_y -= 20 / self.grit
        self.rect.center = (self.pos_x, self.pos_y)

    def move_right(self) -> None:
        self.pos_x += 20 / self.grit
        self.rect.center = (self.pos_x, self.pos_y)

    def move_down(self) -> None:
        self.pos_y += 20 / self.grit
        self.rect.center = (self.pos_x, self.pos_y)

    def move_left(self) -> None:
        self.pos_x -= 20 / self.grit
        self.rect.center = (self.pos_x, self.pos_y)

class Background(object):
    def __init__(self) -> None:
        super().__init__()
        self.image = pygame.image.load(os.path.join(Settings.imagepath("table.png")))
        self.image = pygame.transform.scale(self.image, (Settings.dim())).convert()
    
    def draw(self, screen) -> None:
        screen.blit(self.image, (0, 0))


class Table(object):
    def __init__(self) -> None:
        self.width = 500
        self.height = 700
        self.margin_t = 100
        self.margin_lr = 150
        self.t_guide = self.margin_t
        self.r_guide = self.width + self.margin_lr
        self.b_guide = self.height + self.margin_t
        self.l_guide = self.margin_lr
        self.objects()

    def objects(self) -> None:
        self.walls = pygame.sprite.Group()
        self.launchlane()
        self.exitlanes()
        self.borders()
        self.ball = pygame.sprite.GroupSingle(Ball())
        self.chargedlauncher = pygame.sprite.GroupSingle(ChargedLauncher(self.ball, self.r_guide - 18, self.b_guide - 140, 2000))
        self.chargedlauncher.sprite.place_ball()
        self.debuglauncher = pygame.sprite.GroupSingle(DebugLauncher(self.ball, 440, 120, 600, 0))
        
    def launchlane(self) -> None:
        self.walls.add(WallV(self.r_guide - 40, self.t_guide + 40, self.height - 140))
        self.walls.add(WallDTB(self.r_guide - 25, self.t_guide, 38))

    def exitlanes(self) -> None:
        self.walls.add(WallDTB(self.l_guide + 40, self.b_guide - 198, self.width / 3))
        self.walls.add(WallDBT(self.r_guide - 76, self.b_guide - 197, self.width / 3))

    def borders(self) -> None:
        self.walls.add(WallH(self.l_guide, self.t_guide, self.width))
        self.walls.add(WallV(self.l_guide, self.t_guide, self.height))
        self.walls.add(WallV(self.r_guide, self.t_guide, self.height))
        self.walls.add(WallDTB(self.l_guide, self.b_guide - 179, self.width / 2))
        self.walls.add(WallDBT(self.r_guide - 36, self.b_guide - 177, self.width / 2))

    def collision(self) -> None:
        collide = pygame.sprite.groupcollide(self.walls, self.ball, False, False, pygame.sprite.collide_mask)
        if pygame.sprite.groupcollide(self.chargedlauncher, self.ball, False, False, pygame.sprite.collide_mask):
            self.chargedlauncher.sprite.hold_ball()
        for wall in collide:
            wall.reflect(self.ball)

    def watch_for_events(self, event) -> None:
        if event.key == K_SPACE:
            self.chargedlauncher.sprite.launch_ball()
            
        #Controls the DebugLauncher
        elif event.key == K_t:
            self.debuglauncher.sprite.increase_grit()
        elif event.key == K_g:
            self.debuglauncher.sprite.decrease_grit()           
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

    def update(self) -> None:
        self.ball.update()
        self.collision()

    def draw(self, screen) -> None:
        self.debuglauncher.draw(screen)
        self.ball.draw(screen)
        self.chargedlauncher.draw(screen)
        self.walls.draw(screen)


#main class    
class Game(object):
    def __init__(self) -> None:
        super().__init__()
        os.environ['SDL_VIDEO_WINDOW_POS'] = "10, 50"
        pygame.init()
        self.screen = pygame.display.set_mode(Settings.dim())
        pygame.display.set_caption(Settings.title)
        self.clock = pygame.time.Clock()
        self.background = Background()
        self.table = Table()
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
                else:
                    self.table.watch_for_events(event)

    def update(self) -> None:
        self.table.update()
    
    def draw(self) -> None:
        self.background.draw(self.screen)
        self.table.draw(self.screen)
        pygame.display.flip()


if __name__ == '__main__':
    game = Game()
    game.run()
