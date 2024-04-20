import math
from random import randint

import pygame


class Spark:
    def __init__(self, pos, angle, speed, color=(255, 255, 255)):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
        self.color = color

    def update(self):
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed

        self.speed = max(0, self.speed - 0.1)
        return not self.speed

    def render(self, surf, offset=(0, 0)):
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0],
             self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0],
             self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0],
             self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0],
             self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1]),
        ]

        # full random
        #pygame.draw.polygon(surf, (randint(0, 255), randint(0, 100), randint(0, 55)), render_points)
        # random more red
        # pygame.draw.polygon(surf, (randint(0, 255), randint(0, 255), randint(0, 255)), render_points)
        # white
        pygame.draw.polygon(surf, self.color, render_points)
