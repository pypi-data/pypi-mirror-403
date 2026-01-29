"""Provide tests for version tags."""

import pytest

from vidmux.media import VersionTags, VersionTagOptions


@pytest.fixture(scope="module")
def version_tags() -> VersionTags:
    """Provide the version tags filter."""
    return VersionTags()


def test_tag_order_forced(version_tags: VersionTags) -> None:
    """Test the force tag order option."""
    assert version_tags.get_filtered_tags(
        ["1080p", "EN", "Extended Cut"],
        VersionTagOptions(force_tag_order=True),
    ) == ["Extended Cut", "EN", "1080p"]


def test_tag_order_input_preserved(version_tags: VersionTags) -> None:
    """Test the keep tag order option."""
    assert version_tags.get_filtered_tags(
        ["1080p", "EN", "Extended Cut"],
        VersionTagOptions(force_tag_order=False),
    ) == ["1080p", "EN", "Extended Cut"]


def test_exclude_language_tags(version_tags: VersionTags) -> None:
    """Test the exclude language tags option."""
    assert version_tags.get_filtered_tags(
        ["1080p", "EN", "Extended Cut", "DE"],
        VersionTagOptions(include_languages=False, force_tag_order=False),
    ) == ["1080p", "Extended Cut"]


def test_exclude_resolution_tags(version_tags: VersionTags) -> None:
    """Test the exclude resolution tags option."""
    assert version_tags.get_filtered_tags(
        ["1080p", "EN", "1080i", "Extended Cut"],
        VersionTagOptions(include_resolution=False, force_tag_order=False),
    ) == ["EN", "Extended Cut"]
