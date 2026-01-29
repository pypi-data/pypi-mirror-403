"""
Game core module defining the Game class and configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter, sleep
from typing import Dict, Literal

from mini_arcade_core.backend import Backend, WindowSettings
from mini_arcade_core.backend.events import EventType
from mini_arcade_core.backend.keys import Key
from mini_arcade_core.engine.commands import (
    CommandContext,
    CommandQueue,
    QuitCommand,
    ToggleDebugOverlayCommand,
    ToggleEffectCommand,
)
from mini_arcade_core.engine.render.context import RenderContext
from mini_arcade_core.engine.render.effects.base import (
    EffectParams,
    EffectStack,
)
from mini_arcade_core.engine.render.effects.crt import CRTEffect
from mini_arcade_core.engine.render.effects.registry import EffectRegistry
from mini_arcade_core.engine.render.effects.vignette import VignetteNoiseEffect
from mini_arcade_core.engine.render.frame_packet import FramePacket
from mini_arcade_core.engine.render.packet import RenderPacket
from mini_arcade_core.engine.render.pipeline import RenderPipeline
from mini_arcade_core.engine.render.render_service import RenderService
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
class PostFXConfig:
    """
    Configuration for post-processing effects.

    :ivar enabled (bool): Whether post effects are enabled by default.
    :ivar active (list[str]): List of active effect IDs by default.
    """

    enabled: bool = True
    active: list[str] = field(default_factory=list)


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
    postfx: PostFXConfig = field(default_factory=PostFXConfig)


Difficulty = Literal["easy", "normal", "hard", "insane"]


@dataclass
class GameSettings:
    """
    Game settings that can be modified during gameplay.

    :ivar difficulty (Difficulty): Current game difficulty level.
    """

    difficulty: Difficulty = "normal"
    effects_stack: EffectStack | None = None


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
            render=RenderService(),
        )

        self.command_queue = CommandQueue()
        self.cheat_manager = CheatManager()

    def quit(self):
        """Request that the main loop stops."""
        self._running = False

    # TODO: Fix too-many-statements and too-many-locals warnings
    # Justification: Main game loop with multiple responsibilities.
    # pylint: disable=too-many-statements,too-many-locals
    # TODO: Fix too-many-branches warning
    # Justification: Complex control flow in main loop.
    # pylint: disable=too-many-branches
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

        effects_registry = EffectRegistry()
        effects_registry.register(CRTEffect())
        effects_registry.register(VignetteNoiseEffect())

        effects_stack = EffectStack(
            enabled=self.config.postfx.enabled,
            active=list(self.config.postfx.active),
            params={
                "crt": EffectParams(intensity=0.35, wobble_speed=1.0),
                "vignette_noise": EffectParams(
                    intensity=0.25, wobble_speed=1.0
                ),
            },
        )
        self.settings.effects_stack = effects_stack

        for p in pipeline.passes:
            if getattr(p, "name", "") == "PostFXPass":
                p.registry = effects_registry

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
        time_s = 0.0

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
                # if F1 pressed, toggle debug overlay
                if e.type == EventType.KEYDOWN:
                    if e.key == Key.F1:
                        self.command_queue.push(ToggleDebugOverlayCommand())
                    elif e.key == Key.F2:
                        self.command_queue.push(ToggleEffectCommand("crt"))
                    elif e.key == Key.F3:
                        self.command_queue.push(
                            ToggleEffectCommand("vignette_noise")
                        )
                    elif e.key == Key.F4:
                        effects_stack.enabled = not effects_stack.enabled
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

            # ---------------- TO REPLACE WITH RENDERING PIPELINE ----------------
            timer.mark("render_start")

            vp = self.services.window.get_viewport()

            # gather visible packets
            frame_packets: list[RenderPacket] = []
            for entry in self.services.scenes.visible_entries():
                scene = entry.scene
                packet = packet_cache.get(id(scene))
                if packet is None:
                    packet = scene.tick(_neutral_input(frame_index, 0.0), 0.0)
                    packet_cache[id(scene)] = packet
                frame_packets.append(
                    FramePacket(
                        scene_id=entry.scene_id,
                        is_overlay=entry.is_overlay,
                        packet=packet,
                    )
                )

            render_ctx = RenderContext(
                viewport=vp,
                debug_overlay=getattr(self.settings, "debug_overlay", False),
                frame_ms=dt * 1000.0,
            )
            time_s += dt
            render_ctx.meta["frame_index"] = frame_index
            render_ctx.meta["time_s"] = time_s
            render_ctx.meta["effects_stack"] = effects_stack

            self.services.render.last_frame_ms = render_ctx.frame_ms
            self.services.render.last_stats = render_ctx.stats
            pipeline.render_frame(backend, render_ctx, frame_packets)

            timer.mark("render_done")
            # ---------------- END RENDERING PIPELINE ----------------------------
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
