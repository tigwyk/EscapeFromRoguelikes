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

        self._max_ammo = max_ammo
        if(ammo):
            self._ammo = ammo
        else:
            self._ammo = max_ammo

        self._ammo_type = ammo_type
    
    @property
    def max_ammo(self):
        return self._max_ammo
    
    @property
    def ammo(self):
        return self._ammo
    
    @ammo.setter
    def ammo(self, value):
        self._ammo = value if value > -1 else 0

    @max_ammo.setter
    def max_ammo(self, value):
        self._max_ammo = value if value > -1 else 0

    @property
    def ammo_type(self):
        return self._ammo_type

    @ammo_type.setter
    def ammo_type(self, ammo_type):
        self._ammo_type = ammo_type
    
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

        attack_desc = f"{actor.name.capitalize()} shoots {target.name} with {actor.equipment.weapon.name if actor.equipment.weapon is not None else 'a spitball'}"
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


class Blade(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.MELEE_WEAPON, power_bonus=2)

class Firearm(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=6, max_ammo=6,ammo_type="9x18mm")

class BodyArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3)

class Helmet(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.HEAD, defense_bonus=3)

class LegArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.LEGS, defense_bonus=1)

class Boots(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.FEET, defense_bonus=2)