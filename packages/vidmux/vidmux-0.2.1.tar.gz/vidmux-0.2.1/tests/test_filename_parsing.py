"""Provide tests for parsing media information from filenames."""

import pytest

from vidmux.media import FilenameParser


@pytest.fixture(scope="module")
def parser() -> FilenameParser:
    """Provide the filename parser."""
    return FilenameParser()


def test_movie_parsing(parser: FilenameParser, movie_test_data: dict) -> None:
    """Test the parsing of a movie filename."""
    media = parser.parse(movie_test_data["filename"])

    assert media == movie_test_data["media"]


def test_episode_parsing(parser: FilenameParser, episode_test_data: dict) -> None:
    """Test the parsing of a episode filename."""
    media = parser.parse(episode_test_data["filename"])

    assert media == episode_test_data["media"]


@pytest.mark.parametrize(
    "raw, tokens, normalized",
    [
        (
            "DE [Extended Version]",
            ["DE", "Extended Version"],
            "[DE] [Extended Version]",
        ),
        (
            "[Director's Cut] 4K HDR",
            ["Director's Cut", "4K", "HDR"],
            "[Director's Cut] [4K] [HDR]",
        ),
        ("1080p EN", ["1080p", "EN"], "[1080p] [EN]"),
        ("[DE]", ["DE"], "[DE]"),
        (None, [], None),
    ],
)
def test_version_tokenization_and_normalization(
    parser: FilenameParser, raw: str, tokens: list[str], normalized: str
) -> None:
    """Test internal handling of versions, i.e. tokenization and normalization."""
    assert parser._tokenize_version(raw) == tokens
    assert parser._normalize_version(raw) == normalized
