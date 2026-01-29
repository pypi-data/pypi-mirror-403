"""Provide tests for creating filenames from media information."""

import pytest

from vidmux.media import FilenameCreator, VersionTagOptions


@pytest.fixture(scope="module")
def creator() -> FilenameCreator:
    """Provide the filename parser."""
    return FilenameCreator()


@pytest.fixture(scope="module")
def tag_options() -> VersionTagOptions:
    """
    Provide the tag options.

    For the tests in this module, include all tags in the original order.
    """
    return VersionTagOptions(
        include_audio=True,
        include_editions=True,
        include_languages=True,
        include_misc=True,
        include_origin=True,
        include_resolution=True,
        force_tag_order=False,
    )


def test_movie_filename_creation(
    creator: FilenameCreator, tag_options: VersionTagOptions, movie_test_data: dict
) -> None:
    """Test the creation of a movie filename."""
    canonical_name = creator.create(movie_test_data["media"], options=tag_options)

    assert canonical_name == movie_test_data["canonical"]


def test_episode_filename_creation(
    creator: FilenameCreator, tag_options: VersionTagOptions, episode_test_data: dict
) -> None:
    """Test the creation of a episode filename."""
    canonical_name = creator.create(episode_test_data["media"], options=tag_options)

    assert canonical_name == episode_test_data["canonical"]
