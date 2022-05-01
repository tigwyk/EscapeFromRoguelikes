from __future__ import annotations

from typing import List, TYPE_CHECKING

import dice

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
        Unlearns a skill
        """
        self.skills.remove(skill)
        self.engine.message_log.add_message(f"You unlearned {skill.name}.")
    
    def learn(self, skill: Skill) -> None:
        """
        Learns a skill
        """
        self.skills.append(skill)
        self.engine.message_log.add_message(f"You learned {skill.name}.")
    
    def check(self, skill: Skill) -> bool:
        if(skill in self.skills):
            for roll in dice.roll('d100'):
                if roll > skill.level:
                    return False
                else:
                    return True
        else:
            return False

    def learned(self, skill: Skill) -> bool:
        if(skill in self.skills):
            return True
        else:
            return False

    def skill_by_name(self, name: str) -> Skill:
        if name in self.skill_names:
            s = [x for x in self.skills if x.name.lower() == name].pop()
            # print(s)
            return s

    @property
    def skill_names(self) -> list(str):
        return [x.name.lower() for x in self.skills]