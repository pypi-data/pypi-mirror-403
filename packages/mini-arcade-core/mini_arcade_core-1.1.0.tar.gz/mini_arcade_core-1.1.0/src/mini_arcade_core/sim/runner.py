"""
Simulation runner module.
Defines the SimRunner class for running simulation scenes.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter, sleep
from typing import Dict, Optional

from mini_arcade_core.backend import Backend
from mini_arcade_core.engine.render.packet import RenderPacket
from mini_arcade_core.engine.render.pipeline import RenderPipeline
from mini_arcade_core.runtime.input_frame import InputFrame
from mini_arcade_core.runtime.scene.scene_port import SceneEntry
from mini_arcade_core.runtime.services import RuntimeServices


def _neutral_input(frame_index: int, dt: float) -> InputFrame:
    # InputFrame is frozen; create a clean snapshot for non-input scenes.
    return InputFrame(frame_index=frame_index, dt=dt)


def _has_tick(scene: object) -> bool:
    # Avoid isinstance(..., Protocol). Structural check.
    return callable(getattr(scene, "tick", None))


def _has_draw(scene: object) -> bool:
    return callable(getattr(scene, "draw", None))


def _has_update(scene: object) -> bool:
    return callable(getattr(scene, "update", None))


def _has_handle_event(scene: object) -> bool:
    return callable(getattr(scene, "handle_event", None))


@dataclass(frozen=True)
class SimRunnerConfig:
    """
    Config for sim runner.

    - record: if True, capture a frame each tick using deterministic naming.
    - run_id: required when record=True.
    - max_frames: optional safety stop (useful for offline sims/tests).
    """

    fps: int = 60
    record: bool = False
    run_id: str = "run"
    max_frames: Optional[int] = None
    # If True, still forward raw events to the input scene's handle_event (legacy UI / text input).
    forward_events_to_input_scene: bool = True


class SimRunner:
    """
    Simulation-first runner.

    Uses:
      - services.scenes.update_entries() for ticking (policy-aware)
      - services.scenes.visible_entries() for rendering (opaque-aware)
      - services.scenes.input_entry() for input focus
    """

    def __init__(
        self,
        backend: Backend,
        services: RuntimeServices,
        *,
        render_pipeline: Optional[RenderPipeline] = None,
    ):
        if services.scenes is None:
            raise ValueError("RuntimeServices.scenes must be set")
        if services.input is None:
            raise ValueError("RuntimeServices.input must be set")
        if services.capture is None:
            # recording is optional, but capture port should exist in v1
            raise ValueError("RuntimeServices.capture must be set")

        self.backend = backend
        self.services = services
        self.pipeline = render_pipeline or RenderPipeline()

        # cache: scene object id -> last RenderPacket
        self._packets: Dict[int, RenderPacket] = {}

        self._running: bool = False

    def stop(self):
        """
        Stop the simulation loop.
        """
        self._running = False

    # TODO: Solve too-many-statements, too-many-branches and too-many-locals
    # warning later
    # Justification: The run method orchestrates multiple complex steps in the
    # simulation loop.
    # pylint: disable=too-many-statements,too-many-branches,too-many-locals
    def run(
        self, initial_scene_id: str, *, cfg: Optional[SimRunnerConfig] = None
    ):
        """
        Run the simulation loop starting from the initial scene.

        :param initial_scene_id: ID of the initial scene to load.
        :type initial_scene_id: str

        :param cfg: Optional SimRunnerConfig instance.
        :type cfg: Optional[SimRunnerConfig]
        """
        cfg = cfg or SimRunnerConfig()

        scenes = self.services.scenes
        assert scenes is not None

        # start at initial scene
        scenes.change(initial_scene_id)

        self._running = True
        target_dt = 1.0 / cfg.fps if cfg.fps > 0 else 0.0

        last_time = perf_counter()
        frame_index = 0

        while self._running:
            if cfg.max_frames is not None and frame_index >= cfg.max_frames:
                break

            now = perf_counter()
            dt = now - last_time
            last_time = now

            # 1) poll events -> build InputFrame
            events = list(self.backend.poll_events())
            input_frame = self.services.input.build(events, frame_index, dt)

            # 2) OS quit request is a hard stop
            if input_frame.quit:
                # use ScenePort.quit so Game.quit can be centralized there
                scenes.quit()
                break

            # 3) input focus scene (top of visible stack)
            input_entry: Optional[SceneEntry] = scenes.input_entry()
            if input_entry is None:
                break

            # Optional legacy: forward raw events to focused scene
            if cfg.forward_events_to_input_scene and _has_handle_event(
                input_entry.scene
            ):
                for ev in events:
                    input_entry.scene.handle_event(ev)

            # 4) tick/update policy-aware scenes
            for entry in scenes.update_entries():
                scene_obj = entry.scene
                scene_key = id(scene_obj)

                # Only the input-focused scene receives the actual input_frame
                effective_input = (
                    input_frame
                    if entry is input_entry
                    else _neutral_input(frame_index, dt)
                )

                if _has_tick(scene_obj):
                    packet = scene_obj.tick(effective_input, dt)  # SimScene
                    if not isinstance(packet, RenderPacket):
                        raise TypeError(
                            f"{entry.scene_id}.tick() must "
                            f"return RenderPacket, got {type(packet)!r}"
                        )
                    self._packets[scene_key] = packet
                elif _has_update(scene_obj):
                    # legacy scene; keep packet cache if any
                    scene_obj.update(dt)

            # 5) render visible stack (policy-aware)
            self.backend.begin_frame()

            for entry in scenes.visible_entries():
                scene_obj = entry.scene
                scene_key = id(scene_obj)

                if _has_tick(scene_obj):
                    packet = self._packets.get(scene_key)
                    # If first frame and no packet exists yet, do a dt=0 tick to bootstrap
                    if packet is None:
                        packet = scene_obj.tick(
                            _neutral_input(frame_index, 0.0), 0.0
                        )
                        self._packets[scene_key] = packet
                    self.pipeline.draw_packet(self.backend, packet)

                elif _has_draw(scene_obj):
                    # legacy scene draw path
                    scene_obj.draw(self.backend)

            self.backend.end_frame()

            # 6) deterministic capture (optional)
            if cfg.record:
                # label could be "frame" or something semantic later
                self.services.capture.screenshot_sim(
                    cfg.run_id, frame_index, label="frame"
                )

            # 7) frame pacing
            if target_dt > 0 and dt < target_dt:
                sleep(target_dt - dt)

            frame_index += 1

        # cleanup scenes
        scenes.clean()
