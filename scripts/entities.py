import math
import random

import pygame

from scripts.particle import Particle
from scripts.spark import Spark


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0:
            self.flip = False
        elif movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.velocity[1] = min(5, self.velocity[1] + 0.1)

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        render_pos = (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1])
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), render_pos)


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.max_jumps = 1
        self.jumps = self.max_jumps
        self.wall_slide = False
        self.dashing = 0
        self.enemy_collide_time = 0

    def update(self, tilemap, movement=(0, 0)):
        #print(self.action, self.last_movement, self.wall_slide)
        #print(self.velocity)
        super().update(tilemap, movement=movement)

        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = self.max_jumps

        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.air_time = 5
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['right']:
                self.flip = False
                self.last_movement = (1, 0)
            elif self.collisions['left']:
                self.flip = True
                self.last_movement = (-1, 0)
            self.set_action('wall_slide')

        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                frame = random.randint(0, 7)
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, pvelocity, frame))

        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        elif self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.3
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            frame = random.randint(0, 7)
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, pvelocity, frame))

        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

        # if fell down respawn player
        if self.air_time > 150:
            self.game.dead += 1
            self.dying()
            self.game.screenshake = max(self.game.shake_value * 2, self.game.screenshake)
            self.game.sfx['fall_1'].play()
            self.game.sfx['fall_2'].play()

    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset)

    def respawn(self):
        #self.pos = list(self.game.spawn_points[self.game.current_spawn_point])
        self.velocity = [0, 0]
        self.last_movement = [0, 0]
        self.game.movement = [0, 0]
        self.wall_slide = False
        self.air_time = 0
        self.jumps = self.max_jumps
        self.dashing = 0

    def dying(self, color=(255, 255, 255)):
        for i in range(30):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            pos = self.rect().center
            velocity = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5]
            frame = random.randint(0, 7)
            particle_effect = Particle(self.game, 'particle', pos, velocity, frame)
            self.game.particles.append(particle_effect)
            self.game.sparks.append(Spark(pos, angle, 2 + random.random(), color))

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
            self.velocity[1] = -2.5
            self.air_time = 5
            self.jumps = max(1, self.jumps - 1)
            return True

        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)

        self.walking = 0
        self.player_collide_time = 0

    def update(self, tilemap, movement=(0, 0)):
        tiles_around = {
            'forward_one_tile_bot': tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)),
            'forward_two_tile_bot': tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 46)),
            'forward_three_tile_bot': tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 69)),
            'forward_one_tile_top': tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] - 23)),
        }
        if self.walking:
            # if there's a solid tile to not drop down
            if any([tiles_around[forward_tiles] for forward_tiles in list(tiles_around)[0:3]]):
                # if there's solid tile in front of enemy
                if self.collisions['right'] or self.collisions['left']:
                    # If the enemy can't jump over
                    if tiles_around['forward_one_tile_top']:
                        # turning back
                        self.flip = not self.flip
                    else:
                        self.velocity[1] = -2
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            # if not jumping
            elif self.velocity[1] == 0:
                # turning back
                self.flip = not self.flip

            self.walking = max(0, self.walking - 1)
            if not self.walking:
                # at the end of walking an enemy will automatically shoot if it is possibly
                self.shoot()
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        elif random.random() < 0.01:
            self.shoot()
        super().update(tilemap, movement=movement)

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if self.rect().colliderect(self.game.player.rect()):    # if enemy collide player
            if abs(self.game.player.dashing) >= 50:             # if player was dashing then enemy dies
                self.game.sfx['hit'].play()
                self.game.screenshake = max(self.game.shake_value, self.game.screenshake)
                self.game.player.dying()
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random() * 4))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random() * 4))
                return True
            if not self.game.dead:
                if self.pos[0] > self.game.player.pos[0] and self.flip or self.pos[0] < self.game.player.pos[0] and not self.flip:
                    self.player_collide_time += 1
        else:
            self.player_collide_time = max(0, self.player_collide_time - 1)

        if self.player_collide_time >= 7:
            self.game.sfx['shoot'].play()
            self.game.sfx['hit'].play()
            self.player_collide_time = 0
            self.game.dead += 1
            self.game.player.dying()
            self.game.screenshake = max(self.game.shake_value, self.game.screenshake)

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset)

        if self.flip:
            image = pygame.transform.flip(self.game.assets['gun'], True, False)
            pos = (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0],
                   self.rect().centery - offset[1])
        else:
            image = self.game.assets['gun']
            pos = (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1])
        surf.blit(image, pos)

    def shoot(self):
        """ Will shoot if it is possible """
        dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
        if abs(dis[1]) < 16 and abs(dis[0]) < 180:
            if self.flip and dis[0] < 0:
                self.game.sfx['shoot'].play()
                self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                for i in range(4):
                    self.game.sparks.append(
                        Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
            if not self.flip and dis[0] > 0:
                self.game.sfx['shoot'].play()
                self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                for i in range(4):
                    self.game.sparks.append(
                        Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))