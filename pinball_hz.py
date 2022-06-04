import pygame
from pygame.constants import (QUIT, K_ESCAPE, KEYDOWN, KEYUP, K_UP, K_RIGHT, K_DOWN, K_LEFT, K_a, K_d, K_r, K_t, K_h, K_g, K_f, K_u, K_i, K_k, K_SPACE)
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
    gameover = False

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
        self.image_template = pygame.image.load(Settings.imagepath("wall.png")).convert_alpha()

    def rect_from_image(self, angle) -> None:
        self.transform_image(angle)
        self.generate_rect()

    def transform_image(self, angle) -> None:
        self.image = pygame.transform.scale(self.image_template, (self.width, self.size)).convert_alpha()
        self.image = pygame.transform.rotate(self.image, angle)

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
        self.image = pygame.transform.scale(self.image_template, (self.width, self.size)).convert_alpha()
        self.image = pygame.transform.rotate(self.image, angle)


class Flipper(pygame.sprite.Sprite, ABC):
    def __init__(self, pos_x, pos_y, width, height, ball) -> None:
        super().__init__()
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height
        self.ball = ball
        self.image_template = pygame.image.load(Settings.imagepath("flipper.png")).convert_alpha()
        self.image = self.image_template

    def generate_rect(self) -> None:
        self.rect = self.image.get_rect()
        self.rect.left = self.pos_x
        self.rect.centery = self.pos_y
        self.mask = pygame.mask.from_surface(self.image)

    def flip_image(self, on_x, on_y) -> None:
        self.image = pygame.transform.flip(self.image_template, on_x, on_y)
        self.scale_image()

    def scale_image(self) -> None:
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    @abstractmethod
    def move(self) -> None:
        pass

    @abstractmethod
    def move_back(self) -> None:
        pass

    @abstractmethod
    def move_ball_upward(self):
        pass


class LeftFlipper(Flipper):
    def __init__(self, pos_x, pos_y, width, height, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, ball)
        self.scale_image()
        self.generate_rect()
   
    def move(self) -> None:
        self.flip_image(False, True)

    def move_back(self) -> None:
        self.flip_image(False, False)

    def move_ball_upward(self) -> None:
        self.ball.sprite.direction[1] = -3000
    

class RightFlipper(Flipper):
    def __init__(self, pos_x, pos_y, width, height, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, ball)
        self.flip_image(True, False)   
        self.generate_rect()
        
    def move(self) -> None:
        self.flip_image(True, True)

    def move_back(self) -> None:
        self.flip_image(True, False)

    def move_ball_upward(self) -> None:
        self.ball.sprite.direction[1] = -3000



class RailDTB(WallDTB):
    def __init__(self, x, y, size) -> None:
        super().__init__(x, y, size)
        self.width = 1
        self.rect_from_image(45)
    
    def connect_ball(self, ball) -> None:
        y = (ball.sprite.rect.centery - self.rect.centery) - (ball.sprite.rect.centerx - self.rect.centerx)
        ball.sprite.rect.centerx += y


class RailDBT(WallDBT):
    def __init__(self, x, y, size) -> None:
        super().__init__(x, y, size)
        self.width = 1
        self.rect_from_image(315)

    def connect_ball(self, ball) -> None:
        y = (ball.sprite.rect.centery - self.rect.centery) + (ball.sprite.rect.centerx - self.rect.centerx)
        ball.sprite.rect.centerx -= y


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
        self.charging = False
        self.charge_speed = 1000
        self.force = 0
        self.holding = False
        self.ball_number = 0
        self.display = Display(self.pos_x, self.pos_y - 100, self.ball_number)

    def update(self) -> None:
        if self.charging and self.force <= 3000:
            self.force += self.charge_speed * Settings.deltatime

    def reset(self) -> None:
        self.ball_number = 0
        self.place_ball()

    def place_ball(self) -> None:
        if self.ball_number < 3:
            self.ball_number += 1 
            self.display.update(self.ball_number)
            self.ball.sprite.rect.center = (self.pos_x, self.pos_y - 300)
        else:
            Settings.gameover = True
            self.display.update("G")

    def hold_ball(self) -> None:
        self.ball.sprite.direction[1] = 0
        self.ball.sprite.rect.centerx = self.pos_x
        self.ball.sprite.rect.bottom = self.pos_y

    def charge(self) -> None:
        self.charging = True

    def launch_ball(self) -> None:
        if self.holding:
            super().launch_ball()
            self.position_ball_launch()
        self.charging = False
        self.force = 0

    def position_ball_launch(self) -> None:
        self.ball.sprite.rect.bottom = self.rect.top - 1
        self.ball.sprite.rect.centerx = self.pos_x

    def draw(self, screen) -> None:
        screen.blit(self.image, self.rect)
        self.display.draw(screen)
        
        
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


#Displaying Text
class Display(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, text) -> None:
        super().__init__()
        self.fontsize = 24
        self.fontfamily = pygame.font.get_default_font()
        self.fontcolor = [255, 255, 255]
        self.font = pygame.font.Font(self.fontfamily, self.fontsize)
        self.render_text(text)
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.generate_rect()

    def render_text(self, text) -> None:
        if not isinstance(text, str):
            text = str(text)
        self.rendered_text = self.font.render(text, True, self.fontcolor)

    def generate_rect(self) -> None:
        self.rect = self.rendered_text.get_rect()
        self.rect.centerx = self.pos_x
        self.rect.centery = self.pos_y

    def update(self, text) -> None:
        self.render_text(text)

    def draw(self, screen) -> None:
        screen.blit(self.rendered_text, self.rect)


class Score(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y) -> None:
        self.points = 0
        self.scoredisplay = Display(pos_x, pos_y, self.points)

    def add_points(self, points) -> None:
        self.points += points
        self.scoredisplay.update(self.points)

    def reset(self) -> None:
        self.points = 0
        self.scoredisplay.update(self.points)

    def draw(self, screen) -> None:
        self.scoredisplay.draw(screen)


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
        self.cx_guide = self.margin_lr + self.width / 2
        self.objects()

    def restart(self) -> None:
        Settings.gameover = False
        self.score.reset()
        self.chargedlauncher.sprite.reset()

    def objects(self) -> None:
        self.ball = pygame.sprite.GroupSingle(Ball())
        self.chargedlauncher = pygame.sprite.GroupSingle(ChargedLauncher(self.ball, self.r_guide - 17, self.b_guide - 140, 2000))
        self.chargedlauncher.sprite.place_ball()
        self.walls = pygame.sprite.Group()
        self.flipperpair = pygame.sprite.Group()
        self.rails = pygame.sprite.Group()
        self.launchlane()
        self.exitlanes()
        self.borders()
        self.flippers()
        self.debuglauncher = pygame.sprite.GroupSingle(DebugLauncher(self.ball, 440, 120, 600, 0))
        self.score = Score(self.cx_guide, self.t_guide * 2)

    def launchlane(self) -> None:
        self.walls.add(WallV(self.r_guide - 40, self.t_guide + 40, self.height - 140))
        self.walls.add(WallDTB(self.r_guide - 13, self.t_guide, 20))

    def exitlanes(self) -> None:
        self.walls.add(WallDTB(self.l_guide + 40, self.b_guide - 198, 70))
        self.walls.add(WallDBT(self.r_guide - 76, self.b_guide - 197, 70))

    def borders(self) -> None:
        self.walls.add(WallH(self.l_guide, self.t_guide, self.width))
        self.walls.add(WallV(self.l_guide, self.t_guide, self.height))
        self.walls.add(WallV(self.r_guide, self.t_guide, self.height))
        self.walls.add(WallDTB(self.l_guide, self.b_guide - 179, 100))
        self.walls.add(WallDBT(self.r_guide - 36, self.b_guide - 177, 100))
        self.rails.add(RailDTB(self.l_guide + 34, self.b_guide - 172, self.width / 2))
        self.rails.add(RailDBT(self.r_guide - 70, self.b_guide - 172, self.width / 2))

    def flippers(self) -> None:
        self.flipperlist = []
        self.flipperlist.append(LeftFlipper(self.l_guide + 90, self.b_guide - 148, 100, 100, self.ball))
        self.flipperlist.append(RightFlipper(self.r_guide - 226, self.b_guide - 147, 100, 100, self.ball))
        self.flipperpair.add(self.flipperlist[0])
        self.flipperpair.add(self.flipperlist[1])


    def collision(self) -> None:
        collide = pygame.sprite.groupcollide(self.walls, self.ball, False, False, pygame.sprite.collide_mask)
        if pygame.sprite.groupcollide(self.chargedlauncher, self.ball, False, False, pygame.sprite.collide_mask):
            self.chargedlauncher.sprite.hold_ball()
            self.chargedlauncher.sprite.holding = True
        else:
            self.chargedlauncher.sprite.holding = False
        for wall in collide:
            wall.reflect(self.ball)
        collide = pygame.sprite.groupcollide(self.rails, self.ball, False, False, pygame.sprite.collide_mask)
        for rail in collide:
            rail.connect_ball(self.ball)

    def out_of_table(self):
        if self.ball.sprite.rect.top > self.b_guide:
            self.score.add_points(10000)
            self.chargedlauncher.sprite.place_ball()

    def watch_for_events(self, event) -> None:
        if event.type == KEYDOWN:
            if event.key == K_a:
                collide = pygame.sprite.groupcollide(self.flipperpair, self.ball, False, False, pygame.sprite.collide_mask)
                for flipper in collide:
                    flipper.move_ball_upward()
                self.flipperlist[0].move()
            elif event.key == K_d:
                collide = pygame.sprite.groupcollide(self.flipperpair, self.ball, False, False, pygame.sprite.collide_mask)
                for flipper in collide:
                    flipper.move_ball_upward()
                self.flipperlist[1].move()
            elif event.key == K_SPACE:
                self.chargedlauncher.sprite.charge()
            elif event.key == K_r:
                self.restart()
                
            #Controls the DebugLauncher
            elif event.key == K_i:
                self.debuglauncher.sprite.increase_grit()
            elif event.key == K_k:
                self.debuglauncher.sprite.decrease_grit()           
            elif event.key == K_LEFT:
                self.debuglauncher.sprite.rotate_left()
            elif event.key == K_RIGHT:
                self.debuglauncher.sprite.rotate_right()
            elif event.key == K_UP:
                self.debuglauncher.sprite.increase_force()
            elif event.key == K_DOWN:
                self.debuglauncher.sprite.decrease_force()
            elif event.key == K_t:
                self.debuglauncher.sprite.move_up()
            elif event.key == K_h:
                self.debuglauncher.sprite.move_right()
            elif event.key == K_g:
                self.debuglauncher.sprite.move_down()
            elif event.key == K_f:
                self.debuglauncher.sprite.move_left()
            elif event.key == K_u:
                self.debuglauncher.sprite.launch_ball()
        
        elif event.type == KEYUP:
            if event.key == K_a:
                self.flipperlist[0].move_back()
            elif event.key == K_d:
                self.flipperlist[1].move_back()
            elif event.key == K_SPACE:
                self.chargedlauncher.sprite.launch_ball()

    def update(self) -> None:
        self.ball.update()
        self.chargedlauncher.update()
        self.collision()
        self.out_of_table()

    def draw(self, screen) -> None:
        self.debuglauncher.draw(screen)
        self.chargedlauncher.sprite.draw(screen)
        self.walls.draw(screen)
        self.flipperpair.draw(screen)
        self.rails.draw(screen)
        self.score.draw(screen)
        self.ball.draw(screen)


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
            if not Settings.gameover: 
                self.update()
            self.draw()
        pygame.quit()

    def watch_for_events(self) -> None:
        for event in pygame.event.get():
            self.table.watch_for_events(event)
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
              

    def update(self) -> None:
        self.table.update()
    
    def draw(self) -> None:
        self.background.draw(self.screen)
        self.table.draw(self.screen)
        pygame.display.flip()


if __name__ == '__main__':
    game = Game()
    game.run()
