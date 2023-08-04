from __future__ import annotations
import argparse
import collections
import re
import sys
from datetime import datetime
from typing import Any, Sequence

from rapidfuzz import fuzz

FUZZY_MATCH_TODO_COMMENT = (
    " TODO: This license is not consistent with the license used in the project."
)
FUZZY_MATCH_TODO_INSTRUCTIONS = (
    "       Delete the inconsistent license and above line"
    " and rerun pre-commit to insert a good license."
)
FUZZY_MATCH_EXTRA_LINES_TO_CHECK = 3

SKIP_LICENSE_INSERTION_COMMENT = "SKIP LICENSE INSERTION"

DEBUG_LEVENSHTEIN_DISTANCE_CALCULATION = False

LicenseInfo = collections.namedtuple(
    "LicenseInfo",
    [
        "prefixed_license",
        "plain_license",
        "eol",
        "comment_start",
        "comment_prefix",
        "comment_end",
        "num_extra_lines",
    ],
)


class LicenseUpdateError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="filenames to check")
    parser.add_argument("--license-filepath", default="LICENSE.txt")
    parser.add_argument(
        "--comment-style",
        default="#",
        help="Can be a single prefix or a triplet: "
        "<comment-start>|<comment-prefix>|<comment-end>"
        "E.g.: /*| *| */",
    )
    parser.add_argument(
        "--no-space-in-comment-prefix",
        action="store_true",
        help="Do not add extra space beyond the comment-style spec",
    )
    parser.add_argument(
        "--no-extra-eol",
        action="store_true",
        help="Do not add extra End of Line after license comment",
    )
    parser.add_argument("--detect-license-in-X-top-lines", type=int, default=5)
    parser.add_argument("--fuzzy-match-generates-todo", action="store_true")
    parser.add_argument("--fuzzy-ratio-cut-off", type=int, default=85)
    parser.add_argument("--fuzzy-match-todo-comment", default=FUZZY_MATCH_TODO_COMMENT)
    parser.add_argument(
        "--fuzzy-match-todo-instructions", default=FUZZY_MATCH_TODO_INSTRUCTIONS
    )
    parser.add_argument(
        "--fuzzy-match-extra-lines-to-check",
        type=int,
        default=FUZZY_MATCH_EXTRA_LINES_TO_CHECK,
    )
    parser.add_argument(
        "--skip-license-insertion-comment", default=SKIP_LICENSE_INSERTION_COMMENT
    )
    parser.add_argument(
        "--insert-license-after-regex",
        default="",
        help="Insert license after line matching regex (ex: '^<\\?php$')",
    )
    parser.add_argument("--remove-header", action="store_true")
    parser.add_argument(
        "--use-current-year",
        action="store_true",
        help=(
            "Use the current year in inserted and updated licenses, implies --allow-past-years"
        ),
    )
    parser.add_argument(
        "--allow-past-years",
        action="store_true",
        help=(
            "Allow past years in headers. License comments are not updated if they contain past years."
        ),
    )
    args = parser.parse_args(argv)
    if args.use_current_year:
        args.allow_past_years = True

    license_info = get_license_info(args)

    changed_files: list[str] = []
    todo_files: list[str] = []

    check_failed = process_files(args, changed_files, todo_files, license_info)

    if check_failed:
        print("")
        if changed_files:
            print(f"Some sources were modified by the hook {changed_files}")
        if todo_files:
            print(
                f"Some sources contain TODO about inconsistent licenses: {todo_files}"
            )
        print("Now aborting the commit.")
        print(
            'You should check the changes made. Then simply "git add --update ." and re-commit'
        )
        print("")
        return 1
    return 0


def _replace_year_in_license_with_current(plain_license: list[str], filepath: str):
    current_year = datetime.now().year
    for i, line in enumerate(plain_license):
        updated = try_update_year(line, filepath, current_year, introduce_range=False)
        if updated:
            plain_license[i] = updated
            break
    return plain_license


def get_license_info(args) -> LicenseInfo:
    comment_start, comment_end = None, None
    comment_prefix = args.comment_style.replace("\\t", "\t")
    extra_space = (
        " " if not args.no_space_in_comment_prefix and comment_prefix != "" else ""
    )
    if "|" in comment_prefix:
        comment_start, comment_prefix, comment_end = comment_prefix.split("|")
    with open(args.license_filepath, encoding="utf8") as license_file:
        plain_license = license_file.readlines()

    if args.use_current_year:
        plain_license = _replace_year_in_license_with_current(
            plain_license, args.license_filepath
        )

    prefixed_license = [
        f'{comment_prefix}{extra_space if line.strip() else ""}{line}'
        for line in plain_license
    ]
    eol = "\r\n" if prefixed_license[0][-2:] == "\r\n" else "\n"
    num_extra_lines = 0

    if not prefixed_license[-1].endswith(eol):
        prefixed_license[-1] += eol
        num_extra_lines += 1
    if comment_start:
        prefixed_license = [comment_start + eol] + prefixed_license
        num_extra_lines += 1
    if comment_end:
        prefixed_license = prefixed_license + [comment_end + eol]
        num_extra_lines += 1

    license_info = LicenseInfo(
        prefixed_license=prefixed_license,
        plain_license=plain_license,
        eol="" if args.no_extra_eol else eol,
        comment_start=comment_start,
        comment_prefix=comment_prefix,
        comment_end=comment_end,
        num_extra_lines=num_extra_lines,
    )
    return license_info


def process_files(args, changed_files, todo_files, license_info: LicenseInfo):
    """
    Processes all license files
    :param args: arguments of the hook
    :param changed_files: list of changed files
    :param todo_files: list of files where t.o.d.o. is detected
    :param license_info: license info named tuple
    :return: True if some files were changed, t.o.d.o is detected or an error occurred while updating the year
    """
    license_update_failed = False
    after_regex = args.insert_license_after_regex
    for src_filepath in args.filenames:
        src_file_content, encoding = _read_file_content(src_filepath)
        if skip_license_insert_found(
            src_file_content=src_file_content,
            skip_license_insertion_comment=args.skip_license_insertion_comment,
            top_lines_count=args.detect_license_in_X_top_lines,
        ):
            continue
        if fail_license_todo_found(
            src_file_content=src_file_content,
            fuzzy_match_todo_comment=args.fuzzy_match_todo_comment,
            top_lines_count=args.detect_license_in_X_top_lines,
        ):
            todo_files.append(src_filepath)
            continue
        license_header_index = find_license_header_index(
            src_file_content=src_file_content,
            license_info=license_info,
            top_lines_count=args.detect_license_in_X_top_lines,
            match_years_strictly=not args.allow_past_years,
        )
        fuzzy_match_header_index = None
        if args.fuzzy_match_generates_todo and license_header_index is None:
            fuzzy_match_header_index = fuzzy_find_license_header_index(
                src_file_content=src_file_content,
                license_info=license_info,
                top_lines_count=args.detect_license_in_X_top_lines,
                fuzzy_match_extra_lines_to_check=args.fuzzy_match_extra_lines_to_check,
                fuzzy_ratio_cut_off=args.fuzzy_ratio_cut_off,
            )
        if license_header_index is not None:
            try:
                if license_found(
                    remove_header=args.remove_header,
                    update_year_range=args.use_current_year,
                    license_header_index=license_header_index,
                    license_info=license_info,
                    src_file_content=src_file_content,
                    src_filepath=src_filepath,
                    encoding=encoding,
                ):
                    changed_files.append(src_filepath)
            except LicenseUpdateError as error:
                print(error)
                license_update_failed = True
        else:
            if fuzzy_match_header_index is not None:
                if fuzzy_license_found(
                    license_info=license_info,
                    fuzzy_match_header_index=fuzzy_match_header_index,
                    fuzzy_match_todo_comment=args.fuzzy_match_todo_comment,
                    fuzzy_match_todo_instructions=args.fuzzy_match_todo_instructions,
                    src_file_content=src_file_content,
                    src_filepath=src_filepath,
                    encoding=encoding,
                ):
                    todo_files.append(src_filepath)
            else:
                if license_not_found(
                    remove_header=args.remove_header,
                    license_info=license_info,
                    src_file_content=src_file_content,
                    src_filepath=src_filepath,
                    encoding=encoding,
                    after_regex=after_regex,
                ):
                    changed_files.append(src_filepath)
    return changed_files or todo_files or license_update_failed


def _read_file_content(src_filepath):
    last_error = None
    for encoding in (
        "utf8",
        "ISO-8859-1",
    ):  # we could use the chardet library to support more encodings
        try:
            with open(src_filepath, encoding=encoding) as src_file:
                return src_file.readlines(), encoding
        except UnicodeDecodeError as error:
            last_error = error
    print(
        f"Error while processing: {src_filepath} - file encoding is probably not supported"
    )
    if last_error is not None:  # Avoid mypy message
        raise last_error
    raise RuntimeError("Unexpected branch taken (_read_file_content)")


def license_not_found(  # pylint: disable=too-many-arguments
    remove_header: bool,
    license_info: LicenseInfo,
    src_file_content: list[str],
    src_filepath: str,
    encoding: str,
    after_regex: str,
) -> bool:
    """
    Executed when license is not found.
    It either adds license if remove_header is False,
        does nothing if remove_header is True.
    :param remove_header: whether header should be removed if found
    :param license_info: license info named tuple
    :param src_file_content: content of the src_file
    :param src_filepath: path of the src_file
    :return: True if change was made, False otherwise
    """
    if not remove_header:
        index = 0
        for line in src_file_content:
            stripped_line = line.strip()
            # Special treatment for user provided regex,
            # or shebang, file encoding directive,
            # and empty lines when at the beginning of the file.
            # (adds license only after those)
            if after_regex is not None and after_regex != "":
                if re.match(after_regex, stripped_line):
                    index += 1  # Skip matched line
                    break  # And insert after that line.
            elif (
                stripped_line.startswith("#!")
                or stripped_line.startswith("# -*- coding")
                or stripped_line == ""
            ):
                index += 1
            else:
                break
        src_file_content = (
            src_file_content[:index]
            + license_info.prefixed_license
            + [license_info.eol]
            + src_file_content[index:]
        )
        with open(src_filepath, "w", encoding=encoding) as src_file:
            src_file.write("".join(src_file_content))
        return True
    return False


# a year, then optionally a dash (with optional spaces before and after), and another year, surrounded by word boundaries
_YEAR_RANGE_PATTERN = re.compile(r"\b\d{4}(?: *- *\d{2,4})?\b")


def try_update_year(
    line: str, filepath: str, current_year: int, introduce_range: bool
) -> str | None:
    """
    Update the last match in self.line.
    :param line: the line to update
    :param filepath: the file the line is from
    :param introduce_range:
        Decides what to do when a single year is found and not a range of years.
        If True, create a range ending in the current year. If False, just replace the year.
        If a range is already present, it will be updated regardless of this parameter.
    :return: The updated line if there was an update. None otherwise.
    """
    matches = _YEAR_RANGE_PATTERN.findall(line)
    if matches:
        match = matches[-1]
        start_year = int(match[:4])
        end_year = match[5:].lstrip(" -,")
        if end_year and int(end_year) < current_year:  # range detected
            return _try_update_year_range_in_matched_line(
                line, match, start_year, current_year, filepath
            )
        if not end_year and start_year < current_year:
            if introduce_range:
                return _try_update_year_range_in_matched_line(
                    line, match, start_year, current_year, filepath
                )
            return line.replace(match, str(current_year))
    return None


def _try_update_year_range_in_matched_line(
    line: str, match: Any, start_year: int, current_year: int, filepath: str
):
    """match: a match object for the _YEAR_RANGE_PATTERN regex"""
    updated = line.replace(match, str(start_year) + "-" + str(current_year))
    # verify the current list of years ends in the current one
    if _YEARS_PATTERN.findall(updated)[-1][-4:] != str(current_year):
        raise LicenseUpdateError(
            f"Year range detected in license header, but we were unable to update it.\n"
            f"File: {filepath}\nInput line: {line.rstrip()}\nDiscarded result: {updated.rstrip()}"
        )
    return updated


def try_update_year_range(
    src_file_content: list[str],
    src_filepath: str,
    license_header_index: int,
    license_length: int,
) -> tuple[Sequence[str], bool]:
    """
    Updates the years in a copyright header in src_file_content by
        ensuring it contains a range ending in the current year.
    Does nothing if the current year is already present as the end of
        the range.
    The change will affect only the first line containing years.
    :param src_file_content: the lines in the source file
    :param license_header_index: line where the license starts
    :return: source file contents and a flag indicating update
    """
    current_year = datetime.now().year
    for i in range(license_header_index, license_header_index + license_length):
        updated = try_update_year(
            src_file_content[i], src_filepath, current_year, introduce_range=True
        )
        if updated:
            src_file_content[i] = updated
            return src_file_content, True
    return src_file_content, False


def license_found(
    remove_header,
    update_year_range,
    license_header_index,
    license_info,
    src_file_content,
    src_filepath,
    encoding,
):  # pylint: disable=too-many-arguments
    """
    Executed when license is found. It does nothing if remove_header is False,
        removes the license if remove_header is True.
    :param remove_header: whether header should be removed if found
    :param update_year_range: whether to update license with the current year
    :param license_header_index: index where license found
    :param license_info: license_info tuple
    :param src_file_content: content of the src_file
    :param src_filepath: path of the src_file
    :return: True if change was made, False otherwise
    """
    updated = False
    if remove_header:
        last_license_line_index = license_header_index + len(
            license_info.prefixed_license
        )
        if (
            last_license_line_index < len(src_file_content)
            and src_file_content[last_license_line_index].strip()
        ):
            src_file_content = (
                src_file_content[:license_header_index]
                + src_file_content[
                    license_header_index + len(license_info.prefixed_license) :
                ]
            )
        else:
            src_file_content = (
                src_file_content[:license_header_index]
                + src_file_content[
                    license_header_index + len(license_info.prefixed_license) + 1 :
                ]
            )
        updated = True
    elif update_year_range:
        src_file_content, updated = try_update_year_range(
            src_file_content,
            src_filepath,
            license_header_index,
            len(license_info.prefixed_license),
        )

    if updated:
        with open(src_filepath, "w", encoding=encoding) as src_file:
            src_file.write("".join(src_file_content))

    return updated


def fuzzy_license_found(
    license_info,  # pylint: disable=too-many-arguments
    fuzzy_match_header_index,
    fuzzy_match_todo_comment,
    fuzzy_match_todo_instructions,
    src_file_content,
    src_filepath,
    encoding,
):
    """
    Executed when fuzzy license is found. It inserts comment indicating that the license should be
        corrected.
    :param license_info: license info tuple
    :param fuzzy_match_header_index: index where
    :param fuzzy_match_todo_comment: comment to add when fuzzy match found
    :param fuzzy_match_todo_instructions: instructions for fuzzy_match removal
    :param src_file_content: content of the src_file
    :param src_filepath: path of the src_file
    :return: True if change was made, False otherwise
    """
    src_file_content = (
        src_file_content[:fuzzy_match_header_index]
        + [license_info.comment_prefix + fuzzy_match_todo_comment + license_info.eol]
        + [
            license_info.comment_prefix
            + fuzzy_match_todo_instructions
            + license_info.eol
        ]
        + src_file_content[fuzzy_match_header_index:]
    )
    with open(src_filepath, "w", encoding=encoding) as src_file:
        src_file.write("".join(src_file_content))
    return True


# More flexible than _YEAR_RANGE_PATTERN. For detecting all years in a line, not just a range.
_YEARS_PATTERN = re.compile(r"\b\d{4}([ ,-]+\d{2,4})*\b")


def _strip_years(line):
    return _YEARS_PATTERN.sub("", line)


def _license_line_matches(license_line, src_file_line, match_years_strictly):
    license_line = license_line.strip()
    src_file_line = src_file_line.strip()

    if match_years_strictly:
        return license_line == src_file_line

    return _strip_years(license_line) == _strip_years(src_file_line)


def find_license_header_index(
    src_file_content, license_info: LicenseInfo, top_lines_count, match_years_strictly
):
    """
    Returns the line number, starting from 0 and lower than `top_lines_count`,
    where the license header comment starts in this file, or else None.
    """
    for i in range(top_lines_count):
        license_match = True
        for j, license_line in enumerate(license_info.prefixed_license):
            if i + j >= len(src_file_content) or not _license_line_matches(
                license_line, src_file_content[i + j], match_years_strictly
            ):
                license_match = False
                break
        if license_match:
            return i
    return None


def skip_license_insert_found(
    src_file_content, skip_license_insertion_comment, top_lines_count
):
    """
    Returns True if skip license insert comment is found in top X lines
    """
    for i in range(top_lines_count):
        if (
            i < len(src_file_content)
            and skip_license_insertion_comment in src_file_content[i]
        ):
            return True
    return False


def fail_license_todo_found(
    src_file_content, fuzzy_match_todo_comment, top_lines_count
):
    """
    Returns True if "T.O.D.O" comment is found in top X lines
    """
    for i in range(top_lines_count):
        if (
            i < len(src_file_content)
            and fuzzy_match_todo_comment in src_file_content[i]
        ):
            return True
    return False


def fuzzy_find_license_header_index(
    src_file_content,  # pylint: disable=too-many-locals
    license_info,
    top_lines_count,
    fuzzy_match_extra_lines_to_check,
    fuzzy_ratio_cut_off,
):
    """
    Returns the line number, starting from 0 and lower than `top_lines_count`,
    where the fuzzy matching found best match with ratio higher than the cutoff ratio.
    """
    best_line_number_match = None
    best_ratio = 0
    best_num_token_diff = 0
    license_string = (
        " ".join(license_info.plain_license).replace("\n", "").replace("\r", "").strip()
    )
    expected_num_tokens = len(license_string.split(" "))
    for i in range(top_lines_count):
        candidate_array = src_file_content[
            i : i
            + len(license_info.plain_license)
            + license_info.num_extra_lines
            + fuzzy_match_extra_lines_to_check
        ]
        license_string_candidate, candidate_offset = get_license_candidate_string(
            candidate_array, license_info
        )
        ratio = fuzz.token_set_ratio(license_string, license_string_candidate)
        num_tokens = len(license_string_candidate.split(" "))
        num_tokens_diff = abs(num_tokens - expected_num_tokens)
        if DEBUG_LEVENSHTEIN_DISTANCE_CALCULATION:  # pragma: no cover
            print(f"License_string: {license_string}")
            print(f"License_string_candidate: {license_string_candidate}")
            print(f"Candidate offset: {candidate_offset}")
            print(f"Ratio: {ratio}")
            print(f"Number of tokens: {num_tokens}")
            print(f"Expected number of tokens: {expected_num_tokens}")
            print(f"Num tokens diff: {num_tokens_diff}")
        if ratio >= fuzzy_ratio_cut_off:
            if ratio > best_ratio or (
                ratio == best_ratio and num_tokens_diff < best_num_token_diff
            ):
                best_ratio = ratio
                best_line_number_match = i + candidate_offset
                best_num_token_diff = num_tokens_diff
                if DEBUG_LEVENSHTEIN_DISTANCE_CALCULATION:  # pragma: no cover
                    print(
                        f"Setting best line number match: {best_line_number_match}, ratio {best_ratio}, num tokens diff {best_num_token_diff}"
                    )
        if DEBUG_LEVENSHTEIN_DISTANCE_CALCULATION:  # pragma: no cover
            print(f"Best offset match {best_line_number_match}")
    return best_line_number_match


def get_license_candidate_string(candidate_array, license_info):
    """
    Return license candidate string from the array of strings retrieved
    :param candidate_array: array of lines of the candidate strings
    :param license_info: LicenseInfo named tuple containing information about the license
    :return: Tuple of string version of the license candidate and offset in lines where it starts.
    """
    license_string_candidate = ""
    stripped_comment_start = (
        license_info.comment_start.strip() if license_info.comment_start else ""
    )
    stripped_comment_prefix = (
        license_info.comment_prefix.strip() if license_info.comment_prefix else ""
    )
    stripped_comment_end = (
        license_info.comment_end.strip() if license_info.comment_end else ""
    )
    in_license = False
    current_offset = 0
    found_license_offset = 0
    for license_line in candidate_array:
        stripped_line = license_line.strip()
        if not in_license:
            if stripped_comment_start:
                if stripped_line.startswith(stripped_comment_start):
                    in_license = True
                    found_license_offset = (
                        current_offset + 1
                    )  # License starts in the next line
                    continue
            else:
                if stripped_comment_prefix:
                    if stripped_line.startswith(stripped_comment_prefix):
                        in_license = True
                        found_license_offset = (
                            current_offset  # License starts in this line
                        )
                else:
                    in_license = True
                    found_license_offset = current_offset  # We have no data :(. We start license immediately
        else:
            if stripped_comment_end and stripped_line.startswith(stripped_comment_end):
                break
        if in_license and (
            not stripped_comment_prefix
            or stripped_line.startswith(stripped_comment_prefix)
        ):
            license_string_candidate += (
                stripped_line[len(stripped_comment_prefix) :] + " "
            )
        current_offset += 1
    return license_string_candidate.strip(), found_license_offset


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
