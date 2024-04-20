import json


def add_rotation_to_json(path):
    with open(path, 'r') as file:
        map_data = json.load(file)

    tilemap = map_data['tilemap']

    for loc in tilemap:
        tile = tilemap[loc]
        tile['rotation'] = 0

    with open(path, 'w') as file:
        json.dump(map_data, file)


def offgrid_add_rotation_to_json(path):
    with open(path, 'r') as file:
        map_data = json.load(file)

    offgrid = map_data['offgrid']

    for tile in offgrid:
        tile['rotation'] = 0

    with open(path, 'w') as file:
        json.dump(map_data, file)


def offgrid_hover_to_json(path):
    with open(path, 'r') as file:
        map_data = json.load(file)

    map_data['offgrid_hover_tiles'] = []

    with open(path, 'w') as file:
        json.dump(map_data, file)


def add_spawnpoints_to_map(path):
    with open(path, 'r') as file:
        map_data = json.load(file)

    map_data['spawn_points'] = {}

    with open(path, 'w') as file:
        json.dump(map_data, file)


def fix_three_maps():
    for path in ('../data/maps/0.json', '../data/maps/1.json', '../data/maps/2.json'):
        add_rotation_to_json(path)
        offgrid_add_rotation_to_json(path)
        offgrid_hover_to_json(path)
        add_spawnpoints_to_map(path)


def fix_enemies_in_offgrid_hover(path):
    with open(path, 'r') as file:
        map_data = json.load(file)

    offgrid = map_data['offgrid']
    offgrid_h = map_data['offgrid_hover_tiles']

    for tile in offgrid_h.copy():

        if tile['type'] == 'spawners':
            offgrid.append(tile)
            offgrid_h.remove(tile)

    with open(path, 'w') as file:
        json.dump(map_data, file)


fix_enemies_in_offgrid_hover('../data/maps/3.json')