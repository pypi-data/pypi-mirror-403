from __future__ import annotations
from typing import TYPE_CHECKING, Type

from tgzr.package_management.plugin_manager import Plugin, PluginManager


if TYPE_CHECKING:
    from .asset import Asset


class PipelinePlugin(Plugin):
    @classmethod
    def plugin_type_name(cls) -> str:
        return "PipelinePlugin"

    def get_asset_types(self) -> list[Type[Asset]]:
        return []


class PipelinePluginManager(PluginManager[PipelinePlugin]):

    EP_GROUP = "tgzr.pipeline.plugin"


# NB: we use a "global" plugin manager so it is automatically
# picked up by `tgzr plugins ls`:
plugin_manager = PipelinePluginManager()
