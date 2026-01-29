"""
Debug overlay scene that displays FPS, window size, and scene stack information.
"""

from __future__ import annotations

from mini_arcade_core.engine.render.packet import RenderPacket
from mini_arcade_core.runtime.context import RuntimeContext
from mini_arcade_core.runtime.input_frame import InputFrame
from mini_arcade_core.scenes.autoreg import register_scene
from mini_arcade_core.sim.protocols import SimScene


@register_scene("debug_overlay")
class DebugOverlayScene(SimScene):
    """
    A debug overlay scene that displays FPS, window size, and scene stack information.
    """

    def __init__(self, ctx: RuntimeContext):
        super().__init__(ctx)
        self._accum = 0.0
        self._frames = 0
        self._fps = 0.0

    def tick(self, input_frame: InputFrame, dt: float) -> RenderPacket:
        self._accum += dt
        self._frames += 1
        if self._accum >= 0.5:
            self._fps = self._frames / self._accum
            self._accum = 0.0
            self._frames = 0

        services = (
            self.context.services
        )  # or ctx.services (depends on your scene base)
        # Justification: type checker can't infer type here
        # pylint: disable=assignment-from-no-return
        vp = services.window.get_viewport()
        stack = services.scenes.visible_entries()
        # pylint: enable=assignment-from-no-return

        lines = [
            f"FPS: {self._fps:5.1f}",
            f"dt:  {dt*1000.0:5.2f} ms",
            f"virtual: {vp.virtual_w}x{vp.virtual_h}",
            f"window:   {vp.window_w}x{vp.window_h}",
            f"scale: {vp.scale:.3f}",
            f"offset: ({vp.offset_x},{vp.offset_y})",
            "stack:",
        ]
        for e in stack:
            lines.append(f"  - {e.scene_id} overlay={e.is_overlay}")

        def draw(backend):
            # translucent background panel
            backend.draw_rect(
                8, 8, 360, 18 * (len(lines) + 1), color=(0, 0, 0, 0.65)
            )
            y = 14
            for line in lines:
                backend.draw_text(
                    16, y, line, color=(255, 255, 255), font_size=14
                )
                y += 18

        return RenderPacket(ops=[draw])
