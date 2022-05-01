from __future__ import annotations

from typing import TYPE_CHECKING,List, Set, Dict, Tuple, Optional

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

if TYPE_CHECKING:
    from entity import Actor, Item
    from effects import Effect
    from skill import Skill


class Equippable(BaseComponent):

    def __init__(
        self,
        equipment_type: EquipmentType,
        ammo: int = 0,
        power_bonus: int = 0,
        defense_bonus: int = 0,
        ammo_type: str = "None",        
        max_ammo: int = 0,
        effects: list[Effect] = [],
        fire_skill: Skill = None
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

        self._charges = 0
        self._after_melee_damage_effects = []
        self._after_ranged_damage_effects = []
        self._after_damaged_effects = []

        self.fire_skill = fire_skill

        if effects:
            if self.equipment_type == EquipmentType.RANGED_WEAPON:
                for e in effects:
                    self.add_after_ranged_damage_effect(e)
            if self.equipment_type == EquipmentType.MELEE_WEAPON:
                for e in effects:
                    self.add_after_melee_damage_effect(e)
    
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
    
    @property
    def charges(self):
        return self._charges
    
    @charges.setter
    def charges(self, num_charges):
        if(num_charges > -1):
            self._charges = num_charges
        else:
            self._charges = 0

    def use_charge(self, amount=1):
        if self.charges > 0:
            charges = self.charges-amount
            self.charges = charges
            return charges

    def add_after_melee_damage_effect(self, effect):
        """ Add a component that triggers after doing melee damage."""        
        self._after_melee_damage_effects.append(effect)

    def add_after_ranged_damage_effect(self, effect):
        """ Add a component that triggers after doing ranged damage."""
        self._after_ranged_damage_effects.append(effect)

    def add_after_damaged_effect(self, effect):
        """ Add a component that triggers after doing taking damage."""
        self._after_damaged_effects.append(effect)

    def after_melee_damage(self, damage_dealt, target=None):
        for effect in self._after_melee_damage_effects:
            effect.trigger(self.parent.parent.parent, damage_dealt, target)
            # self.use_charge()

    def after_ranged_damage(self, damage_dealt, target=None):
        for effect in self._after_ranged_damage_effects:
            effect.trigger(self.parent.parent.parent, damage_dealt, target)
            # self.use_charge()

    def after_damaged(self, damage_taken, source=None):
        for effect in self._after_damaged_effects:
            effect.trigger(source, damage_taken, self.parent.parent.parent)
            # self.use_charge()

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

        attack_desc = f"{actor.name.capitalize()} shoots {target.name} with {actor.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON).name if actor.equipment.item_is_equipped(EquipmentType.RANGED_WEAPON) else 'a spitball'}"
        if actor is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if(self.fire_skill):
            print(f"Checking {self.fire_skill.name}...")
            if(actor.skills.check(self.fire_skill)):
                print(f"Pass")
            else:
                print(f"Fail")

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.take_damage(damage)
            actor.fighter.after_ranged_damage(damage, target)
            target.fighter.after_damaged(damage, actor)
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )
        self.ammo = self.ammo - 1
        actor.fighter.fighting = target
        target.fighter.fighting = actor
        self.engine.sound.play_sound('pistol_shot')


class Blade(Equippable):
    def __init__(self, power_bonus: int = 2, defense_bonus: int = 0, effects: list[Effect] = []) -> None:
        super().__init__(equipment_type=EquipmentType.MELEE_WEAPON, power_bonus=power_bonus, defense_bonus=defense_bonus, effects=effects)

class Firearm(Equippable):
    def __init__(self, power_bonus: int = 6, max_ammo: int = 6, ammo:int = 6, ammo_type:str = '9x18mm', effects: list[Effect] = [], fire_skill: Skill = None) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=power_bonus, max_ammo=max_ammo,ammo_type=ammo_type, effects=effects, fire_skill=fire_skill)

class BodyArmor(Equippable):
    def __init__(self, defense_bonus: int = 3) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=defense_bonus)

class Helmet(Equippable):
    def __init__(self, defense_bonus: int = 3) -> None:
        super().__init__(equipment_type=EquipmentType.HEAD, defense_bonus=defense_bonus)

class LegArmor(Equippable):
    def __init__(self, defense_bonus: int = 1) -> None:
        super().__init__(equipment_type=EquipmentType.LEGS, defense_bonus=defense_bonus)

class Boots(Equippable):
    def __init__(self, defense_bonus: int = 2) -> None:
        super().__init__(equipment_type=EquipmentType.FEET, defense_bonus=defense_bonus)