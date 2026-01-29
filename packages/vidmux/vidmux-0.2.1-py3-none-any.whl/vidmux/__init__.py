"""Vidmux: Inspect and modify video/audio/subtitle tracks using FFmpeg."""

import logging

from vidmux.filesystem import InvalidJSONFileTypeError, JSONFile, JSONTypes

__all__ = ["InvalidJSONFileTypeError", "JSONFile", "JSONTypes"]

logging.basicConfig(format="[{levelname}:{name}]: {message}", style="{")
