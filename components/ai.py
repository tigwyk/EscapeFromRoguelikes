from __future__ import annotations
from ast import Eq

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod
import dice

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction, FireAction
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor

class BaseAI(Action):

    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an enitiy blocks movement and the cost isn't zero (blocking.)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]

class ConfusedEnemy(BaseAI):
    """
    A confused enemy will stumble around aimlessly for a given number of turns, then revert back to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack.
    """

    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} is no longer confused."
            )
            self.entity.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # Its possible the actor will just bump into the wall, wasting a turn.
            return BumpAction(self.entity, direction_x, direction_y,).perform()

class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()

class HostileHumanEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        if self.entity.inventory.items:
            melee_weapons = []
            ranged_weapons = []
            for item in self.entity.inventory.items:
                if item.equippable.equipment_type == EquipmentType.WEAPON:
                    melee_weapons.append(item)
                if item.equippable.equipment_type == EquipmentType.RANGED_WEAPON:
                    ranged_weapons.append(item)

            if self.entity.equipment.weapon is None:
                if(len(melee_weapons)):
                    self.entity.equipment.toggle_equip(melee_weapons[0], add_message=False)
                    # print(f"Equipping {melee_weapons[0].name}")
                elif(len(ranged_weapons)):
                    self.entity.equipment.toggle_equip(ranged_weapons[0], add_message=False)
                    # print(f"Equipping {ranged_weapons[0].name}")



        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if self.entity.equipment.weapon:
                if distance > 1 and distance <= 3 and self.entity.equipment.weapon.equippable.equipment_type == EquipmentType.RANGED_WEAPON:
                    for roll in dice.roll('d20'):
                        # print(f"Fire roll: {roll}")
                        if roll > 15:
                            return FireAction(self.entity, self.entity.equipment.weapon, (target.x, target.y)).perform()
                if distance <= 1 and self.entity.equipment.weapon.equippable.equipment_type == EquipmentType.RANGED_WEAPON:
                    self.entity.equipment.toggle_equip(self.entity.equipment.weapon, add_message=False)
                if distance <= 1:
                    if self.entity.equipment.weapon:
                        if self.entity.equipment.weapon.equippable.equipment_type == EquipmentType.WEAPON:
                            return MeleeAction(self.entity, dx, dy).perform()
                    else:
                        return MeleeAction(self.entity, dx, dy).perform()    
            else:
                if distance <= 1:
                    return MeleeAction(self.entity, dx, dy).perform()
            
            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()