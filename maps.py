from __future__ import annotations

from typing import Iterable, Iterator, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console
import tcod.noise
import tcod.color
from random import randint
import itertools

import urizen as uz

from scipy.spatial import cKDTree as KDTree

from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

class Tile:

    def __init__(self, height,temp,precip,drainage, biome):
        self.temp = temp
        self.height = height
        self.precip = precip
        self.drainage = drainage
        self.biome = biome
        
    hasRiver = False
    isCiv = False

    biomeID = 0
    prosperity = 0

class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player has seen before

        self.downstairs_location = (0, 0)
    
    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this maps living actors."""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )
    
    @property
    def enemies(self) -> Iterator[Actor]:
        """Iterate over this maps living actors."""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive and entity != self.engine.player
        )

    @property
    def items(self) -> Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_size(self):
        return self.width, self.height

    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int,
    ) -> Optional[Entity]:
        for entity in self.entities:
            if (
                entity.blocks_movement
                and entity.x == location_x
                and entity.y == location_y
            ):
                return entity
        
        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor

        return None
    
    def find_closest_kdtree(self, character: Actor, enemies: KDTree) -> Tuple[int, int]:
        """
        Finds the closest enemy in enemies

        :param character: An (x, y) representing the position of the character\n
        :param enemies: A KDTree that represent enemies

        :return: A tuple (x, y) of the closest enemy
        """
        _, i = enemies.query([(character.x,character.y)], 1)
        return i[0]

    def find_closest_enemy_radius(self, character: Actor, enemies: KDTree, radius: int) -> Tuple[int, int]:
        
        i = enemies.query_ball_point((character.x, character.y),radius)
        if(i):
            # print(f"find_closest_enemy_radius {i[0]}")
            return i[0]
        else:
            # print(f"find_closest_enemy_radius None")
            return None

    def update_enemies_tree(self):
        if(len(list(self.engine.game_map.enemies))):
            self.engine.game_map.enemies_tree = KDTree([(e.x,e.y) for e in self.engine.game_map.enemies])
        else:
            self.engine.game_map.enemies_tree = None

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, then draw it with the "light" colors.
        If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
        Otherwise, the default is "SHROUD".
        """
        console.tiles_rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            # Only print entities that are in the FOV
            if self.visible[entity.x, entity.y]:
                console.print(
                    x=entity.x, y=entity.y, string=entity.char, fg=entity.color
                )

class DungeonWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 0
    ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.current_floor = current_floor

    def generate_floor(self) -> None:
        from procgen import generate_dungeon

        self.current_floor += 1

        self.engine.game_map = generate_dungeon(
            max_rooms=self.max_rooms,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            engine=self.engine,
        )
        # print(f"floor {self.current_floor} entities: {[i.name for i in self.engine.game_map.enemies]}")
        # print(f"floor {self.current_floor} items: {[i.name for i in self.engine.game_map.items]}")
        self.engine.game_map.update_enemies_tree()
        # print(f"floor {self.current_floor} enemies_tree: {self.engine.game_map.enemies_tree}")

class OverWorldGenerator(object):
  """Randomly generates a new world with terrain and objects"""
  def __init__(
            self,
            *,
            engine: Engine,
            map_width: int,
            map_height: int,
            current_floor: int = 0
        ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.current_floor = current_floor


  def generate_world(self):
    from procgen import generate_overworld
    """Randomly generate a new world with some water, swamps, hills, some objects etc"""

    self.engine.game_map = generate_overworld(
        map_width=self.map_width,
        map_height=self.map_height,
        engine=self.engine,
    )

  