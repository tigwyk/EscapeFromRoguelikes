from __future__ import annotations

from typing import Iterable, Iterator, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console
import tcod.noise
import tcod.color
from random import randint
import itertools
import math

from pprint import pprint

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

        self.light_levels = np.full((width, height), fill_value=1.0, order="F")

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

    @property
    def lights(self):
        yield from(entity for entity in self.entities if entity.light_source and entity.light_source.radius > 0)

    def get_size(self):
        return self.width, self.height

    def reveal_map(self):
        self.explored = np.full((self.width, self.height), fill_value=True, order="F")

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
    
    def get_viewport(self):
        x = self.engine.player.x
        y = self.engine.player.y
        width = self.engine.game_world.viewport_width
        height = self.engine.game_world.viewport_height
        half_width = int(width / 2)
        half_height = int(height / 2)
        origin_x = x - half_width
        origin_y = y - half_height
        # print(f'player: ({x}, {y}), modifier: {half_width}, {half_height}, origin: ({origin_x}, {origin_y})')
        if origin_x < 0:
            origin_x = 0
        if origin_y < 0:
            origin_y = 0

        end_x = origin_x + width
        end_y = origin_y + height
        #print(f'End: ({end_x},{end_y})')
        if end_x > self.width:
            x_diff = end_x - self.width
            origin_x -= x_diff
            end_x    -= x_diff

        if end_y > self.height:
            y_diff = end_y - self.height
            origin_y -= y_diff
            end_y    -= y_diff
        return ((origin_x, origin_y, end_x-1, end_y-1))

    def get_coords_in_radius(self, x, y, radius):
        coords = []
        for tx in range(x-radius, x+radius+1):
            for ty in range(y-radius, y+radius+1):
                if math.sqrt((x - tx) ** 2 + (y - ty) **2) <= radius and self.in_bounds(tx, ty):
                    coords.append((tx,ty))
        return coords

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

        o_x, o_y, e_x, e_y = self.get_viewport()
        s_x = slice(o_x, e_x+1)
        s_y = slice(o_y,e_y+1)
        viewport_tiles    = self.tiles[s_x,s_y]#[o_x:e_x+1,o_y:e_y + 1]
        viewport_visible  = self.visible[s_x,s_y]
        viewport_explored = self.explored[s_x,s_y]

        # print(f'({o_x},{o_y}), ({e_x},{e_y})')
        # print(f'Viewport Tiles: ({len(viewport_tiles)},{len(viewport_tiles[0])})')
        # print(f'Viewport Visible: ({len(viewport_visible)},{len(viewport_visible[0])})')
        # print(f'Viewport Explored: ({len(viewport_explored)},{len(viewport_explored[0])})')

        console.tiles_rgb[0 : self.engine.game_world.viewport_width, 0 : self.engine.game_world.viewport_height] = np.select(
            condlist=[viewport_explored],
            choicelist=[viewport_tiles["dark"]],
            default=tile_types.SHROUD,
        )

        player = self.engine.player
        # Add our player light to our light map
        light_levels = self.light_levels.copy()
        viewport_light_levels = light_levels[s_x,s_y]
        visible_light_levels = np.select(condlist=[viewport_visible], choicelist=[viewport_light_levels], default=1)
        # Try some more dynamic lighting
        lit = np.where(visible_light_levels < 1.0)
        #print(lit)
        #print(f'Player is at ({self.engine.player.x},{self.engine.player.y}).  These tile are lit: {lit}')

        for i in range(len(lit[0])):
            x, y = lit[0][i], lit[1][i]
            brightness_diff = visible_light_levels[x][y]
            #distance = self.engine.player.distance(x + o_x, y + o_y)
            #brightness_diff = distance / (self.engine.player.visibility+2)
            #print(f'({x},{y}) is lit, translated to ({x-o_x},{y-o_y}) in viewport.  Distance to player: {distance}.')
            light_fg = viewport_tiles[x][y]['light']['fg']
            light_bg = viewport_tiles[x][y]['light']['bg']
            dark_fg = viewport_tiles[x][y]['dark']['fg']
            dark_bg = viewport_tiles[x][y]['dark']['bg']
            new_fg = []
            new_bg = []
            for j in range(0,3):
                new_fg.append(light_fg[j] - int((light_fg[j] - dark_fg[j]) * brightness_diff))
                new_bg.append(light_bg[j] - int((light_bg[j] - dark_bg[j]) * brightness_diff))
            #print(f'Light fg:{light_fg}, bg:{light_bg}, Dark fg:{dark_fg}, bg{dark_bg}.  Multiplier: {brightness_diff}.  New fg:{new_fg}, bg:{new_bg}')
            console.tiles_rgb['bg'][x,y] = tuple(new_bg)
            console.tiles_rgb['fg'][x,y] = tuple(new_fg)

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            # Only print entities that are in the FOV
            if self.visible[entity.x, entity.y] and light_levels[entity.x][entity.y] < 1:
                console.print(
                    x=entity.x - o_x,
                    y=entity.y - o_y,
                    string=entity.char, 
                    fg=entity.color,
                )

class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        # map_width: int,
        # map_height: int,
        viewport_width: int,
        viewport_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 0
    ):
        self.engine = engine

        # self.map_width = map_width
        # self.map_height = map_height
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self.min_map_width = viewport_width
        self.min_map_height = viewport_height
        
        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.current_floor = current_floor

    def generate_overworld(self):
        from procgen import generate_random_overworld
        """Randomly generate a new world with some water, swamps, hills, some objects etc"""

        self.engine.game_map = generate_random_overworld(
            map_width=self.min_map_width,
            map_height=self.min_map_height,
            engine=self.engine,
        )
    def generate_floor(self) -> None:
        from procgen import generate_bsp_dungeon
        from procgen import generate_dungeon

        self.current_floor += 1

        random_map_width = randint(self.min_map_width, self.min_map_width+128)
        random_map_height = randint(self.min_map_height, self.min_map_height+128)
        
        if(self.current_floor % 3):
            self.engine.game_map = generate_dungeon(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=random_map_width,
                map_height=random_map_height,
                engine=self.engine,
            )
        else:
            self.engine.game_map = generate_bsp_dungeon(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=random_map_width,
                map_height=random_map_height,
                engine=self.engine,
            )
        # print(f"floor {self.current_floor} entities: {[i.name for i in self.engine.game_map.enemies]}")
        # print(f"floor {self.current_floor} items: {[i.name for i in self.engine.game_map.items]}")
        self.engine.game_map.update_enemies_tree()
        # print(f"floor {self.current_floor} enemies_tree: {self.engine.game_map.enemies_tree}")