from datetime import datetime
from itertools import chain, product
import shutil
import pytest

from pre_commit_hooks.insert_license import main as insert_license, LicenseInfo
from pre_commit_hooks.insert_license import find_license_header_index

from .utils import chdir_to_test_resources, capture_stdout


# pylint: disable=too-many-arguments


def _convert_line_ending(file_path, new_line_endings):
    for encoding in (
        "utf8",
        "ISO-8859-1",
    ):  # we could use the chardet library to support more encodings
        last_error = None
        try:
            with open(file_path, encoding=encoding, newline="") as f_in:
                content = f_in.read()

            with open(
                file_path, "w", encoding=encoding, newline=new_line_endings
            ) as f_out:
                f_out.write(content)

            return
        except UnicodeDecodeError as error:
            last_error = error
    print(
        f"Error while processing: {file_path} - file encoding is probably not supported"
    )
    if last_error is not None:  # Avoid mypy message
        raise last_error
    raise RuntimeError("Unexpected branch taken (_convert_line_ending)")


@pytest.mark.parametrize(
    (
        "license_file_path",
        "line_ending",
        "src_file_path",
        "comment_prefix",
        "new_src_file_expected",
        "message_expected",
        "fail_check",
        "extra_args",
    ),
    map(
        lambda a: a[:2] + a[2],
        chain(
            product(  # combine license files with other args
                (
                    "LICENSE_with_trailing_newline.txt",
                    "LICENSE_without_trailing_newline.txt",
                ),
                ("\n", "\r\n"),
                (
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license.py",
                        "",
                        True,
                        None,
                    ),
                    ("module_without_license_skip.py", "#", None, "", False, None),
                    ("module_with_license.py", "#", None, "", False, None),
                    ("module_with_license_todo.py", "#", None, "", True, None),
                    (
                        "module_without_license.jinja",
                        "{#||#}",
                        "module_with_license.jinja",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license_skip.jinja",
                        "{#||#}",
                        None,
                        "",
                        False,
                        None,
                    ),
                    ("module_with_license.jinja", "{#||#}", None, "", False, None),
                    ("module_with_license_todo.jinja", "{#||#}", None, "", True, None),
                    (
                        "module_without_license_and_shebang.py",
                        "#",
                        "module_with_license_and_shebang.py",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license_and_shebang_skip.py",
                        "#",
                        None,
                        "",
                        False,
                        None,
                    ),
                    ("module_with_license_and_shebang.py", "#", None, "", False, None),
                    (
                        "module_with_license_and_shebang_todo.py",
                        "#",
                        None,
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license.groovy",
                        "//",
                        "module_with_license.groovy",
                        "",
                        True,
                        None,
                    ),
                    ("module_without_license_skip.groovy", "//", None, "", False, None),
                    ("module_with_license.groovy", "//", None, "", False, None),
                    ("module_with_license_todo.groovy", "//", None, "", True, None),
                    (
                        "module_without_license.css",
                        "/*| *| */",
                        "module_with_license.css",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license_and_few_words.css",
                        "/*| *| */",
                        "module_with_license_and_few_words.css",
                        "",
                        True,
                        None,
                    ),  # Test fuzzy match does not match greedily
                    (
                        "module_without_license_skip.css",
                        "/*| *| */",
                        None,
                        "",
                        False,
                        None,
                    ),
                    ("module_with_license.css", "/*| *| */", None, "", False, None),
                    ("module_with_license_todo.css", "/*| *| */", None, "", True, None),
                    (
                        "main_without_license.cpp",
                        "/*|\t| */",
                        "main_with_license.cpp",
                        "",
                        True,
                        None,
                    ),
                    (
                        "main_iso8859_without_license.cpp",
                        "/*|\t| */",
                        "main_iso8859_with_license.cpp",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license.txt",
                        "",
                        "module_with_license_noprefix.txt",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license_nospace.py",
                        "",
                        True,
                        ["--no-space-in-comment-prefix"],
                    ),
                    (
                        "module_without_license.php",
                        "/*| *| */",
                        "module_with_license.php",
                        "",
                        True,
                        ["--insert-license-after-regex", "^<\\?php$"],
                    ),
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license.py",
                        "",
                        True,
                        # Test that when the regex is not found, the license is put at the first line
                        ["--insert-license-after-regex", "^<\\?php$"],
                    ),
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license_noeol.py",
                        "",
                        True,
                        ["--no-extra-eol"],
                    ),
                    (
                        "module_without_license.groovy",
                        "//",
                        "module_with_license.groovy",
                        "",
                        True,
                        ["--use-current-year"],
                    ),
                    (
                        "module_with_stale_year_in_license.py",
                        "#",
                        "module_with_year_range_in_license.py",
                        "",
                        True,
                        ["--use-current-year"],
                    ),
                    (
                        "module_with_stale_year_range_in_license.py",
                        "#",
                        "module_with_year_range_in_license.py",
                        "",
                        True,
                        ["--use-current-year"],
                    ),
                    (
                        "module_with_stale_year_range_in_license.py",
                        "#",
                        "module_with_stale_year_range_in_license.py",
                        "",
                        False,
                        ["--allow-past-years"],
                    ),
                    (
                        "module_with_badly_formatted_stale_year_range_in_license.py",
                        "#",
                        "module_with_badly_formatted_stale_year_range_in_license.py",
                        "module_with_badly_formatted_stale_year_range_in_license.py",
                        True,
                        ["--use-current-year"],
                    ),
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license.py",
                        "",
                        True,
                        None,
                    ),
                    ("module_without_license_skip.py", "#", None, "", False, None),
                    ("module_with_license.py", "#", None, "", False, None),
                    ("module_with_license_todo.py", "#", None, "", True, None),
                    (
                        "module_without_license.jinja",
                        "{#||#}",
                        "module_with_license.jinja",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license_skip.jinja",
                        "{#||#}",
                        None,
                        "",
                        False,
                        None,
                    ),
                    ("module_with_license.jinja", "{#||#}", None, "", False, None),
                    ("module_with_license_todo.jinja", "{#||#}", None, "", True, None),
                    (
                        "module_without_license_and_shebang.py",
                        "#",
                        "module_with_license_and_shebang.py",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license_and_shebang_skip.py",
                        "#",
                        None,
                        "",
                        False,
                        None,
                    ),
                    ("module_with_license_and_shebang.py", "#", None, "", False, None),
                    (
                        "module_with_license_and_shebang_todo.py",
                        "#",
                        None,
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license.groovy",
                        "//",
                        "module_with_license.groovy",
                        "",
                        True,
                        None,
                    ),
                    ("module_without_license_skip.groovy", "//", None, "", False, None),
                    ("module_with_license.groovy", "//", None, "", False, None),
                    ("module_with_license_todo.groovy", "//", None, "", True, None),
                    (
                        "module_without_license.css",
                        "/*| *| */",
                        "module_with_license.css",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license_and_few_words.css",
                        "/*| *| */",
                        "module_with_license_and_few_words.css",
                        "",
                        True,
                        None,
                    ),  # Test fuzzy match does not match greedily
                    (
                        "module_without_license_skip.css",
                        "/*| *| */",
                        None,
                        "",
                        False,
                        None,
                    ),
                    ("module_with_license.css", "/*| *| */", None, "", False, None),
                    ("module_with_license_todo.css", "/*| *| */", None, "", True, None),
                    (
                        "main_without_license.cpp",
                        "/*|\t| */",
                        "main_with_license.cpp",
                        "",
                        True,
                        None,
                    ),
                    (
                        "main_iso8859_without_license.cpp",
                        "/*|\t| */",
                        "main_iso8859_with_license.cpp",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license.txt",
                        "",
                        "module_with_license_noprefix.txt",
                        "",
                        True,
                        None,
                    ),
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license_nospace.py",
                        "",
                        True,
                        ["--no-space-in-comment-prefix"],
                    ),
                    (
                        "module_without_license.php",
                        "/*| *| */",
                        "module_with_license.php",
                        "",
                        True,
                        ["--insert-license-after-regex", "^<\\?php$"],
                    ),
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license_noeol.py",
                        "",
                        True,
                        ["--no-extra-eol"],
                    ),
                    (
                        "module_without_license.groovy",
                        "//",
                        "module_with_license.groovy",
                        "",
                        True,
                        ["--use-current-year"],
                    ),
                    (
                        "module_with_stale_year_in_license.py",
                        "#",
                        "module_with_year_range_in_license.py",
                        "",
                        True,
                        ["--use-current-year"],
                    ),
                    (
                        "module_with_stale_year_range_in_license.py",
                        "#",
                        "module_with_year_range_in_license.py",
                        "",
                        True,
                        ["--use-current-year"],
                    ),
                    (
                        "module_with_badly_formatted_stale_year_range_in_license.py",
                        "#",
                        "module_with_badly_formatted_stale_year_range_in_license.py",
                        "module_with_badly_formatted_stale_year_range_in_license.py",
                        True,
                        ["--use-current-year"],
                    ),
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license.py",
                        "",
                        True,
                        [
                            "--license-filepath",
                            "LICENSE_2_without_trailing_newline.txt",
                        ],
                    ),
                    (
                        "module_with_license_2.py",
                        "#",
                        None,
                        "",
                        False,
                        [
                            "--license-filepath",
                            "LICENSE_2_without_trailing_newline.txt",
                        ],
                    ),
                    (
                        "module_with_license.py",
                        "#",
                        None,
                        "",
                        False,
                        [
                            "--license-filepath",
                            "LICENSE_2_without_trailing_newline.txt",
                        ],
                    ),
                    (
                        "module_with_license_todo.py",
                        "#",
                        None,
                        "",
                        True,
                        [
                            "--license-filepath",
                            "LICENSE_2_without_trailing_newline.txt",
                        ],
                    ),
                ),
            ),
            product(
                ("LICENSE_with_year_range_and_trailing_newline.txt",),
                ("\n", "\r\n"),
                (
                    (
                        "module_without_license.groovy",
                        "//",
                        "module_with_year_range_license.groovy",
                        "",
                        True,
                        ["--use-current-year"],
                    ),
                ),
            ),
            product(
                ("LICENSE_with_multiple_year_ranges.txt",),
                ("\n",),
                (
                    (
                        "module_with_multiple_stale_years_in_license.py",
                        "#",
                        "module_with_multiple_years_in_license.py",
                        "",
                        True,
                        ["--use-current-year"],
                    ),
                ),
            ),
        ),
    ),
)
def test_insert_license(
    license_file_path,
    line_ending,
    src_file_path,
    comment_prefix,
    new_src_file_expected,
    message_expected,
    fail_check,
    extra_args,
    tmpdir,
):
    encoding = "ISO-8859-1" if "iso8859" in src_file_path else "utf-8"
    with chdir_to_test_resources():
        path = tmpdir.join(src_file_path)
        shutil.copy(src_file_path, path.strpath)
        _convert_line_ending(path.strpath, line_ending)
        args = [
            "--license-filepath",
            license_file_path,
            "--comment-style",
            comment_prefix,
            path.strpath,
        ]
        if extra_args is not None:
            args.extend(extra_args)

        with capture_stdout() as stdout:
            assert insert_license(args) == (1 if fail_check else 0)
            assert message_expected in stdout.getvalue()

        if new_src_file_expected:
            with open(
                new_src_file_expected, encoding=encoding, newline=line_ending
            ) as expected_content_file:
                expected_content = expected_content_file.read()
                if "--use-current-year" in args:
                    expected_content = expected_content.replace(
                        "2017", str(datetime.now().year)
                    )
            new_file_content = path.open(encoding=encoding).read()
            assert new_file_content == expected_content


@pytest.mark.parametrize(
    ("license_file_path", "src_file_path", "comment_prefix"),
    map(
        lambda a: a[:1] + a[1],
        product(  # combine license files with other args
            (
                "LICENSE_with_trailing_newline.txt",
                "LICENSE_without_trailing_newline.txt",
                "LICENSE_with_year_range_and_trailing_newline.txt",
            ),
            (
                ("module_with_license.groovy", "//"),
                ("module_with_license_and_numbers.py", "#"),
                ("module_with_year_range_in_license.py", "#"),
                ("module_with_spaced_year_range_in_license.py", "#"),
            ),
        ),
    ),
)
def test_insert_license_current_year_already_there(
    license_file_path, src_file_path, comment_prefix, tmpdir
):
    with chdir_to_test_resources():
        with open(src_file_path, encoding="utf-8") as src_file:
            input_contents = src_file.read().replace("2017", str(datetime.now().year))
        path = tmpdir.join("src_file_path")
        with open(path.strpath, "w", encoding="utf-8") as input_file:
            input_file.write(input_contents)

        args = [
            "--license-filepath",
            license_file_path,
            "--comment-style",
            comment_prefix,
            "--use-current-year",
            path.strpath,
        ]
        assert insert_license(args) == 0
        # ensure file was not modified
        with open(path.strpath, encoding="utf-8") as output_file:
            output_contents = output_file.read()
            assert output_contents == input_contents


@pytest.mark.parametrize(
    (
        "license_file_path",
        "line_ending",
        "src_file_path",
        "comment_style",
        "new_src_file_expected",
        "fail_check",
        "extra_args",
    ),
    map(
        lambda a: a[:2] + a[2] + a[3],
        chain(
            product(  # combine license files with other args
                (
                    "LICENSE_with_trailing_newline.txt",
                    "LICENSE_without_trailing_newline.txt",
                ),
                ("\n", "\r\n"),
                (
                    (
                        "module_without_license.jinja",
                        "{#||#}",
                        "module_with_license.jinja",
                        True,
                    ),
                    ("module_with_license.jinja", "{#||#}", None, False),
                    (
                        "module_with_fuzzy_matched_license.jinja",
                        "{#||#}",
                        "module_with_license_todo.jinja",
                        True,
                    ),
                    ("module_with_license_todo.jinja", "{#||#}", None, True),
                    ("module_without_license.py", "#", "module_with_license.py", True),
                    ("module_with_license.py", "#", None, False),
                    (
                        "module_with_fuzzy_matched_license.py",
                        "#",
                        "module_with_license_todo.py",
                        True,
                    ),
                    ("module_with_license_todo.py", "#", None, True),
                    ("module_with_license_and_shebang.py", "#", None, False),
                    (
                        "module_with_fuzzy_matched_license_and_shebang.py",
                        "#",
                        "module_with_license_and_shebang_todo.py",
                        True,
                    ),
                    ("module_with_license_and_shebang_todo.py", "#", None, True),
                    (
                        "module_without_license.groovy",
                        "//",
                        "module_with_license.groovy",
                        True,
                    ),
                    ("module_with_license.groovy", "//", None, False),
                    (
                        "module_with_fuzzy_matched_license.groovy",
                        "//",
                        "module_with_license_todo.groovy",
                        True,
                    ),
                    ("module_with_license_todo.groovy", "//", None, True),
                    (
                        "module_without_license.css",
                        "/*| *| */",
                        "module_with_license.css",
                        True,
                    ),
                    ("module_with_license.css", "/*| *| */", None, False),
                    (
                        "module_with_fuzzy_matched_license.css",
                        "/*| *| */",
                        "module_with_license_todo.css",
                        True,
                    ),
                    ("module_with_license_todo.css", "/*| *| */", None, True),
                ),
                (
                    (tuple(),),
                    (
                        (
                            "--license-filepath",
                            "LICENSE_2_without_trailing_newline.txt",
                        ),
                    ),
                ),
            ),
            product(
                ("LICENSE_2_without_trailing_newline.txt",),
                ("\n", "\r\n"),
                (
                    (
                        "module_without_license.py",
                        "#",
                        "module_with_license_2.py",
                        True,
                    ),
                    ("module_with_license.py", "#", None, False),
                    ("module_with_license_todo.py", "#", None, True),
                    ("module_with_license_and_shebang.py", "#", None, False),
                    ("module_with_license_and_shebang_todo.py", "#", None, True),
                ),
                (
                    (
                        (
                            "--license-filepath",
                            "LICENSE_with_trailing_newline.txt",
                        ),
                    ),
                    (
                        (
                            "--license-filepath",
                            "LICENSE_without_trailing_newline.txt",
                        ),
                    ),
                ),
            ),
        ),
    ),
)
def test_fuzzy_match_license(
    license_file_path,
    line_ending,
    src_file_path,
    comment_style,
    new_src_file_expected,
    fail_check,
    extra_args,
    tmpdir,
):
    with chdir_to_test_resources():
        path = tmpdir.join("src_file_path")
        shutil.copy(src_file_path, path.strpath)
        _convert_line_ending(path.strpath, line_ending)
        args = [
            "--license-filepath",
            license_file_path,
            "--comment-style",
            comment_style,
            "--fuzzy-match-generates-todo",
            path.strpath,
        ]
        if extra_args is not None:
            args.extend(extra_args)
        assert insert_license(args) == (1 if fail_check else 0)
        if new_src_file_expected:
            with open(new_src_file_expected, encoding="utf-8") as expected_content_file:
                expected_content = expected_content_file.read()
            new_file_content = path.open(encoding="utf-8").read()
            assert new_file_content == expected_content


@pytest.mark.parametrize(
    ("src_file_content", "expected_index", "match_years_strictly"),
    (
        (["foo\n", "bar\n"], None, True),
        (["# License line 1\n", "# Copyright 2017\n", "\n", "foo\n", "bar\n"], 0, True),
        (["\n", "# License line 1\n", "# Copyright 2017\n", "foo\n", "bar\n"], 1, True),
        (
            ["\n", "# License line 1\n", "# Copyright 2017\n", "foo\n", "bar\n"],
            1,
            False,
        ),
        (
            ["# License line 1\n", "# Copyright 1984\n", "\n", "foo\n", "bar\n"],
            None,
            True,
        ),
        (
            ["# License line 1\n", "# Copyright 1984\n", "\n", "foo\n", "bar\n"],
            0,
            False,
        ),
        (
            [
                "\n",
                "# License line 1\n",
                "# Copyright 2013,2015-2016\n",
                "foo\n",
                "bar\n",
            ],
            1,
            False,
        ),
    ),
)
def test_is_license_present(src_file_content, expected_index, match_years_strictly):
    license_info = LicenseInfo(
        plain_license="",
        eol="\n",
        comment_start="",
        comment_prefix="#",
        comment_end="",
        num_extra_lines=0,
        prefixed_license=["# License line 1\n", "# Copyright 2017\n"],
    )
    assert expected_index == find_license_header_index(
        src_file_content, license_info, 5, match_years_strictly=match_years_strictly
    )


@pytest.mark.parametrize(
    (
        "license_file_path",
        "line_ending",
        "src_file_path",
        "comment_style",
        "fuzzy_match",
        "new_src_file_expected",
        "fail_check",
        "use_current_year",
    ),
    map(
        lambda a: a[:2] + a[2],
        product(  # combine license files with other args
            (
                "LICENSE_with_trailing_newline.txt",
                "LICENSE_without_trailing_newline.txt",
            ),
            ("\n", "\r\n"),
            (
                (
                    "module_with_license.css",
                    "/*| *| */",
                    False,
                    "module_without_license.css",
                    True,
                    False,
                ),
                (
                    "module_with_license_and_few_words.css",
                    "/*| *| */",
                    False,
                    "module_without_license_and_few_words.css",
                    True,
                    False,
                ),
                ("module_with_license_todo.css", "/*| *| */", False, None, True, False),
                (
                    "module_with_fuzzy_matched_license.css",
                    "/*| *| */",
                    False,
                    None,
                    False,
                    False,
                ),
                ("module_without_license.css", "/*| *| */", False, None, False, False),
                (
                    "module_with_license.py",
                    "#",
                    False,
                    "module_without_license.py",
                    True,
                    False,
                ),
                (
                    "module_with_license_and_shebang.py",
                    "#",
                    False,
                    "module_without_license_and_shebang.py",
                    True,
                    False,
                ),
                (
                    "init_with_license.py",
                    "#",
                    False,
                    "init_without_license.py",
                    True,
                    False,
                ),
                (
                    "init_with_license_and_newline.py",
                    "#",
                    False,
                    "init_without_license.py",
                    True,
                    False,
                ),
                # Fuzzy match
                (
                    "module_with_license.css",
                    "/*| *| */",
                    True,
                    "module_without_license.css",
                    True,
                    False,
                ),
                ("module_with_license_todo.css", "/*| *| */", True, None, True, False),
                (
                    "module_with_fuzzy_matched_license.css",
                    "/*| *| */",
                    True,
                    "module_with_license_todo.css",
                    True,
                    False,
                ),
                ("module_without_license.css", "/*| *| */", True, None, False, False),
                (
                    "module_with_license_and_shebang.py",
                    "#",
                    True,
                    "module_without_license_and_shebang.py",
                    True,
                    False,
                ),
                # Strict and flexible years
                (
                    "module_with_stale_year_in_license.py",
                    "#",
                    False,
                    None,
                    False,
                    False,
                ),
                (
                    "module_with_stale_year_range_in_license.py",
                    "#",
                    False,
                    None,
                    False,
                    False,
                ),
                (
                    "module_with_license.py",
                    "#",
                    False,
                    "module_without_license.py",
                    True,
                    True,
                ),
                (
                    "module_with_stale_year_in_license.py",
                    "#",
                    False,
                    "module_without_license.py",
                    True,
                    True,
                ),
                (
                    "module_with_stale_year_range_in_license.py",
                    "#",
                    False,
                    "module_without_license.py",
                    True,
                    True,
                ),
                (
                    "module_with_badly_formatted_stale_year_range_in_license.py",
                    "#",
                    False,
                    "module_without_license.py",
                    True,
                    True,
                ),
            ),
        ),
    ),
)
def test_remove_license(
    license_file_path,
    line_ending,
    src_file_path,
    comment_style,
    fuzzy_match,
    new_src_file_expected,
    fail_check,
    use_current_year,
    tmpdir,
):
    with chdir_to_test_resources():
        path = tmpdir.join("src_file_path")
        shutil.copy(src_file_path, path.strpath)
        _convert_line_ending(path.strpath, line_ending)
        argv = [
            "--license-filepath",
            license_file_path,
            "--remove-header",
            path.strpath,
            "--comment-style",
            comment_style,
        ]
        if fuzzy_match:
            argv = ["--fuzzy-match-generates-todo"] + argv
        if use_current_year:
            argv = ["--use-current-year"] + argv
        assert insert_license(argv) == (1 if fail_check else 0)
        if new_src_file_expected:
            with open(new_src_file_expected, encoding="utf-8") as expected_content_file:
                expected_content = expected_content_file.read()
            new_file_content = path.open(encoding="utf-8").read()
            assert new_file_content == expected_content
