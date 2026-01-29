"""Provide tools to identify media information by processing the filename."""

import re

from vidmux.media.models import BaseMedia, Episode, Movie


MOVIE_PATTERN = re.compile(
    r"""
    ^
    (?P<title>.+?)
    (?:\s*\((?P<year>\d{4})\))?
    (?:\s*\[(?P<provider>[^\]]+)\])?
    (?:\s*-\s*
        (?:
            (?P<part>
                (?:cd|dvd|part|pt|disc|disk)
                [ .\-_]?
                (?:\d+|[a-d])
            )
            |
            (?P<version>
                (?:\[[^\]]+\]\s*)+
                |
                .+
            )
        )
    )?
    $
""",
    re.VERBOSE | re.IGNORECASE,
)

# Take everything before year as title -> make dashes possible
MOVIE_SPLIT_PATTERN = re.compile(
    r"""
    ^
    (?P<title>.+?)
    (?:\s*\[(?P<provider>[^\]]+)\])?
    \s*\(
        (?P<year>\d{4})
    \)
    (?P<suffix>.*)?
$
""",
    re.VERBOSE | re.IGNORECASE,
)

MOVIE_SUFFIX_PATTERN = re.compile(
    r"""
    ^
    (?:\s*\[(?P<provider>[^\]]+)\])?
    (?:\s*-\s*
        (?:
            (?P<part>
                (?:cd|dvd|part|pt|disc|disk)
                [ .\-_]?
                (?:\d+|[a-d])
            )
            |
            (?P<version>
                (?:\[[^\]]+\]\s*)+
                |
                .+
            )
        )
    )?
    $
""",
    re.VERBOSE | re.IGNORECASE,
)

SHOW_PATTERN = re.compile(
    r"""
    ^
    (?P<series>.+?)
    (?:\s*\((?P<year>\d{4})\))?
    (?:\s*\[(?P<provider>[^\]]+)\])?
    \s+
    S(?P<season>\d{1,2})
    E(?P<episode>\d{1,3})
    (?:\s+(?P<episodename>.*?))?
    (?:\s*-\s*(?P<version>.+))?
    $
""",
    re.VERBOSE | re.IGNORECASE,
)

VERSION_TOKEN_PATTERN = re.compile(r"\[([^\]]+)\]|(\S+)")

PART_PATTERN = re.compile(
    r"(cd|dvd|part|pt|disc|disk)[ .\-_]?(\d+|[a-d])", re.IGNORECASE
)


class FilenameParser:
    """Identify media information by processing the filename."""

    def __call__(self, filename: str) -> BaseMedia | None:
        """Identify media information by processing the filename."""
        return self.parse(filename)

    def parse(self, filename: str) -> BaseMedia | None:
        """Identify media information by processing the filename."""
        filename = filename.strip()

        if re_match := SHOW_PATTERN.match(filename):
            return self._parse_show(filename, re_match)

        if re_match := MOVIE_SPLIT_PATTERN.match(filename):
            return self._parse_movie_with_year(filename, re_match)

        if re_match := MOVIE_PATTERN.match(filename):
            return self._parse_movie(filename, re_match)

        return None

    def _parse_movie(self, raw: str, re_match: re.Match) -> Movie:
        """Return Movie object with the information from re_match."""
        part = self._normalize_part(re_match.group("part"))
        version = None if part else self._normalize_version(re_match.group("version"))

        return Movie(
            raw=raw,
            title=re_match.group("title").strip(),
            year=self._optional_to_int(re_match.group("year")),
            metadata_provider_id=re_match.group("provider"),
            version=version,
            version_tokens=self._tokenize_version(version),
            part=part,
        )

    def _parse_movie_with_year(self, raw: str, re_match: re.Match) -> Movie:
        """Return Movie object with the information from re_match (dash friendly)."""
        suffix = re_match.group("suffix")
        suffix_re_match = MOVIE_SUFFIX_PATTERN.match(suffix)
        part = self._normalize_part(suffix_re_match.group("part"))
        version = (
            None if part else self._normalize_version(suffix_re_match.group("version"))
        )

        provider = re_match.group("provider") or suffix_re_match.group("provider")

        return Movie(
            raw=raw,
            title=re_match.group("title").strip(),
            year=self._optional_to_int(re_match.group("year")),
            metadata_provider_id=provider,
            version=version,
            version_tokens=self._tokenize_version(version),
            part=part,
        )

    def _parse_show(self, raw: str, re_match: re.Match) -> Episode:
        """Return Episode object with the information from re_match."""
        version = self._normalize_version(re_match.group("version"))

        series_title = re_match.group("series").strip()

        return Episode(
            raw=raw,
            series=series_title,
            title=series_title,
            year=self._optional_to_int(re_match.group("year")),
            metadata_provider_id=re_match.group("provider"),
            season=int(re_match.group("season")),
            episode=int(re_match.group("episode")),
            episode_title=re_match.group("episodename"),
            version=version,
            version_tokens=self._tokenize_version(version),
            part=None,
        )

    def _normalize_version(self, version: str | int | None) -> str | None:
        """Return the normalized version information."""
        if not version:
            return None

        tokens = self._tokenize_version(version)

        return " ".join(f"[{token}]" for token in tokens)

    def _tokenize_version(self, version: str | int | None) -> list[str]:
        """Tokenize the version information."""
        if not version:
            return []

        # The regex search returns tuples (in_brackets, not_in_brackets) where one of
        # the values is always empty, e.g. "[Extended Version] EN" will return
        # [("Extended Version", ""), ("", "EN")]
        return [
            in_brackets or not_in_brackets
            for in_brackets, not_in_brackets in VERSION_TOKEN_PATTERN.findall(version)
        ]

    def _normalize_part(self, part: str | int | None) -> str | None:
        """Normalize the part information."""
        if not part:
            return None

        re_match = PART_PATTERN.match(part)
        if not re_match:
            return None

        return f"{re_match.group(1).lower()}{re_match.group(2)}"

    @staticmethod
    def _optional_to_int(value: str | int | None) -> int | None:
        """Return an integer conversion of the given value if it has a truth value."""

        return int(value) if value else None


DEFAULT_PARSER = FilenameParser()


def get_media_from_filename(filename: str) -> Episode | Movie | None:
    """Parse a media filename and return a Movie, Episode or None."""

    return DEFAULT_PARSER.parse(filename)
