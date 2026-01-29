"""
Module providing runtime adapters for window and scene management.
"""

from __future__ import annotations

from venv import logger

from mini_arcade_core.engine.render.viewport import (
    Viewport,
    ViewportMode,
    ViewportState,
)
from mini_arcade_core.runtime.window.window_port import WindowPort


class WindowAdapter(WindowPort):
    """
    Manages multiple game windows (not implemented).
    """

    def __init__(self, backend, window_settings):
        self.backend = backend
        self.window_settings = window_settings

        self._initialized = False

        # Default: virtual resolution == initial window resolution.
        # You can override via set_virtual_resolution().
        self._viewport = Viewport(
            window_settings.width,
            window_settings.height,
            mode=ViewportMode.FIT,
        )

        # Cached current window size
        self.size = (window_settings.width, window_settings.height)

    def set_window_size(self, width, height):
        width = int(width)
        height = int(height)
        self.size = (width, height)

        self.window_settings.width = width
        self.window_settings.height = height

        if not self._initialized:
            self.backend.init(self.window_settings)
            self._initialized = True
        else:
            self.backend.resize_window(width, height)

        self._viewport.resize(width, height)

    def set_virtual_resolution(self, width: int, height: int):
        self._viewport.set_virtual_resolution(int(width), int(height))
        # re-apply using current window size
        w, h = self.size
        self._viewport.resize(w, h)

    def set_viewport_mode(self, mode: ViewportMode):
        self._viewport.set_mode(mode)

    def get_viewport(self) -> ViewportState:
        return self._viewport.state

    def screen_to_virtual(self, x: float, y: float) -> tuple[float, float]:
        return self._viewport.screen_to_virtual(x, y)

    def set_title(self, title):
        self.backend.set_window_title(title)

    def set_clear_color(self, r, g, b):
        self.backend.set_clear_color(r, g, b)

    def on_window_resized(self, width: int, height: int):
        logger.debug(f"Window resized event: {width}x{height}")
        width = int(width)
        height = int(height)

        # Update cached size, but DO NOT call backend.resize_window here.
        self.size = (width, height)
        self.window_settings.width = width
        self.window_settings.height = height

        self._viewport.resize(width, height)

    def get_virtual_size(self) -> tuple[int, int]:
        s = self.get_viewport()
        return (s.virtual_w, s.virtual_h)
