from __future__ import annotations

from typing import Iterable, Iterator, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console
import tcod.noise
import tcod.color
from random import randint
import itertools

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
            print(f"find_closest_enemy_radius {i[0]}")
            return i[0]
        else:
            print(f"find_closest_enemy_radius None")
            return None

    def update_enemies_tree(self):
        self.engine.game_map.enemies_tree = KDTree([(e.x,e.y) for e in self.engine.game_map.enemies])

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
        print(f"floor {self.current_floor} entities: {[i.name for i in self.engine.game_map.enemies]}")
        print(f"floor {self.current_floor} items: {[i.name for i in self.engine.game_map.items]}")
        # self.engine.game_map.enemies_tree = KDTree([(e.x,e.y) for e in self.engine.game_map.enemies])
        self.engine.game_map.update_enemies_tree()
        print(f"floor {self.current_floor} enemies_tree: {self.engine.game_map.enemies_tree}")

class OverWorldGenerator(object):
  """Randomly generates a new world with terrain and objects"""
  def __init__(
            self,
            *,
            engine: Engine,
            map_width: int,
            map_height: int,
        ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height


  def regular(self):
    from procgen import generate_overworld
    """Randomly generate a new world with some water, swamps, hills, some objects etc"""

    idx = [ 0 , 15, 75, 90, 101 ] # indexes of the keys 
    col = [ tcod.color.Color(0,100,100),
            tcod.color.Color(0,75,0), 
            tcod.color.Color(50,150,0), 
            tcod.color.Color(150,120,80), 
            tcod.color.Color(180,180,180)]

    map=tcod.color_gen_map(col,idx)

    tiles = zip(idx, [[tile_types.swamp, tile_types.plains],
                      [tile_types.plains, tile_types.forest], 
                      [tile_types.hills, tile_types.forest],
                      [tile_types.hills, tile_types.hills, tile_types.mountains],
                      [tile_types.hills, tile_types.mountains,tile_types.mountains]])

    self.engine.game_map = self.__generate(map, tiles)
    
  def __generate(self, colormap, mtiles, noise_zoom=1, noise_octaves=10):
    WORLD_WIDTH = self.map_width
    WORLD_HEIGHT = self.map_height
    SCALE = noise_zoom*1.0

    map = GameMap(self.engine, self.map_width, self.map_height, entities=[self.engine.player])

    noise = tcod.noise.Noise(
        dimensions=2,
        algorithm=tcod.noise.Algorithm.SIMPLEX,
        seed=42
    )

    hm = noise[tcod.noise.grid(shape=(map.width,map.height), scale=SCALE)]
    hm1 = noise[tcod.noise.grid(shape=(map.width,map.height), scale=SCALE)]
    hm2 = noise[tcod.noise.grid(shape=(map.width,map.height), scale=SCALE)]
    
    hm[:] = hm1[:] * hm2[:]
    hm = (hm + 1.0) * 0.5 #normalize
    print(f"Normalized heightmap: {hm}")

    #Initialize Tiles with Map values

    # make coordinate grid on [0,1]^2
    x_idx = np.linspace(0, 1, map.width)
    y_idx = np.linspace(0, 1, map.height)
    world_x, world_y = np.meshgrid(x_idx, y_idx)

    map.tiles = np.zeros((map.width,map.height))
    # apply perlin noise, instead of np.vectorize, consider using itertools.starmap()
    map.tiles = itertools.starmap(noise.get_point, (map.width/SCALE,map.height/SCALE))
    print('- Tiles Initialized -')
    print(map)
    # for x in range(map.width):
    #     for y in range(map.height):
    #         print(f"Coords: {x},{y}")
    #         print(f"World Tile: {map.tiles.next()}")
            
            # if World[x][y].height <= 0.2:
            #     World[x][y].biomeID = 0

            # if World[x][y].temp <= 0.2 and World[x][y].height > 0.15:
            #     World[x][y].biomeID = randint(11,13)

            # if World[x][y].height > 0.6:
            #     World[x][y].biomeID = 9
            # if World[x][y].height > 0.9:
            #     World[x][y].biomeID = 10
                  
            
    print('- BiomeIDs Atributed -')

    return map

  