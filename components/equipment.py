from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType
from sound import play_sound

if TYPE_CHECKING:
    from entity import Actor, Item


class ItemSlot:
  def __init__(self, equipment_type, slot_name, item=None):
    self.equipment_type = equipment_type
    self.slot_name = slot_name
    self.item = item

class Equipment(BaseComponent):
    parent: Actor

    def __init__(self, weapon: Optional[Item] = None, armor: Optional[Item] = None, head: Optional[Item] = None, legs: Optional[Item] = None, feet: Optional[Item] = None):
        self.item_slots = [
      ItemSlot(EquipmentType.MELEE_WEAPON, 'Melee Weapon'),
      ItemSlot(EquipmentType.RANGED_WEAPON, 'Ranged Weapon'),
      ItemSlot(EquipmentType.ARMOR, 'Armor'),
      ItemSlot(EquipmentType.HEAD, 'Head'),
      ItemSlot(EquipmentType.LEGS, 'Legs'),
      ItemSlot(EquipmentType.FEET, 'Feet'),
    ]
        self.weapon = weapon
        self.armor = armor
        self.head = head
        self.legs = legs
        self.feet = feet

    @property
    def defense_bonus(self):
        bonus = 0
        for item_slot in self.item_slots:
            if item_slot.item:
                bonus += item_slot.item.equippable.defense_bonus
        return bonus

    @property
    def power_bonus(self):
        bonus = 0
        for item_slot in self.item_slots:
            if item_slot.item:
                bonus += item_slot.item.equippable.power_bonus
        return bonus

    def item_is_equipped(self, equipment_type: EquipmentType) -> bool:
        for slot in self.item_slots:
            if slot.equipment_type == equipment_type and slot.item is not None:
                return True
        return False

    def get_item_in_slot(self, equipment_type):
        for slot in self.item_slots:
            if slot.equipment_type == equipment_type and slot.item is not None:
                return slot.item
        return None

    def unequip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You equip the {item_name}."
        )

    def equip_to_slot(self, item: Item, add_message: bool) -> None:
        for item_slot in self.item_slots:
            if item_slot.equipment_type == item.equippable.equipment_type:
                if item_slot.item:
                    self.unequip_from_slot(item_slot.equipment_type, add_message=add_message)
                item_slot.item = item
                if add_message:
                    self.equip_message(item.name)
                if(item.equippable.equipment_type == EquipmentType.RANGED_WEAPON):
                    # print(f"Playing reload equip sound for {self.parent.name}")
                    # print(f"Player is? {self.engine.player}")
                    # play_sound('reload')
                    pass

    def unequip_from_slot(self, equipment_type: EquipmentType, add_message: bool) -> None:
        for item_slot in self.item_slots:
            if item_slot.equipment_type == equipment_type:
                if add_message:
                    self.unequip_message(item_slot.item.name)
                item_slot.item = None
                break

    def toggle_equip(self, item, add_message=True):
        for item_slot in self.item_slots:
            if item_slot.equipment_type == item.equippable.equipment_type:
                if item_slot.item == item:
                    self.unequip_from_slot(equipment_type=item.equippable.equipment_type, add_message=add_message)
                else:
                    self.equip_to_slot(item=item, add_message=add_message)
                break