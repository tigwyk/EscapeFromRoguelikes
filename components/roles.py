from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item


class Role(BaseComponent):
    parent: Actor

    def __init__(self, name: str):
        print(name)
        self.name: str = name

class Scientist(Role):
    def __init__(self) -> None:
        super().__init__(name="Scientist")

class Soldier(Role):
    def __init__(self) -> None:
        super().__init__(name="Soldier")

class Scavenger(Role):
    def __init__(self) -> None:
        super().__init__(name="Scavenger")