from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item


class Lore(BaseComponent):
    parent: Actor

    def __init__(self, previous_job:str = ''):
        self.previous_job = previous_job
