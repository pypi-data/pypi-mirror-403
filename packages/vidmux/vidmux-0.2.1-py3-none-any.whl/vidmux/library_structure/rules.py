"""Define the rules used in the validation process."""

from vidmux.library_structure.core import (
    registry,
    IssueCode,
    ValidationFile,
    ValidationIssue,
    Severity,
)


@registry.register(default_severity=Severity.WARNING)
def check_file_in_correct_folder(file: ValidationFile, params) -> list[ValidationIssue]:
    """Check whether the file is in the correct subfolder."""
    issues = []

    current_parent_folder = file.path.parent.as_posix()
    wanted_parent_folder = file.canonical_name.directory

    if not (
        wanted_parent_folder in current_parent_folder
        and current_parent_folder.endswith(wanted_parent_folder)
    ):
        issues.append(
            ValidationIssue(
                path=file.path,
                code=IssueCode.FILE_IN_WRONG_FOLDER,
                message=(
                    f"File is located in '{current_parent_folder}', but should be in "
                    f"'.../{wanted_parent_folder}'"
                ),
                severity=Severity.WARNING,
            )
        )

    return issues


@registry.register(
    default_severity=Severity.ERROR,
    default_params={"bad_chars": r'<>:"/\\|?*'},
)
def check_for_bad_characters(file: ValidationFile, params) -> list[ValidationIssue]:
    """Check whether the filename contains illegal characters."""
    path = file.path

    bad_chars = set(params["bad_chars"])
    found = sorted({char for char in path.name if char in bad_chars})
    if not found:
        return []

    return [
        ValidationIssue(
            path=path,
            code=IssueCode.BAD_CHARACTER_IN_NAME,
            message=f"Filename contains illegal character(s): {' '.join(found)}",
            severity=Severity.ERROR,
        )
    ]


@registry.register(default_severity=Severity.WARNING)
def check_year_in_filename(file: ValidationFile, params) -> list[ValidationIssue]:
    """Check whether a year (YYYY) is given in the filename."""
    issues = []
    if not file.media.year:
        issues.append(
            ValidationIssue(
                path=file.path,
                code=IssueCode.MISSING_YEAR,
                message="Filename should include year in parentheses",
                severity=Severity.WARNING,
            )
        )

    return issues
