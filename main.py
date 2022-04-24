#!/usr/bin/env python3
import traceback

import tcod

import color
import exceptions
import input_handlers
import setup_game

# WIDTH, HEIGHT = 720, 480
WIDTH, HEIGHT = 1280, 720
# FLAGS = tcod.context.SDL_WINDOW_FULLSCREEN_DESKTOP | tcod.context.SDL_WINDOW_MAXIMIZED
FLAGS = tcod.context.SDL_WINDOW_MAXIMIZED | tcod.context.SDL_WINDOW_RESIZABLE
# FLAGS = tcod.context.SDL_WINDOW_RESIZABLE

def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")


def main() -> None:
    screen_width = 80
    screen_height = 60

    tcod.lib.SDL_SetHint(b"SDL_RENDER_SCALE_QUALITY", b"0")

    tileset = tcod.tileset.load_tilesheet(
        # "img\dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
        "img\Taffer_10x10.png", 16, 16, tcod.tileset.CHARMAP_CP437
        # "img\onebit.png", 20, 21, tcod.tileset.CHARMAP_CP437
    )

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

    # root_console = context.new_console(
    #     min_columns=min_c,
    #     min_rows=min_r,
    #     order="F",
    #     magnification=2,
    # )
    root_console = tcod.Console(
        width=screen_width,
        height=screen_height,
        order="F",
        # magnification=2,
    )


    with tcod.context.new(
        width=WIDTH,
        height=HEIGHT,
        columns=root_console.width,
        rows=root_console.height,
        tileset=tileset,
        title="L.U.R.K.E.R.",
        vsync=True,
        sdl_window_flags=FLAGS,
        renderer=tcod.context.RENDERER_OPENGL2
    ) as context:
        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console, integer_scaling=True, keep_aspect=True)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error
                        )
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and quit.
            save_game(handler, "savegame.sav")
            raise
        except BaseException:  # Save on any other unexpected exception.
            save_game(handler, "savegame.sav")
            raise


if __name__ == "__main__":
    main()