"""
Post-processing effects render pass implementation.
"""

from dataclasses import dataclass

from mini_arcade_core.backend import Backend
from mini_arcade_core.engine.render.context import RenderContext
from mini_arcade_core.engine.render.packet import RenderPacket


@dataclass
class PostFXPass:
    """
    PostFX Render Pass.
    This pass handles post-processing effects like CRT simulation.
    """

    name: str = "PostFXPass"

    # Justification: No implementation yet
    # pylint: disable=unused-argument
    def run(
        self, backend: Backend, ctx: RenderContext, packets: list[RenderPacket]
    ):
        """Run the post-processing effects render pass."""
        # hook/no-op for now (CRT later)
        return
