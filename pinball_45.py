import pygame
from pygame.constants import (QUIT, K_ESCAPE, KEYDOWN, KEYUP, K_UP, K_RIGHT, K_DOWN, K_LEFT, K_a, K_d, K_r, K_t, K_h, K_g, K_f, K_u, K_i, K_k, K_SPACE)
import os
import math
from abc import ABC, abstractmethod


class Settings(object):
    window = {'width': 800, 'height': 800}
    fps = 120
    deltatime = 1.0 / fps
    title = "Pinball 45"
    path = {}
    path['file'] = os.path.dirname(os.path.abspath(__file__))
    path['image'] = os.path.join(path['file'], "images")
    path['sound'] = os.path.join(path['file'], 'sounds')
    gameover = False

    @staticmethod
    def dim():
        return (Settings.window['width'], Settings.window['height'])

    @staticmethod
    def imagepath(name):
        return os.path.join(Settings.path['image'], name)

    def soundpath(name):
        return os.path.join(Settings.path['sound'], name)


#Displaying Text
class Display(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, text) -> None:
        super().__init__()
        self.pos_x = pos_x
        self.pos_y = pos_y
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
        self.pos_x = pos_x
        self.pos_y = pos_y
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


#Every object on the table
class TableObject(pygame.sprite.Sprite, ABC):
    def __init__(self, pos_x, pos_y, width, height, image_name) -> None:
        super().__init__()
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height
        self.image_name = image_name
        self.sound = []
        self.load_image()
        self.scale_image()
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect_topleft()

    def load_image(self) -> None:
        self.image = pygame.image.load(Settings.imagepath(self.image_name)).convert_alpha()

    def scale_image(self) -> None:
        self.image = pygame.transform.scale(self.image, (self.width, self.height)).convert_alpha()

    def rotate_image(self, angle) -> None:
        self.image_template = self.image
        self.image = pygame.transform.rotate(self.image_template, angle)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect_topleft()

    def flip_image(self, on_x, on_y) -> None:
        self.image = pygame.transform.flip(self.image_template, on_x, on_y)

    def rect_center(self) -> None:
        self.rect.center = (self.pos_x, self.pos_y)

    def rect_topleft(self) -> None:
        self.rect.topleft = (self.pos_x, self.pos_y)

    def rect_topright(self) -> None:
        self.rect.topright = (self.pos_x, self.pos_y)

    def load_sound(self, sound_name):
        return pygame.mixer.Sound((Settings.soundpath(sound_name)))


#Ball on the Pinball-table
class Ball(TableObject):
    def __init__(self, pos_x, pos_y, width, height, image_name) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name)
        self.rect_center()
        self.pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        self.direction = pygame.Vector2(0, 0)
        self.gravity = 281

    def update(self) -> None:
        self.direction[1] = self.direction[1] + self.gravity * Settings.deltatime
        self.pos[0] = self.direction[0] * Settings.deltatime
        self.pos[1] = self.direction[1] * Settings.deltatime
        self.rect.centerx += round(self.pos[0])
        self.rect.centery += round(self.pos[1])


class TableObjectFixed(TableObject, ABC):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name)
        self.ball = ball

    @abstractmethod
    def control_ball(self):
        pass


#Walls of the table to keep the ball inside
class Wall(TableObjectFixed, ABC):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
        self.preserved_energy = 0.9

    @abstractmethod
    def control_ball(self) -> None:
        self.ball.sprite.direction[0] = self.ball.sprite.direction[0] * self.preserved_energy
        self.ball.sprite.direction[1] = self.ball.sprite.direction[1] * self.preserved_energy

    @abstractmethod
    def ball_out_wall(self) -> None:
        pass


#Vertical Wall
class WallV(Wall):
    def __init__(self, pos_x, pos_y, width, size, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, size, image_name, ball)
        self.rotate_image(0)

    def control_ball(self) -> None:
        super(WallV, self).control_ball()
        self.ball_out_wall()
        self.ball.sprite.direction = self.ball.sprite.direction.reflect(pygame.Vector2(1, 0))

    def ball_out_wall(self) -> None:
        if self.ball.sprite.direction[0] < 0:
            self.ball.sprite.rect.left = self.rect.right + 1
        else:
            self.ball.sprite.rect.right = self.rect.left - 1


#Horizontal Wall
class WallH(Wall):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
        self.rotate_image(90)

    def control_ball(self) -> None:
        super(WallH, self).control_ball()
        self.ball_out_wall()
        self.ball.sprite.direction = self.ball.sprite.direction.reflect(pygame.Vector2(0, 1))

    def ball_out_wall(self) -> None:
        if self.ball.sprite.direction[1] < 0:
            self.ball.sprite.rect.top = self.rect.bottom + 1
        else:
            self.ball.sprite.rect.bottom = self.rect.top - 1


#Diagonal Wall top to bottom
class WallDTB(Wall):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
        self.rotate_image(45)

    def control_ball(self) -> None:
        super(WallDTB, self).control_ball()
        self.ball.sprite.direction = self.ball.sprite.direction.reflect(pygame.Vector2(-1, 1))
        self.ball_out_wall()

    def ball_out_wall(self) -> None:
        y = (self.ball.sprite.rect.centery - self.rect.centery) - (self.ball.sprite.rect.centerx - self.rect.centerx)
        self.ball.sprite.rect.centery += y


#Diagonal Wall bottom to top
class WallDBT(Wall):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
        self.rotate_image(315)
        self.rect_topright()

    def control_ball(self) -> None:
        super(WallDBT, self).control_ball()
        self.ball.sprite.direction = self.ball.sprite.direction.reflect(pygame.Vector2(-1, -1))
        self.ball_out_wall()

    def ball_out_wall(self) -> None:
        y = (self.ball.sprite.rect.centery - self.rect.centery) + (self.ball.sprite.rect.centerx - self.rect.centerx)
        self.ball.sprite.rect.centery += y


class Flipper(TableObjectFixed, ABC):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
        self.image_template = self.image
        self.sound = self.load_sound("flipper.wav")

    def generate_rect(self) -> None:
        self.rect.left = self.pos_x
        self.rect.centery = self.pos_y

    @abstractmethod
    def move(self) -> None:
        self.sound.play()

    @abstractmethod
    def move_back(self) -> None:
        pass

    @abstractmethod
    def control_ball(self):
        pass


class LeftFlipper(Flipper):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
        self.generate_rect()
   
    def move(self) -> None:
        super(LeftFlipper, self).move()
        self.flip_image(False, True)

    def move_back(self) -> None:
        self.flip_image(False, False)

    def control_ball(self) -> None:
        if self.ball.sprite.rect.centerx > self.rect.centerx:
            self.ball.sprite.direction[0] += 100
        else:
            self.ball.sprite.direction[0] -= 100
        self.ball.sprite.direction[1] = -800
    

class RightFlipper(Flipper):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
        self.flip_image(True, False)   
        self.generate_rect()
        
    def move(self) -> None:
        super(RightFlipper, self).move()
        self.flip_image(True, True)

    def move_back(self) -> None:
        self.flip_image(True, False)

    def control_ball(self) -> None:
        if self.ball.sprite.rect.centerx > self.rect.centerx:
            self.ball.sprite.direction[0] -= 100
        else:
            self.ball.sprite.direction[0] += 100
        self.ball.sprite.direction[1] = -800


class RailDTB(WallDTB):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
    
    def control_ball(self) -> None:
        y = (self.ball.sprite.rect.centery - self.rect.centery) - (self.ball.sprite.rect.centerx - self.rect.centerx)
        self.ball.sprite.rect.centerx += y


class RailDBT(WallDBT):
    def __init__(self, pos_x, pos_y, width, height, image_name, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)

    def control_ball(self) -> None:
        y = (self.ball.sprite.rect.centery - self.rect.centery) + (self.ball.sprite.rect.centerx - self.rect.centerx)
        self.ball.sprite.rect.centerx -= y


#Launches the ball where it is in a given angle with a given force
class Launcher(TableObjectFixed, ABC):
    def __init__(self, pos_x, pos_y, width, height, image_name, angle, force, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, ball)
        self.angle = angle
        self.force = force

    def launch_ball(self) -> None:
        self.ball.sprite.direction[0] = - self.force * math.sin(math.radians(self.angle))
        self.ball.sprite.direction[1] = - self.force * math.cos(math.radians(self.angle))

    def position_ball_launch(self) -> None:
        self.ball.sprite.rect.center = (self.pos_x, self.pos_y)

    def generate_rect(self) -> None:
        self.rotate_image(self.angle)
        self.rect_center()

    @abstractmethod
    def control_ball(self):
        pass


#Launcher which will later charge when pressing space. Right now it launches with 100%
class ChargedLauncher(Launcher):
    def __init__(self, pos_x, pos_y, width, height, image_name, angle, force, ball, display) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, angle, force, ball)
        self.generate_rect()
        self.launch_sound = self.load_sound("launch.wav")
        self.new_game_sound = self.load_sound("new_game.wav")
        self.charging = False
        self.charge_speed = 1000
        self.force = 0
        self.controlling = False
        self.ball_number = 0
        self.new_game_sound.play()
        self.display = display
        self.display.update("Hold Space and release")
        self.display_small = Display(self.pos_x, self.pos_y - 100, self.ball_number)

    def update(self) -> None:
        if self.charging and self.force <= 3000:
            self.force += self.charge_speed * Settings.deltatime

    def reset(self) -> None:
        self.ball_number = 0
        self.new_game_sound.play()
        self.display.update("Hold Space and release")
        self.place_ball()

    def place_ball(self) -> None:
        if self.ball_number < 3:
            self.ball_number += 1 
            self.display_small.update(self.ball_number)
            self.ball.sprite.direction[0] = 0
            self.ball.sprite.direction[1] = 0
            self.ball.sprite.rect.center = (self.pos_x, self.pos_y - 300)
        else:
            Settings.gameover = True
            self.display.update("Gameover Press R to restart")

    def control_ball(self) -> None:
        self.ball.sprite.direction[1] = 0
        self.ball.sprite.rect.centerx = self.pos_x
        self.ball.sprite.rect.bottom = self.pos_y

    def charge(self) -> None:
        self.charging = True

    def launch_ball(self) -> None:
        self.launch_sound.play()
        self.display.update("")
        if self.controlling:
            super().launch_ball()
            self.position_ball_launch()
        self.charging = False
        self.force = 0

    def position_ball_launch(self) -> None:
        self.ball.sprite.rect.bottom = self.rect.top - 1
        self.ball.sprite.rect.centerx = self.pos_x
        
        
#For testing the ball-physics. Inherits from Launcher. Ball can be launched again with the r-key
class DebugLauncher(Launcher):
    def __init__(self, pos_x, pos_y, width, height, image_name, angle, force, ball) -> None:
        super().__init__(pos_x, pos_y, width, height, image_name, angle, force, ball)
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

    def control_ball(self):
        pass

    def launch_ball(self) -> None:
        super().launch_ball()
        self.position_ball_launch()
    
    def rotate_left(self) -> None:
        self.angle += 22.5 / self.grit
        if self.angle >= 360:
            self.angle -= 360
        self.rotate_image(self.angle)
        self.rect_center()
    
    def rotate_right(self) -> None:
        self.angle -= 22.5 / self.grit
        if self.angle < 0:
            self.angle += 360
        self.rotate_image(self.angle)
        self.rect_center()

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
        self.load_sound("fall.wav")
        self.objects()

    def restart(self) -> None:
        Settings.gameover = False
        self.score.reset()
        self.chargedlauncher.sprite.reset()

    def objects(self) -> None:
        self.ball = pygame.sprite.GroupSingle(Ball(self.r_guide - 17, self.t_guide + 50, 25, 25, "ball.png"))
        self.displays()
        self.chargedlauncher = pygame.sprite.GroupSingle(ChargedLauncher(self.r_guide - 17, self.b_guide - 140, 25, 30, "chargedlauncher.png", 0, 2000, self.ball, self.chargedlauncher_display))
        self.chargedlauncher.sprite.place_ball()
        self.walls = pygame.sprite.Group()
        self.rails = pygame.sprite.Group()
        self.launchlane()
        self.exitlanes()
        self.borders()
        self.flippers()

        #Uncomment the next line and line 626 for testing physics
        #self.debuglauncher = pygame.sprite.GroupSingle(DebugLauncher(440, 120, 25, 25, "debuglauncher.png", 0, 600, self.ball))

    def displays(self) -> None:
        self.chargedlauncher_display = Display(self.l_guide + 100, self.t_guide * 2 + 50, "Error")
        self.score = Score(self.cx_guide, self.t_guide * 2)

    def load_sound(self, sound_name) -> None:
        self.sound = pygame.mixer.Sound((Settings.soundpath(sound_name)))

    def launchlane(self) -> None:
        self.walls.add(WallV(self.r_guide - 40, self.t_guide + 40, 5, self.height - 140, "wall.png", self.ball))
        self.walls.add(WallDTB(self.r_guide - 13, self.t_guide, 5, 20, "wall.png", self.ball))

    def exitlanes(self) -> None:
        self.walls.add(WallDTB(self.l_guide + 40, self.b_guide - 198, 5, 70, "wall.png", self.ball))
        self.walls.add(WallDBT(self.r_guide - 76, self.b_guide - 197, 5, 70, "wall.png", self.ball))

    def borders(self) -> None:
        self.walls.add(WallH(self.l_guide, self.t_guide, 5, self.width, "wall.png", self.ball))
        self.walls.add(WallV(self.l_guide, self.t_guide, 5, self.height, "wall.png", self.ball))
        self.walls.add(WallV(self.r_guide, self.t_guide, 5, self.height, "wall.png", self.ball))
        self.walls.add(WallDTB(self.l_guide, self.b_guide - 179, 5, 100, "wall.png", self.ball))
        self.walls.add(WallDBT(self.r_guide - 36, self.b_guide - 177, 5, 100, "wall.png", self.ball))
        self.rails.add(RailDTB(self.l_guide + 34, self.b_guide - 172, 1, self.width / 2, "wall.png", self.ball))
        self.rails.add(RailDBT(self.r_guide - 70, self.b_guide - 172, 1, self.width / 2, "wall.png", self.ball))

    def flippers(self) -> None:
        self.leftflipper = pygame.sprite.GroupSingle(LeftFlipper(self.l_guide + 90, self.b_guide - 148, 150, 150, "flipper.png", self.ball))
        self.rightflipper = pygame.sprite.GroupSingle(RightFlipper(self.r_guide - 276, self.b_guide - 148, 150, 150, "flipper.png", self.ball))

    #Collision between ball and another group
    def collision(self, collidegroup):
        return pygame.sprite.groupcollide(collidegroup, self.ball, False, False, pygame.sprite.collide_mask)

    def assign_collision(self) -> None:
        if self.collision(self.chargedlauncher):
            self.chargedlauncher.sprite.control_ball()
            self.chargedlauncher.sprite.controlling = True
        else:
            self.chargedlauncher.sprite.controlling = False

        for wall in self.collision(self.walls):
            wall.control_ball()
            self.score.add_points(1000)

        for rail in self.collision(self.rails):
            rail.control_ball()

    def out_of_table(self):
        if self.ball.sprite.rect.top > self.b_guide:
            self.sound.play()
            self.score.add_points(10000)
            self.chargedlauncher.sprite.place_ball()

    def watch_for_events(self, event) -> None:
        if event.type == KEYDOWN:
            if event.key == K_a:
                if pygame.sprite.groupcollide(self.leftflipper, self.ball, False, False, pygame.sprite.collide_mask):
                    self.leftflipper.sprite.control_ball()
                self.leftflipper.sprite.move()
            elif event.key == K_d:
                if pygame.sprite.groupcollide(self.rightflipper, self.ball, False, False, pygame.sprite.collide_mask):
                    self.rightflipper.sprite.control_ball()
                self.rightflipper.sprite.move()
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
                self.leftflipper.sprite.move_back()
            elif event.key == K_d:
                self.rightflipper.sprite.move_back()
            elif event.key == K_SPACE:
                self.chargedlauncher.sprite.launch_ball()

    def update(self) -> None:
        self.ball.update()
        self.chargedlauncher.update()
        self.assign_collision()
        self.out_of_table()

    def draw(self, screen) -> None:
        #self.debuglauncher.draw(screen)
        self.chargedlauncher.draw(screen)
        self.chargedlauncher.sprite.display.draw(screen)
        self.chargedlauncher.sprite.display_small.draw(screen)
        self.walls.draw(screen)
        self.leftflipper.draw(screen)
        self.rightflipper.draw(screen)
        self.rails.draw(screen)
        self.score.draw(screen)
        self.ball.draw(screen)


class Background(object):
    def __init__(self) -> None:
        super().__init__()
        self.image = pygame.image.load(os.path.join(Settings.imagepath("table.png")))
        self.image = pygame.transform.scale(self.image, (Settings.dim())).convert()
    
    def draw(self, screen) -> None:
        screen.blit(self.image, (0, 0))


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
