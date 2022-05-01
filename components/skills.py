from __future__ import annotations
from email.mime import base

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item
    from skill import Skill


class Skills(BaseComponent):
    parent: Actor

    def __init__(self, base_learn_bonus: int):
        self.base_learn_bonus = base_learn_bonus
        self.skills: List[Skill] = []

    def unlearn(self, skill: Skill) -> None:
        """
        Removes an item from the inventory and restores it to the game map, at the player's current location.
        """
        self.skills.remove(skill)
        self.engine.message_log.add_message(f"You unlearned {skill.name}.")
    
    def learn(self, skill: Skill) -> None:
        """
        Removes an item from the inventory and restores it to the game map, at the player's current location.
        """
        self.skills.append(skill)
        self.engine.message_log.add_message(f"You learned {skill.name}.")