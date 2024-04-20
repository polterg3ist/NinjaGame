import math
import os
import random
import sys

import pygame

from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.spark import Spark
from scripts.tilemap import Tilemap
from scripts.utils import load_image, load_images, Animation
from scripts.clouds import Clouds
from scripts.particle import Particle


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Ninja Game')

        self.fullscreen = True
        if self.fullscreen:
            self.WIDTH, self.HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
            self.render_scale = 4.0
            self.shake_value = 25
        else:
            self.WIDTH, self.HEIGHT = 640, 480
            self.render_scale = 2.0
            self.shake_value = 16

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.display_width, self.display_height = (self.WIDTH // self.render_scale, self.HEIGHT // self.render_scale)
        self.display = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((self.display_width, self.display_height))

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'player/idle': Animation(load_images('entities/player/idle'), 6),
            'player/run': Animation(load_images('entities/player/run'), 4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
            'salute': pygame.mixer.Sound('data/sfx/salute.wav'),
            'salute_and_song': pygame.mixer.Sound('data/sfx/salute_and_song.wav'),
            'fall_1': pygame.mixer.Sound('data/sfx/fall_2.mp3'),
            'fall_2': pygame.mixer.Sound('data/sfx/fall_3.wav'),
        }
        self.general_volume = 1

        self.sfx['ambience'].set_volume(0.2 * self.general_volume)
        self.sfx['shoot'].set_volume(0.4 * self.general_volume)
        self.sfx['hit'].set_volume(0.5 * self.general_volume)
        self.sfx['dash'].set_volume(0.3 * self.general_volume)
        self.sfx['jump'].set_volume(0.3 * self.general_volume)
        self.sfx['salute'].set_volume(0.5 * self.general_volume)
        self.sfx['salute_and_song'].set_volume(0.6 * self.general_volume)
        self.sfx['fall_1'].set_volume(0.6 * self.general_volume)
        self.sfx['fall_2'].set_volume(0.6 * self.general_volume)

        self.background = pygame.transform.scale(self.assets['background'], (self.display_width, self.display_height))

        self.clock = pygame.time.Clock()

        self.img = pygame.image.load('data/images/clouds/cloud_1.png')
        self.img.set_colorkey((0, 0, 0))

        self.movement = [False, False]    # UP DOWN LEFT RIGHT

        self.clouds = Clouds(self.assets['clouds'], count=16)

        self.player = Player(self, (50, 50), (8, 15))
        self.tilemap = Tilemap(self, tile_size=16)

        self.level_number = 0
        self.load_level()

        self.screenshake = 0

        self.show_shadows = False
        self.shadow = 8
        self.shadow_dir = 'inc'
        self.shadow_speed = 0.01

        self.ctrl = False

        #self.spawn_points = {1: (50, 50), 2: (120, 100), 3: (200, 90), 4: (340, -21), 5: (460, -40), 6: (590, -52), 7: (735, -63)}
        #self.current_spawn_point = 1

    def load_level(self):
        map_id = self.level_number
        try:
            self.tilemap.load(f"data/maps/{map_id}.json")
        except FileNotFoundError:
            print('Map was not Found')
        self.leaf_spawners = []
        for tree in self.tilemap.extract(id_pairs=[('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        self.enemies = []
        for spawner in self.tilemap.extract(id_pairs=[('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.is_playing_salute = False

        #self.scroll = [-112, -30]
        self.scroll = [self.player.pos[0] - 162, self.player.pos[1] - 82]
        self.dead = 0
        self.transition = -30

    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5 * self.general_volume)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.background, (0, 0))

            self.screenshake = max(0, self.screenshake - 1)

            if not self.enemies:
                self.player.dying(color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
                self.transition += 0.13
                if not self.is_playing_salute:
                    self.sfx['salute'].play()
                    self.sfx['salute_and_song'].play()
                    self.is_playing_salute = True
                if self.transition > 30:
                    self.level_number = (self.level_number + 1) % len(os.listdir('data/maps/'))
                    self.load_level()
            if self.transition < 0:
                self.transition += 1

            if self.dead:
                pygame.event.clear()
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level()
                    self.player.respawn()
                    pygame.event.clear()
                    # I added continue here just in hope that this is gonna solve player afterdeath input bug
                    continue

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    velocity = [round(random.uniform(-0.3, 0.3), 2), round(random.uniform(0.1, 0.5), 2)]
                    frame = random.randint(0, len(self.assets['particle/leaf'].images))
                    self.particles.append(Particle(self, 'leaf', pos, velocity, frame))

            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)

            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)

            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                pos = (projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                       projectile[0][1] - img.get_height() / 2 - render_scroll[1])
                self.display_2.blit(img, pos)
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(14):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]) and not self.dead:
                        self.sfx['hit'].play()
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.player.dying()
                        self.screenshake = max(16, self.screenshake)

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)

            if self.show_shadows:
                if self.shadow_dir == 'inc':
                    self.shadow += self.shadow_speed
                    if self.shadow >= 8:
                        self.shadow_dir = 'dec'
                if self.shadow_dir == 'dec':
                    self.shadow -= self.shadow_speed
                    if self.shadow <= -8:
                        self.shadow_dir = 'inc'
                self.display_2.blit(display_sillhouette, (self.shadow, self.shadow))

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.ctrl:
                        if event.button == 4 and self.render_scale < 8:
                            self.render_scale += 0.2
                        elif event.button == 5 and self.render_scale > 1.2:
                            self.render_scale -= 0.2

                        screen_width, screen_height = pygame.display.get_surface().get_size()
                        self.display_width = screen_width // self.render_scale
                        self.display_height = screen_height // self.render_scale
                        self.display = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA)
                        self.display_2 = pygame.Surface((self.display_width, self.display_height))

                        new_size = (self.display_width, self.display_height)
                        self.background = pygame.transform.scale(self.assets['background'], new_size)
                        print('size', self.background.get_size())
                        print(f'x={self.display_width} y={self.display_height} scale={self.render_scale}')

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = True
                    if event.key == pygame.K_f:
                        self.player.dash()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = False

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255),
                                   (self.display_width // 2, self.display_height // 2),
                                   (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                                  random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)


Game().run()
