from typing import Literal, TypeVar, Any

import dataclasses
from functools import wraps

from nicegui import ui
from nicegui.event import Event

Direction = Literal["t", "b", "tl", "tr", "bl", "br", "r", "l"]
Size = Literal["xs", "sm", "md", "lg", "xl", "2xl", "3xl", "4xl", "none", "full"]
FontFamily = (
    Literal[
        "sans",
        "serif",
        "mono",
        "[ui-sans-serif]",
        "[system-ui]",
        "[Arial]",
        "[-apple-system]",
        "[Apple Color Emoji]",
        "[BlinkMacSystemFont]",
        "[Helvetica Neue]",
        "[Inter var]",
        "[Noto Color Emoji]",
        "[Noto Sans]",
        "[Roboto]",
        "[sans-serif]",
        "[Segoe UI]",
        "[Segoe UI Emoji]",
        "[Segoe UI Symbol]",
    ]
    | str
)
FontTracking = Literal["tighter", "tight", "normal", "wide", "wider", "widest"] | str


@dataclasses.dataclass
class ThemePreset:
    dark: bool = True
    brightness: int = 0

    # load_google_font: str|None=None
    load_google_font: str | None = "Urbanist:ital,wght@0,100..900;1,100..900"
    font_family: FontFamily = "[Urbanist]"
    # font_family: FontFamily = "[Roboto]"
    font_tracking: FontTracking = "normal"  # "[.5em]"

    # hue:str = "emerald"
    # hue:str = "amber"
    # hue:str = "slate"
    # hue:str = "orange"
    # hue:str = "blue"
    # hue:str = "purple"
    # hue: str = "stone"
    hue: str = "neutral"
    level: int = 500

    brand: str = "#33A491"

    @property
    def color(self) -> str:
        return f"{self.hue}-{self.level}"

    @classmethod
    def opposite_direction(cls, direction: str) -> str:
        return dict(
            t="b",
            b="t",
            tl="br",
            tr="bl",
            bl="tr",
            br="tl",
            r="l",
            l="r",
        )[direction]

    @classmethod
    def size_to_rem(cls, size: str) -> str:
        return {
            "xs": "0.125rem",
            "sm": "0.25rem",
            "md": "0.375rem",
            "lg": "0.5rem",
            "xl": "0.75rem",
            "2xl": "1rem",
            "3xl": "1.5rem",
            "4xl": "2rem",
            "none": "0.rem",
        }[size]


class ThemePresets[PresetType: ThemePreset]:

    def __init__(self) -> None:
        super().__init__()
        self._presets: dict[str, PresetType] = {}

    def register(self, **presets: PresetType) -> None:
        for name, preset in presets.items():
            self._presets[name] = preset

    def get(self, preset_name: str) -> PresetType:
        return self._presets[preset_name]

    def preset_names(self) -> tuple[str, ...]:
        return tuple(self._presets.keys())


class _EmptyTheme:
    """
    This namespace is filled with all the nicegui.ui object.
    But your IDE will not detect these objects.
    """

    # To my surprise, SimpleNamespace is way slower than a simple class
    # see: https://discuss.python.org/t/add-builtins-namespace/78343/3
    pass


for name, value in vars(ui).items():
    setattr(_EmptyTheme, name, value)


class BaseTheme(_EmptyTheme):
    """
    This class contains nicegui.ui.*
    But code completion will only work on objects declared here.
    Please update the list when needed.
    """

    element = ui.element
    row = ui.row
    column = ui.column
    space = ui.space
    separator = ui.separator
    # splitter = ui.splitter overridden
    scroll_area = ui.scroll_area

    label = ui.label
    icon = ui.icon
    button = ui.button
    fab = ui.fab
    avatar = ui.avatar
    image = ui.image

    list = ui.list
    item = ui.item
    item_label = ui.item_label
    item_section = ui.item_section

    # notify = ui.notify # wont work: it's a function :/
    # add_head_html = ui.add_head_html  # wont work: it's a function :/

    dark_mode = ui.dark_mode
    fullscreen = ui.fullscreen
    refreshable = ui.refreshable

    def __init__(self, preset: ThemePreset):
        self._params = preset

    def page_setup(self):
        """
        Do page level commands like loadign google font, fontawesome, settings dark mode...
        """
        self.dark_mode(self._params.dark)
        ui.add_head_html(
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">'
        )
        if self._params.load_google_font is not None:
            self.load_google_font(self._params.load_google_font)

        ui.add_head_html(
            """
            <style type="text/tailwindcss">
                @layer utilities {

                /* Chrome, Safari and Opera */
                .no-scrollbar::-webkit-scrollbar {
                display: none;
                }

                .no-scrollbar {
                -ms-overflow-style: none; /* IE and Edge */
                scrollbar-width: none; /* Firefox */
                }

                }
            </style>
        """
        )

        ui.add_head_html(
            """
            <style type="text/tailwindcss">
                @layer components {
                    .blue-box {
                        @apply bg-blue-500 p-12 text-center shadow-lg rounded-lg text-white;
                    }
                }
            </style>
        """
        )

    def load_google_font(self, family: str = "Poppins:wght@400;700"):
        self.add_head_html(
            f"""
<!-- Preconnect for faster loading -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- Load Google Font -->
<link href="https://fonts.googleapis.com/css2?family={family}&display=swap" rel="stylesheet">
"""
        )

    def notify(
        self,
        message: Any,
        *,
        position: Literal[
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "top",
            "bottom",
            "left",
            "right",
            "center",
        ] = "bottom",
        close_button: bool | str = False,
        type: (
            Literal[  # pylint: disable=redefined-builtin
                "positive",
                "negative",
                "warning",
                "info",
                "ongoing",
            ]
            | None
        ) = None,
        color: str | None = None,
        multi_line: bool = False,
        **kwargs: Any,
    ):
        ui.notify(
            message=message,
            position=position,
            close_button=close_button,
            type=type,
            color=color,
            multi_line=multi_line,
            **kwargs,
        )

    def add_head_html(self, code: str, *, shared: bool = False) -> None:
        return ui.add_head_html(code, shared=shared)

    def div(self) -> ui.element:
        return ui.element()

    def p(self, padding: int) -> ui.element:
        return self.div().classes(f"p-{padding}")

    def splitter(
        self,
        value: float,
        hide_scrollbars: Literal["before", "after", "both", "none"] = "none",
    ) -> ui.splitter:
        """
        If scrollbars is hidden in berore or after, that panel also receives
        the "@container" class. So you can then use container breakpoints in
        your responsive design
        (https://tailwindcss.com/docs/responsive-design#container-size-reference)
        """
        splitter = ui.splitter(value=value).props("separator-class=opacity-0")

        if hide_scrollbars != "none":
            hidden_scrollbars = []
            if hide_scrollbars in ("before", "both"):
                hidden_scrollbars.append("q-splitter__before")
            if hide_scrollbars in ("after", "both"):
                hidden_scrollbars.append("q-splitter__after")
            for panel_class in hidden_scrollbars:
                ui.query(f"#c{splitter.id} .{panel_class}").classes(
                    "no-scrollbar @container"
                )
        return splitter

    def fullpage(self) -> ui.column:
        """
        Returns a column with 100% width and 100% height.

        NB: This sets the global view padding to 0 in order to work
        properly. You should use only once per page.
        """
        _ = self._params
        self.page_setup()
        ui.query(".nicegui-content").classes("p-0")
        with self.div().classes(
            f"darkplate-fullpage w-[100vw] h-[100vh] p-4 bg-[#000000]"
        ):
            top = ui.column().classes(
                f"w-full h-full "
                "p-0 "
                "rounded-4xl overflow-hidden "
                f"bg-{_.color} brightness-{100+self._params.brightness*10} "
                f"font-{_.font_family} "
                f"tracking-{_.font_tracking} "
            )
        return top

    def theme_button(self, presets: ThemePresets, refresh_all_event: Event) -> ui.fab:
        def on_click(preset_name):
            refresh_all_event.emit()
            self._params = presets.get(preset_name)

        with ui.fab("palette", direction="down", color="none").props(
            "padding=xs flat vertical-actions-align=left"
        ).classes(f"text-{self._params.hue}") as fab:
            for preset_name in presets.preset_names():
                preset = presets.get(preset_name)
                ui.fab_action(
                    "colorize",
                    label=preset_name,
                    on_click=lambda preset_name=preset_name: on_click(preset_name),
                    color=preset.color,
                ).props("label-position=right")
        return fab


ThemeType = TypeVar("ThemeType", bound=BaseTheme)
