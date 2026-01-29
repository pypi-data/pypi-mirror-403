"""
Game core module defining the Game class and configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter, sleep
from typing import Dict, Literal

from mini_arcade_core.backend import Backend, WindowSettings
from mini_arcade_core.backend.events import EventType
from mini_arcade_core.engine.commands import (
    CommandContext,
    CommandQueue,
    QuitCommand,
)
from mini_arcade_core.engine.render.packet import RenderPacket
from mini_arcade_core.engine.render.pipeline import RenderPipeline
from mini_arcade_core.managers.cheats import CheatManager
from mini_arcade_core.runtime.audio.audio_adapter import SDLAudioAdapter
from mini_arcade_core.runtime.capture.capture_adapter import CaptureAdapter
from mini_arcade_core.runtime.file.file_adapter import LocalFilesAdapter
from mini_arcade_core.runtime.input.input_adapter import InputAdapter
from mini_arcade_core.runtime.input_frame import InputFrame
from mini_arcade_core.runtime.scene.scene_adapter import SceneAdapter
from mini_arcade_core.runtime.services import RuntimeServices
from mini_arcade_core.runtime.window.window_adapter import WindowAdapter
from mini_arcade_core.scenes.registry import SceneRegistry
from mini_arcade_core.utils import logger


@dataclass
class WindowConfig:
    """
    Configuration for a game window (not implemented).

    :ivar width (int): Width of the window in pixels.
    :ivar height (int): Height of the window in pixels.
    :ivar background_color (tuple[int, int, int]): RGB background color.
    :ivar title (str): Title of the window.
    """

    width: int
    height: int
    background_color: tuple[int, int, int]
    title: str


@dataclass
class GameConfig:
    """
    Configuration options for the Game.

    :ivar window (WindowConfig | None): Optional window configuration.
    :ivar fps (int): Target frames per second.
    :ivar backend (Backend | None): Optional Backend instance to use for rendering and input.
    """

    window: WindowConfig | None = None
    fps: int = 60
    backend: Backend | None = None


Difficulty = Literal["easy", "normal", "hard", "insane"]


@dataclass
class GameSettings:
    """
    Game settings that can be modified during gameplay.

    :ivar difficulty (Difficulty): Current game difficulty level.
    """

    difficulty: Difficulty = "normal"


def _neutral_input(frame_index: int, dt: float) -> InputFrame:
    """Create a neutral InputFrame with no input events."""
    return InputFrame(frame_index=frame_index, dt=dt)


@dataclass
class FrameTimer:
    """
    Simple frame timer for marking and reporting time intervals.

    :ivar enabled (bool): Whether timing is enabled.
    :ivar marks (Dict[str, float]): Recorded time marks.
    """

    enabled: bool = False
    marks: Dict[str, float] = field(default_factory=dict)

    def mark(self, name: str):
        """
        Record a time mark with the given name.

        :param name: Name of the mark.
        :type name: str
        """
        if not self.enabled:
            return
        self.marks[name] = perf_counter()

    def diff_ms(self, start: str, end: str) -> float:
        """
        Get the time difference in milliseconds between two marks.

        :param start: Name of the start mark.
        :type start: str

        :param end: Name of the end mark.
        :type end: str

        :return: Time difference in milliseconds.
        :rtype: float
        """
        return (self.marks[end] - self.marks[start]) * 1000.0

    def report_ms(self) -> Dict[str, float]:
        """
        Returns diffs between consecutive marks in insertion order.

        :return: Dictionary mapping "start->end" to time difference in milliseconds.
        :rtype: Dict[str, float]
        """
        if not self.enabled:
            return {}

        keys = list(self.marks.keys())
        out: Dict[str, float] = {}
        for a, b in zip(keys, keys[1:]):
            out[f"{a}->{b}"] = self.diff_ms(a, b)
        return out

    def clear(self):
        """Clear all recorded marks."""
        if not self.enabled:
            return
        self.marks.clear()


# TODO: Fix too-many-instance-attributes warning
# Justification: Core game class with many dependencies.
# pylint: disable=too-many-instance-attributes
class Game:
    """Core game object responsible for managing the main loop and active scene."""

    def __init__(
        self, config: GameConfig, registry: SceneRegistry | None = None
    ):
        """
        :param config: Game configuration options.
        :type config: GameConfig

        :param registry: Optional SceneRegistry for scene management.
        :type registry: SceneRegistry | None

        :raises ValueError: If the provided config does not have a valid Backend.
        """
        self.config = config
        self._running: bool = False

        if config.backend is None:
            raise ValueError(
                "GameConfig.backend must be set to a Backend instance"
            )
        if config.window is None:
            raise ValueError("GameConfig.window must be set")

        self.backend: Backend = config.backend
        self.registry = registry or SceneRegistry(_factories={})
        self.settings = GameSettings()
        self.services = RuntimeServices(
            window=WindowAdapter(
                self.backend,
                WindowSettings(
                    width=self.config.window.width,
                    height=self.config.window.height,
                ),
            ),
            scenes=SceneAdapter(self.registry, self),
            audio=SDLAudioAdapter(self.backend),
            files=LocalFilesAdapter(),
            capture=CaptureAdapter(self.backend),
            input=InputAdapter(),
        )

        self.command_queue = CommandQueue()
        self.cheat_manager = CheatManager()

    def quit(self):
        """Request that the main loop stops."""
        self._running = False

    # TODO: Fix too-many-statements and too-many-locals warnings
    # Justification: Main game loop with multiple responsibilities.
    # pylint: disable=too-many-statements,too-many-locals
    def run(self, initial_scene_id: str):
        """
        Run the main loop starting with the given scene.

        This is intentionally left abstract so you can plug pygame, pyglet,
        or another backend.

        :param initial_scene_id: The scene id to start the game with (must be registered).
        :type initial_scene_id: str
        """
        backend = self.backend

        self._initialize_window()

        self.services.scenes.change(initial_scene_id)

        pipeline = RenderPipeline()

        self._running = True
        target_dt = 1.0 / self.config.fps if self.config.fps > 0 else 0.0
        last_time = perf_counter()
        frame_index = 0

        # cache packets so blocked-update scenes still render their last frame
        packet_cache: dict[int, RenderPacket] = {}

        timer = FrameTimer(enabled=True)
        # report_every = 60  # print once per second at 60fps

        # TODO: Integrate SimRunner for simulation stepping
        # TODO: Fix assignment-from-no-return warning in self.services.input.build
        # & self.services.scenes.input_entry
        # Justification: These methods are expected to return values.
        # pylint: disable=assignment-from-no-return

        while self._running:
            timer.clear()
            timer.mark("frame_start")

            now = perf_counter()
            dt = now - last_time
            last_time = now

            events = list(backend.poll_events())

            for e in events:
                if e.type == EventType.WINDOWRESIZED and e.size:
                    w, h = e.size
                    logger.debug(f"Window resized event: {w}x{h}")
                    self.services.window.on_window_resized(w, h)
            timer.mark("events_polled")

            input_frame = self.services.input.build(events, frame_index, dt)
            timer.mark("input_built")

            # Window/OS quit (close button)
            if input_frame.quit:
                self.command_queue.push(QuitCommand())

            # who gets input?
            input_entry = self.services.scenes.input_entry()
            if input_entry is None:
                break

            # tick policy-aware scenes
            timer.mark("tick_start")
            for entry in self.services.scenes.update_entries():
                scene = entry.scene
                effective_input = (
                    input_frame
                    if entry is input_entry
                    else _neutral_input(frame_index, dt)
                )

                packet = scene.tick(effective_input, dt)
                packet_cache[id(scene)] = packet
            timer.mark("tick_end")

            timer.mark("command_ctx_start")
            command_context = CommandContext(
                services=self.services,
                commands=self.command_queue,
                settings=self.settings,
                world=self._resolve_world(),
            )
            timer.mark("command_ctx_end")

            timer.mark("cheats_start")
            self.cheat_manager.process_frame(
                input_frame,
                context=command_context,
                queue=self.command_queue,
            )
            timer.mark("cheats_end")

            # Execute commands at the end of the frame (consistent write path)
            timer.mark("cmd_exec_start")
            for cmd in self.command_queue.drain():
                cmd.execute(command_context)
            timer.mark("cmd_exec_end")

            timer.mark("render_start")
            backend.begin_frame()
            timer.mark("begin_frame_done")

            vp = self.services.window.get_viewport()
            for entry in self.services.scenes.visible_entries():
                scene = entry.scene
                packet = packet_cache.get(id(scene))
                if packet is None:
                    # bootstrap (first frame visible but not updated)
                    packet = scene.tick(_neutral_input(frame_index, 0.0), 0.0)
                    packet_cache[id(scene)] = packet

                pipeline.draw_packet(backend, packet, vp)

            timer.mark("draw_done")
            backend.end_frame()
            timer.mark("end_frame_done")

            timer.mark("sleep_start")
            if target_dt > 0 and dt < target_dt:
                sleep(target_dt - dt)
            timer.mark("sleep_end")

            # --- report ---
            # if timer.enabled and (
            #     frame_index % report_every == 0 and frame_index > 0
            # ):
            #     ms = timer.report_ms()
            #     total = (perf_counter() - timer.marks["frame_start"]) * 1000.0
            #     logger.debug(
            #         f"[Frame {frame_index}] total={total:.2f}ms | {ms}"
            #     )

            frame_index += 1

        # pylint: enable=assignment-from-no-return

        # exit remaining scenes
        self.services.scenes.clean()

    # pylint: enable=too-many-statements,too-many-locals

    def _initialize_window(self):
        """Initialize the game window based on the configuration."""
        self.services.window.set_window_size(
            self.config.window.width, self.config.window.height
        )
        self.services.window.set_title(self.config.window.title)

        br, bg, bb = self.config.window.background_color
        self.services.window.set_clear_color(br, bg, bb)

        # the “authoring resolution”
        self.services.window.set_virtual_resolution(800, 600)

    def _resolve_world(self) -> object | None:
        # Prefer gameplay world underneath overlays:
        # scan from top to bottom and pick the first scene that has .world
        for entry in reversed(self.services.scenes.visible_entries()):
            scene = entry.scene
            world = getattr(scene, "world", None)
            if world is not None:
                return world
        return None


# pylint: enable=too-many-instance-attributes
