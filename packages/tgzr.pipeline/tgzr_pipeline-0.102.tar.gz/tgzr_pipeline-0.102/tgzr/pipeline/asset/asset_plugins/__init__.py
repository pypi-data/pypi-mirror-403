from __future__ import annotations
from typing import Type, TYPE_CHECKING

from ..plugin import PipelinePlugin

from .builder import Builder
from .casting import Casting
from .creator import ShotCreator
from .env import EnvAsset, EnvEdit
from .workscene import Workscene

if TYPE_CHECKING:
    from ..asset import Asset


class DefaultAssetsPlugin(PipelinePlugin):
    def get_asset_types(self) -> list[Type[Asset]]:
        return [
            Builder,
            Casting,
            ShotCreator,
            EnvAsset,
            EnvEdit,
            Workscene,
        ]
