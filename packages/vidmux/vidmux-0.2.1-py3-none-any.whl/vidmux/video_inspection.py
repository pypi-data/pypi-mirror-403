"""Tools for video inspection (format, streams, resolution, ...)."""

import json
import subprocess
from pathlib import Path
from typing import Any


def get_file_info(
    file_path: Path, stream_type: str | None = "all", include_format: bool = True
) -> dict[str, Any]:
    """
    Return the interesting ffprobe info of a file.

    stream_type:
        "all"  = all streams
        "a"    = audio only
        "v"    = video only
        "s"    = subtitles only
        "none" = no streams
    """
    if stream_type and stream_type not in ("all", "none", "a", "v", "s"):
        raise ValueError("Invalid stream_type. Must be 'all', 'none', 'a', 'v' or 's'.")

    # Create ffprobe command
    # TODO: Maybe use -show-entries to only read out interesting entries (speed!)
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
    ]
    if include_format:
        cmd.append("-show_format")
    if stream_type and stream_type != "none":
        cmd.append("-show_streams")
        if stream_type != "all":
            cmd.extend(["-select_streams", stream_type])
    cmd.append(str(file_path))

    # Run ffprobe
    # TODO: Better error handling
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        info = json.loads(result.stdout)
        return info
    except json.JSONDecodeError:
        # TODO: log warning
        return {}


def get_format(file_path: Path) -> str:
    """Return the container format of a file (e.g., 'mov,mp4,m4a,3gp,3g2,mj2')."""
    info = get_file_info(file_path, stream_type="none", include_format=True)

    return info.get("format", {}).get("format_name", "")


def get_streams(file_path: Path, stream_type: str):
    """
    Extract media streams using ffprobe (ffmpeg).

    stream_type: "all" = All streams, "a" = Audio, "v" = Video, "s" = Subtitle
    """
    info = get_file_info(file_path, stream_type=stream_type, include_format=False)

    return info.get("streams", [])


def group_streams_by_types(streams: list[dict]) -> dict[str, list]:
    """Classify streams by their stream type."""
    grouped_streams = {"audio": [], "subtitle": [], "video": []}

    for stream in streams:
        match stream_type := stream.get("codec_type"):
            case "audio":
                grouped_streams["audio"].append(stream)
            case "subtitle":
                grouped_streams["subtitle"].append(stream)
            case "video":
                grouped_streams["video"].append(stream)
            case _:
                print(f"Unkown {stream_type=}")

    return grouped_streams


def get_all_tracks(file_path: Path):
    """Extract audio, subtitle and video tracks using ffprobe (ffmpeg)."""
    streams = get_streams(file_path, "all")

    return group_streams_by_types(streams)


def get_audio_tracks(file_path: Path):
    """Extract audio tracks using ffprobe (ffmpeg)."""
    return get_streams(file_path, "a")


def get_subtitles(file_path: Path):
    """Extract subtitles using ffprobe (ffmpeg)."""
    return get_streams(file_path, "s")


def get_video_tracks(file_path: Path):
    """Extract video tracks using ffprobe (ffmpeg)."""
    return get_streams(file_path, "v")


def get_video_resolution(path_or_url: str | Path) -> tuple[int, int] | None:
    """Get the video resolution for a file or URL."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        str(path_or_url),
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
        width, height = output.split("x")
        return int(width), int(height)
    except subprocess.CalledProcessError as err:
        print("ffprobe error:", err.output.decode())
        return None
