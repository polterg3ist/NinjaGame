import json

import pygame

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,

}

NEIGHBOR_OFFSETS = [(0, 0), (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1)]
PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        self.offgrid_hover_tiles = []

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
                    
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]

        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])

        return tiles

    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rect_x, rect_y = tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size
                rect_size = (self.tile_size, self.tile_size)
                rects.append(pygame.Rect(rect_x, rect_y, *rect_size))
        return rects

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                check_loc = f"{tile['pos'][0] + shift[0]};{tile['pos'][1] + shift[1]}"
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            asset = self.game.assets[tile['type']]
            tile_img = pygame.transform.rotate(asset[tile['variant']], tile['rotation'])
            render_pos = (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1])
            surf.blit(tile_img, render_pos)

        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = f"{x};{y}"
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    asset = self.game.assets[tile['type']]
                    tile_img = pygame.transform.rotate(asset[tile['variant']], tile['rotation'])
                    render_pos = (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1])
                    surf.blit(tile_img, render_pos)

        for tile in self.offgrid_hover_tiles:
            asset = self.game.assets[tile['type']]
            tile_img = pygame.transform.rotate(asset[tile['variant']], tile['rotation'])
            render_pos = (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1])
            surf.blit(tile_img, render_pos)

    def save(self, path):
        with open(path, 'w') as f:
            map_data = {'tilemap': self.tilemap,
                        'tile_size': self.tile_size,
                        'offgrid': self.offgrid_tiles,
                        'offgrid_hover_tiles': self.offgrid_hover_tiles}
            json.dump(map_data, f)

        print(f'Saved tilemap to {path}')

    def load(self, path):
        with open(path, 'r') as f:
            map_data = json.load(f)

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']
        self.offgrid_hover_tiles = map_data['offgrid_hover_tiles']

        print(f'Loaded tilemap from {path}')

