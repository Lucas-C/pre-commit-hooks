#!/usr/bin/env python

from __future__ import annotations
import argparse
import collections
import re
import sys

from fuzzywuzzy import fuzz

FUZZY_MATCH_TODO_COMMENT = (" TODO: This license is not consistent with"
                            " license used in the project.")
FUZZY_MATCH_TODO_INSTRUCTIONS = (
    "       Delete the inconsistent license and above line"
    " and rerun pre-commit to insert a good license." )
FUZZY_MATCH_EXTRA_LINES_TO_CHECK = 3

SKIP_LICENSE_INSERTION_COMMENT = "SKIP LICENSE INSERTION"

DEBUG_LEVENSHTEIN_DISTANCE_CALCULATION = False

LicenseInfo = collections.namedtuple('LicenseInfo', [
    'prefixed_license',
    'plain_license',
    'eol',
    'comment_start',
    'comment_prefix',
    'comment_end',
    'num_extra_lines'
])


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    parser.add_argument('--license-filepath', default='LICENSE.txt')
    parser.add_argument('--comment-style', default='#',
                        help='Can be a single prefix or a triplet: '
                             '<comment-start>|<comment-prefix>|<comment-end>'
                             'E.g.: /*| *| */')
    parser.add_argument('--no-space-in-comment-prefix', action='store_true',
                        help='Do not add extra space beyond the comment-style spec')
    parser.add_argument('--detect-license-in-X-top-lines', type=int, default=5)
    parser.add_argument('--fuzzy-match-generates-todo', action='store_true')
    parser.add_argument('--fuzzy-ratio-cut-off', type=int, default=85)
    parser.add_argument('--fuzzy-match-todo-comment', default=FUZZY_MATCH_TODO_COMMENT)
    parser.add_argument('--fuzzy-match-todo-instructions', default=FUZZY_MATCH_TODO_INSTRUCTIONS)
    parser.add_argument('--fuzzy-match-extra-lines-to-check', type=int,
                        default=FUZZY_MATCH_EXTRA_LINES_TO_CHECK)
    parser.add_argument('--skip-license-insertion-comment', default=SKIP_LICENSE_INSERTION_COMMENT)
    parser.add_argument('--insert-license-after-regex', default="",
                        help="Insert license after line matching regex (ex: '^<\\?php$')")
    parser.add_argument('--remove-header', action='store_true')
    args = parser.parse_args(argv)

    license_info = get_license_info(args)

    changed_files: list[str] = []
    todo_files: list[str] = []

    check_failed = process_files(args, changed_files, todo_files, license_info)

    if check_failed:
        print('')
        if changed_files:
            print(f'Some sources were modified by the hook {changed_files}')
        if todo_files:
            print(f'Some sources {todo_files} contain TODO about inconsistent licenses')
        print('Now aborting the commit.')
        print('You should check the changes made. Then simply "git add --update ." and re-commit')
        print('')
        return 1
    return 0


def get_license_info(args) -> LicenseInfo:
    comment_start, comment_end = None, None
    comment_prefix = args.comment_style.replace('\\t', '\t')
    extra_space = ' ' if not args.no_space_in_comment_prefix and comment_prefix != '' else ''
    if '|' in comment_prefix:
        comment_start, comment_prefix, comment_end = comment_prefix.split('|')
    with open(args.license_filepath, encoding='utf8') as license_file:
        plain_license = license_file.readlines()
    prefixed_license = [f'{comment_prefix}{extra_space if line.strip() else ""}{line}'
                        for line in plain_license]
    eol = '\r\n' if prefixed_license[0][-2:] == '\r\n' else '\n'

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
        eol=eol,
        comment_start=comment_start,
        comment_prefix=comment_prefix,
        comment_end=comment_end,
        num_extra_lines=num_extra_lines)
    return license_info


def process_files(args, changed_files, todo_files, license_info: LicenseInfo):
    """
    Processes all license files
    :param args: arguments of the hook
    :param changed_files: list of changed files
    :param todo_files: list of files where t.o.d.o. is detected
    :param license_info: license info named tuple
    :return: True if some files were changed or t.o.d.o is detected
    """
    after_regex = args.insert_license_after_regex
    for src_filepath in args.filenames:
        src_file_content, encoding = _read_file_content(src_filepath)
        if skip_license_insert_found(
                src_file_content=src_file_content,
                skip_license_insertion_comment=args.skip_license_insertion_comment,
                top_lines_count=args.detect_license_in_X_top_lines):
            continue
        if fail_license_todo_found(
                src_file_content=src_file_content,
                fuzzy_match_todo_comment=args.fuzzy_match_todo_comment,
                top_lines_count=args.detect_license_in_X_top_lines):
            todo_files.append(src_filepath)
            continue
        license_header_index = find_license_header_index(
            src_file_content=src_file_content,
            license_info=license_info,
            top_lines_count=args.detect_license_in_X_top_lines)
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
            if license_found(remove_header=args.remove_header,
                             license_header_index=license_header_index,
                             license_info=license_info,
                             src_file_content=src_file_content,
                             src_filepath=src_filepath,
                             encoding=encoding):
                changed_files.append(src_filepath)
        else:
            if fuzzy_match_header_index is not None:
                if fuzzy_license_found(license_info=license_info,
                                       fuzzy_match_header_index=fuzzy_match_header_index,
                                       fuzzy_match_todo_comment=args.fuzzy_match_todo_comment,
                                       fuzzy_match_todo_instructions=args.fuzzy_match_todo_instructions,
                                       src_file_content=src_file_content,
                                       src_filepath=src_filepath,
                                       encoding=encoding):
                    todo_files.append(src_filepath)
            else:
                if license_not_found(remove_header=args.remove_header,
                                     license_info=license_info,
                                     src_file_content=src_file_content,
                                     src_filepath=src_filepath,
                                     encoding=encoding,
                                     after_regex=after_regex):
                    changed_files.append(src_filepath)
    return changed_files or todo_files


def _read_file_content(src_filepath):
    last_error = None
    for encoding in ('utf8', 'ISO-8859-1'):  # we could use the chardet library to support more encodings
        try:
            with open(src_filepath, encoding=encoding) as src_file:
                return src_file.readlines(), encoding
        except UnicodeDecodeError as error:
            last_error = error
    print(f"Error while processing: {src_filepath} - file encoding is probably not supported")
    if last_error is not None:   # Avoid mypy message
        raise last_error
    raise RuntimeError("Unexpected branch taken (_read_file_content)")


def license_not_found(remove_header: bool, license_info: LicenseInfo, src_file_content: List[str], src_filepath: str, encoding: str, after_regex: str) -> bool:
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
                    break       # And insert after that line.
            elif stripped_line.startswith("#!") \
                    or stripped_line.startswith("# -*- coding") \
                    or stripped_line == "":
                index += 1
            else:
                break
        src_file_content = src_file_content[:index] + license_info.prefixed_license + \
            [license_info.eol] + src_file_content[index:]
        with open(src_filepath, 'w', encoding=encoding) as src_file:
            src_file.write(''.join(src_file_content))
        return True
    return False


def license_found(remove_header, license_header_index, license_info, src_file_content, src_filepath, encoding):  # pylint: disable=too-many-arguments
    """
    Executed when license is found. It does nothing if remove_header is False,
        removes the license if remove_header is True.
    :param remove_header: whether header should be removed if found
    :param license_header_index: index where license found
    :param license_info: license_info tuple
    :param src_file_content: content of the src_file
    :param src_filepath: path of the src_file
    :return: True if change was made, False otherwise
    """
    if remove_header:
        last_license_line_index = license_header_index + len(license_info.prefixed_license)
        if last_license_line_index < len(src_file_content) and src_file_content[last_license_line_index].strip():
            src_file_content = src_file_content[:license_header_index] + \
                               src_file_content[license_header_index + len(license_info.prefixed_license):]
        else:
            src_file_content = src_file_content[:license_header_index] + \
                               src_file_content[license_header_index +
                                                len(license_info.prefixed_license) + 1:]
        with open(src_filepath, 'w', encoding=encoding) as src_file:
            src_file.write(''.join(src_file_content))
        return True
    return False


def fuzzy_license_found(license_info,  # pylint: disable=too-many-arguments
                        fuzzy_match_header_index,
                        fuzzy_match_todo_comment,
                        fuzzy_match_todo_instructions,
                        src_file_content,
                        src_filepath,
                        encoding):
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
    src_file_content = \
        src_file_content[:fuzzy_match_header_index] + \
        [license_info.comment_prefix + fuzzy_match_todo_comment + license_info.eol] + \
        [license_info.comment_prefix + fuzzy_match_todo_instructions + license_info.eol] + \
        src_file_content[fuzzy_match_header_index:]
    with open(src_filepath, 'w', encoding=encoding) as src_file:
        src_file.write(''.join(src_file_content))
    return True


def find_license_header_index(src_file_content,
                              license_info,
                              top_lines_count):
    """
    Returns the line number, starting from 0 and lower than `top_lines_count`,
    where the license header comment starts in this file, or else None.
    """
    for i in range(top_lines_count):
        license_match = True
        for j, license_line in enumerate(license_info.prefixed_license):
            if i + j >= len(src_file_content) or license_line.strip() != src_file_content[i + j].strip():
                license_match = False
                break
        if license_match:
            return i
    return None


def skip_license_insert_found(
        src_file_content,
        skip_license_insertion_comment,
        top_lines_count):
    """
    Returns True if skip license insert comment is found in top X lines
    """
    for i in range(top_lines_count):
        if i < len(src_file_content) and skip_license_insertion_comment in src_file_content[i]:
            return True
    return False


def fail_license_todo_found(
        src_file_content,
        fuzzy_match_todo_comment,
        top_lines_count):
    """
    Returns True if "T.O.D.O" comment is found in top X lines
    """
    for i in range(top_lines_count):
        if i < len(src_file_content) and fuzzy_match_todo_comment in src_file_content[i]:
            return True
    return False


def fuzzy_find_license_header_index(src_file_content,  # pylint: disable=too-many-locals
                                    license_info,
                                    top_lines_count,
                                    fuzzy_match_extra_lines_to_check,
                                    fuzzy_ratio_cut_off):
    """
    Returns the line number, starting from 0 and lower than `top_lines_count`,
    where the fuzzy matching found best match with ratio higher than the cutoff ratio.
    """
    best_line_number_match = None
    best_ratio = 0
    best_num_token_diff = 0
    license_string = " ".join(license_info.plain_license).replace("\n", "").replace("\r", "").strip()
    expected_num_tokens = len(license_string.split(" "))
    for i in range(top_lines_count):
        candidate_array = \
            src_file_content[i:i + len(license_info.plain_license) + license_info.num_extra_lines +
                             fuzzy_match_extra_lines_to_check]
        license_string_candidate, candidate_offset = get_license_candidate_string(candidate_array,
                                                                                  license_info)
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
            if ratio > best_ratio or (ratio == best_ratio and num_tokens_diff < best_num_token_diff):
                best_ratio = ratio
                best_line_number_match = i + candidate_offset
                best_num_token_diff = num_tokens_diff
                if DEBUG_LEVENSHTEIN_DISTANCE_CALCULATION:  # pragma: no cover
                    print(f"Setting best line number match: {best_line_number_match}, ratio {best_ratio}, num tokens diff {best_num_token_diff}")
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
    stripped_comment_start = license_info.comment_start.strip() if license_info.comment_start else ""
    stripped_comment_prefix = license_info.comment_prefix.strip() if license_info.comment_prefix else ""
    stripped_comment_end = license_info.comment_end.strip() if license_info.comment_end else ""
    in_license = False
    current_offset = 0
    found_license_offset = 0
    for license_line in candidate_array:
        stripped_line = license_line.strip()
        if not in_license:
            if stripped_comment_start:
                if stripped_line.startswith(stripped_comment_start):
                    in_license = True
                    found_license_offset = current_offset + 1  # License starts in the next line
                    continue
            else:
                if stripped_comment_prefix:
                    if stripped_line.startswith(stripped_comment_prefix):
                        in_license = True
                        found_license_offset = current_offset  # License starts in this line
                else:
                    in_license = True
                    found_license_offset = current_offset  # We have no data :(. We start license immediately
        else:
            if stripped_comment_end and stripped_line.startswith(stripped_comment_end):
                break
        if in_license and (not stripped_comment_prefix or
                           stripped_line.startswith(stripped_comment_prefix)):
            license_string_candidate += stripped_line[len(stripped_comment_prefix):] + " "
        current_offset += 1
    return license_string_candidate.strip(), found_license_offset


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
