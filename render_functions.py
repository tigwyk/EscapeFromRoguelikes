from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

import color

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
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    bar_width = int(float(current_value) / maximum_value * total_width)

    console.draw_rect(x=0, y=45, width=total_width, height=1, ch=1, bg=color.bar_empty)

    if bar_width > 0:
        console.draw_rect(
            x=0, y=45, width=bar_width, height=1, ch=1, bg=color.bar_filled
        )

    console.print(
        x=1, y=45, string=f"HP: {current_value}/{maximum_value}", fg=color.bar_text
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

    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    console.print(x=x, y=y, string=names_at_mouse_location)