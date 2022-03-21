from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Item


class Equippable(BaseComponent):
    parent: Item

    def __init__(
        self,
        equipment_type: EquipmentType,
        power_bonus: int = 0,
        defense_bonus: int = 0,
        ammo_type: str = "None",
        ammo: int = 0,
        max_ammo: int = 0,
    ):
        self.equipment_type = equipment_type

        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus

        self.max_ammo = max_ammo
        self.ammo = self.max_ammo


class Knife(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)

class Sword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)

class Handgun(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=6, max_ammo=6,ammo_type="9x18mm")

class Shotgun(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=7, max_ammo=4, ammo_type="12g shell")

class Rifle(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.RANGED_WEAPON, power_bonus=8, max_ammo=10, ammo_type="7.62x54R")


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