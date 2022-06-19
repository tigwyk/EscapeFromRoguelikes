from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent
from input_handlers import ShopInventoryPurchaseHandler

if TYPE_CHECKING:
    from entity import Actor, Item


class Shop(BaseComponent):

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[Item] = []

    def drop(self, item: Item) -> None:
        """
        Removes an item from the shop inventory and restores it to the game map, at the player's current location.
        """
        self.items.remove(item)
        item.place(self.parent.x, self.parent.y, self.gamemap)

        self.engine.message_log.add_message(f"{item.name} lands at your feet.")
    
    def sell_handler(self) -> None:
        return ShopInventoryPurchaseHandler(self.engine)

    def sell(self, item: Item) -> None:
        """
        Removes an item from the shop inventory and restores it to the game map, at the player's current location.
        """
        inventory = self.parent.inventory
        if (self.parent.currency.roubles >= item.cost):
            self.parent.currency.take_roubles(item.cost)
            self.items.remove(item)
            if(self.parent == self.engine.player):
                self.engine.message_log.add_message(f"You buy {item.name}.")
            if(len(inventory.items)<inventory.capacity):
                item.parent = self.parent.inventory
                inventory.items.append(item)
            else:
                if(self.parent == self.engine.player):
                    self.engine.message_log.add_message(f"{item.name} at your your feet.")
                item.place(self.parent.x, self.parent.y, self.gamemap)
        else:
            self.engine.message_log.add_message(f"{self.parent.name} tries to buy {item.name} and fails.")