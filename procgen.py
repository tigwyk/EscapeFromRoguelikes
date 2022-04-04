from __future__ import annotations

import random
from uuid import uuid4
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING

import tcod

import entity_factories
from maps import GameMap
import tile_types

import numpy as np

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
    0: [(entity_factories.medkit, 35)],
    2: [(entity_factories.throwing_sand, 10), (entity_factories.combat_knife, 15), (random.choice([entity_factories.hiking_boots,entity_factories.rusty_helmet,entity_factories.body_armor]), 1)],
    4: [(entity_factories.lightning_scroll, 25), (entity_factories.sword, 5), (entity_factories.pistol, 2), (random.choice([entity_factories.hiking_boots,entity_factories.rusty_helmet,entity_factories.body_armor]), 5),(entity_factories.makarov_mag, 10)],
    6: [(entity_factories.grenade, 25), (entity_factories.body_armor, 15)],
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



def dungeon_bsp_tree(w=30, h=30, optimal_block_size=10):
    """
    Construct the dungeon map using binary space partitioning (BSP) algorithm.
    Visual
    ------
    Rectangular square-like rooms connected with 1-pixel corridors.
    These rooms evenly distributed across the map. All corridors are straight.
    Parameters
    ----------
    w : int
        Map width
    h : int
        Map height
    optimal_block_size : int
        Optimal block size. Approximately equals to room size.
    """

    M = Map(w, h, fill_cell=C.wall_dungeon_rough)
    nodes = {}
    root = BSPNode('v', 1, 1, w - 1, h - 1)
    _recursive_split_tree_node(root, optimal_block_size)
    _load_leafs(root, nodes)
    _fill_rooms(M, nodes.values())
    all_edges = _get_all_edges(nodes.values())
    st_edges = _construct_spanning_tree(list(nodes.keys()), all_edges)
    _create_corridors(M, nodes, st_edges)
    return M


class BSPNode(object):
    """
    Class for BSP-tree nodes.
    """

    def __init__(self, xy_type, x, y, w, h, children=None):
        # UUID
        self.uid = uuid4()

        # Type of node
        # 'v' means that this node should be splitted vertically
        # 'h' means that this node should be splitted horizontally
        self.xy_type = xy_type

        # Parameters of the BSP block
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        # Parameters of the room inside the block, if exists
        self.room_x1 = None
        self.room_y1 = None
        self.room_x2 = None
        self.room_y2 = None

        # Node children, if exists
        self.children = children

    def create_room(self):
        self.room_x1 = random.randint(
            int(self.x + 0.1 * self.w),
            int(self.x + 0.2 * self.w)
        )
        self.room_y1 = random.randint(
            int(self.y + 0.1 * self.h),
            int(self.y + 0.2 * self.h)
        )
        self.room_x2 = random.randint(
            int(self.x + 0.8 * self.w),
            int(self.x + 0.9 * self.w)
        )
        self.room_y2 = random.randint(
            int(self.y + 0.8 * self.h),
            int(self.y + 0.9 * self.h)
        )


def _recursive_split_tree_node(bsp_node, optimal_block_size):
    """
    Make binary space partitioning of the map.
    Partitioning stops when the current node has width/height no more than
    1.5 of the `optimal_block_size` and width/height no more than twice larger
    than height/width.
    """

    if bsp_node.xy_type == 'v':
        if bsp_node.w > int(optimal_block_size * 1.5) or bsp_node.w > 2 * bsp_node.h:
            w_child = random.randint(int(bsp_node.w * 0.25), int(bsp_node.w * 0.75))
            child_left = BSPNode(
                'h',
                bsp_node.x,
                bsp_node.y,
                w_child,
                bsp_node.h
            )
            child_right = BSPNode(
                'h',
                bsp_node.x + w_child,
                bsp_node.y,
                bsp_node.w - w_child,
                bsp_node.h
            )
            bsp_node.children = [child_left, child_right]
            _recursive_split_tree_node(child_left, optimal_block_size)
            _recursive_split_tree_node(child_right, optimal_block_size)
        else:
            bsp_node.create_room()
    elif bsp_node.xy_type == 'h':
        if bsp_node.h > int(optimal_block_size * 1.5) or bsp_node.h > 2 * bsp_node.w:
            h_child = random.randint(int(bsp_node.h * 0.25), int(bsp_node.h * 0.75))
            child_top = BSPNode(
                'v',
                bsp_node.x,
                bsp_node.y,
                bsp_node.w,
                h_child
            )
            child_bottom = BSPNode(
                'v',
                bsp_node.x,
                bsp_node.y + h_child,
                bsp_node.w,
                bsp_node.h - h_child
            )
            bsp_node.children = [child_top, child_bottom]
            _recursive_split_tree_node(child_top, optimal_block_size)
            _recursive_split_tree_node(child_bottom, optimal_block_size)
        else:
            bsp_node.create_room()


def _load_leafs(bsp_node, leafs):
    """
    Collect all leaf nodes in the BSP-tree and put them in the list.
    """

    if bsp_node.children:
        _load_leafs(bsp_node.children[0], leafs)
        _load_leafs(bsp_node.children[1], leafs)
    else:
        leafs[bsp_node.uid] = bsp_node


def _fill_rooms(M, nodes):
    """
    Fill map with rooms given from leaf nodes of BSP-tree.
    """

    for node in nodes:
        for y in range(node.room_y1, node.room_y2):
            for x in range(node.room_x1, node.room_x2):
                M[x, y] = C.floor()


def _get_all_edges(bsp_nodes):
    """
    Get all possible straight edges between rooms in leaf nodes of BSP-tree.
    """

    all_edges = []
    for n1 in bsp_nodes:
        for n2 in bsp_nodes:
            if n1.uid == n2.uid:
                continue
            n1_x2 = n1.x + n1.w
            n1_y2 = n1.y + n1.h
            n2_x2 = n2.x + n2.w
            n2_y2 = n2.y + n2.h
            max_rx1 = max(n1.room_x1, n2.room_x1)
            max_ry1 = max(n1.room_y1, n2.room_y1)
            min_rx2 = min(n1.room_x2, n2.room_x2)
            min_ry2 = min(n1.room_y2, n2.room_y2)
            if ((n1.y == n2_y2 or n1_y2 == n2.y) and
                    (max_rx1 < min_rx2) and
                    min(n1_x2, n2_x2) - max(n1.x, n2.x) > 0.6 * min(n1.w, n2.w)):
                all_edges.append((n1.uid, n2.uid))
            elif ((n1.x == n2_x2 or n1_x2 == n2.x) and
                    (max_ry1 < min_ry2) and
                    min(n1_y2, n2_y2) - max(n1.y, n2.y) > 0.6 * min(n1.h, n2.h)):
                all_edges.append((n1.uid, n2.uid))
    return all_edges


def _construct_spanning_tree(nodes, edges):
    """
    Construct spanning tree of edges graph using Prim's
    (also known as Jarník's) algorithm.
    """

    nodes_to_process = set(nodes)
    first_edge = random.choice(edges)
    st_nodes = [first_edge[0], first_edge[1]]
    st_edges = [first_edge]
    nodes_to_process.remove(first_edge[0])
    nodes_to_process.remove(first_edge[1])
    while nodes_to_process:
        node_uid = random.choice(st_nodes)
        for edge in filter(lambda e: node_uid in e, edges):
            second_node_uid = (
                edge[0]
                if node_uid == edge[1]
                else edge[1]
            )
            if second_node_uid in nodes_to_process:
                st_nodes.append(second_node_uid)
                st_edges.append(edge)
                nodes_to_process.remove(second_node_uid)
                break
    return st_edges


def _create_corridors(M, nodes, edges):
    """
    Create corridors between rooms that should be connected.
    """

    for edge in edges:
        n1 = nodes[edge[0]]
        n2 = nodes[edge[1]]
        if max(n1.room_x1, n2.room_x1) < min(n1.room_x2, n2.room_x2):
            x = random.randint(
                max(n1.room_x1, n2.room_x1),
                min(n1.room_x2, n2.room_x2)
            )
            for y in range(min(n2.room_y2, n1.room_y1), max(n2.room_y2, n1.room_y1)):
                M[x, y] = C.floor()
        elif max(n1.room_y1, n2.room_y1) < min(n1.room_y2, n2.room_y2):
            y = random.randint(
                max(n1.room_y1, n2.room_y1),
                min(n1.room_y2, n2.room_y2)
            )
            for x in range(min(n2.room_x2, n1.room_x1), max(n2.room_x2, n1.room_x1)):
                M[x, y] = C.floor()