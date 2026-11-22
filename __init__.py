"""ComfyUI-HyperFlow-Director: a standalone planner, context cards and renderer for HyperFlow H3 Flash (GPL-3.0)."""
from comfy_api.latest import ComfyExtension, io
from typing_extensions import override

from .hfd.nodes import NODES

WEB_DIRECTORY = "./js"


class HyperFlowDirectorExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return list(NODES)


async def comfy_entrypoint() -> HyperFlowDirectorExtension:
    return HyperFlowDirectorExtension()


__all__ = ["WEB_DIRECTORY", "comfy_entrypoint"]
