"""
Render pipeline module.
Defines the RenderPipeline class for rendering RenderPackets.
"""

from __future__ import annotations

from dataclasses import dataclass

from mini_arcade_core.backend import Backend
from mini_arcade_core.engine.render.packet import RenderPacket
from mini_arcade_core.engine.render.viewport import ViewportState


@dataclass
class RenderPipeline:
    """
    Minimal pipeline for v1.

    Later you can expand this into passes:
      - build draw list
      - cull
      - sort
      - backend draw pass
    """

    def draw_packet(
        self,
        backend: Backend,
        packet: RenderPacket,
        viewport_state: ViewportState,
    ):
        """
        Draw the given RenderPacket using the provided Backend.

        :param backend: Backend to use for drawing.
        :type backend: Backend

        :param packet: RenderPacket to draw.
        :type packet: RenderPacket
        """
        if not packet:
            return

        backend.set_viewport_transform(
            viewport_state.offset_x,
            viewport_state.offset_y,
            viewport_state.scale,
        )

        # backend.set_clip_rect(
        #     viewport_state.offset_x,
        #     viewport_state.offset_y,
        #     viewport_state.viewport_w,
        #     viewport_state.viewport_h,
        # )

        try:
            for op in packet.ops:
                op(backend)
        finally:
            backend.clear_clip_rect()
            backend.clear_viewport_transform()
