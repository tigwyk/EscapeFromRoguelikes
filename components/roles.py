from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent
from skill import blades, medical, shotguns, rifles, handguns, science

if TYPE_CHECKING:
    from entity import Actor, Item
    from skill import Skill


class Role(BaseComponent):

    def __init__(self, name: str):
        self.name: str = name
        self.base_skills: List[Skill]

class Scientist(Role):
    def __init__(self) -> None:
        super().__init__(name="Scientist")
        self.base_skills = [medical, blades, science]

class Soldier(Role):
    def __init__(self) -> None:
        super().__init__(name="Soldier")
        self.base_skills = [blades, handguns, rifles]

class Scavenger(Role):
    def __init__(self) -> None:
        super().__init__(name="Scavenger")
        self.base_skills = [medical, blades, handguns]