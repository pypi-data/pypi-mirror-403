"""Provide tools for version tags."""

import logging
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum, auto

from vidmux.languages import LANGUAGES_ISO_639_1


logger = logging.getLogger("vidmux")


class TagCategory(Enum):
    """Provide categories for version tags."""

    AUDIO = auto()
    EDITION = auto()
    LANGUAGE = auto()
    MISC = auto()
    ORIGIN = auto()
    RESOLUTION = auto()


DEFAULT_TAG_ORDER = [
    TagCategory.EDITION,
    TagCategory.ORIGIN,
    TagCategory.LANGUAGE,
    TagCategory.RESOLUTION,
    TagCategory.AUDIO,
    TagCategory.MISC,
]


CATEGORY_MAX_COUNTS: dict[TagCategory, int | None] = {
    TagCategory.RESOLUTION: 1,
    TagCategory.ORIGIN: 1,
    TagCategory.EDITION: 1,
    TagCategory.LANGUAGE: None,
    TagCategory.AUDIO: None,
    TagCategory.MISC: None,
}


@dataclass
class VersionTagOptions:
    """Provide options for media naming."""

    include_audio: bool = False
    include_editions: bool = True
    include_languages: bool = True
    include_origin: bool = True
    include_misc: bool = False
    include_resolution: bool = True

    force_tag_order: bool = True

    def category_enabled(self, category: TagCategory) -> bool:
        """Check if a category is enabled."""
        match category:
            case TagCategory.AUDIO:
                return self.include_audio
            case TagCategory.EDITION:
                return self.include_editions
            case TagCategory.LANGUAGE:
                return self.include_languages
            case TagCategory.ORIGIN:
                return self.include_origin
            case TagCategory.MISC:
                return self.include_misc
            case TagCategory.RESOLUTION:
                return self.include_resolution
            case _:
                raise ValueError(f"Unknown TagCategory: {category}")


DEFAULT_VERSION_TAG_OPTIONS = VersionTagOptions()


class VersionTags:
    """Provide known version tags and filtering."""

    _editions = (
        "cinematic cut",
        "director's cut",
        "directors cut",
        "extended cut",
        "final cut",
        "special edition",
        "special extended cut",
        "theatrical cut",
    )
    # Language abbreviations according to ISO 639-1
    _languages = LANGUAGES_ISO_639_1
    _origins = (
        "bd",
        "bluray",
        "blu-ray",
        "bd",
        "cd",
        "download",
        "dvd",
        "stream",
        "tv",
    )

    def is_audio(self, tag: str) -> bool:
        """Check if a tag represents an audio."""
        # TODO: Implement logic
        raise NotImplementedError()

    def is_edition(self, tag: str) -> bool:
        """Check if a tag represents a known edition."""
        return tag in self._editions

    def is_language(self, tag: str) -> bool:
        """Check if a tag represents a known language according to ISO 639-1."""
        tag_split = tag.split("+")
        return all(tag_part in self._languages for tag_part in tag_split if tag_part)

    def is_origin(self, tag: str) -> bool:
        """Check if a tag represents a known origin."""
        return tag in self._origins

    def is_resolution(self, tag: str) -> bool:
        """Check if a tag represents a resolution."""
        return tag.endswith(("p", "i")) and len(tag) >= 4 and tag[:-1].isdigit()

    def classify_tag(self, tag: str) -> TagCategory:
        """Return the category of a tag."""
        lowered = tag.lower()
        # TODO: Implement audio
        # if self.is_audio(lowered):
        #     return TagCategory.AUDIO
        if self.is_edition(lowered):
            return TagCategory.EDITION
        if self.is_language(lowered):
            return TagCategory.LANGUAGE
        if self.is_origin(lowered):
            return TagCategory.ORIGIN
        if self.is_resolution(lowered):
            return TagCategory.RESOLUTION

        return TagCategory.MISC

    def group_tags(self, tags: list[str]) -> dict[TagCategory, list[str]]:
        """Group tags by their category."""
        groups = defaultdict(list)
        for tag in tags:
            groups[self.classify_tag(tag)].append(tag)

        return groups

    def get_filtered_tags(
        self, tags: list[str], options: VersionTagOptions = DEFAULT_VERSION_TAG_OPTIONS
    ) -> list[str]:
        """Return the tags filtered by options."""
        groups = self.group_tags(tags)

        if options.force_tag_order:
            ordered_categories = DEFAULT_TAG_ORDER
        else:
            # Original tag order
            ordered_categories = dict.fromkeys(self.classify_tag(tag) for tag in tags)

        result = []

        for category in ordered_categories:
            if not options.category_enabled(category):
                continue
            category_tags = groups.get(category, [])
            self.validate_category_tags(category, category_tags)
            result.extend(category_tags)

        return result

    @staticmethod
    def validate_category_tags(
        category: TagCategory,
        tags: list[str],
    ) -> None:
        """Issue a warning if the number of tags exceeds the category limit."""
        max_count = CATEGORY_MAX_COUNTS.get(category)
        if max_count is None:
            return

        if (n_tags := len(tags)) > max_count:
            msg = (
                f"Multiple {category.name.lower()} tags provided ({tags}, n={n_tags}); "
                f"expected at most {max_count}"
            )
            logger.warning(msg)
