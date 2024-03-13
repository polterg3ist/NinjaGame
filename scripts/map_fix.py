import json


def add_rotation_to_json():
    with open('../map.json', 'r') as file:
        map_data = json.load(file)

    tilemap = map_data['tilemap']

    for loc in tilemap:
        tile = tilemap[loc]
        tile['rotation'] = 0

    with open('../map.json', 'w') as file:
        json.dump(map_data, file)


def offgrid_add_rotation_to_json():
    with open('../map.json', 'r') as file:
        map_data = json.load(file)

    offgrid = map_data['offgrid']

    for tile in offgrid:
        tile['rotation'] = 0

    with open('../map.json', 'w') as file:
        json.dump(map_data, file)


def offgrid_hover_to_json():
    with open('../map.json', 'r') as file:
        map_data = json.load(file)

    map_data['offgrid_hover_tiles'] = []

    with open('../map.json', 'w') as file:
        json.dump(map_data, file)


offgrid_hover_to_json()