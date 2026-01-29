"""
Simulation scene protocol module.
Defines the SimScene protocol for simulation scenes.
"""

from __future__ import annotations

from dataclasses import dataclass

from mini_arcade_core.engine.render.packet import RenderPacket
from mini_arcade_core.runtime.context import RuntimeContext
from mini_arcade_core.runtime.input_frame import InputFrame


@dataclass
class SimScene:
    """
    Simulation-first scene protocol.

    tick() advances the simulation and returns a RenderPacket for this scene.
    """

    context: RuntimeContext

    def on_enter(self):
        """Called when the scene is entered."""

    def on_exit(self):
        """Called when the scene is exited."""

    def tick(self, input_frame: InputFrame, dt: float) -> RenderPacket:
        """
        Advance the simulation by dt seconds, processing input_frame.

        :param input_frame: InputFrame with input events for this frame.
        :param dt: Time delta in seconds since the last tick.

        :return: RenderPacket for this frame.
        :rtype: RenderPacket
        """
        raise NotImplementedError()
