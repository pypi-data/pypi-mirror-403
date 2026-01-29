from __future__ import annotations
from typing import Type, TypeVar, Literal

import dataclasses

from nicegui import ui

from .._utils.page_layout import PageLayout, SectionRenderer
from .._utils.theme import (
    BaseTheme,
    ThemePresets,
    ThemePreset,
    Direction,
    Size,
)


@dataclasses.dataclass
class DarkplatePreset(ThemePreset):

    light_direction: Direction = "tr"
    light_hue: str = "orange"
    light_level: int = 100
    light_spread: int = 30
    light_opacity: int = 50

    @property
    def light(self) -> str:
        return f"{self.light_hue}-{self.light_level}"

    shadow_hue: str = "stone"
    shadow_level: int = 950
    shadow_spread: int = 30
    shadow_opacity: int = 50

    @property
    def shadow_direction(self) -> str:
        return self.opposite_direction(self.light_direction)

    @property
    def shadow(self) -> str:
        return f"{self.shadow_hue}-{self.shadow_level}"

    mouse_hue: str = "orange"
    mouse_level: int = 300
    mouse_opacity: int = 50
    level_light: int = 700
    level_base: int = 800
    level_dark: int = 900

    rounded: Size = "lg"

    @property
    def round_px(self) -> str:
        return self.size_to_rem(self.rounded)

    border_px = 1


presets = ThemePresets[DarkplatePreset]()

presets.register(
    default=DarkplatePreset(),
    sky=DarkplatePreset(hue="sky"),
    lime=DarkplatePreset(
        brightness=0,
        hue="emerald",
        level=700,
        shadow_hue="emerald",
        shadow_level=800,
        shadow_opacity=100,
        light_hue="lime",
        light_level=200,
        light_opacity=50,
        light_direction="tl",
        mouse_hue="emerald",
        mouse_level=400,
        mouse_opacity=100,
    ),
    fuchsia=DarkplatePreset(
        brightness=0,
        hue="fuchsia",
        level=800,
        shadow_hue="fuchsia",
        shadow_level=900,
        shadow_opacity=100,
        light_hue="pink",
        light_level=300,
        light_opacity=80,
        mouse_hue="rose",
        mouse_level=400,
        mouse_opacity=30,
    ),
    slate=DarkplatePreset(
        hue="slate",
        level=700,
        brightness=-1,
        shadow_hue="slate",
        shadow_level=900,
        shadow_opacity=50,
        light_hue="cyan",
        light_level=500,
        light_opacity=100,
        mouse_hue="cyan",
        mouse_level=800,
        mouse_opacity=100,
    ),
    gray=DarkplatePreset(hue="gray"),
    zinc=DarkplatePreset(hue="zinc"),
    neutral=DarkplatePreset(
        hue="neutral", level=700, brightness=-2, shadow_hue="neutral", shadow_level=900
    ),
    hell=DarkplatePreset(
        hue="orange",
        level=900,
        brightness=0,
        shadow_hue="orange",
        shadow_level=500,
        shadow_opacity=100,
        light_hue="yellow",
        light_level=200,
        light_opacity=100,
        mouse_hue="red",
        mouse_level=500,
        mouse_opacity=100,
    ),
    stone=DarkplatePreset(hue="stone"),
)

T = TypeVar("T", bound=ui.element)


class HeadLeftMain(PageLayout["DarkPlate"]):
    """
    A darkplate layout with header, left and main sections.
    """

    @ui.refreshable_method
    async def render(self) -> ui.element:
        ui = self.theme
        ui.load_google_font()
        with ui.fullpage() as top:
            with ui.gt(30, 4):
                with ui.column().classes("w-full h-full gap-0"):
                    with ui.row(align_items="center").classes("w-full py-3 px-6"):
                        await self._render_section("header")
                    with ui.row().classes("w-full h-full gap-0"):
                        with ui.splitter(value=15, hide_scrollbars="both").classes(
                            "w-full h-full"
                        ) as splitter:
                            with splitter.before:
                                with ui.gb(30, 4):
                                    with ui.p(8).classes("h-full"):
                                        await self._render_section("left")
                        with splitter.after:
                            with ui.gbl(50, 30):
                                with ui.gbr(50, 30):
                                    with ui.gb(100, 80):
                                        with ui.p(8).classes("h-full"):
                                            await self._render_section("main")
        return top


class DarkPlate(BaseTheme):

    def __init__(self, preset: DarkplatePreset):
        self._params = preset
        self.dark_mode(self._params.dark)

    def border(
        self, width: int | None = None, filled: bool = True, p: int = 8
    ) -> ui.element:
        _ = self._params
        width = width or _.border_px
        with self.div().classes(
            "xflex-1 "
            "darkplate-border "
            f"rounded-{_.rounded} overflow-hidden "
            "transition-colors duration-300 "
            f"hover:bg-{_.mouse_hue}-{_.mouse_level}/{_.mouse_opacity} "
        ):
            # Shadow
            with self.div().classes(
                f"rounded-{_.rounded} xp-[{width}px] "
                f"bg-gradient-to-{_.light_direction} from-{_.shadow}/{_.shadow_opacity} to-{_.shadow_spread}% "
                "transition-all duration-300 "
                # f"hover:bg-gradient-to-{_.shadow_direction} "
                # f"hover:to-{_.shadow_spread/2} "
                # f"hover:bg-gradient-to-t "
                "bg-blend-multiply "
            ):
                # Light
                with self.div().classes(
                    f"rounded-{_.rounded} p-[{width}px] "
                    f"bg-gradient-to-{_.shadow_direction} from-{_.light}/{_.light_opacity} to-{_.light_spread}% "
                    "transition-all duration-300 "
                    # f"hover:bg-gradient-to-{_.light_direction} "
                    # f"hover:to-{_.light_spread*2} "
                    # f"hover:bg-gradient-to-b "
                    "bg-blend-screen "
                ):
                    # Fill
                    fill = self.div().classes(
                        f"rounded-[calc({_.round_px}-{width}px)] overflow-hidden "
                    )
                    if filled:
                        fill.classes(f"bg-{_.color} p-{p}")
        return fill

    def add_gradient(
        self, el: T, depth: int, spread: int, direction: Direction = "t"
    ) -> T:
        if depth:
            _ = self._params
            el.classes(
                f"bg-gradient-to-{direction} from-{_.shadow}/{depth} to-{spread}% "
            )
        return el

    def gt(self, depth: int, spread: int = 100) -> ui.element:
        div = self.div().classes(f"darkplate-gt-{depth} w-full h-full xborder")
        self.add_gradient(div, depth, spread, direction="b")
        return div

    def gb(self, depth: int, spread: int = 100) -> ui.element:
        div = self.div().classes(f"darkplate-gb-{depth} xborder")
        div.classes("w-full h-full")
        self.add_gradient(div, depth, spread, direction="t")
        return div

    def gbl(self, depth: int, spread: int = 100) -> ui.element:
        div = self.div().classes(f"darkplate-gbl-{depth} xborder")
        div.classes("w-full h-full")
        self.add_gradient(div, depth, spread, direction="tr")
        return div

    def gbr(self, depth: int, spread: int = 100) -> ui.element:
        div = self.div().classes(f"darkplate-gbr-{depth} xborder")
        div.classes("w-full h-full")
        self.add_gradient(div, depth, spread, direction="tl")
        return div

    def gtb(self, depth: int, spread: int = 10) -> ui.element:
        with self.gt(depth, spread):
            el = self.gb(depth, spread)
        return el

    def hbox(self) -> ui.row:
        o = ui.row(wrap=False, align_items="center").classes(
            "w-full h-full gap-0 p-0 xborder"
        )
        return o  # _.framed(o, depth)

    def vbox(self) -> ui.column:
        o = ui.column(wrap=False, align_items="center").classes(
            f"w-full h-full gap-0 p-0 xbg-{self._params.color} xborder border-red-500 "
        )
        return o  # _.framed(o, depth)

    def header_left_main(
        self,
        header_renderer: SectionRenderer,
        left_renderer: SectionRenderer,
        main_renderer: SectionRenderer,
    ) -> HeadLeftMain:
        return HeadLeftMain(
            self, header=header_renderer, left=left_renderer, main=main_renderer
        )
