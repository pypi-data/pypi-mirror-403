"""
Module providing runtime adapters for window and scene management.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image

from mini_arcade_core.backend import Backend
from mini_arcade_core.runtime.capture.capture_port import CapturePort
from mini_arcade_core.utils import logger


@dataclass
class CapturePathBuilder:
    """
    Helper to build file paths for captured screenshots.

    :ivar directory (str): Directory to save screenshots in.
    :ivar prefix (str): Prefix for screenshot filenames.
    :ivar ext (str): File extension/format for screenshots.
    """

    directory: str = "screenshots"
    prefix: str = ""
    ext: str = "png"  # final output format

    def build(self, label: str) -> Path:
        """
        Build a file path for a screenshot with the given label.

        :param label: Label to include in the filename.
        :type label: str

        :return: Full path for the screenshot file.
        :rtype: Path
        """
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_label = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in label
        )
        name = f"{self.prefix}{stamp}_{safe_label}.{self.ext}"
        return Path(self.directory) / name

    def build_sim(self, run_id: str, frame_index: int, label: str) -> Path:
        """
        Build a file path for a simulation frame screenshot.

        :param run_id: Unique identifier for the simulation run.
        :type run_id: str

        :param frame_index: Index of the frame in the simulation.
        :type frame_index: int

        :param label: Label to include in the filename.
        :type label: str

        :return: Full path for the screenshot file.
        :rtype: Path
        """
        safe_label = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in label
        )
        # deterministic: run_id + frame index
        name = (
            f"{self.prefix}{run_id}_f{frame_index:08d}_{safe_label}.{self.ext}"
        )
        return Path(self.directory) / run_id / name


class CaptureAdapter(CapturePort):
    """Adapter for capturing frames."""

    def __init__(
        self,
        backend: Backend,
        path_builder: Optional[CapturePathBuilder] = None,
    ):
        self.backend = backend
        self.path_builder = path_builder or CapturePathBuilder()

    def _bmp_to_image(self, bmp_path: str, out_path: str):
        img = Image.open(bmp_path)
        img.save(out_path)

    def screenshot(self, label: str | None = None) -> str:
        label = label or "shot"
        out_path = self.path_builder.build(label)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # If backend only saves BMP, capture to a temp bmp next to output
        bmp_path = out_path.with_suffix(".bmp")

        self.backend.capture_frame(str(bmp_path))
        if not bmp_path.exists():
            raise RuntimeError("Backend capture_frame did not create BMP file")

        self._bmp_to_image(str(bmp_path), str(out_path))
        try:
            bmp_path.unlink(missing_ok=True)
        # Justification: Various exceptions can occur on file deletion
        # pylint: disable=broad-exception-caught
        except Exception:
            logger.warning(f"Failed to delete temporary BMP file: {bmp_path}")
        # pylint: enable=broad-exception-caught

        return str(out_path)

    def screenshot_bytes(self) -> bytes:
        data = self.backend.capture_frame(path=None)
        if data is None:
            raise RuntimeError("Backend returned None for screenshot_bytes()")
        return data

    def screenshot_sim(
        self, run_id: str, frame_index: int, label: str = "frame"
    ) -> str:
        """Screenshot for simulation frames."""
        out_path = self.path_builder.build_sim(run_id, frame_index, label)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        bmp_path = out_path.with_suffix(".bmp")
        self.backend.capture_frame(str(bmp_path))

        if not bmp_path.exists():
            raise RuntimeError("Backend capture_frame did not create BMP file")

        self._bmp_to_image(str(bmp_path), str(out_path))

        try:
            bmp_path.unlink(missing_ok=True)
        # Justification: Various exceptions can occur on file deletion
        # pylint: disable=broad-exception-caught
        except Exception:
            logger.warning(f"Failed to delete temporary BMP file: {bmp_path}")
        # pylint: enable=broad-exception-caught

        return str(out_path)
