from __future__ import annotations
from typing import TYPE_CHECKING, Union, Type, Literal, Callable, Any
from typing import get_args, get_origin

import sys
import inspect
import contextlib

import pydantic
from nicegui import ui

if TYPE_CHECKING:
    from . import AssetParams


# This is to be compatible with python 3.9
# because it does not have types.UnionType
# so we can't just do "xx is UnionType"
# TODO: trash this when ToonBoom got working and we stop need to support py3.9 anymore.
def is_union_type(tp):
    # 1. Check for the modern | syntax (Python 3.10+)
    if sys.version_info >= (3, 10):
        from types import UnionType

        if tp is UnionType:
            # TODO: I'm pretty sure this is wrong, but our usage doesn't work w/o it ¯\_(ツ)_/¯
            return True

        if isinstance(tp, UnionType):
            return True

    # 2. Check for the traditional Union[int, str] syntax
    # In 3.9, we check the __origin__ of the type
    return getattr(tp, "__origin__", None) is Union


class FieldRenderer:
    @classmethod
    def handles(cls, value_type) -> bool:
        raise NotImplementedError(f"on {cls}")

    def __init__(
        self,
        panel: ParamsPanel,
        name: str,
        getter: Callable[[], Any],
        setter: Callable[[Any], None],
        default_factory: Callable[[], Any] | None,
    ):
        self._panel = panel
        self._name = name
        self._getter = getter
        self._setter = setter
        self._default_factory = default_factory
        self._options: dict[str, Any] = {}

    def set_optional(self, b: bool = False):
        self._options["optional"] = b

    def set_options(self, *args, **kwargs) -> None:
        if args:
            raise ValueError(
                f"FiedlRenderer default set_option() implementation does not accept *args, but got {args} on field {self._name} ({self}) !"
            )
        self._options.update(kwargs)

    def render(self):
        # print("RENDER LABEL ON", self)
        self.render_label()
        # print("RENDER FIELD", self)
        self.render_field()

    def render_label(self):
        with self._panel.field_label_parent():
            if self._panel.editable:
                self._render_label_editable()
            else:
                self._render_label_readonly()

    def _render_label_editable(self):
        ui.label(self._name.replace("_", " ").title())

    def _render_label_readonly(self):
        ui.label(self._name.replace("_", " ").title())

    def render_field(self):
        with self._panel.field_value_parent() as p:
            p.classes("col-span-2")
            if self._panel.editable:
                e = self._render_editable_value()
                if e is not None:
                    e.on("mousedown", js_handler="(e)=>{e.stopPropagation()}")
            else:
                self._render_readonly_value()

    def _render_editable_value(self) -> ui.element | None:
        raise NotImplementedError(f"on {self}")

    def _render_readonly_value(self):
        raise NotImplementedError(f"on {self}")


class StrField(FieldRenderer):
    @classmethod
    def handles(cls, value_type) -> bool:
        return value_type is str

    def _render_editable_value(self):
        def on_key(event):
            if event.args["key"] == "Enter":
                self._setter(event.sender.value)
                event.sender.run_method("blur")

        e = (
            ui.input(value=str(self._getter()))
            .props("dense rounded standout")
            .classes("w-full")
            .on("keydown", on_key)
        )
        return e

    def _render_readonly_value(self):
        ui.label(self._getter()).classes("w-full")


class BoolField(FieldRenderer):
    @classmethod
    def handles(cls, value_type) -> bool:
        return value_type is bool

    def _render_editable_value(self):
        e = ui.checkbox(
            value=self._getter(), on_change=lambda e: self._setter(e.value)
        ).classes("w-full")
        return e

    def _render_readonly_value(self):
        ui.icon(
            self._getter() and "sym_o_check_box" or "sym_o_check_box_outline_blank",
            size="sm",
        )


class ChoiceField(FieldRenderer):
    @classmethod
    def handles(cls, value_type) -> bool:
        return value_type is Literal

    def set_options(
        self,
        *choices: Any,
    ) -> None:
        super().set_options(choices=choices)

    def _render_editable_value(self):
        choices = self._options["choices"]
        value = self._getter()

        selectable = dict([(str(i), i) for i in choices])
        if str(value) not in selectable:
            selectable[str(value)] = value
        e = (
            ui.select(
                selectable,
                value=value,
                new_value_mode="add",
                key_generator=str,
                on_change=lambda e: self._setter(e.value),
            )
            .props("dense rounded standout")
            .classes("w-full")
        )

        return e

    def _render_readonly_value(self):
        ui.label(str(self._getter()))


class ListField(FieldRenderer):
    @classmethod
    def handles(cls, value_type) -> bool:
        return value_type is list

    def set_options(
        self,
        *args,
        allow_reorder: bool = True,
        open: bool = False,
        default_open: bool | None = None,
    ) -> None:
        self._item_type = args[0]
        return super().set_options(
            open=open, default_open=default_open, allow_reorder=allow_reorder
        )

    def on_add_item(self):
        if self._default_factory is None:
            raise ValueError("Cannot add item in list fiels without a default factory!")
        list_values = self._getter()
        list_values.append(self._item_type())
        # list_values.append(self._default_factory())
        self.render_content.refresh()

    def move_item_up(self, index: int):
        list_values = self._getter()
        value = list_values.pop(index)
        list_values.insert(index - 1, value)
        self.render_content.refresh()

    def move_item_down(self, index: int):
        list_values = self._getter()
        value = list_values.pop(index)
        list_values.insert(index + 1, value)
        self.render_content.refresh()

    def delete_item(self, index: int):
        list_values = self._getter()
        list_values.pop(index)
        self.render_content.refresh()

    def toggle_open(self):
        if self._content.visible:
            self._open_close_btn.icon = "arrow_right"
            self._content.visible = False
            self._add_item_btn.visible = False
            self._options["open"] = False
        else:
            self._open_close_btn.icon = "arrow_drop_down"
            self._content.visible = True
            if self._panel.editable:
                self._add_item_btn.visible = True
            self._options["open"] = True

    def render_label(self):
        with ui.row(align_items="center").classes(
            f"gap-0 xmin-h-[{self._panel.min_h}]"
        ) as p:
            p.classes("col-span-3")
            self._render_header()

    def _render_header(self):
        self._open_close_btn = ui.button(icon="arrow_drop_down").props("flat dense")
        ui.label(self._name.replace("_", " ").title())

        with ui.row(align_items="center").classes("gap-0 col-span-2"):
            self._add_item_btn = (
                ui.button(icon="sym_o_list_alt_add")
                .tooltip("Add Item")
                .props("flat dense")
            )
            self._add_item_btn.set_visibility(self._panel.editable)

        self._open_close_btn.on_click(self.toggle_open)
        self._add_item_btn.on_click(self.on_add_item)

        ui.space()

    @ui.refreshable_method
    def render_content(self):
        list_values = self._getter()
        with ui.column().classes(
            f"w-full gap-1 col-span-2 pl-[{self._panel.min_h}]"
        ) as self._content:
            for i, value in enumerate(list_values):
                with ui.row(wrap=False).classes(
                    "w-full border border-neutral-500/50 gap-0"
                ):
                    with ui.column().classes("gap-0"):
                        b = (
                            ui.button(
                                icon="sym_o_arrow_upward_alt",
                                on_click=lambda e, i=i: self.move_item_up(i),
                            )
                            .props("flat dense")
                            .tooltip("Move Up")
                        )
                        b.set_visibility(self._panel.editable)
                        b = (
                            ui.button(
                                icon="sym_o_arrow_downward_alt",
                                on_click=lambda e, i=i: self.move_item_down(i),
                            )
                            .props("flat dense")
                            .tooltip("Move Down")
                        )
                        b.set_visibility(self._panel.editable)
                    name = ""  # f"#{i}"
                    getter = lambda: value
                    self._panel.render_field(
                        name, getter, setter=None, value_type=self._item_type
                    )
                    with ui.column():
                        b = (
                            ui.button(
                                icon="sym_o_delete_forever",
                                on_click=lambda e, i=i: self.delete_item(i),
                            )
                            .props("dense flat")
                            .tooltip("Delete this Item")
                        )
                        b.set_visibility(self._panel.editable)

    def _render_editable_value(self):
        default_open = self._options.get("default_open")
        if default_open is None:
            self._options["open"] = True
        self.render_content()

    def _render_readonly_value(self):
        default_open = self._options.get("default_open")
        if default_open is None:
            self._options["open"] = False
        self.render_content()


class ModelField(FieldRenderer):
    @classmethod
    def handles(cls, value_type) -> bool:
        return inspect.isclass(value_type) and issubclass(
            value_type, pydantic.BaseModel
        )

    def _render_editable_value(self):
        self._render_value()

    def _render_readonly_value(self):
        self._render_value()

    def _render_value(self):
        model: pydantic.BaseModel = self._getter()
        model_type = type(model)
        with ui.grid(columns="auto 1fr auto").classes(
            "w-full gap-0 gap-x-1 col-span-2"
        ):
            for name, field in model_type.model_fields.items():
                getter = lambda m=model, n=name: getattr(m, n)
                setter = lambda v, m=model, n=name: setattr(m, n, v)
                self._panel.render_field(
                    name, getter, setter, value_type=field.annotation
                )
        # ui.label(str(model_type))


class DefaultField(FieldRenderer):
    @classmethod
    def handles(cls, value_type) -> bool:
        return True

    def set_options(self, *args, **kwargs) -> None:
        kwargs["*args"] = args
        self._options.update(kwargs)

    def _render_editable_value(self):
        self._render_value()

    def _render_readonly_value(self):
        self._render_value()

    def _render_value(self):
        value = self._getter()
        ui.label(repr(value)).classes("w-full")
        # ui.label(f"(!! {type(value)})")


class FieldRendererFactory:
    def __init__(self):
        self._field_renderers: list[Type[FieldRenderer]] = []
        self._default_field_renderer = DefaultField

    def add_renderer(self, FieldRendererType: Type[FieldRenderer]):
        self._field_renderers.insert(0, FieldRendererType)

    def register_renderers(self, *FieldRendererType: Type[FieldRenderer]):
        self._field_renderers.extend(FieldRendererType)

    def get_field_renderer(
        self, panel, value_type, name, getter, setter
    ) -> FieldRenderer:

        # Amazing trick from this comment:
        # https://stackoverflow.com/questions/56832881/check-if-a-field-is-typing-optional/62641842#62641842
        # optional = Union[value_type, None] == Union[value_type]
        # (not using it tho bc I still need to find out the non-optional type, but you gotta read this! <3)

        # Remove the optional None type and assert there's only one other valid type, then use it:
        # if get_origin(value_type) is Union or get_origin(value_type) is UnionType:
        if get_origin(value_type) is Union or is_union_type(get_origin(value_type)):
            accepted_types = list(get_args(value_type))
            if type(None) in accepted_types:
                optional = True
                accepted_types.remove(type(None))
            if len(accepted_types) > 1:
                raise TypeError(
                    f"Multiple type for field {name} ({value_type}) is not supported!"
                )
            value_type = accepted_types[0]

        field_type = value_type
        sub_types = ()

        origin = get_origin(value_type)
        if origin is not None:
            field_type = origin
            sub_types = get_args(value_type)

        optional = False
        args = get_args(field_type)
        if args:
            if type(None) in args:
                optional = True
                args = [i for i in args if i is not type(None)]

        # print("    --->>", args)
        if args:
            if len(args) > 1:
                raise ValueError("Unsuported dual-type field :/")
            field_type = args[0]

        # print(
        #     ">>>>>>>>",
        #     field_type,
        #     is_union_type(field_type),
        # )
        # if is_union_type(field_type):
        #     print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # print("    >>", value_type)
        # print("    >>", origin, get_args(origin))
        # print("    >>", field_type)
        # print("    >>", sub_types)
        # print("    >>", optional)

        for FieldRendererType in self._field_renderers:
            if FieldRendererType.handles(field_type):
                field_renderer = FieldRendererType(
                    panel, name, getter, setter, lambda: field_type()
                )
                field_renderer.set_optional(optional)
                field_renderer.set_options(*sub_types)
                # print("    Created field", field_renderer)
                return field_renderer
        print(f"!!!! No Field Renderer found for {value_type} ({name}), using default")
        return self._default_field_renderer(panel, name, getter, setter, None)


class ParamsPanel:
    def __init__(
        self, params: AssetParams, allow_edit: bool = True, editable: bool = False
    ):
        self.params = params
        self.min_h = "4em"
        self.allow_edit = allow_edit
        self.editable = editable
        self._on_save = None

        self._field_renderer_factory = FieldRendererFactory()
        self._field_renderer_factory.register_renderers(
            StrField, BoolField, ChoiceField, ListField, ModelField, DefaultField
        )

    def add_field_renderer(self, FieldRendererType: Type[FieldRenderer]):
        self._field_renderer_factory.add_renderer(FieldRendererType)

    def set_on_save(self, cb: Callable[[AssetParams], None]):
        self._on_save = cb

    def save(self):
        print("Saving:", self.params)
        if self._on_save is not None:
            self._on_save(self.params)
        self.stop_edit()

    def stop_edit(self):
        self.editable = False
        print("Edit mode", self.editable)
        self.edit_save_btn.icon = "sym_o_edit"
        self.render_all.refresh()

    def start_edit(self):
        if not self.allow_edit:
            return
        self.editable = True
        print("Edit mode", self.editable)
        self.edit_save_btn.icon = "sym_o_save"
        self.render_all.refresh()

    def _on_edit_save_btn(self):
        if self.editable:
            self.save()
        else:
            self.start_edit()

    def render(self):
        with ui.column().classes("gap-0"):
            with (
                ui.fab(icon="sym_o_menu", direction="left")
                .props("padding=sm")
                .classes("absolute right-3")
            ):
                if self.editable:
                    icon = "sym_o_save"
                else:
                    icon = "sym_o_edit"
                self.edit_save_btn = ui.fab_action(
                    icon, on_click=self._on_edit_save_btn
                ).tooltip("Edit")
                ui.fab_action("sym_o_content_copy").tooltip("Copy")
        self.render_all()

    @ui.refreshable_method
    def render_all(self):
        with ui.grid(columns="auto 1fr auto").classes("w-full gap-0 gap-x-1"):
            self.render_field("", lambda: self.params, None, type(self.params))

    @contextlib.contextmanager
    def field_label_parent(self):
        with ui.column(align_items="end"):
            with ui.row(align_items="center").classes(
                f"h-full xmin-h-[{self.min_h}]"
            ) as p:
                yield p

    @contextlib.contextmanager
    def field_value_parent(self):
        with ui.row(align_items="center").classes(
            f"w-full py-1 xmin-h-[{self.min_h}]"
        ) as p:
            yield p

    def render_field_label(self, name: str):
        with self.field_label_parent():
            ui.label(name.replace("_", " ").title())

    def render_field(self, name, getter, setter, value_type):
        field_renderer = self._field_renderer_factory.get_field_renderer(
            self, value_type, name, getter, setter
        )
        field_renderer.render()
