from math import cos, sin, degrees, sqrt, atan2, pi
from random import randint

import pygame
import sys

from pygame_magics.camera import camera
from pygame_magics.entities import enemy
from pygame_magics.entities import player
from pygame_magics.entities import experience_orb
from pygame_magics.entities.magic_bolt import MagicBolt


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Settings(metaclass=Singleton):

    def __init__(self):
        self.map_x = 2800 * 5
        self.map_y = 1300 * 5


class PlayerStats(metaclass=Singleton):

    def __init__(self):
        self.health = 100
        self.player = None
        self.experience = 0
        self.n = 1
        self.oil = 0
        self.amount_of_oil = 0

    def check_experience(self):
        if self.experience_growth() <= self.experience:
            self.experience = 0
            self.n += 1

    def experience_growth(self):
        return 5 * (1.57 ** (self.n - 1))


class Player(player.Player):
    def __init__(self, pos, image, size, speed, group):
        super().__init__(pos, image, size, speed, group)

    def update(self, oil_group, orb_group, rocket_group):
        self.input()
        self.rect.center += self.direction * self.speed

        collided_oil = pygame.sprite.spritecollideany(self, oil_group)
        if collided_oil:
            print("Player collided with oil!")
            oil_group.remove(collided_oil)
            collided_oil.kill()
            PlayerStats().oil += 1

        collided_orb = pygame.sprite.spritecollideany(self, orb_group)
        if collided_orb:
            print("Player collided with orb!")
            orb_group.remove(collided_orb)
            collided_orb.kill()
            global total_amount
            total_amount -= 1
            PlayerStats().experience += 1

        keys = pygame.key.get_pressed()
        if pygame.sprite.spritecollideany(self, rocket_group):
            if keys[pygame.K_RETURN]:
                if PlayerStats().oil < 5:
                    print('Not enough')
                else:
                    if PlayerStats().oil == PlayerStats().amount_of_oil:
                        print('You win')
                    else:
                        print('You lose')


class Oil(pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.original_image = pygame.image.load('graphics/carbons/oil.png').convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (40, 40))
        self.rect = self.image.get_rect()
        self.rect.center = pos


class Rocket(pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.original_image = pygame.image.load('graphics/rocket/rocketttt.png').convert_alpha()
        self.image = pygame.transform.scale(self.original_image, (
            self.original_image.get_width() * 0.5,
            self.original_image.get_height() * 0.5
        ))
        self.rect = self.image.get_rect(center=pos)


class Enemy(enemy.Enemy):
    def __init__(self, pos, image, image_size, speed, health, group):
        super().__init__(pos, image, image_size, speed, health, group)

    def update(self, player):
        direction_vector = pygame.math.Vector2(player.rect.center) - pygame.math.Vector2(self.rect.center)
        direction_vector.normalize_ip()
        self.rect.move_ip(direction_vector * self.speed)
        if pygame.sprite.collide_rect(self, player):
            PlayerStats().health -= 1


pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

camera_group = camera.CameraGroup(Settings().map_x, Settings().map_y,
                                  'graphics/mars_photogrammetry/map.png', 12)

player = Player((640, 360), "graphics/engineer/engineer_0_0.png", (100, 100), 20, camera_group)
PlayerStats().player = player

oil_group = pygame.sprite.Group()
orb_group = pygame.sprite.Group()
rocket_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
magic_bolt_group = pygame.sprite.Group()

magic_bolt = MagicBolt(player.rect.center, "graphics/magic-bolt/bullet_ranger_init_weapon_xx8_0.png")
amount_of_oil = randint(5, 9)
PlayerStats().amount_of_oil = amount_of_oil
for i in range(amount_of_oil):
    random_x = randint(-Settings().map_x, Settings().map_x)
    random_y = randint(-Settings().map_y, Settings().map_y)
    Oil((random_x, random_y), oil_group)

Rocket((0, 0), rocket_group)

total_amount = 0


def spawn_orbs(amount):
    global total_amount
    for _ in range(amount):
        experience_orb.ExperienceOrb(
            (randint(-Settings().map_x, Settings().map_x), randint(-Settings().map_y, Settings().map_y)),
            'graphics/experience_orb/experience.png', (40, 40),
            orb_group)
    total_amount = amount


def create_enemy():
    Enemy(player.rect.center + pygame.math.Vector2(
        (-1) * randint(1, 2) * screen.get_width() * 1.5,
        (-1) * randint(1, 2) * screen.get_height() * 1.5), "graphics/ufo/ui2_106.png",
          (80, 80), 20, 100, enemy_group)


def get_nearest_enemy():
    arr = []
    for enemy in enemy_group.sprites():
        delta = sqrt((enemy.rect.centerx - player.rect.centerx) ** 2 + (enemy.rect.centery - player.rect.centery) ** 2)
        arr.append((delta, enemy))
    return min(arr, key=lambda x: x[0])[1] if arr else 0


normal_amount = 400
enemy_timer = 0
magic_bolt_timer = 0
ENEMY_SPAWN_INTERVAL = 3000
SPAWN_COEFFICIENT = 0.997

MAGIC_BOLT_SPAWN_INTERVAL = 1000
MAGIC_BOLT_FIRE_INTERVAL = 1000

MAGIC_BOLT_FIRE_SPEED = 200

spawn_orbs(normal_amount)
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    screen.fill('#71ddee')
    camera_group.update(oil_group, orb_group, rocket_group)
    current_time = pygame.time.get_ticks()
    if current_time - enemy_timer > ENEMY_SPAWN_INTERVAL * (SPAWN_COEFFICIENT ** (current_time // 1000)):
        create_enemy()
        enemy_timer = current_time
    camera_group.custom_draw(player, oil_group, orb_group, rocket_group, enemy_group, magic_bolt_group)
    enemy_group.update(player)
    orb_group.update()
    oil_group.update()
    magic_bolt_group.update(enemy_group)
    if PlayerStats().health <= 0:
        break
    PlayerStats().check_experience()
    if current_time - magic_bolt_timer > MAGIC_BOLT_SPAWN_INTERVAL:
        magic_bolt.update(player.rect.center, magic_bolt_group, PlayerStats().n, get_nearest_enemy)
        magic_bolt_timer = current_time
    if current_time - magic_bolt_timer > MAGIC_BOLT_FIRE_INTERVAL:
        magic_bolt.stop_fire(magic_bolt_group, enemy_group)
        magic_bolt_group.update(magic_bolt_group)
    pygame.display.flip()
    if total_amount < normal_amount // 2:
        spawn_orbs(normal_amount)
    pygame.display.update()
    clock.tick(60)
