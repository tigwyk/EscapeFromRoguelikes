from __future__ import annotations

from typing import TYPE_CHECKING

import color
import copy
from components.base_component import BaseComponent
from render_order import RenderOrder
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor


class Fighter(BaseComponent):
    fighting: Actor
    killer: Actor

    def __init__(self, hp: int, base_defense: int, base_power: int):
        self.max_hp = hp
        self._hp = hp
        self.base_defense = base_defense
        self.base_power = base_power
        self.fighting = None
        self.killer = None
        self.victims = []

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    @property
    def defense(self) -> int:
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> int:
        return self.base_power + self.power_bonus

    @property
    def defense_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def power_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return 0

    def after_melee_damage(self, damage_dealt, target):
        equipment = self.parent.equipment
        if equipment:
            for item_slot in equipment.item_slots:
                if item_slot.item and item_slot.item.equippable.equipment_type in (EquipmentType.MELEE_WEAPON,EquipmentType.HEAD):
                    item_slot.item.equippable.after_melee_damage(damage_dealt, target)

    def after_ranged_damage(self, damage_dealt, target):
        equipment = self.parent.equipment
        if equipment:
            for item_slot in equipment.item_slots:
                if item_slot.item and item_slot.item.equippable.equipment_type in (EquipmentType.RANGED_WEAPON,EquipmentType.HEAD):
                    item_slot.item.equippable.after_ranged_damage(damage_dealt, target)

    def after_damaged(self, damage_taken, source):
        if self.engine.game_map.visible[self.parent.x, self.parent.y]:
            equipment = self.parent.equipment
            if equipment:
                for item_slot in equipment.item_slots:
                    if item_slot.item and item_slot.item.equippable.equipment_type in (EquipmentType.ARMOR,EquipmentType.HEAD):
                        item_slot.item.equippable.after_damaged(damage_taken, source)

    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_color = color.player_die
            roubles_to_reward = 0
            self.engine.player.fighter.killer = copy.deepcopy(self.engine.player.fighter.fighting)
            self.engine.dump_character_log()
            self.engine.sound.play_sound('death', volume=1)
            self.engine.sound.play_sound('game_over',volume=1.5)
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die
            roubles_to_reward = self.parent.currency.roubles
            self.engine.player.fighter.victims.append(self.parent.name)

        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE

        if(self.parent.inventory and self.parent.inventory.items):
            while self.parent.inventory.items:
                item = self.parent.inventory.items.pop()
                # print(f"Spilling inventory item upon death: {item.name}")
                item.x = self.parent.x
                item.y = self.parent.y
                item.parent = self.engine.game_map
                self.engine.game_map.entities.add(item)
                # print(f"Map entities now: {[x.name for x in self.engine.game_map.entities]}")
                

        self.engine.message_log.add_message(death_message, death_message_color)

        self.engine.player.level.add_xp(self.parent.level.xp_given)
        self.engine.player.currency.add_roubles(roubles_to_reward)
    
    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp -= amount
