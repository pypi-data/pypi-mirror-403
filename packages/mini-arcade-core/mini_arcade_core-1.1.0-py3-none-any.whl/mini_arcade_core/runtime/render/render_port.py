"""
Render service definition.
"""

from __future__ import annotations

from typing import Protocol

from mini_arcade_core.engine.render.context import RenderStats


class RenderServicePort(Protocol):
    """
    Render Service.
    This service manages rendering statistics and state.

    :ivar last_frame_ms (float): Time taken for the last frame in milliseconds.
    :ivar last_stats (RenderStats): Rendering statistics from the last frame.
    """

    last_frame_ms: float
    last_stats: RenderStats
