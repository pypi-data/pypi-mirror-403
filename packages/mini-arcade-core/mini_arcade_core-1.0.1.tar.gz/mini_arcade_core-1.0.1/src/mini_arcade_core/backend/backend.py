"""
Backend interface for rendering and input.
This is the only part of the code that talks to SDL/pygame directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from .events import Event
from .types import Color


@dataclass
class WindowSettings:
    """
    Settings for the backend window.

    :ivar width (int): Width of the window in pixels.
    :ivar height (int): Height of the window in pixels.
    """

    width: int
    height: int


# TODO: Refactor backend interface into smaller protocols?
# Justification: Many public methods needed for backend interface
# pylint: disable=too-many-public-methods
class Backend(Protocol):
    """
    Interface that any rendering/input backend must implement.

    mini-arcade-core only talks to this protocol, never to SDL/pygame directly.
    """

    def init(self, window_settings: WindowSettings):
        """
        Initialize the backend and open a window.
        Should be called once before the main loop.

        :param window_settings: Settings for the backend window.
        :type window_settings: WindowSettings
        """

    def set_window_title(self, title: str):
        """
        Set the window title.

        :param title: The new title for the window.
        :type title: str
        """
        raise NotImplementedError

    def poll_events(self) -> Iterable[Event]:
        """
        Return all pending events since last call.
        Concrete backends will translate their native events into core Event objects.

        :return: An iterable of Event objects.
        :rtype: Iterable[Event]
        """

    def set_clear_color(self, r: int, g: int, b: int):
        """
        Set the background/clear color used by begin_frame.

        :param r: Red component (0-255).
        :type r: int

        :param g: Green component (0-255).
        :type g: int

        :param b: Blue component (0-255).
        :type b: int
        """

    def begin_frame(self):
        """
        Prepare for drawing a new frame (e.g. clear screen).
        """

    def end_frame(self):
        """
        Present the frame to the user (swap buffers).
        """

    # Justification: Simple drawing API for now
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def draw_rect(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: Color = (255, 255, 255),
    ):
        """
        Draw a filled rectangle in some default color.
        We'll keep this minimal for now; later we can extend with colors/sprites.

        :param x: X position of the rectangle's top-left corner.
        :type x: int

        :param y: Y position of the rectangle's top-left corner.
        :type y: int

        :param w: Width of the rectangle.
        :type w: int

        :param h: Height of the rectangle.
        :type h: int

        :param color: RGB color tuple.
        :type color: Color
        """

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: Color = (255, 255, 255),
        font_size: int | None = None,
    ):
        """
        Draw text at the given position in a default font and color.

        Backends may ignore advanced styling for now; this is just to render
        simple labels like menu items, scores, etc.

        :param x: X position of the text's top-left corner.
        :type x: int

        :param y: Y position of the text's top-left corner.
        :type y: int

        :param text: The text string to draw.
        :type text: str

        :param color: RGB color tuple.
        :type color: Color
        """

    # pylint: enable=too-many-arguments,too-many-positional-arguments

    def measure_text(self, text: str) -> tuple[int, int]:
        """
        Measure the width and height of the given text string in pixels.

        :param text: The text string to measure.
        :type text: str

        :return: A tuple (width, height) in pixels.
        :rtype: tuple[int, int]
        """
        raise NotImplementedError

    def capture_frame(self, path: str | None = None) -> bytes | None:
        """
        Capture the current frame.
        If `path` is provided, save to that file (e.g. PNG).
        Returns raw bytes (PNG) or None if unsupported.

        :param path: Optional file path to save the screenshot.
        :type path: str | None

        :return: Raw image bytes if no path given, else None.
        :rtype: bytes | None
        """
        raise NotImplementedError

    def init_audio(
        self, frequency: int = 44100, channels: int = 2, chunk_size: int = 2048
    ):
        """
        Initialize SDL_mixer audio.

        :param frequency: Audio frequency in Hz.
        :type frequency: int

        :param channels: Number of audio channels (1=mono, 2=stereo).
        :type channels: int

        :param chunk_size: Size of audio chunks.
        :type chunk_size: int
        """

    def shutdown_audio(self):
        """Shutdown SDL_mixer audio and free loaded sounds."""

    def load_sound(self, sound_id: str, path: str):
        """
        Load a WAV sound and store it by ID.
        Example: backend.load_sound("hit", "assets/sfx/hit.wav")

        :param sound_id: Unique identifier for the sound.
        :type sound_id: str

        :param path: File path to the WAV sound.
        :type path: str
        """

    def play_sound(self, sound_id: str, loops: int = 0):
        """
        Play a loaded sound.
        loops=0 => play once
        loops=-1 => infinite loop
        loops=1 => play twice (SDL convention)

        :param sound_id: Unique identifier for the sound.
        :type sound_id: str

        :param loops: Number of times to loop the sound.
        :type loops: int
        """

    def set_master_volume(self, volume: int):
        """
        Master volume: 0..128
        """

    def set_sound_volume(self, sound_id: str, volume: int):
        """
        Per-sound volume: 0..128

        :param sound_id: Unique identifier for the sound.
        :type sound_id: str

        :param volume: Volume level (0-128).
        :type volume: int
        """

    def stop_all_sounds(self):
        """Stop all channels."""

    def set_viewport_transform(
        self, offset_x: int, offset_y: int, scale: float
    ):
        """
        Apply a transform so draw_* receives VIRTUAL coords and backend maps to screen.

        :param offset_x: X offset in pixels.
        :type offset_x: int

        :param offset_y: Y offset in pixels.
        :type offset_y: int

        :param scale: Scale factor.
        :type scale: float
        """
        raise NotImplementedError

    def clear_viewport_transform(self):
        """Reset any viewport transform back to identity."""
        raise NotImplementedError

    def resize_window(self, width: int, height: int):
        """
        Resize the actual OS window (SDL_SetWindowSize in native backend).

        :param width: New width in pixels.
        :type width: int

        :param height: New height in pixels.
        :type height: int
        """
        raise NotImplementedError

    def set_clip_rect(self, x: int, y: int, w: int, h: int):
        """
        Set a clipping rectangle for rendering.

        :param x: X position of the rectangle's top-left corner.
        :type x: int

        :param y: Y position of the rectangle's top-left corner.
        :type y: int

        :param w: Width of the rectangle.
        :type w: int

        :param h: Height of the rectangle.
        :type h: int
        """
        raise NotImplementedError

    def clear_clip_rect(self):
        """Clear any clipping rectangle."""
        raise NotImplementedError
