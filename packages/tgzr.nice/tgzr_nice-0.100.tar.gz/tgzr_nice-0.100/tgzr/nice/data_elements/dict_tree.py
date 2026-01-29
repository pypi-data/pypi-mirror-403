from __future__ import annotations
from typing import Callable, Any, Awaitable, Type
from typing_extensions import Protocol

from nicegui import ui
import pydantic

from ..tgzr_visid import TGZRVisId

import rich

# IDKY these do not please the linter :(
# class InputRenderer:
#     def __call__(self, tree_item: _TreeItem) -> ValueSetter: ...
# class ToolsRenderer:
#     def __call__(self, tree_item: _TreeItem) -> None: ...
# So I use those:
ValueSetter = Callable[[Any], Awaitable[None]]
InputRenderer = Callable[["_TreeItem"], Awaitable[ValueSetter]]
ToolsRenderer = Callable[["_TreeItem"], Awaitable[None]]


class OnClickedCallback(Protocol):
    async def __call__(self, tree_item: _TreeItem) -> None: ...
class OnEditedCallback(Protocol):
    async def __call__(
        self, tree_item: _TreeItem, op: str, op_kwargs: dict[str, Any]
    ) -> None: ...
class OnUpdateRequestCallback(Protocol):
    async def __call__(self, tree_item: _TreeItem, item_path: list[str]) -> None: ...


async def default_input_renderer(tree_item: _TreeItem) -> ValueSetter:
    value = tree_item.value
    if value in (True, False):
        el = ui.switch(value=value)
        set_value = el.set_value
    else:
        el = ui.input(value=str(value))
        set_value = el.set_value
    el.props("dense rounded standout").classes("w-full")

    async def setter(value):
        set_value(value)

    return setter


async def read_only_input_renderer(tree_item: _TreeItem) -> ValueSetter:
    value = tree_item.value
    with ui.row(align_items="center").classes(
        "min-h-[3em] w-full hover:border-l-2 hover:border-neutral-500 p-2"
    ):
        if value in (True, False):
            el = ui.checkbox(value=value)
            el.enabled = False
        elif isinstance(value, set):
            if value:
                el = ui.label(", ".join([i for i in sorted(value)]))
            else:
                el = ui.label("<emtpty set>")
        else:
            el = ui.label(str(value))
        el.props("dense rounded standout").classes("w-full")

    def read_only(value):
        pass

    return read_only


async def default_tools_renderer(tree_item: _TreeItem):
    if isinstance(tree_item, TreeGroup):
        return

    value = tree_item.value
    props = "dense flat"
    if isinstance(value, list):
        ui.button(icon="add").props(props)
        ui.button(icon="variable_remove").props(props)
    elif isinstance(value, list):
        ui.button(icon="delete").props(props)


class TreeView:
    def __init__(
        self,
        visid: TGZRVisId,
        defaults: pydantic.BaseModel | None = None,
        input_renderer: InputRenderer | None = None,
        tools_renderer: ToolsRenderer | None = None,
        on_clicked: OnClickedCallback | None = None,
        on_edited: OnEditedCallback | None = None,
        on_update_request: OnUpdateRequestCallback | None = None,
        expanded_icon: str | None = None,
        collapsed_icon: str | None = None,
        value_icon: str | None = None,
        auto_expand_groups: bool = True,
    ) -> None:
        self._visid = visid
        self._defaults = defaults
        self._defaults_dict = (
            defaults and defaults.model_dump(exclude_computed_fields=True) or {}
        )
        self._input_renderer = input_renderer or default_input_renderer
        self._tools_renderer = tools_renderer or default_tools_renderer
        self._on_clicked = on_clicked
        self._on_edited = on_edited
        self._on_update_request = on_update_request

        self.expanded_icon = expanded_icon or "arrow_drop_down"
        self.collapsed_icon = collapsed_icon or "arrow_right"
        self.auto_expand_groups = auto_expand_groups

        self.show_value_icon = False
        self.value_icon = value_icon or "sym_o_sliders"
        self.value_icon = value_icon or "sym_o_variables"
        self.value_icon = value_icon or "edit_attributes"

    @property
    def visid(self) -> TGZRVisId:
        return self._visid

    def get_defaults(self, tree_item: _TreeItem) -> pydantic.BaseModel | None:
        if not self._defaults:
            return None
        curr_model = self._defaults
        for name in tree_item.path:
            try:
                curr_model = getattr(curr_model, name)
            except AttributeError:
                break
        return curr_model

    async def render_input(self, tree_item: _TreeItem) -> ValueSetter:
        set_value = await self._input_renderer(tree_item)
        return set_value

    async def render_tools(self, tree_item: _TreeItem) -> None:
        return await self._tools_renderer(tree_item)

    async def on_clicked(self, tree_item: _TreeItem) -> None:
        if self._on_clicked is not None:
            await self._on_clicked(tree_item)

    async def on_edited(self, tree_item: _TreeItem, op: str, **kwargs: Any) -> None:
        if self._on_edited is not None:
            await self._on_edited(tree_item, op, kwargs)

    async def on_update_request(
        self, tree_item: _TreeItem, item_path: list[str]
    ) -> None:
        if self._on_update_request is not None:
            await self._on_update_request(tree_item, item_path)


class _TreeItem(ui.column):
    def __init__(
        self,
        view: TreeView,
        /,
        parent_path: list[str],
        name: str | None,
    ) -> None:
        super().__init__()
        self._parent_path = parent_path
        self._name = name
        self._view = view

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def path(self) -> list[str]:
        return self._parent_path + (self._name and [self._name] or [])

    @property
    def value(self) -> Any | None:
        return None

    async def set_value(self, value) -> Any | None:
        raise TypeError("Cannot set value on base _TreeItem")

    @property
    def expanded(self) -> bool:
        return False

    def expand(self):
        pass

    def collapse(self):
        pass

    async def toggle_expanded(self):
        await self._view.on_clicked(self)
        if self.expanded:
            self.collapse()
        else:
            self.expand()

    async def on_edited(self, op: str, **op_kwargs: Any):
        await self._view.on_edited(self, op, **op_kwargs)

    async def request_update(self, item_path: list[str]):
        await self._view.on_update_request(self, item_path)


class TreeGroup(_TreeItem):
    def __init__(
        self,
        view: TreeView,
        /,
        parent_path: list[str],
        name: str | None,
        label: str | None = None,
        icon: str | None = None,
        expandable: bool = True,
    ) -> None:
        super().__init__(
            view,
            parent_path=parent_path,
            name=name,
        )
        label = label or (name or "").replace("_", " ").title()

        indent_width = 8
        self._expandable = expandable
        self._expanded = True

        self._forced_icon = icon
        self._expandable = expandable
        self._children_items: list[_TreeItem] = []

        hover_classes = ""
        header_cursor_classes = ""
        if self._expandable:
            hover_classes = f"border border-[{view.visid.theme.B}] hover:border-[{view.visid.theme.primary}]"
            header_cursor_classes = "cursor-pointer"

        self.classes("gap-0 w-full col-span-3")
        with self:
            with (
                ui.row(align_items="center")
                .classes(
                    f"min-h-[3em] w-full {hover_classes} {header_cursor_classes} {not label and 'gap-0' or ''}"
                )
                .on("click", self.toggle_expanded)
            ) as self._header:
                self._icon = ui.icon(
                    self._forced_icon or self._view.expanded_icon,
                    size="md",
                    color="neutral-400",
                )
                if label:
                    self._label = ui.label(label)  # .classes("h-[5em]")
                self.header_slot = ui.row(align_items="center").classes("grow")
            self.body = ui.column().classes(f"pl-{indent_width} w-full xcol-span-3")
            with ui.row(wrap=False, align_items="center").classes(
                "w-full gap-0 items-stretch"
            ):
                ui.space().classes(f"pl-{indent_width//2}")
                ui.separator().props("vertical xcolor=dark").classes(
                    "bg-neutral-700/50"
                )
                ui.space().classes(f"pl-{indent_width//2}")
                with ui.column().classes("w-full gap-0") as self._children_col:
                    with ui.grid(columns="auto 1fr auto").classes(
                        f"items-start w-full gap-1"
                    ) as self._values_children_grid:
                        pass
                    with ui.grid(columns="auto 1fr auto").classes(
                        f"items-start w-full gap-1"
                    ) as self._groups_children_grid:
                        pass

    @property
    def expanded(self) -> bool:
        return self._expanded

    def expand(self):
        if not self._expandable:
            return
        self._expanded = True
        self._children_col.visible = True
        self._icon.set_name(self._forced_icon or self._view.expanded_icon)
        if len(self._children_items) == 1:
            self._children_items[0].expand()

    def collapse(self):
        if not self._expandable:
            return
        if not self._children_items:
            return
        self._expanded = False
        self._children_col.visible = False
        self._icon.set_name(self._forced_icon or self._view.collapsed_icon)

    async def set_value(self, value) -> Any | None:
        raise TypeError("Cannot set value on TreeGroup")

    async def set_children(self, children_dict: dict[str, Any]):
        defaults = self._view.get_defaults(self)
        # rich.print(f"Defaults for {self.path}:", defaults)
        if defaults is not None and isinstance(defaults, pydantic.BaseModel):
            defaults_dict = defaults.model_dump()
            defaults_dict.update(children_dict)
            children_dict = defaults_dict

        self._values_children_grid.clear()
        self._groups_children_grid.clear()
        self._expanded = True
        nb_groups = 0

        for k, v in children_dict.items():
            if isinstance(v, dict):
                with self._groups_children_grid:
                    ti = TreeGroup(
                        self._view,
                        parent_path=self.path,
                        name=k,
                        # children=v,
                    )
                    await ti.set_children(v)
                    nb_groups += 1
            else:
                with self._values_children_grid:
                    ti = TreeValue(
                        self._view,
                        parent_path=self.path,
                        name=k,
                        value=v,
                    ).classes("align-middle")
                    with ui.row().classes(f"w-full gap-0"):
                        await ti.render_value_input()
                    with ui.row().classes("gap-0"):
                        await self._view.render_tools(ti)
            self._children_items.append(ti)

        # NB: default state is expanded, so we collapse first:
        self.collapse()
        if self._view.auto_expand_groups:  # and nb_groups == 1:
            self.expand()

    async def request_update(self, item_path: list[str]):
        await super().request_update(item_path)
        for item in self._children_items:
            await item.request_update(item_path)


class TreeValue(_TreeItem):
    def __init__(
        self,
        view: TreeView,
        /,
        parent_path: list[str],
        name: str | None,
        value: Any,
        label: str | None = None,
        icon: str | None = None,
    ) -> None:
        super().__init__(
            view,
            parent_path=parent_path,
            name=name,
        )
        label = label or (name or "").replace("_", " ").title()

        self._value = value

        self._input_parent: ui.element | None = None
        self._input_value_setter: ValueSetter | None = None

        hover_classes = f"border border-[{view.visid.theme.B}] hover:border-[{view.visid.theme.primary}]"
        header_cursor_classes = "cursor-pointer"

        self.classes(f"gap-0")
        with self:
            with (
                ui.row(align_items="center")
                .classes(
                    f"h-[3em] w-full {hover_classes} {header_cursor_classes}"
                )  # h-[3em] is to match height of inputs
                .on("click", self.toggle_expanded)
            ) as self._header:
                if self._view.show_value_icon:
                    self._icon = ui.icon(
                        self._view.value_icon, size="md", color="neutral-600"
                    )
                    ui.space()  #
                    # NB: the p-2 here is to avoid something strange about scrollbar showing up
                    # (only if we show an icon)
                    self._label = ui.label(label.replace("_", " ").title()).classes(
                        "p-2"
                    )
                else:
                    ui.space().classes("min-w-8")
                    self._label = ui.label(label.replace("_", " ").title()).classes(
                        "p-1"
                    )
                self.header_slot = ui.row(align_items="center").classes("grow")

    async def render_value_input(self):
        self._input_value_setter = await self._view.render_input(self)

    @property
    def value(self) -> Any | None:
        return self._value

    async def set_value(self, value) -> Any | None:
        print("---->SET VALUE", self.path, value)
        self._value = value
        if self._input_value_setter is None:
            # we don't have a input ui to update.
            return
        await self._input_value_setter(value)
