from __future__ import annotations
from typing import TYPE_CHECKING

from nicegui import ui


class Movable(ui.element, component="movable.js"):
    def __init__(self, x: int = 0, y: int = 0):
        super().__init__()
        self._props["x"] = x
        self._props["y"] = y
        self._classes.append("movable-item")

    async def size(self) -> tuple[int, int]:
        w, h = await self.run_method("getSize")
        print("=>w,h", w, h)
        return w, h


class MovableContainer(ui.element, component="movable_container.js"):
    def __init__(self, min_width: int = 10, min_height: int = 10):
        super().__init__()
        self._props["minWidth"] = min_width
        self._props["minHeight"] = min_height
