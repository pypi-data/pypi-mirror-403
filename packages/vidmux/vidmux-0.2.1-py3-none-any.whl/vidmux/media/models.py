"""Provide data models for media."""

from dataclasses import dataclass


@dataclass
class BaseMedia:
    """Provide the data model for media."""

    raw: str
    title: str
    year: int | None = None
    metadata_provider_id: str | None = None
    version: str | None = None
    version_tokens: list[str] | None = None
    part: str | None = None


@dataclass
class Movie(BaseMedia):
    """Provide the data model for movies."""

    media_type: str = "movie"


@dataclass
class Episode(BaseMedia):
    """Provide the data model for episodes of a show."""

    # Fields series, season and episode are NOT optional and should always be provided!
    # They are defined as optional since this class inherits from BaseMedia.
    series: str = ""
    season: int = 0
    episode: int = 0
    episode_title: str | None = None
    media_type: str = "show"
