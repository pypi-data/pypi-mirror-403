from __future__ import annotations
from typing import TYPE_CHECKING, Type, TypeVar, Generic
from pathlib import Path

try:
    from types import get_original_bases
except ImportError:
    # Py 3.9 need that:
    def get_original_bases(cls):
        return getattr(cls, "__orig_bases__", cls.__bases__)


import pydantic
import json

from ...asset import Asset

if TYPE_CHECKING:
    from tgzr.pipeline.workspace import Workspace


class AssetParams(pydantic.BaseModel):
    """
    A pydantic model defining the params for an AssetWithParams.
    Subclass it and use it as generic base for you AssetWithParams subclass.

    !!! All field type **MUST** be json dumpable !!!

    !!! If subclass has field of type list or sub-models, these submodels
    need to have default values for all fields or the the Params panel
    will not be able to create them
    """

    pass


AssetParamsType = TypeVar("AssetParamsType", bound=AssetParams)


class AssetWithParams(Asset, Generic[AssetParamsType]):
    """
    If subclasses' ParamModel doesn't provide default values for
    all field, it must implement `get_default_params()` to return
    a instance of AssetParamsType.
    """

    @classmethod
    def init_asset_files(cls, dinit_file: Path) -> None:
        """
        This is called by the asset manager after it created/updated the
        __init__.py file for an asset of this type.
        Subclasses can override this to add more files inside the
        asset package.
        """
        params_file = dinit_file.parent / "params.json"
        defaults = cls.get_default_params()
        cls._save_asset_params(defaults, params_file)

    @classmethod
    def params_type(cls) -> Type[AssetParamsType]:
        # Dont asks. That python generic class dark magic...
        # (But if you know a better way w/o __args__ please tell me! ^_^)
        return get_original_bases(cls)[-1].__args__[0]

    @classmethod
    def get_default_params(cls) -> AssetParamsType:
        return cls.params_type()()

    @classmethod
    def _save_asset_params(cls, params: AssetParamsType, param_file: Path) -> None:
        json_str = (
            params.model_dump_json()
        )  # exclude_unset=True, exclude_defaults=True)
        print("SAVING JSON", json_str)
        with open(param_file, "w") as fp:
            fp.write(json_str)

    @property
    def params_file(self) -> Path:
        return self._init_file.parent / "params.json"

    def read_params(self) -> AssetParamsType:
        with open(self.params_file, "r") as f:
            data = json.load(f)
        return self.params_type()(**data)

    def write_params(self, params: AssetParamsType):
        self._save_asset_params(params, self.params_file)

    @property
    def params(self) -> AssetParamsType:
        # TODO: maybe cache the param ?
        return self.read_params()

    def nice_panel_names(self) -> list[str]:
        return ["params_panel"]

    def _get_params_panel(self):
        from .params_panel import ParamsPanel

        panel = ParamsPanel(self.params)
        return panel

    def params_panel(self, workspace: Workspace) -> None:
        print("???", self.params_type())

        def save_params(params):
            self.write_params(params)
            workspace.bump_asset(self.name, bump="micro")

        panel = self._get_params_panel()
        panel.set_on_save(save_params)
        panel.render()
