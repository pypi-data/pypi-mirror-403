from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
import random

import nicegui.ui
import nicegui.event

from .darkplate import DarkPlate, presets

if TYPE_CHECKING:
    from .darkplate import PageLayout


@nicegui.ui.page("/")
async def demo():

    @dataclass
    class States:
        current_view: str | None = None
        layout: PageLayout | None = None
        set_current_view_event = nicegui.event.Event[str]()
        refresh_all_event = nicegui.event.Event()

        def view_names(self) -> tuple[str, ...]:
            return ("bishop", "king", "queen", "knight", "pawn", "rook")

        def view_icon(self, view_name: str) -> str:
            return f"fa-solid fa-chess-{view_name}"

        @property
        def avatar_url(self) -> str:
            return "https://avataaars.io/?avatarStyle=&topType=LongHairStraight&accessoriesType=Blank&hairColor=BrownDark&facialHairType=Blank&clotheType=BlazerShirt&eyeType=Default&eyebrowType=Default&mouthType=Default&skinColor=Light"

    states = States()

    # ui = DarkPlate(presets.get("default"))
    # ui = DarkPlate(presets.get("sky"))
    # ui = DarkPlate(presets.get("lime"))
    # ui = DarkPlate(presets.get("fuchsia"))
    # ui = DarkPlate(presets.get("neutral"))
    # ui = DarkPlate(presets.get("hell"))
    ui = DarkPlate(presets.get("slate"))

    async def header_renderer(ui: DarkPlate):
        with ui.row(wrap=False, align_items="center"):
            with ui.border(p=2):
                ui.icon("sym_s_diamond", size="xl")
            ui.label("MyApp").classes("text-4xl font-semibold")

        ui.space()

        fullscreen = ui.fullscreen()
        ui.button(
            icon="sym_s_fullscreen",
            color=ui._params.color,
            on_click=fullscreen.toggle,
        ).props("flat dense").classes("opacity-50 hover:opacity-100")

        ui.theme_button(presets, states.refresh_all_event).classes(
            "opacity-50 hover:opacity-100"
        )
        with ui.avatar(color=ui._params.brand).props("round"):
            ui.image(states.avatar_url)

    async def on_left_item(view_name: str):
        states.current_view = view_name
        if states.layout is not None:
            await states.layout.refresh("left")
            await states.layout.refresh("main")

    states.set_current_view_event.subscribe(on_left_item)

    async def left_renderer(ui: DarkPlate):
        with ui.row(align_items="center").classes("h-full"):
            with ui.list().props("xbordered xseparator"):
                if 0:
                    ui.item_label("Classes").props("header").classes("text-bold")
                    ui.separator()
                for view_name in states.view_names():
                    with ui.item(
                        on_click=lambda view_name=view_name: states.set_current_view_event.emit(
                            view_name  # type: ignore
                        )
                    ) as item:
                        with ui.item_section().props("side").classes("p-5"):
                            ui.icon(states.view_icon(view_name))
                        with ui.item_section().classes("@max-3xs:hidden"):
                            ui.item_label(view_name.title())
                    if view_name != states.current_view:
                        item.classes("opacity-50")

    async def main_renderer(ui: DarkPlate):
        current_view = states.current_view
        if current_view is None:
            current_view = "home"
            icon = "sym_o_home"
        else:
            icon = states.view_icon(current_view)

        with ui.row(align_items="center"):
            ui.icon(icon, size="xl")
            ui.label(f"{current_view.title()}").classes("text-4xl text-bold")

        if states.current_view is None:
            return

        _ = ui._params
        with ui.scroll_area().classes("w-full h-full"):
            with ui.column(align_items="center").classes("w-full h-full"):
                with ui.row(align_items="center").classes("xw-full h-full"):
                    # ui.space()
                    with ui.row(wrap=False, align_items="center").classes("w-full"):
                        nb = random.randint(2, 8)
                        index = 0
                        for i in range(nb, 0, -1):
                            index += 1
                            with ui.column(align_items="center"):
                                for j in range(i):
                                    with ui.border(filled=True):
                                        with ui.element().classes(f"bg-{_.color}"):
                                            with ui.row(align_items="center"):
                                                ui.icon("sym_s_box", size="lg")
                                                ui.label(f"#{index}").classes(
                                                    "opacity-100"
                                                )
                # ui.space()

    states.layout = ui.header_left_main(
        header_renderer,
        left_renderer,
        main_renderer,
    )
    states.refresh_all_event.subscribe(states.layout.refresh)
    await states.layout.render()


if __name__ in {"__main__", "__mp_main__"}:
    nicegui.ui.run()
