from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

import color
import tcod

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from maps import GameMap

def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""

    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()

def render_bar(
    console: Console, current_value: int, maximum_value: int, total_width: int, location: Tuple[int, int], caption: str, bar_text_color: Tuple(int, int, int), bar_fill_color: Tuple(int, int, int), bar_empty_color: Tuple(int, int, int)
) -> None:
    bar_width = int(float(current_value) / maximum_value * total_width)
    x, y = location
    console.draw_rect(x=x, y=y, width=total_width, height=1, ch=1, bg=bar_empty_color)

    if bar_width > 0:
        console.draw_rect(
            x=x, y=y, width=bar_width, height=1, ch=1, bg=bar_fill_color
        )

    console.print(
        x=x+1, y=y, string=f"{caption}: {current_value}/{maximum_value}", fg=bar_text_color
    )

def render_bunker_level(
    console: Console, bunker_level: int, location: Tuple[int, int]
) -> None:
    """
    Render the level the player is currently on, at the given location.
    """
    x, y = location

    console.print(x=x, y=y, string=f"Bunker level: {bunker_level}")

def render_rouble_amount(
    console: Console, roubles: int, location: Tuple[int, int]
) -> None:
    """
    Render the player's rouble amount.
    """
    x, y = location
    console.print(x=x, y=y, string=f"Rs:")
    console.print(x=x+4, y=y, string=f"{roubles}", fg=color.roubles_display_text)

def render_ammo_status(
    console: Console, ammo: int, max_ammo: int, location: Tuple[int, int]
) -> None:
    """
    Render the player's weapon ammo status.  
    """
    x, y = location
    ammo_color = color.red if ammo == 0 else color.white
    if(max_ammo == 0):
        return
    console.print(x=x, y=y, string=f"Ammo: {ammo}/{max_ammo}", fg=ammo_color)

def render_coordinates(
    console: Console, coords: Tuple[int, int], location: Tuple[int, int]
) -> None:
    """
    Render the player's weapon ammo status.  
    """
    x, y = location
    xx, yy = coords
    console.print(x=x, y=y, string=f"({xx},{yy})", fg=color.white)

def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.mouse_location

    viewport = engine.game_map.get_viewport()
    map_x = mouse_x + viewport[0]
    map_y = mouse_y + viewport[1]

    names_at_mouse_location = get_names_at_location(
        x=map_x,y=map_y, game_map=engine.game_map
    )
    if names_at_mouse_location:
        # Tooltip to render names
        x = mouse_x - (len(names_at_mouse_location) // 2) - 1
        if x < 0:
            x = 0
        elif x + len(names_at_mouse_location) + 2 > console.width - 1:
            x = console.width - len(names_at_mouse_location) - 3

        if mouse_y <= 3:
            y = mouse_y + 1
        else:
            y = mouse_y - 3

        draw_window(console, x, y, len(names_at_mouse_location) + 2, 3,'')

    console.print(x=x+1,y=y+1, string=names_at_mouse_location)

def draw_window(console, x, y, width, height, title):
  console.draw_frame(
      x=x,
      y=y,
      width=width,
      height=height,
      title='',
      clear=True,
      fg=color.window_border_bright,
      bg=(0, 0, 0),
  )

  r_bright, g_bright, b_bright = color.window_border_bright
  r_dark, g_dark, b_dark = color.window_border_dark
  r_step = (r_bright - r_dark) // 10
  g_step = (g_bright - g_dark) // 10
  b_step = (b_bright - b_dark) // 10
  x1 = x + width - 1
  y1 = y + height - 1
  
  for i in range(0, 11):
    r = r_dark + (r_step * i)
    g = g_dark + (g_step * i)
    b = b_dark + (b_step * i)
    if i <= width // 2:
      console.tiles_rgb['fg'][x+i,y] = (r,g,b)
      console.tiles_rgb['fg'][x1-i,y] = (r,g,b)
      console.tiles_rgb['fg'][x1-i,y1] = (r,g,b)
      console.tiles_rgb['fg'][x+i,y1] = (r,g,b)
    if i <= height // 2:
      console.tiles_rgb['fg'][x,y+i] = (r,g,b)
      console.tiles_rgb['fg'][x1,y+i] = (r,g,b)
      console.tiles_rgb['fg'][x1,y1-i] = (r,g,b)
      console.tiles_rgb['fg'][x,y1-i] = (r,g,b)

  if title:
    console.print_box(x=x, y=y, width=width, height=1, fg=color.window_border_bright, string=f'┤{title}├', alignment=tcod.CENTER)