from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
import components.inventory
from exceptions import Impossible

import actions
import color
import sound

if TYPE_CHECKING:
    from entity import Actor, Item


class AmmoContainer(BaseComponent):
    parent: Item

    def __init__(
        self,
        ammo: int = 0,
        max_ammo: int = 0,
        ammo_type: str = "None",
    ):
        
        self.max_ammo = max_ammo
        self.ammo = ammo
        self.ammo_type = ammo_type
    
    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):
            inventory.items.remove(entity)
            # self.engine.message_log.add_message(f"You toss away the {entity.name}.")


class AmmoMag(AmmoContainer):
    def __init__(
        self,
        ammo: int,
        max_ammo: int,
        ammo_type: str
    ) -> None:
        super().__init__(ammo=8, max_ammo=8,ammo_type="9x18mm")

class AmmoBox(AmmoContainer):
    def __init__(self) -> None:
        super().__init__(ammo=6, max_ammo=6,ammo_type="9x18mm")
