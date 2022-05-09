from __future__ import annotations

import lzma
import pickle
import random
from datetime import datetime
from pathlib import Path
import os.path
from typing import TYPE_CHECKING
from components.equipment import Equipment

import tcod
from tcod.console import Console
from tcod.map import compute_fov
import color

import exceptions
from message_log import MessageLog
import render_functions
from equipment_types import EquipmentType
from sound import Sound

if TYPE_CHECKING:
    from entity import Actor
    from maps import GameMap, GameWorld
    from camera import Camera


class Engine:
    game_map: GameMap
    game_world: GameWorld
    camera: Camera
    sound: Sound

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        self.game_rules = None
        self.sound = Sound()

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            self.update_light_levels()
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
            radius=self.player.visibility,
            algorithm=tcod.FOV_BASIC
        )
        # If a tile is "visible" it should be added to "explored".
        # self.game_map.explored |= self.game_map.visible

    def update_light_levels(self):
        """ Create our light map for all static light entities """
        self.game_map.light_levels[:] = 1
        for light in [self.player]:
            if light == self.player:
                light_walls = True
            else:
                light_walls = self.game_map.visible[light.x][light.y]
            coords = self.game_map.get_coords_in_radius(light.x, light.y, light.light_source.radius)
            light_fov = compute_fov(
                self.game_map.tiles['transparent'],
                (light.x, light.y),
                radius=light.light_source.radius,
                algorithm=tcod.FOV_BASIC,
                light_walls=light_walls
            )
            for x, y in coords:
                if light_fov[x][y]:
                    distance = light.distance(x, y)
                    brightness_diff = distance / (light.light_source.radius+2)
                    if brightness_diff < self.game_map.light_levels[x][y]:
                        self.game_map.light_levels[x][y] = brightness_diff

        explored = (self.game_map.light_levels < 1) & self.game_map.visible
        self.game_map.explored |= explored


    def render(self, console: Console) -> None:
        self.game_map.render(console)

        info_pane_x = self.game_world.viewport_width
        info_pane_width = console.width - info_pane_x
        info_pane_height = self.game_world.viewport_height
        # This is debug info.  Remove it later
        info_pane_title = f'({self.player.x},{self.player.y})'

        sub_pane_x = info_pane_x + 1
        sub_pane_width = info_pane_width - 2

        bar_pane_x = sub_pane_x
        bar_pane_y = 1
        bar_pane_width = sub_pane_width
        bar_pane_height = 5
        render_functions.draw_window(console, bar_pane_x, bar_pane_y, bar_pane_width, bar_pane_height, 'Vitals')

        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=bar_pane_width - 2,
            location=(bar_pane_x+1,bar_pane_y + 1),
            caption="HP",
            bar_fill_color=color.bar_filled,
            bar_empty_color=color.bar_empty,
            bar_text_color=color.bar_text
        )

        char_pane_x =  sub_pane_x
        char_pane_y = bar_pane_y + bar_pane_height
        char_pane_width = sub_pane_width
        char_pane_height = 9
        render_functions.draw_window(console, char_pane_x, char_pane_y, char_pane_width, char_pane_height, info_pane_title)

        render_functions.render_rouble_amount(
            console=console,
            roubles=self.player.currency.roubles,
            location=(char_pane_x+1, char_pane_y+4),
        )

        render_functions.render_char_stats(
            console=console,
            character=self.player,
            location=(char_pane_x+1, char_pane_y+3),
        )

        render_functions.render_char_level(
            console=console,
            character=self.player,
            location=(char_pane_x+1, char_pane_y+2),
        )

        render_functions.render_bar(
            console=console,
            current_value=self.player.level.current_xp,
            maximum_value=self.player.level.experience_to_next_level,
            total_width=char_pane_width - 2,
            location=(char_pane_x+1,char_pane_y + 1),
            caption="EXP",
            bar_fill_color=color.yellow,
            bar_empty_color=color.window_border_bright,
            bar_text_color=color.black
        )
        # render_functions.render_coordinates(
        #     console=console,
        #     coords=(self.player.x,self.player.y),
        #     location=(char_pane_x + 1, char_pane_y + 2),
        # )
        # if self.player.equipment.item_is_equipped(EquipmentType.RANGED_WEAPON):
        #     render_functions.render_ammo_status(
        #         console=console,
        #         ammo=self.player.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON).equippable.ammo,
        #         max_ammo=self.player.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON).equippable.max_ammo,
        #         location=(char_pane_x + 1, char_pane_y + 3),
        #     )

        render_functions.render_bunker_level(
            console=console,
            bunker_level=self.game_world.current_floor,
            location=(char_pane_x + 1,char_pane_y + 7)
        )

        equip_pane_x = sub_pane_x
        equip_pane_y = char_pane_y + char_pane_height
        equip_pane_width = sub_pane_width
        equip_pane_height = (len(self.player.equipment.item_slots) * 2) + 2
        render_functions.draw_window(console, equip_pane_x, equip_pane_y, equip_pane_width, equip_pane_height, 'Equipped')

        equip_y = equip_pane_y + 1
        equip_x = equip_pane_x + 1
    
        for slot in self.player.equipment.item_slots:
            bg_color = None
            console.print(equip_x, equip_y, slot.slot_name, fg=color.yellow)
            if slot.item:
                item_name = f'-{slot.item.name}'
                # if slot.item.powered:
                #     item_name = f'{item_name}'
                if slot.item.equippable.max_ammo > 0:
                    item_name = f'-{slot.item.name} [{slot.item.equippable.ammo}/{slot.item.equippable.max_ammo}]'
                    if slot.item.equippable.ammo == 0:
                        bg_color = color.red
            else:
                item_name = '-(Empty)'
            if bg_color:
                console.print(equip_x, equip_y + 1, item_name, bg=bg_color)
            else:
                console.print(equip_x, equip_y + 1, item_name)
            equip_y += 2
        

        inv_pane_x = sub_pane_x
        inv_pane_y = equip_pane_y + equip_pane_height
        inv_pane_width = sub_pane_width
        # inv_pane_height = (len(self.player.inventory.items)) + 2
        inv_pane_height = console.height - inv_pane_y - 1
        render_functions.draw_window(console, inv_pane_x, inv_pane_y, inv_pane_width, inv_pane_height, 'Inventory')

        inv_y = inv_pane_y + 1
        inv_x = inv_pane_x + 1
        for item in self.player.inventory.items:
            if(item.equippable):
                    is_equipped = (self.player.equipment.item_is_equipped(item.equippable.equipment_type) and self.player.equipment.get_item_in_slot(item.equippable.equipment_type) == item)
            else:
                    is_equipped = False

            item_string = f"{item.name.capitalize()}"

            if is_equipped:
                    item_string = f"{item_string} (E)"         
            
            if item.ammo_container:
                item_string = f'{item.name} [{item.ammo_container.ammo}/{item.ammo_container.max_ammo}]'

            console.print(inv_x, inv_y, f'- {item_string}')
            inv_y += 1

        log_pane_x = 0
        log_pane_y = 0 + self.game_world.viewport_height
        log_pane_width = self.game_world.viewport_width
        log_pane_height = console.height - log_pane_y - 1
        render_functions.draw_window(console, log_pane_x, log_pane_y, log_pane_width, log_pane_height, 'Game Log')

        self.message_log.render(console=console,x=log_pane_x+1,y=log_pane_y+1,width=log_pane_width-2,height=log_pane_height-2)

        # render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine=self)
        render_functions.render_names_at_mouse_location(console=console, x=int(log_pane_width/2), y=log_pane_y-3, engine=self)
    
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
 L.U.R.K.E.R. roguelike post-mortem character dump
--------------------------------------------------------------
"""
            post_mortem_lines = []
            summary_line = self.game_rules.flatten(f" {self.player.name}, level {self.player.level.current_level} #postmortem_summary#")
            post_mortem_lines.append(summary_line)
            if killer != None:
                post_mortem_lines.append(f' {killer.name}, a level {killer.level.current_level}\n')
            else:
                post_mortem_lines.append(f' the invisible forces of the Zone\n')
            post_mortem_lines.append('\n')
            post_mortem_lines.append('-- Special levels --------------------------------------------\n\n')
            post_mortem_lines.append(f' Bunker levels explored : {self.game_world.current_floor}\n\n')
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
            post_mortem_lines.append(f' [a] [ Armor      ]   {self.player.equipment.get_item_in_slot(EquipmentType.ARMOR).name if self.player.equipment.item_is_equipped(EquipmentType.ARMOR) else None}\n')
            if self.player.equipment.item_is_equipped(EquipmentType.RANGED_WEAPON):
                ammo_text = f'[{self.player.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON).equippable.ammo}/{self.player.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON).equippable.max_ammo}]'
            else:
                ammo_text = f''
            post_mortem_lines.append(f' [b] [ M. Weapon  ]   {self.player.equipment.get_item_in_slot(EquipmentType.MELEE_WEAPON).name if self.player.equipment.item_is_equipped(EquipmentType.MELEE_WEAPON) else None}\n')
            post_mortem_lines.append(f' [b] [ R. Weapon  ]   {self.player.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON).name if self.player.equipment.item_is_equipped(EquipmentType.RANGED_WEAPON) else None} {ammo_text}\n')
            post_mortem_lines.append(f' [c] [ Head       ]   {self.player.equipment.get_item_in_slot(EquipmentType.HEAD).name if self.player.equipment.item_is_equipped(EquipmentType.HEAD) else None}\n')
            post_mortem_lines.append(f' [c] [ Legs       ]   {self.player.equipment.get_item_in_slot(EquipmentType.LEGS).name if self.player.equipment.item_is_equipped(EquipmentType.LEGS) else None}\n')
            post_mortem_lines.append(f' [d] [ Feet       ]   {self.player.equipment.get_item_in_slot(EquipmentType.FEET).name if self.player.equipment.item_is_equipped(EquipmentType.FEET) else None}\n')
            post_mortem_lines.append('\n')
            post_mortem_lines.append('-- Inventory -------------------------------------------------\n\n')
            names_only_inventory_list = [i.name for i in self.player.inventory.items]
            counted_inventory_list = {i:(names_only_inventory_list).count(i) for i in names_only_inventory_list}
            unique_inventory_list = set(counted_inventory_list.keys())
            for item in unique_inventory_list:
                count = 'x'+str(counted_inventory_list[item]) if counted_inventory_list[item] >= 2 else f''
                post_mortem_lines.append(f' {item.capitalize()} {count}\n')
            post_mortem_lines.append('\n')
            post_mortem_lines.append('-- Resistances -----------------------------------------------\n\n')
            post_mortem_lines.append(' None\n\n')
            post_mortem_lines.append('-- Kills -----------------------------------------------------\n\n')
            counted_victim_list = {i:self.player.fighter.victims.count(i) for i in self.player.fighter.victims}
            unique_victim_list = set(counted_victim_list.keys())
            for victim in unique_victim_list:
                count = 'x'+str(counted_victim_list[victim]) if counted_victim_list[victim] >= 2 else f''
                post_mortem_lines.append(f' {victim} {count}\n')
            post_mortem_lines.append('\n')
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
        pass
                