import sys

import pygame

from scripts.tilemap import Tilemap
from scripts.utils import load_images, load_image


class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Editor')

        self.fullscreen = True
        if self.fullscreen:
            self.WIDTH, self.HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
            self.render_scale = 4.0
        else:
            self.WIDTH, self.HEIGHT = 640, 480
            self.render_scale = 2.0

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.display_width, self.display_height = (self.WIDTH // self.render_scale, self.HEIGHT // self.render_scale)
        self.display = pygame.Surface((self.display_width, self.display_height))

        self.clock = pygame.time.Clock()

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'spawners': load_images('tiles/spawners'),
        }

        self.background = pygame.transform.scale(load_image('background.png'), (self.display_width, self.display_height))

        self.movement = [False, False, False, False]  # UP DOWN LEFT RIGHT

        self.tilemap = Tilemap(self, tile_size=16)

        self.level = 4

        try:
            self.tilemap.load(f'data/maps/{self.level}.json')
        except FileNotFoundError:
            print('Map was not Found')

        self.scroll = [-100, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ctrl = False
        self.ongrid = True
        self.offgrid_hover_mode = False

        self.rotation = 0
        self.keep_rotating = False

        self.font = pygame.font.SysFont('monospace', 8, True, False)

    def run(self):

        while True:
            self.display.blit(self.background, (0, 0))

            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            if self.keep_rotating:
                self.rotation = (self.rotation + 5) % 360

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img = pygame.transform.rotate(current_tile_img, self.rotation)
            current_tile_img.set_alpha(125)

            # if a spawner is currently selected then reset all tile settings
            if self.tile_group == 4:
                self.ongrid = False
                self.ongrid_hover_mode = False
                self.rotation = 0
                self.keep_rotating = False

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] // self.render_scale, mpos[1] // self.render_scale)
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                        int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

            # drawing current tile at top left corner
            if self.ongrid:
                pre_placed_tile_pos = (
                    tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                    tile_pos[1] * self.tilemap.tile_size - self.scroll[1])
                self.display.blit(current_tile_img, pre_placed_tile_pos)
            else:
                self.display.blit(current_tile_img, mpos)

            # drawing current mouse position
            mpos_place = f"XY={(mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])} TILE={tile_pos}"
            mpos_text_surf = self.font.render(mpos_place, True, (255, 255, 255))
            mpos_text_rect = mpos_text_surf.get_rect(topright=self.display.get_rect().topright)
            self.display.blit(mpos_text_surf, mpos_text_rect)

            if self.clicking and self.ongrid:
                self.tilemap.tilemap[f"{tile_pos[0]};{tile_pos[1]}"] = {
                    'type': self.tile_list[self.tile_group],
                    'variant': self.tile_variant,
                    'pos': tile_pos,
                    'rotation': self.rotation,
                }
            if self.right_clicking:
                tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                else:
                    for offgrid_map in (self.tilemap.offgrid_tiles, self.tilemap.offgrid_hover_tiles):
                        for tile in offgrid_map:
                            tile_img = self.assets[tile['type']][tile['variant']]
                            tile_r = pygame.Rect(
                                tile['pos'][0] - self.scroll[0],
                                tile['pos'][1] - self.scroll[1],
                                tile_img.get_width(),
                                tile_img.get_height())
                            if tile_r.collidepoint(mpos):
                                offgrid_map.remove(tile)

            self.display.blit(current_tile_img, (5, 5))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            if not self.offgrid_hover_mode:
                                tilemap = self.tilemap.offgrid_tiles
                            else:
                                tilemap = self.tilemap.offgrid_hover_tiles
                            tilemap.append({
                                'type': self.tile_list[self.tile_group],
                                'variant': self.tile_variant,
                                'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1]),
                                'rotation': self.rotation,
                            })
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    elif self.ctrl:

                        if event.button == 4 and self.render_scale < 10:
                            self.render_scale += 0.2
                        elif event.button == 5 and self.render_scale > 1.2:
                            self.render_scale -= 0.2

                        screen_width, screen_height = pygame.display.get_surface().get_size()
                        self.display_width = screen_width // self.render_scale
                        self.display_height = screen_height // self.render_scale
                        self.display = pygame.Surface((self.display_width, self.display_height))

                        new_size = (self.display_width, self.display_height)
                        self.background = pygame.transform.scale(self.background, new_size)
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_b:
                        self.offgrid_hover_mode = not self.offgrid_hover_mode
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_o:
                        self.tilemap.save(f'data/maps/{self.level}.json')
                    if event.key == pygame.K_r:
                        self.rotation = (self.rotation + 90) % 360
                    if event.key == pygame.K_e:
                        self.rotation = (self.rotation + 45) % 360
                    if event.key == pygame.K_v:
                        self.rotation = 0
                    if event.key == pygame.K_f:
                        self.keep_rotating = True
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = True

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_f:
                        self.keep_rotating = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = False

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)


Editor().run()
