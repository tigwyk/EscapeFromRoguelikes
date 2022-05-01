from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color
from components import ammo_container
import exceptions

from pprint import pprint

from equipment_types import EquipmentType

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item

class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
       """Perform this action with the objects needed to determine its scope.
       `self.engine` is the scope this action is being performed in.
       `self.entity` is the object performing the action.
       This method must be overridden by Action subclasses.
       """
       raise NotImplementedError()

class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You picked up the {item.name}!")
                return

        raise exceptions.Impossible("There is nothing here to pick up.")

class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self)

class DropItemAction(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item.equippable.equipment_type) and self.entity.equipment.get_item_in_slot(self.item.equippable.equipment_type) == self.item:
            self.entity.equipment.toggle_equip(self.item)

        self.entity.inventory.drop(self.item)

class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)

class FireAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.entity = entity
        self.item = item
        if not self.item:
            return
        if(not self.entity.equipment.item_is_equipped(EquipmentType.MELEE_WEAPON) or not self.entity.equipment.item_is_equipped(EquipmentType.RANGED_WEAPON)):
            return
        
        if not target_xy:
            if(entity.fighter.target):
                target_xy = entity.fighter.target.x, entity.fighter.target.y
            else:
                target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        # pprint(vars(self))
        """Invoke the items ability, this action will be given to provide context."""
        if(self.entity.equipment.item_is_equipped(self.item.equippable.equipment_type) and self.entity.equipment.get_item_in_slot(self.item.equippable.equipment_type) == self.item):
            self.item.equippable.activate(self)

class ReloadAction(Action):
    """Reload the currently equipped ranged weapon"""

    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def filter_ammo_containers(item):
        return True if item.ammo_container is not None else False

    def perform(self) -> None:
        if(not self.item):
            raise exceptions.Impossible("You can't reload your weapon.")

        if self.item.equippable.ammo < self.item.equippable.max_ammo:
            # print(f"Player's items from reload action: {self.entity.inventory.items}")
            ammo_containers = []
            for item in self.entity.inventory.items:
                if item.ammo_container:
                    ammo_containers.append(item)
            if(ammo_containers):
                compatible_ammo = []
                for ammo in ammo_containers:
                    if(ammo.ammo_container.ammo_type == self.item.equippable.ammo_type):
                        compatible_ammo.append(ammo)
                    if(compatible_ammo):
                        # print(f"Ammo containers in inventory: {ammo_containers}")
                        for mag in compatible_ammo:
                            if(mag.ammo_container.ammo > 0):
                                ammo_needed = self.item.equippable.max_ammo - self.item.equippable.ammo
                                # print(f"Ammo in first spare mag: {mag.ammo_container.ammo}")
                                # print(f"Ammo needed: {ammo_needed}")
                                if(ammo_needed <= mag.ammo_container.ammo):
                                    new_ammo_amount = mag.ammo_container.ammo - ammo_needed
                                    # print(f"Remaining ammo in {mag.name}: {new_ammo_amount}")
                                    mag.ammo_container.ammo = new_ammo_amount
                                else:
                                    ammo_needed -= mag.ammo_container.ammo
                                    # print(f"Ammo still needed? {ammo_needed}")
                                    mag.ammo_container.ammo = 0
                                # print(f"Adding ammo: {ammo_needed}")
                                self.item.equippable.ammo += ammo_needed
                                self.engine.message_log.add_message(f"You reload the {self.item.name}!")
                                self.engine.sound.play_sound('reload')
                                if(mag.ammo_container.ammo < 1):
                                        mag.ammo_container.consume()  
                                    
                        return
                    else:
                        raise exceptions.Impossible(f"You don't have any compatible ammo for your {item.name}.")
            else:
                raise exceptions.Impossible("You don't have any spare ammo.")
        else:
            raise exceptions.Impossible("You can't reload your weapon.")

class WaitAction(Action):
    def perform(self) -> None:
        pass

class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            # self.engine.sound.play_music(self.engine.game_map.music)
            # self.engine.sound.play_sound('stairs')
            self.engine.message_log.add_message(
                "You descend the staircase.", color.descend
            )
        else:
            raise exceptions.Impossible("There are no stairs here.")

class ActivateAction(Action):
    def perform(self) -> None:
        """
        Activate thing at player's location
        """
        pass

class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)
        self.dx = dx
        self.dy = dy
    
    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name} with {self.entity.equipment.weapon.name if self.entity.equipment.weapon is not None else 'their fists'}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.take_damage(damage)
            self.entity.fighter.after_melee_damage(damage, target)
            target.fighter.after_damaged(damage, self.entity)
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )
        self.entity.fighter.fighting = target
        target.fighter.fighting = self.entity

class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an entity.
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)

class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            if(self.entity.equipment and self.entity.equipment.weapon):
                if(self.entity.equipment.weapon.equippable.equipment_type != EquipmentType.RANGED_WEAPON):
                    return MeleeAction(self.entity, self.dx, self.dy).perform()
            else:
                return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()