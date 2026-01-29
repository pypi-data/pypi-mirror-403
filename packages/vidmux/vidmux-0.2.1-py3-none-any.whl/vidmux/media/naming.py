"""Provide tools for media file naming."""

from dataclasses import dataclass

from vidmux.media.models import BaseMedia, Episode, Movie
from vidmux.media.version_tags import (
    VersionTagOptions,
    VersionTags,
    DEFAULT_VERSION_TAG_OPTIONS,
)


@dataclass
class CanonicalName:
    """Provide a canonical name for a media object."""

    filename: str
    directory: str
    version_tokens: list[str]


class FilenameCreator:
    """Creator for media filenames based on the media information."""

    tag_filter = VersionTags()

    def __call__(
        self,
        media: BaseMedia,
        additional_tags: list[str] | None = None,
        options: VersionTagOptions = DEFAULT_VERSION_TAG_OPTIONS,
    ) -> CanonicalName:
        """Create filename according to media information."""
        return self.create(media, additional_tags=additional_tags, options=options)

    def create(
        self,
        media: BaseMedia,
        additional_tags: list[str] | None = None,
        options: VersionTagOptions = DEFAULT_VERSION_TAG_OPTIONS,
    ) -> CanonicalName | None:
        """Create filename according to media information."""
        if not additional_tags:
            additional_tags = []

        match media.media_type:
            case "movie":
                return self._get_movie_title(media, additional_tags, options)
            case "show":
                return self._get_episode_title(media, additional_tags, options)
            case _:
                return None

    def _get_base_title(self, media: BaseMedia) -> str:
        """Create the basic string title for a media object."""
        basename = media.title  # Should work for shows as well!
        if media.year:
            basename += f" ({media.year})"
        if media.metadata_provider_id:
            basename += f" [{media.metadata_provider_id}]"

        return basename

    def _get_version(
        self, media: BaseMedia, additional_tags: list[str], options: VersionTagOptions
    ) -> tuple[str, list[str]]:
        """Create the version string for a media object."""
        # tokens = set(media.version_tokens + additional_tags)
        # This way we preserve the tag order
        tokens = media.version_tokens
        for tag in additional_tags:
            if tag not in tokens:
                tokens.append(tag)

        # Filter tags according to options
        tokens = self.tag_filter.get_filtered_tags(tokens, options=options)

        if not tokens:
            return "", []

        return " ".join(f"[{token}]" for token in tokens), tokens

    def _get_movie_title(
        self,
        media: Movie,
        additional_tags: list[str],
        options: VersionTagOptions,
    ) -> CanonicalName:
        """Create filename for a movie."""
        basename = self._get_base_title(media)
        version, version_tokens = self._get_version(media, additional_tags, options)

        directory = basename
        filename = basename
        # Current specification: version info is not supported if there are parts
        if media.part:
            filename += f"-{media.part}"
        elif version:
            filename += f" - {version}"

        return CanonicalName(filename, directory, version_tokens)

    def _get_episode_title(
        self,
        media: Episode,
        additional_tags: list[str],
        options: VersionTagOptions,
    ) -> CanonicalName:
        """Create filename for an episode."""
        basename = self._get_base_title(media)
        version, version_tokens = self._get_version(media, additional_tags, options)

        directory = f"{basename}/Season {media.season:02d}"
        filename = f"{basename} S{media.season:02d}E{media.episode:02d}"
        if media.episode_title:
            filename += f" {media.episode_title}"
        # Current specification: version info is not supported if there are parts
        if media.part:
            filename += f"-{media.part}"
        elif version:
            filename += f" - {version}"

        return CanonicalName(filename, directory, version_tokens)


DEFAULT_CREATOR = FilenameCreator()


def get_canonical_name(
    media: BaseMedia,
    additional_tags: list[str] | None = None,
    options: VersionTagOptions = DEFAULT_VERSION_TAG_OPTIONS,
) -> CanonicalName:
    """Create a canonical name from a media object.."""

    return DEFAULT_CREATOR.create(
        media, additional_tags=additional_tags, options=options
    )
