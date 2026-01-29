from __future__ import annotations
from typing import Type, TypeVar, Callable, Awaitable

from .theme import BaseTheme, ThemeType

from nicegui import ui

SectionRenderer = Callable[[ThemeType], Awaitable[None]]


class LayoutSection:
    def __init__(self, layout: PageLayout, renderer: SectionRenderer) -> None:
        self.layout = layout
        self.renderer = renderer

    @ui.refreshable_method
    async def render(self) -> None:
        await self.renderer(self.layout.theme)


SectionType = TypeVar("SectionType", bound=LayoutSection)


class PageLayout[ThemeType: BaseTheme]:
    """
    A generic layout manager
    """

    def __init__(self, theme: ThemeType, **section_renderers: SectionRenderer):
        self.theme = theme
        self._sections: dict[str, LayoutSection] = {}

        for section_name, section_renderer in section_renderers.items():
            self._add_section(section_name, section_renderer)

    def _add_section(self, name: str, renderer: SectionRenderer) -> None:
        self._sections[name] = LayoutSection(self, renderer)

    async def _render_section(self, name: str):
        await self._sections[name].render()

    @ui.refreshable_method
    async def render(self) -> ui.element:
        with self.theme.div() as top:
            self.theme.label(
                "Base PageLayout (probably not what you're looking for ^^')"
            )
        return top

    async def refresh(self, section_name: str | None = None):
        if section_name is None:
            await self.render.refresh()
        else:
            section = self._sections[section_name]
            await section.render.refresh()
