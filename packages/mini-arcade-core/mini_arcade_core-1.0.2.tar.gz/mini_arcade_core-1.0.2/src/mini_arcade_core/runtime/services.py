"""
Service container for runtime components.
"""

from __future__ import annotations

from dataclasses import dataclass

from mini_arcade_core.runtime.audio.audio_port import AudioPort
from mini_arcade_core.runtime.capture.capture_port import CapturePort
from mini_arcade_core.runtime.file.file_port import FilePort
from mini_arcade_core.runtime.input.input_port import InputPort
from mini_arcade_core.runtime.scene.scene_port import ScenePort
from mini_arcade_core.runtime.window.window_port import WindowPort


@dataclass
class RuntimeServices:
    """
    Container for runtime service ports.

    :ivar window (WindowPort): Window service port.
    :ivar scenes (ScenePort): Scene management service port.
    :ivar audio (AudioPort): Audio service port.
    :ivar files (FilePort): File service port.
    :ivar capture (CapturePort): Capture service port.
    :ivar input (InputPort): Input handling service port.
    """

    window: WindowPort
    scenes: ScenePort
    audio: AudioPort
    files: FilePort
    capture: CapturePort
    input: InputPort
