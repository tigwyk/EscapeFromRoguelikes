from __future__ import annotations

from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union
from equipment_types import EquipmentType

import tcod

from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction,
    FireAction,
    ReloadAction,
    TakeStairsAction,
    EquipAction,
    DropItemAction,
    ActivateAction
)
import color
import exceptions
import traceback
import os
import sys
# import psutil
# import logging
import ui

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_w,
}

ACTIVATE_KEYS = {
    tcod.event.K_e,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

FIRE_CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
    tcod.event.K_f,
}

LOOK_KEYS = {
    tcod.event.K_SLASH,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

QUIT_KEYS = {
    tcod.event.K_ESCAPE,
    tcod.event.K_q,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                # return GameOverEventHandler(self.engine)
                return PostMortemViewer(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()
        self.engine.update_fov()
        return True


    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """By default any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)

class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        # width = len(self.TITLE) + 4
        width = 30

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=26,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(
            x=x + 1, y=y + 1, string=f"Name: {self.engine.player.name}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 3, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 4,
            string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
        )

        console.print(
            x=x + 1,
            y=y + 6,
            string=f"Head : {self.engine.player.equipment.head.name if self.engine.player.equipment.head else None}"
        )
        console.print(
            x=x + 1,
            y=y + 7,
            string=f"Armor: {self.engine.player.equipment.armor.name if self.engine.player.equipment.armor else None}"
        )
        console.print(
            x=x + 1,
            y=y + 8,
            string=f"Legs : {self.engine.player.equipment.legs.name if self.engine.player.equipment.legs else None}"
        )
        console.print(
            x=x + 1,
            y=y + 9,
            string=f"Feet : {self.engine.player.equipment.feet.name if self.engine.player.equipment.feet else None}"
        )

        console.print(
            x=x + 1,
            y=y + 11,
            string=f"Weapon: {self.engine.player.equipment.weapon.name if self.engine.player.equipment.weapon else None}"
        )

        console.print(
            x=x + 1,
            y=y + 13,
            string=f"Roubles: {self.engine.player.currency.roubles}"
        )

        console.print(
            x=x + 1,
            y=y + 15,
            string=f"Attack : {self.engine.player.fighter.power}"
        )
        console.print(
            x=x + 1,
            y=y + 16,
            string=f"Defense: {self.engine.player.fighter.defense}"
        )

        for i,skill in enumerate(self.engine.player.skills.skills):
            console.print(
                x=x + 1,
                y=18+i,
                string=f"{skill.name}"
            )
            console.print(
                x=9,
                y=18+i,
                string=":",
            )
            console.print(
                x=11,
                y=18+i,
                string=f"{skill.level}"
            )
        

class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=35,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=1, string="Congratulations! You level up!")
        console.print(x=x + 1, y=2, string="Select an attribute to increase.")

        console.print(
            x=x + 1,
            y=4,
            string=f"a) Constitution (+20 HP, from {self.engine.player.fighter.max_hp})",
        )
        console.print(
            x=x + 1,
            y=5,
            string=f"b) Strength (+1 attack, from {self.engine.player.fighter.power})",
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"c) Agility (+1 defense, from {self.engine.player.fighter.defense})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            elif index == 1:
                player.level.increase_power()
            else:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None

class EscapeMenuEventHandler(AskUserEventHandler):
    TITLE = "PAUSE MENU"

    
    def restart_game(self) -> None:
        """Handle restarting a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        # try:
        #     p = psutil.Process(os.getpid())
        #     for handler in p.open_files() + p.connections():
        #         os.close(handler.fd)
        # except Exception as e:
        #     logging.error(e)

        python = sys.executable
        os.execl(python, python, *sys.argv)

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=35,
            height=30,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(
            x=x + 1,
            y=4,
            string=f"q) Save and Quit",
        )
        console.print(
            x=x + 1,
            y=5,
            string=f"l) Load Game",
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"r) Restart",
        )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[BaseEventHandler]:
        if event.sym == tcod.event.K_q:
            raise SystemExit()
        elif event.sym == tcod.event.K_l:
            try:
                return MainGameEventHandler(("savegame.sav"))
            except FileNotFoundError:
                return PopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()  # Print to stderr.
                return PopupMessage(self, f"Failed to load save:\n{exc}")
        elif event.sym == tcod.event.K_r:
            self.restart_game()
        
        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None

class BasicMenuHandler(AskUserEventHandler):
  TITLE = '<missing title>'
  def __init__(self, engine, options, x=0, y=0, height=None, width=None):
    super().__init__(engine)
    self.options = options
    if not height:
      height = len(self.options) + 2
    if not width:
      width = 20

    if y + height > engine.game_world.viewport_height:
      height = engine.game_world.viewport_height - y

    self.menu = ui.BasicMenu(self.options, x, y, height, width, title=self.TITLE)

  def on_item_selected(self):
    return PopupMessage(MainGameEventHandler(self.engine), self.options[self.menu.cursor])

  def ev_keydown(self, event):
    key = event.sym

    if key in (tcod.event.K_UP, tcod.event.K_KP_8):
      self.menu.up()
      return None
    elif key in (tcod.event.K_DOWN, tcod.event.K_KP_2):
      self.menu.down()
      return None
    elif key in CONFIRM_KEYS:
      return self.on_item_selected()

    elif key == tcod.event.K_ESCAPE:
      return MainGameEventHandler(self.engine)

  def ev_mousemotion(self, event):
    self.menu.mouse_select(event.tile.x, event.tile.y)

  def ev_mousebuttondown(self, event):
    selected = self.menu.mouse_select(event.tile.x, event.tile.y)
    if selected is not None:
      return self.on_item_selected()

  def ev_mousewheel(self, event):
    if event.y > 0:
      self.menu.up()
    elif event.y < 0:
      self.menu.down()

  def on_render(self, console):
    super().on_render(console)
    self.menu.render(console)

class InventoryEventHandler(BasicMenuHandler):
  """ This handler lets the user select an item.
  What happens then depends on the subclass."""
  TITLE = '<missing title>'

  def __init__(self, engine, filter_function=lambda x: True):
    self.filter_function = filter_function
    self.filtered_items = []
    for item in engine.player.inventory.items:
      if self.filter_function(item):
        self.filtered_items.append(item)
    self.options = options = []

    min_width = len(self.TITLE) + 6
    for i in self.filtered_items:
        is_equipped = False
        if i.equippable:
            is_equipped = engine.player.equipment.item_is_equipped(i.equippable.equipment_type)
        item_name = i.name
        if is_equipped:
            item_name += ' (E)'
        options.append(item_name)
        if len(item_name) > min_width:
            min_width = len(item_name)

    super().__init__(engine, options, width=min_width + 2)

  def on_render(self, console):
    super().on_render(console)

  def on_item_selected(self, item):
    """Called when the user selectes a valid item."""
    raise NotImplementedError()

class ShopInventoryEventHandler(BasicMenuHandler):
  """ This handler lets the user select an item.
  What happens then depends on the subclass."""
  TITLE = '<missing title>'

  def __init__(self, engine, filter_function=lambda x: True):
    self.filter_function = filter_function
    self.filtered_items = []
    for item in self.entity.shop.items:
      if self.filter_function(item):
        self.filtered_items.append(item)
    self.options = options = []

    min_width = len(self.TITLE) + 6
    for i in self.filtered_items:
        item_name = i.name
        options.append(item_name)
        if len(item_name) > min_width:
            min_width = len(item_name)

    super().__init__(engine, options, width=min_width + 2)

  def on_render(self, console):
    super().on_render(console)

  def on_item_selected(self, item):
    """Called when the user selectes a valid item."""
    raise NotImplementedError()

class ShopInventoryPurchaseHandler(ShopInventoryEventHandler):
  """Handle using an inventory item."""

  TITLE = 'Select an item to buy'

  def on_item_selected(self):#, item):
    """Return the action for the selected item"""
    item = self.filtered_items[self.menu.cursor]
    self.entity.shop.sell(item)


class InventoryActivateHandler(InventoryEventHandler):
  """Handle using an inventory item."""

  TITLE = 'Select an item to use'

  def on_item_selected(self):#, item):
    """Return the action for the selected item"""
    item = self.filtered_items[self.menu.cursor]
    if item.consumable:
      return item.consumable.get_action(self.engine.player)
    elif item.equippable:
      return EquipAction(self.engine.player, item)
    else:
      return None


class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    TITLE = "Select an item to drop"

    # def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
    #     """Drop this item."""
    #     return DropItemAction(self.engine.player, item)
    def on_item_selected(self) -> Optional[ActionOrHandler]:
        """Drop this item."""
        item = self.filtered_items[self.menu.cursor]
        return DropItemAction(self.engine.player, item)

class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        viewport = self.engine.game_map.get_viewport()
        engine.mouse_location = player.x - viewport[0], player.y - viewport[1]

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)        
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        viewport = self.engine.game_map.get_viewport()
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            # x = max(0, min(x, self.engine.game_map.width - 1))
            viewport_width = viewport[2] - viewport[0]
            viewport_height = viewport[3] - viewport[1]
            # print(f'Viewport width: {viewport_width}')
            # print(f'Viewport height: {viewport_height}')
            x = max(0, min(x,  viewport_width - 1))
            # y = max(0, min(y, self.engine.game_map.height - 1))
            y = max(0, min(y, viewport_height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                viewport = self.engine.game_map.get_viewport()
                x = event.tile.x + viewport[0]
                y = event.tile.y + viewport[1]
                return self.on_index_selected(x,y)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()

class FireSelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        viewport = self.engine.game_map.get_viewport()
        # print(f"Player x,y           : {player.x},{player.y}")
        # print(f"Player x,y[viewport] : {player.x - viewport[0]},{player.y - viewport[1]}")
        engine.mouse_location = player.x - viewport[0], player.y - viewport[1]
        enemies = []
        for enemy in self.engine.game_map.enemies:
            # print(f"Appending: ({enemy},{enemy.distance(player.x, player.y)})")
            enemies.append((enemy,enemy.distance(player.x, player.y)))
        enemies.sort(key=lambda enemies: enemies[1])
        
        for enemy,distance in enemies:
            if self.engine.game_map.visible[enemy.x, enemy.y]:
                engine.mouse_location = (enemy.x- viewport[0],enemy.y- viewport[1])
                break       
            

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.red
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        viewport = self.engine.game_map.get_viewport()
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            # x = max(0, min(x, self.engine.game_map.width - 1))
            x = max(0, min(x,  (viewport[2]-viewport[0]) - 1))
            # y = max(0, min(y, self.engine.game_map.height - 1))
            y = max(0, min(y, (viewport[3]-viewport[1]) - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in FIRE_CONFIRM_KEYS:
            mouse_x,mouse_y = self.engine.mouse_location
            # print(f"Mouse           ? {mouse_x, mouse_y}")
            # print(f"Mouse [viewport]? {mouse_x+ viewport[0], mouse_y+ viewport[1]}")
            map_x = mouse_x + viewport[0]
            map_y = mouse_y + viewport[1]
            # return self.on_index_selected(*self.engine.mouse_location)
            return self.on_index_selected(map_x, map_y)
        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                viewport = self.engine.game_map.get_viewport()
                x = event.tile.x + viewport[0]
                y = event.tile.y + viewport[1]
                return self.on_index_selected(x,y)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()

class LookHandler(SelectIndexHandler):
    """Lets the player look around using the keyboard."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return to main handler."""
        return MainGameEventHandler(self.engine)

class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))

class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))
     
class SingleAimedRangedAttackHandler(FireSelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location
        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        # console.draw_rect(
        #     x=x,
        #     y=y,
        #     ch=0,
        #     width=0,
        #     height=1,
        #     fg=color.red,
        # )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))

class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & (
            tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT
        ):
            return TakeStairsAction(player)

        if key in ACTIVATE_KEYS:
            # print(f'Pressing Activate Key')
            if (player.x, player.y) == self.engine.game_map.downstairs_location:
                return TakeStairsAction(player)
            else:
                return ActivateAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.K_ESCAPE:
            return EscapeMenuEventHandler(self.engine)
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_F1:
            return self.engine.game_map.reveal_map()
        elif key == tcod.event.K_F2:
            return self.engine.player.fighter.die()
        elif key == tcod.event.K_f:
            action =  player.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON).equippable.get_fire_action(player) if player.equipment.item_is_equipped(EquipmentType.RANGED_WEAPON) else None

        elif key == tcod.event.K_g:
            action = PickupAction(player)

        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)

        elif key == tcod.event.K_r:
            action = ReloadAction(player, player.equipment.get_item_in_slot(EquipmentType.RANGED_WEAPON))

        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)
        elif key in LOOK_KEYS:
            return LookHandler(self.engine)

        # No valid key was pressed
        # print(key)
        return action

class GameOverEventHandler(EventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        #PostMortemViewer(engine)

    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def on_restart(self) -> None:
        """Handle restarting a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        # try:
        #     p = psutil.Process(os.getpid())
        #     for handler in p.open_files() + p.connections():
        #         os.close(handler.fd)
        # except Exception as e:
        #     logging.error(e)

        python = sys.executable
        os.execl(python, python, *sys.argv)

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()
        
        if event.sym == tcod.event.K_r:
            self.on_restart()

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
        return None

class PostMortemViewer(EventHandler):
    """Print the post-mortem on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        postmortem_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        postmortem_console.draw_frame(0, 0, postmortem_console.width, postmortem_console.height)
        postmortem_console.print_box(
            0, 0, postmortem_console.width, 1, "┤Post-Mortem [Escape twice to Quit]├", alignment=tcod.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.mortem_log.render_messages(
            postmortem_console,
            1,
            1,
            postmortem_console.width - 2,
            postmortem_console.height - 2,
            self.engine.mortem_log.messages[: self.cursor + 1],
        )
        postmortem_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[GameOverEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        elif event.sym in QUIT_KEYS:  # Any other key moves back to the main game state.
            # return MainGameEventHandler(self.engine)
            return GameOverEventHandler(self.engine)
        return None