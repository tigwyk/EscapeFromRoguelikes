from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType
from exceptions import Impossible
from input_handlers import (
    ActionOrHandler,
    AreaRangedAttackHandler,
    SingleRangedAttackHandler,
    SingleAimedRangedAttackHandler,
)
import actions
import color
import sound

if TYPE_CHECKING:
    from entity import Actor, Item


class Equippable(BaseComponent):
    parent: Item

    def __init__(
        self,
        equipment_type: EquipmentType,
        ammo: int = 0,
        power_bonus: int = 0,
        defense_bonus: int = 0,
        ammo_type: str = "None",        
        max_ammo: int = 0,
    ):
        self.equipment_type = equipment_type

        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus

        self.max_ammo = max_ammo
        if(ammo):
            self.ammo = ammo
        else:
            self.ammo = max_ammo

        self.ammo_type = ammo_type

    def get_fire_action(self, actor: Actor) -> SingleAimedRangedAttackHandler:
        if(self.equipment_type != EquipmentType.RANGED_WEAPON):
            return
        self.engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return SingleAimedRangedAttackHandler(
            self.engine,
            callback=lambda xy: actions.FireAction(actor, self.parent, xy),
        )

    def activate(self, action: actions.FireAction) -> None:
        actor = action.entity
        target = action.target_actor

        if not self.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")
        if not target:
            raise Impossible("You must select an enemy to target.")
        if target is actor:
            raise Impossible("You cannot shoot yourself!")
        if self.ammo < 1:
            raise Impossible("Not enough ammo. Reload!")

        damage = actor.fighter.power - target.fighter.defense

        attack_desc = f"{actor.name.capitalize()} shoots {target.name} with {actor.equipment.weapon.name if actor.equipment.weapon is not None else 'their fists'}"
        if actor is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )
        self.ammo = self.ammo - 1
        actor.fighter.fighting = target
        target.fighter.fighting = actor
        sound.play_sound('pistol_shot')


class Knife(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.MELEE_WEAPON, power_bonus=2)

class Sword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.MELEE_WEAPON, power_bonus=4)

class Handgun(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=6, max_ammo=6,ammo_type="9x18mm")

class Shotgun(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=7, max_ammo=4, ammo_type="12g")

class Rifle(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=8, max_ammo=10, ammo_type="7.62x54R")

class AssaultRifle(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=8, max_ammo=10, ammo_type="5.45x39mm")        


class Shirt(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1)

class BodyArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3)


class BasicHelmet(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.HEAD, defense_bonus=3)


class Pants(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.LEGS, defense_bonus=1)

class ArmoredPants(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.LEGS, defense_bonus=4)


class Shoes(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.FEET, defense_bonus=1)

class Boots(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.FEET, defense_bonus=2)