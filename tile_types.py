from typing import Tuple

import numpy as np  # type: ignore

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # Unicode codepoint.
        ("fg", "3B"),  # 3 unsigned bytes, for RGB colors.
        ("bg", "3B"),
    ]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("walkable", np.bool),  # True if this tile can be walked over.
        ("transparent", np.bool),  # True if this tile doesn't block FOV.
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light", graphic_dt),  # Graphics for when the tile is in FOV.
    ]
)

def new_tile(
    *,  # Enforce the use of keywords, so that parameter order doesn't matter.
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

wall_tile = 256 
floor_tile = 257
player_tile = 258
orc_tile = 259
troll_tile = 260
scroll_tile = 261
healingpotion_tile = 262
sword_tile = 263
shield_tile = 264
# stairsdown_tile = 265
stairsdown_tile = ord('>')
dagger_tile = 266

floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (50, 50, 150)),
    light=(ord(" "), (255, 255, 255), (200, 180, 50)),
    # dark=(floor_tile, (255, 255, 255), (50, 50, 150)),
    # light=(floor_tile, (255, 255, 255), (200, 180, 50)),
)
wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord(" "), (255, 255, 255), (0, 0, 100)),
    light=(ord(" "), (255, 255, 255), (130, 110, 50)),
    # dark=(wall_tile, (255, 255, 255), (0, 0, 100)),
    # light=(wall_tile, (255, 255, 255), (130, 110, 50)),
)
down_stairs = new_tile(
    walkable=True,
    transparent=True,
    # dark=(ord(">"), (0, 0, 100), (50, 50, 150)),
    # light=(ord(">"), (255, 255, 255), (200, 180, 50)),
    dark=(stairsdown_tile, (0, 0, 100), (50, 50, 150)),
    light=(stairsdown_tile, (255, 255, 255), (200, 180, 50)),
)

beach = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (122, 122, 104)),
    light=(ord(" "), (255, 255, 255), (255, 253, 208)),
)
swamp = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (114, 135, 0)),
    light=(ord(" "), (255, 255, 255), (167, 191, 147)),
)
plains = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (102,51,0)),
    light=(ord(" "), (255, 255, 255), (187,153,102)),
)
forest = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("♠"), (0,128,0), (0,50,0)),
    light=(ord("♠"), (0, 100, 0), (0,128,0)),
)
hills = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("^"), (200, 180, 50), (70, 60, 50)),
    light=(ord("^"), (200, 180, 50), (130, 110, 50)),
)
mountains = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("^"), (255, 255, 255), (50, 50, 150)),
    light=(ord("^"), (255, 255, 255), (200, 180, 50)),
)
ocean = new_tile(
    walkable=False,
    transparent=False,
    # dark=(ord(" "), (255, 255, 255), (0, 0, 100)),
    # light=(ord(" "), (255, 255, 255), (130, 110, 50)),
    dark=(wall_tile, (255, 255, 255), (1, 106, 134)),
    light=(wall_tile, (255, 255, 255), (0, 84, 119)),
)