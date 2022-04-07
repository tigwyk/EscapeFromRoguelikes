from __future__ import annotations

import random
import itertools
from uuid import uuid4
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING

import tcod

import entity_factories
from maps import GameMap
import tile_types

import numpy as np

MAP_WIDTH = 80
MAP_HEIGHT = 43

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.medkit, 35), (entity_factories.combat_knife, 5),(entity_factories.makarov_mag, 2)],
    2: [(entity_factories.throwing_sand, 10), (entity_factories.combat_knife, 15), (random.choice([entity_factories.hiking_boots,entity_factories.rusty_helmet,entity_factories.body_armor]), 1), (entity_factories.pistol, 1)],
    4: [(entity_factories.lightning_scroll, 25), (entity_factories.sword, 5), (entity_factories.pistol, 2), (entity_factories.hiking_boots, 2), (entity_factories.rusty_helmet, 2), (entity_factories.body_armor, 5),(entity_factories.makarov_mag, 10)],
    6: [(entity_factories.grenade, 25), (entity_factories.body_armor, 15), (entity_factories.rifle, 2),(entity_factories.assault_rifle, 2)],
    8: [(entity_factories.hiking_boots, 2)],
}

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.rat, 60),(entity_factories.dog, 40)],
    1: [(entity_factories.scav, 20),(entity_factories.dog, 20)],
    2: [(entity_factories.scav, 30),(entity_factories.dog, 25)],
    3: [(entity_factories.raider, 15)],
    5: [(entity_factories.mutant1, 30),(entity_factories.mutant2, 10)],
    7: [(entity_factories.mutant1, 60),(entity_factories.mutant2, 30)],
}

def get_max_value_for_floor(
    max_value_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value

def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities

class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

def place_dungeon_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int,) -> None:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)

def place_labs_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int,) -> None:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )
    
    bonus = random.randint(0, int(floor_number/2))
    number_of_items += bonus
    number_of_monsters += bonus

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number+1
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number+1
    )

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)

def place_overworld_entities(overworld: GameMap, floor_number: int,) -> None:
    number_of_monsters = random.randint(
        0, 10
    )
    number_of_items = random.randint(
        0, 10
    )

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for entity in monsters + items:
        x = random.randint(1, 79)
        y = random.randint(1, 42)

        if not any(entity.x == x and entity.y == y for entity in overworld.entities):
            entity.spawn(overworld, x, y)

def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y

def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(*new_room.center, dungeon)
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

            center_of_last_room = new_room.center

        place_dungeon_entities(new_room, dungeon, engine.game_world.current_floor)
        
        dungeon.tiles[center_of_last_room] = tile_types.down_stairs
        dungeon.downstairs_location = center_of_last_room

        # Finally, append the new room to the list.
        rooms.append(new_room)

    return dungeon

DEPTH = 5
MIN_SIZE = 5
FULL_ROOMS = False

def generate_bsp_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    
    map = GameMap(engine, map_width, map_height, entities=[player])

    #Empty global list for storing room coordinates
    rooms: List[RectangularRoom] = []
    
    center_of_last_room = (0, 0)
    
    #New root node
    bsp = tcod.bsp.BSP(x=0, y=0, width=map_width, height=map_height)
    

    #Split into nodes
    bsp.split_recursive(
        DEPTH, 
        room_min_size, 
        room_min_size, 
        1.5, 
        1.5
    )

    #Traverse the nodes and create rooms                            

    for room in bsp.pre_order():
        new_room = RectangularRoom(room.x, room.y, room.width, room.height)
        if room.children:
            room1, room2 = room.children
            # print('Connect the rooms:\n%s\n%s' % (room1, room2))
            rect_room1 = RectangularRoom(room1.x, room1.y, room1.width, room1.height)
            rect_room2 = RectangularRoom(room2.x, room2.y, room2.width, room2.height)
            for x,y in tcod.los.bresenham(rect_room1.center, rect_room2.center):
                map.tiles[x, y] = tile_types.floor
        else:
            # print('Dig a room for %s.' % room)
            
            map.tiles[new_room.inner] = tile_types.floor

            if len(rooms) == 0:
            # The first room, where the player starts.
                player.place(*new_room.center, map)
            else:      
                center_of_last_room = new_room.center

            place_labs_entities(new_room, map, engine.game_world.current_floor)

            # Finally, append the new room to the list.
            rooms.append(new_room)

    # print(len(rooms))
    map.tiles[center_of_last_room] = tile_types.down_stairs
    map.downstairs_location = center_of_last_room

    return map

def generate_overworld(
    map_width: int,
    map_height: int,
    engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    worldmap = GameMap(engine, map_width, map_height, entities=[player])
    
    noise = tcod.noise.Noise(
            dimensions=2,
            algorithm=tcod.noise.Algorithm.SIMPLEX,
            seed=random.randint(0,500)
    )

    noisemap = noise[tcod.noise.grid(shape=(2048,2048), scale=0.07, origin=(0,0))]
    noisemap = (noisemap + 1.0) * 0.5

    for x in range(map_width):
        for y in range(map_height)[1:]:
            if(not y):
                break
            # print(f"Noise reading: {noisemap[x,y]}")
            worldmap.tiles[x,y] = tile_types.ocean
            if(noisemap[x,y] > 0):
                worldmap.tiles[x,y] = tile_types.beach
            if(noisemap[x,y] > 0.2):
                worldmap.tiles[x,y] = tile_types.swamp
            if(noisemap[x,y] > 0.3):
                worldmap.tiles[x,y] = tile_types.plains
            if(noisemap[x,y] > 0.6):
                worldmap.tiles[x,y] = tile_types.forest
            if(noisemap[x,y] > 0.8):
                worldmap.tiles[x,y] = tile_types.hills
            if(noisemap[x,y] > 0.9):
                worldmap.tiles[x,y] = tile_types.mountains

    # worldmap.tiles[slice(0,80),slice(0,43)] = tile_types.floor
    # worldmap.tiles[slice(center),slice((map_width/2)+10,(map_height/2)+10)] = tile_types.floor
    player.place(40, 21, worldmap)
    place_overworld_entities(worldmap, engine.game_world.current_floor)
    
    worldmap.tiles[44,25] = tile_types.down_stairs
    worldmap.downstairs_location = (44,25)

    return worldmap

def traverse_node(node, dat):
    global map, bsp_rooms

    #Create rooms
    if tcod.bsp_is_leaf(node):
        minx = node.x + 1
        maxx = node.x + node.w - 1
        miny = node.y + 1
        maxy = node.y + node.h - 1

        if maxx == MAP_WIDTH - 1:
            maxx -= 1
        if maxy == MAP_HEIGHT - 1:
            maxy -= 1

        #If it's False the rooms sizes are random, else the rooms are filled to the node's size
        if FULL_ROOMS == False:
            minx = tcod.random_get_int(None, minx, maxx - MIN_SIZE + 1)
            miny = tcod.random_get_int(None, miny, maxy - MIN_SIZE + 1)
            maxx = tcod.random_get_int(None, minx + MIN_SIZE - 2, maxx)
            maxy = tcod.random_get_int(None, miny + MIN_SIZE - 2, maxy)

        node.x = minx
        node.y = miny
        node.w = maxx-minx + 1
        node.h = maxy-miny + 1

        #Dig room
        for x in range(minx, maxx + 1):
            for y in range(miny, maxy + 1):
                map[x][y].blocked = False
                map[x][y].block_sight = False
        
        #Add center coordinates to the list of rooms
        bsp_rooms.append(((minx + maxx) / 2, (miny + maxy) / 2))

    #Create corridors    
    else:
        left = tcod.bsp_left(node)
        right = tcod.bsp_right(node)
        node.x = min(left.x, right.x)
        node.y = min(left.y, right.y)
        node.w = max(left.x + left.w, right.x + right.w) - node.x
        node.h = max(left.y + left.h, right.y + right.h) - node.y
        if node.horizontal:
            if left.x + left.w - 1 < right.x or right.x + right.w - 1 < left.x:
                x1 = tcod.random_get_int(None, left.x, left.x + left.w - 1)
                x2 = tcod.random_get_int(None, right.x, right.x + right.w - 1)
                y = tcod.random_get_int(None, left.y + left.h, right.y)
                vline_up(map, x1, y - 1)
                hline(map, x1, y, x2)
                vline_down(map, x2, y + 1)

            else:
                minx = max(left.x, right.x)
                maxx = min(left.x + left.w - 1, right.x + right.w - 1)
                x = tcod.random_get_int(None, minx, maxx)

                # catch out-of-bounds attempts
                while x > MAP_WIDTH - 1:
                        x -= 1

                vline_down(map, x, right.y)
                vline_up(map, x, right.y - 1)

        else:
            if left.y + left.h - 1 < right.y or right.y + right.h - 1 < left.y:
                y1 = tcod.random_get_int(None, left.y, left.y + left.h - 1)
                y2 = tcod.random_get_int(None, right.y, right.y + right.h - 1)
                x = tcod.random_get_int(None, left.x + left.w, right.x)
                hline_left(map, x - 1, y1)
                vline(map, x, y1, y2)
                hline_right(map, x + 1, y2)
            else:
                miny = max(left.y, right.y)
                maxy = min(left.y + left.h - 1, right.y + right.h - 1)
                y = tcod.random_get_int(None, miny, maxy)

                # catch out-of-bounds attempts
                while y > MAP_HEIGHT - 1:
                         y -= 1

                hline_left(map, right.x - 1, y)
                hline_right(map, right.x, y)

    return True

def vline(map, x, y1, y2):
    if y1 > y2:
        y1,y2 = y2,y1

    for y in range(y1,y2+1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
        
def vline_up(map, x, y):
    while y >= 0 and map[x][y].blocked == True:
        map[x][y].blocked = False
        map[x][y].block_sight = False
        y -= 1
        
def vline_down(map, x, y):
    while y < MAP_HEIGHT and map[x][y].blocked == True:
        map[x][y].blocked = False
        map[x][y].block_sight = False
        y += 1
        
def hline(map, x1, y, x2):
    if x1 > x2:
        x1,x2 = x2,x1
    for x in range(x1,x2+1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
        
def hline_left(map, x, y):
    while x >= 0 and map[x][y].blocked == True:
        map[x][y].blocked = False
        map[x][y].block_sight = False
        x -= 1
        
def hline_right(map, x, y):
    while x < MAP_WIDTH and map[x][y].blocked == True:
        map[x][y].blocked = False
        map[x][y].block_sight = False
        x += 1