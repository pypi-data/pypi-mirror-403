"""
Module providing runtime adapters for window and scene management.
"""

from __future__ import annotations

from mini_arcade_core.runtime.audio.audio_port import AudioPort


class SDLAudioAdapter(AudioPort):
    """A no-op audio adapter."""

    def __init__(self, backend):
        self.backend = backend

    def load_sound(self, sound_id: str, file_path: str):
        self.backend.load_sound(sound_id, file_path)

    def play(self, sound_id: str, loops: int = 0):
        self.backend.play_sound(sound_id, loops)
