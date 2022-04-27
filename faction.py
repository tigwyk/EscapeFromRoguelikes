
from building import Building
from entity import Actor
from typing import Optional, List, TYPE_CHECKING

class Faction:
    name: str
    hq: Building
    enemies: list()
    _leader: Actor

    def __init__(self, name: str, leader: Actor):
        self.name = name
        self._leader = leader
        self.hq = self.generate_hq()

    def generate_hq(self):
        pass

    @property
    def leader(self) -> Actor:
        return self._leader
    
    @leader.setter
    def leader(self, value):
        if type(value) == Actor:
            self._leader = value