from __future__ import annotations

import copy
import math
from time import time
from russian_names import RussianNames
from camera import Camera
import random
import entity_factories

from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

from pprint import pprint

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.consumable import Consumable
    from components.equipment import Equipment
    from components.equippable import Equippable
    from components.fighter import Fighter
    from components.inventory import Inventory
    from components.level import Level
    from components.currency import Currency
    from components.ammo_container import AmmoContainer
    from components.lore import Lore
    from components.roles import Role
    from maps import GameMap
    from faction import Faction

T = TypeVar("T", bound="Entity")

class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """

    parent: Union[GameMap, Inventory]

    def __init__(
        self,
        parent: Optional[GameMap] = None,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        blocks_movement: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
        light_source = None,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        self.light_source = light_source
        if light_source:
            self.light_source.parent = self
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap
    
    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        if(type(clone) == Actor):
            if(clone.gen_name):
                clone.name = clone.generate_russian_name()

            if(clone.inventory and clone.gen_kit):
                clone.generate_kit()
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone
    
    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Place this entity at a new location.  Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):  # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy

class Actor(Entity):
    faction: Faction

    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type[BaseAI],
        equipment: Equipment,
        fighter: Fighter,
        inventory: Inventory,
        level: Level,
        currency: Currency,
        lore: Lore = None,
        role: Role = None,
        gen_name: bool = False,
        gen_kit: bool = False,
        light_source=None,
        skills=None,
        visibility=5
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
            light_source=light_source
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.equipment: Equipment = equipment
        self.equipment.parent = self

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.level = level
        self.level.parent = self

        self.currency = currency
        self.currency.parent = self

        if(lore):
            self.lore = lore
            self.lore.parent = self

        if(role):
            self.role = role
            self.role.parent = self

        self.gen_name = gen_name

        self.gen_kit = gen_kit

        if(skills):
            self.skills = skills
            self.skills.parent = self

        self.visibility = visibility

        # if(gen_name):
        #     self.name = self.generate_russian_name()

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        super().spawn(gamemap=gamemap, x=x, y=y)

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)

    def generate_russian_name(self) -> str:
        return RussianNames(patronymic=False, name_reduction=True, transliterate=True).get_person()
    
    def generate_kit(self):
        # print(f"Generating kit...")
        
        shirt = copy.deepcopy(entity_factories.shirt)
        shirt.parent = self.inventory
        self.inventory.items.append(shirt)
        self.equipment.toggle_equip(shirt, add_message=False)
        
        if(random.choice([True,False,True,True])):
            knife = copy.deepcopy(entity_factories.kitchen_knife)
            knife.parent = self.inventory
            self.inventory.items.append(knife)
            self.equipment.toggle_equip(knife, add_message=False)
        else:
            pistol = copy.deepcopy(entity_factories.pistol)
            pistol.parent = self.inventory
            self.inventory.items.append(pistol)
            self.equipment.toggle_equip(pistol, add_message=False)


        

class Item(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        consumable: Optional[Consumable] = None,
        equippable: Optional[Equippable] = None,
        ammo_container: Optional[AmmoContainer] = None,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )

        self.consumable = consumable
        
        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable

        if self.equippable:
            self.equippable.parent = self

        self.ammo_container = ammo_container

        if self.ammo_container:
            self.ammo_container.parent = self


class Container(Entity):
  def __init__(self,
               *,
               x = 0,
               y = 0,
               char='?',
               color= (255,255,255),
               name = '<Container>',
               inventory: Inventory):
    super().__init__(
      x=x,
      y=y,
      char=char,
      color=color,
      name=name,
      blocks_movement=True,
      render_order=RenderOrder.ITEM,
    )
    self.inventory = inventory
    self.inventory.parent = self

  def add_items(self, items):
    if type(items) == Item:
      items = [items]
    self.inventory.extend(items)