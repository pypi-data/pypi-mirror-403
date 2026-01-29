"""
Provide legacy string-based filename heuristics.

These functions are deprecated and should NOT be used for new code paths. They are kept
only for migration and comparison purposes.
"""

import warnings
from pathlib import Path

from vidmux.video_library_scan import suggest_name_tags


def extract_basename_from_filename(
    filename: str, parentname: str, tags: list[str]
) -> str:
    """
    Extract the basename from filename given a list of tags.

    Note:
    This is the bottleneck. Good filenames and structures as an input are recommended.
    """
    warnings.warn(
        "extract_basename_from_filename is deprecated. "
        "Use FilenameParser and BaseMedia instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Delete tags from filename
    clean_name = filename
    for tag in tags:
        clean_name = clean_name.replace(tag, "")
    # Delete additional information separated by " - "
    clean_name = clean_name.strip()
    if (separator := " - ") in clean_name:
        parts = clean_name.split(separator)
        # If the separated part is in the directory name, treat it as part of the name
        if parts[-1] not in parentname:
            return separator.join(parts[:-1]).strip()

    return clean_name


def extract_version_from_filename(filename: str, basename: str, tags: list[str]) -> str:
    """Extract the version name."""
    warnings.warn(
        "extract_version_from_filename is deprecated. "
        "Use FilenameParser and BaseMedia instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    remainder = filename.removeprefix(basename).strip()
    if remainder.startswith("-"):
        remainder = remainder[1:].strip()

    # Delete tags from filename
    for tag in tags:
        remainder = remainder.replace(tag, "").strip()

    # Treat remainder as version name
    if remainder:
        remainder = remainder.strip(" []")  # Strip old brackets
        return f"[{remainder}]"

    return ""


def suggest_name(report: dict, undefined_language: str = "??") -> str:
    """Suggest a name based on the report."""
    warnings.warn(
        "This version of suggest_name is deprecated. "
        "Use BaseMedia and FilenameCreator instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    original_path = Path(report["filename"])
    filename = original_path.stem
    extension = original_path.suffix
    parent = original_path.parent

    # Get tags
    tags = suggest_name_tags(report, undefined_language=undefined_language)

    # Get basename and guess version (if provided)
    basename = extract_basename_from_filename(filename, parent.name, tags)
    guessed_version = extract_version_from_filename(filename, basename, tags)

    # Construct new filename
    parts = [guessed_version] if guessed_version else []
    parts.extend(tags)
    suffix = (" - " + " ".join(parts)) if parts else ""

    new_filename = f"{basename}{suffix}{extension}"

    # Check whether a subfolder has to be created
    if parent.name == basename:
        new_path = parent / new_filename
    else:
        new_path = parent / basename / new_filename

    return str(new_path)
