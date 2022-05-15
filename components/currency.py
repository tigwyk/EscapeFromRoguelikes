from __future__ import annotations

from typing import TYPE_CHECKING

import color
from components.base_component import BaseComponent
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor


class Currency(BaseComponent):

    def __init__(self, roubles: int):
        self._roubles = roubles

    @property
    def roubles(self) -> int:
        return self._roubles

    @roubles.setter
    def roubles(self, value: int) -> None:
        if value < 0:
            self._roubles = 0 
        else:
            self._roubles = value

    
    def add_roubles(self, amount: int) -> int:
        if amount == 0:
            return

        self.roubles += amount

        self.engine.message_log.add_message(f"You find {amount} roubles.", color.roubles_add_text)

    def take_roubles(self, amount: int) -> None:
        self.roubles -= amount
        self.engine.message_log.add_message(f"You lose {amount} roubles.", color.roubles_remove_text)