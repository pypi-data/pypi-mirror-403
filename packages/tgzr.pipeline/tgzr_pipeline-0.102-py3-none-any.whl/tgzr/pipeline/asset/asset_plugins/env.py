from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, Type, Any, Literal

import os
import logging

import rich
import pydantic

from ..asset import Asset, AssetTypeInfo
from .asset_with_params import AssetWithParams, AssetParams

if TYPE_CHECKING:
    from tgzr.pipeline.workspace import Workspace

logger = logging.getLogger(__name__)


class EnvOp:
    @classmethod
    def op_name(cls) -> str:
        return cls.__name__

    def __init__(self, var_name: str, **kwargs):
        self._var_name = var_name
        self._kwargs = kwargs
        self.configure(**kwargs)

    def configure(self, **kwargs) -> None:
        raise NotImplementedError()

    def var_name(self) -> str:
        return self._var_name

    def kwargs(self) -> dict[str, Any]:
        return self._kwargs

    def apply_to(self, env: dict[str, str]) -> None:
        raise NotImplementedError()


class Set(EnvOp):
    """Set a env var value."""

    def configure(self, value: str) -> None:
        self.value = value

    def apply_to(self, base: dict[str, str]) -> None:
        base[self.var_name()] = self.value


class Delete(EnvOp):
    """Remove a env var."""

    def configure(self, value=None) -> None:
        if value is not None:
            logger.debug(f"Skipping provided value {value} for delete operation.")

    def apply_to(self, base: dict[str, str]) -> None:
        try:
            del base[self.var_name()]
        except KeyError:
            pass


class Append(EnvOp):
    """Append a value to a path env var."""

    def configure(self, value: str) -> None:
        self.value = value

    def apply_to(self, base: dict[str, str]) -> None:
        base_value = base.get(self.var_name(), "")
        if base_value:
            base_list = base_value.split(os.path.pathsep)
        else:
            base_list = []
        base_list.append(self.value)
        base[self.var_name()] = os.path.pathsep.join(base_list)


class Prepend(EnvOp):
    """Insert a value at the begining of a path env var."""

    def configure(self, value: str) -> None:
        self.value = value

    def apply_to(self, base: dict[str, str]) -> None:
        base_value = base.get(self.var_name(), "")
        base_list = base_value.split(os.path.pathsep)
        base_list.insert(0, self.value)
        base[self.var_name()] = os.path.pathsep.join(base_list)


class Env:
    OPS: dict[str, Type[EnvOp]] = dict(
        set=Set, delete=Delete, append=Append, prepend=Prepend
    )

    @classmethod
    def op_names(cls) -> tuple[str, ...]:
        """The valid values for the `op_name` argument of `self.add_op(...)`"""
        return tuple(cls.OPS.keys())

    def __init__(self, *bases: Env):
        self._bases: tuple[Env, ...] = bases
        self._ops: list[EnvOp] = []

    def add_bases(self, *bases: Env, validate_bases: bool = True) -> None:
        validated = []
        if validate_bases:
            for base in bases:
                if not isinstance(base, self.__class__):
                    print(
                        f"WARNING: can't use {base} as base for {self}: it is not a {self.__class__} ! (skipping it)"
                    )
                else:
                    validated.append(base)
        else:
            validated = bases
        self._bases = self._bases + tuple(validated)

    def ops(self) -> tuple[EnvOp, ...]:
        return tuple(self._ops)

    def add_op(self, op_name: str, var_name: str, **op_kwargs: Any):
        op = self.OPS[op_name](var_name=var_name, **op_kwargs)
        self._ops.append(op)

    def set(self, name: str, value: str) -> None:
        self.add_op("set", name, value=value)

    def delete(self, name: str) -> None:
        self.add_op("delete", name)

    def append(self, name: str, value) -> None:
        self.add_op("append", name, value=value)

    def prepend(self, name: str, value) -> None:
        self.add_op("prepend", name, value=value)

    def apply_to(self, env: dict[str, str]):
        for base in self._bases:
            base.apply_to(env)
        for op in self._ops:
            op.apply_to(env)


class EnvAssetMixin:
    def get_local_env(self) -> Env: ...

    def get_output(self) -> Env:
        env = self.get_local_env()
        for asset in self.get_input_assets():  # type: ignore
            output = asset.get_output()
            env.add_bases(output)
        return env

    def _execute(self, print):
        print(f"Hello from {self.__class__.__name__} {self.name} ({self.is_editable=})")  # type: ignore
        print("Here is the aggregated Env at this point:")
        env = {}
        self.get_output().apply_to(env)
        print(env)


class EnvAsset(EnvAssetMixin, Asset):
    # NOTE: the mixin class must be first in inherit order!

    ASSET_TYPE_INFO = AssetTypeInfo(
        category="env",
        color="#82fffb",
        icon="landscape",
    )

    def get_local_env(self) -> Env:
        env = Env()
        env.append("visited_env_assets", self.name)
        return env


class OpParam(pydantic.BaseModel):
    enabled: bool = True
    var_name: str = "MyVar"
    op_name: Literal["set", "delete", "append", "prepend"] = "set"
    value: str | None = None


class EnvEditParams(AssetParams):
    enabled: bool = True
    operations: list[OpParam] = []


class EnvEdit(EnvAssetMixin, AssetWithParams[EnvEditParams]):
    ASSET_TYPE_INFO = AssetTypeInfo(
        category="env",
        color="#82fffb",
        icon="sym_o_add_photo_alternate",
    )

    def get_local_env(self) -> Env:
        env = Env()
        params = self.params
        if not params.enabled:
            return env

        env.append("visited_env_assets", self.name)
        for op in params.operations:
            if not op.enabled:
                continue
            kwargs = {}
            if op.value is not None:
                kwargs["value"] = op.value
            env.add_op(op.op_name, op.var_name, **kwargs)
        return env

    def _get_params_panel(self):
        """Overridden to add custom field renderers"""
        panel = super()._get_params_panel()

        from .asset_with_params.params_panel import ModelField, ui

        class OpField(ModelField):
            @classmethod
            def handles(cls, value_type) -> bool:
                return value_type is OpParam

            def op_symbol(self, op_name: str) -> str:
                return dict(
                    set="=",
                    delete="delete",
                    append="+=",
                    prepend="+@0",
                ).get(op_name, f"--{op_name}-->")

            def _render_readonly_value(self):
                op_param: OpParam = self._getter()
                ui.label(
                    f"{op_param.var_name} {self.op_symbol(op_param.op_name)} {op_param.value or ''}"
                ).classes("pl-1 w-full font-mono").style(replace="")

        panel.add_field_renderer(OpField)
        return panel
