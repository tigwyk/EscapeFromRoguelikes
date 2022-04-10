# from config.constants import TILES_ON_SCREEN
from math import floor


class Camera:
    """Positioned in the top left corner of the game screen and follows the Party. Used by ArtistHandler to render
    tiles relative to Camera coordinates. """
    
    def __init__(self, x: int, y: int, width: int, height: int, map_width: int, map_height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height

    def refocus(self, px, py):
        """Called when Party coordinates changes, most commonly through a successful MOVE action or using a Transition
        to another Map or Dungeon. Fits to walls/corners as Party approaches."""
        (width, height) = 80,43

        # Ensures all tiles are valid to avoid bound errors/displaying "empty" tiles on potentially half of the screen
        if px < width/2:
            self.x = 0
        elif px > self.engine.game_map.width - width/2:
            self.x = self.engine.game_map.width - width
        else:
            self.x = int(px - floor(width/2))
        if py < height/2:
            self.y = 0
        elif py > self.engine.game_map.width - height/2:
            self.y = self.engine.game_map.width - height
        else:
            self.y = int(py - floor(height/2))