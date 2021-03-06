"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

import copy
import lzma
import pickle
import traceback
from turtle import back
from typing import Optional
from main import main
from sound import Sound

import tcod

import color
from engine import Engine
import entity_factories
from maps import GameWorld
import input_handlers

from skill import handguns, rifles, shotguns, medical, blades

from russian_names import RussianNames

import procgen

# Load the background image and remove the alpha channel.
# background_image = tcod.image.load(".\img\menu_background.png")[:, :, :3]
background_image = tcod.image.load(".\img\menu_background2.png")[:, :, :3]


def new_game() -> Engine:
    """Return a brand new game session as an Engine instance."""
    # map_width = 80
    # map_height = 43

    WIDTH = 50
    HEIGHT = 50
    
    viewport_width = WIDTH
    viewport_height = HEIGHT

    room_max_size = 25
    room_min_size = 8
    max_rooms = 75

    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)
    
    engine.game_rules = procgen.load_rules()

    # print(f"Game rules: {engine.game_rules}")
    # for i in range(0,10):
    #     print(engine.game_rules.flatten(f"{i+1}. {player.name}#fake_postmortem#"))

    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
    )
    engine.game_world.generate_overworld()
    # engine.game_world.generate_floor()
    engine.update_fov()
    engine.update_light_levels()
    
    engine.game_world.generate_factions()

    engine.message_log.add_message(
        "Welcome to L.U.R.K.E.R.", color.welcome_text
    )

    engine.message_log.add_message(
        f"You are {player.name}, a {player.role.name.capitalize()}.", color.red
    )

    engine.sound.play_music(engine.game_map.music)

    knife = copy.deepcopy(entity_factories.kitchen_knife)
    # sword = copy.deepcopy(entity_factories.sword)
    shirt = copy.deepcopy(entity_factories.shirt)
    pistol = copy.deepcopy(entity_factories.pistol)

    # handguns_skill = copy.deepcopy(handguns)
    # rifles_skill = copy.deepcopy(rifles)
    # shotguns_skill = copy.deepcopy(shotguns)
    # medical_skill = copy.deepcopy(medical)
    # blade_skill = copy.deepcopy(blades)

    # starting_skills = {handguns_skill, rifles_skill, shotguns_skill, medical_skill, blade_skill}

    for skill in player.role.base_skills:
        player.skills.learn(skill)

    knife.parent = player.inventory
    shirt.parent = player.inventory
    pistol.parent = player.inventory
    # sword.parent = player.inventory

    player.inventory.items.append(knife)
    player.equipment.toggle_equip(knife, add_message=False)

    player.inventory.items.append(shirt)
    player.equipment.toggle_equip(shirt, add_message=False)

    player.inventory.items.append(pistol)
    player.equipment.toggle_equip(pistol, add_message=False)

    # player.inventory.items.append(sword)
    # player.equipment.toggle_equip(sword, add_message=False)

    # player.lore.previous_job = procgen.random_occupation(engine)

    return engine


def load_game(filename: str) -> Engine:
    """Load an Engine instance from a file."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine

class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def __init__(self):
        self.sound = Sound()
        self.main_menu_music = self.sound.play_music("main_menu")
        # self.sound.test_sound()

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "L.U.R.K.E.R.",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )
        console.print(
            # console.width // 2,
            4,
            console.height - 2,
            "By Tigwyk",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(
            ["[N] Play a new game", "[C] Continue last game", "[Q] Quit"]
        ):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=tcod.CENTER,
                bg_blend=tcod.BKGND_ALPHA(64),
            )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.K_c:
            try:
                self.main_menu_music.stop()
                return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()  # Print to stderr.
                return input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")
        elif event.sym == tcod.event.K_n:
            self.sound.play_sound('new_game', volume=0.7)
            self.main_menu_music.stop()
            return input_handlers.MainGameEventHandler(new_game())

        return None