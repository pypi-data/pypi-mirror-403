"""Test the library structure submodule."""

from pathlib import Path

import pytest

from vidmux.library_structure import load_default_rules, run_validation

MOVIES = {
    "Example Movie A/Example Movie A.mp4": ["MISSING_YEAR"],
    "Example Movie B (20)/Example Movie B (20).mp4": ["MISSING_YEAR"],
    "Example Movie C (2009)/Example Movie C (2009).mp4": [],
    "Example Movie D (2003)/Example Movie D (2003) - [EN+DE].mp4": [],
    "Example Movie E (2003)/Example Movie E2 (2003).mp4": ["FILE_IN_WRONG_FOLDER"],
    "Example Movie F.mp4": ["MISSING_YEAR", "FILE_IN_WRONG_FOLDER"],
    "Example Movie G (2003).mp4": ["FILE_IN_WRONG_FOLDER"],
}

SHOWS = {
    "Example Show A/Season 01/Example Show A S01E01.mp4": ["MISSING_YEAR"],
    "Example Show B (20)/Season 01/Example Show B (20) S01E01.mp4": ["MISSING_YEAR"],
    "Example Show C (2000)/Season 01/Example Show C (2000) S01E01.mp4": [],
    "Example Show D2 (2000)/Season 01/Example Show D (2000) S01E01.mp4": [
        "FILE_IN_WRONG_FOLDER"
    ],
    "Example Show E (2000)/Season 02/Example Show E (2000) S01E01.mp4": [
        "FILE_IN_WRONG_FOLDER"
    ],
    "Example Show F (2000)/Example Show F (2000) S01E01.mp4": ["FILE_IN_WRONG_FOLDER"],
    "Example Show G S01E01.mp4": ["MISSING_YEAR", "FILE_IN_WRONG_FOLDER"],
    "Example Show H (2000) S01E01.mp4": ["FILE_IN_WRONG_FOLDER"],
}

ALL_MEDIA = MOVIES | SHOWS  # Merge movies and shows


@pytest.fixture(scope="module")
def example_library(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_path = tmp_path_factory.mktemp("library")

    for name in ALL_MEDIA.keys():
        path = tmp_path / name

        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    return tmp_path


@pytest.fixture(autouse=True, scope="module")
def _load_default_rules():
    """Automatically load default rules for this test module."""
    load_default_rules()


@pytest.mark.parametrize("total_name,expected_codes", ALL_MEDIA.items())
def test_library_issues(example_library, total_name, expected_codes):
    """Test each movie against expected validation results."""
    reports = run_validation(example_library.rglob("*.mp4"))
    file_name = total_name.split("/")[-1]

    # Find report for file
    entry = next((report for report in reports if file_name in report["path"]), None)
    assert entry is not None, f"{file_name} missing in report"

    codes = [issue["code"] for issue in entry["issues"]]
    assert sorted(codes) == sorted(expected_codes)


# def test_debug_report(example_library):
#     """Show the report of the example library check and fail."""
#     import json

#     report = run_validation(example_library.rglob("*.mp4"))
#     print(json.dumps(report, indent=2))
#     print("Used rules:", registry.rules)
#     assert False, "Manual debug stop"
