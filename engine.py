from __future__ import annotations

import lzma
import pickle
from datetime import datetime
from pathlib import Path
import os.path
from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import exceptions
from message_log import MessageLog
import render_functions
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld

class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible


    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)

        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        render_functions.render_bunker_level(
            console=console,
            bunker_level=self.game_world.current_floor,
            location=(0, 47),
        )

        render_functions.render_rouble_amount(
            console=console,
            roubles=self.player.currency.roubles,
            location=(0, 48),
        )
        if self.player.equipment.weapon != None and self.player.equipment.weapon.equippable.equipment_type == EquipmentType.RANGED_WEAPON:
            render_functions.render_ammo_status(
                console=console,
                ammo=self.player.equipment.weapon.equippable.ammo,
                max_ammo=self.player.equipment.weapon.equippable.max_ammo,
                location=(0, 49),
            )

        render_functions.render_names_at_mouse_location(
            console=console, x=21, y=44, engine=self
        )
    
    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)

    def dump_character_log(self) -> None:
        post_mortem_path = 'mortem'
        try:
            Path(post_mortem_path).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        save_filename = '['+datetime.now(tz=None).strftime("%m-%d-%Y %H-%M-%S")+'] '+self.player.name+'.txt'
        with open(os.path.join(post_mortem_path,save_filename), 'w') as post_mortem:
            killer = self.player.fighter.killer
            post_mortem_header_text = """
--------------------------------------------------------------
 L.U.R.K.E.R. (0.1.2) roguelike post-mortem character dump
--------------------------------------------------------------
"""
            post_mortem_lines = []
            post_mortem_lines.append(f' {self.player.name}, level {self.player.level.current_level} Human L.U.R.K.E.R.\n')
            if killer != None:
                post_mortem_lines.append(f' was murdered by {killer.name}, a level {killer.level.current_level}\n')
            else:
                post_mortem_lines.append(f' was murdered by the invisible forces of the zone\n')
            post_mortem_lines.append('\n')
            post_mortem_lines.append('-- Special levels --------------------------------------------\n\n')
            post_mortem_lines.append(f' Bunker levels generated : {self.game_world.current_floor}\n\n')
            post_mortem_lines.append('-- Awards ----------------------------------------------------\n\n')
            post_mortem_lines.append(' None\n\n')
            post_mortem_lines.append('-- Graveyard -------------------------------------------------\n\n')
            post_mortem_lines.append(' None\n\n')
            post_mortem_lines.append('-- Statistics ------------------------------------------------\n\n')
            post_mortem_lines.append(f' Health {self.player.fighter.hp}/{self.player.fighter.max_hp}  Experience {self.player.level.current_xp}\n')
            post_mortem_lines.append(f' Base power {self.player.fighter.base_power}  Base defense {self.player.fighter.base_defense}\n')
            post_mortem_lines.append(f'\n')
            post_mortem_lines.append('-- Traits ----------------------------------------------------\n\n')
            post_mortem_lines.append(' None\n\n')
            post_mortem_lines.append('-- Equipment -------------------------------------------------\n\n')
            post_mortem_lines.append(f' [a] [ Armor      ]   {self.player.equipment.armor.name if self.player.equipment.armor else None}\n')
            if(self.player.equipment.weapon.equippable.equipment_type == EquipmentType.RANGED_WEAPON):
                ammo_text = f'[{self.player.equipment.weapon.equippable.ammo}/{self.player.equipment.weapon.equippable.max_ammo}]'
            else:
                ammo_text = f''
            post_mortem_lines.append(f' [b] [ Weapon     ]   {self.player.equipment.weapon.name if self.player.equipment.weapon else None} {ammo_text}\n')
            post_mortem_lines.append(f' [c] [ Legs       ]   {self.player.equipment.legs.name if self.player.equipment.legs else None}\n')
            post_mortem_lines.append(f' [d] [ Feet       ]   {self.player.equipment.feet.name if self.player.equipment.feet else None}\n')
            post_mortem_lines.append('\n')
            post_mortem_lines.append('-- Inventory -------------------------------------------------\n\n')
            names_only_inventory_list = [i.name for i in self.player.inventory.items]
            counted_inventory_list = {i:(names_only_inventory_list).count(i) for i in names_only_inventory_list}
            unique_inventory_list = set(counted_inventory_list.keys())
            for item in unique_inventory_list:
                count = 'x'+str(counted_inventory_list[item]) if counted_inventory_list[item] >= 2 else f''
                post_mortem_lines.append(f' {item} {count}\n')
            post_mortem_lines.append('\n')
            post_mortem_lines.append('-- Resistances -----------------------------------------------\n\n')
            post_mortem_lines.append(' None\n\n')
            post_mortem_lines.append('-- Kills -----------------------------------------------------\n\n')
            for victim in self.player.fighter.victims:
                post_mortem_lines.append(f' {victim.name}')
            post_mortem_lines.append('-- History ---------------------------------------------------\n\n')
            post_mortem_lines.append(' None\n\n')
            post_mortem_lines.append('-- Messages --------------------------------------------------\n\n')
            for log_message in self.message_log.messages:
                post_mortem_lines.append(f' {log_message.full_text}\n')
            post_mortem_lines.append('-- General ---------------------------------------------------\n\n')
            #post_mortem_lines.append(' 2 brave souls have ventured into Phobos:\n')
            #post_mortem_lines.append('  2 of those were killed.\n')

            post_mortem.write(post_mortem_header_text)
            post_mortem.writelines(post_mortem_lines)
            post_mortem.close()
            self.display_postmortem_log(save_filename)

    def display_postmortem_log(self, filename):
        print(filename)
        pass
                