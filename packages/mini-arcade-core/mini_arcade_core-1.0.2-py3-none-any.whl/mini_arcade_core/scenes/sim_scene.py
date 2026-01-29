"""
Simulation scene protocol module.
Defines the SimScene protocol for simulation scenes.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mini_arcade_core.engine.render.packet import RenderPacket
from mini_arcade_core.runtime.input_frame import InputFrame


@runtime_checkable
class SimScene(Protocol):
    """ "Protocol for a simulation scene in the mini arcade core."""

    def on_enter(self):
        """Called when the scene is entered."""

    def on_exit(self):
        """Called when the scene is exited."""

    def tick(self, input_frame: InputFrame, dt: float):
        """
        Advance the simulation by one tick.

        :param input_frame: Current input frame.
        :type input_frame: InputFrame

        :param dt: Delta time since last tick.
        :type dt: float
        """

    def build_render_packet(self) -> RenderPacket:
        """
        Build the render packet for the current scene state.

        :return: RenderPacket instance.
        :rtype: RenderPacket
        """
