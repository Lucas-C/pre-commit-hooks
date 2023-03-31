import pytest

from pre_commit_hooks.utils import is_text


@pytest.mark.parametrize(
    ("input_s", "expected"),
    (
        (b"foo \r\nbar", True),
        (b"<a>\xe9 \n</a>\n", False),
        (b"foo \x00bar", False),  # NUL character is not considered text
        (b"", True),  # Empty file is considered text
    ),
)
def test_is_text(input_s, expected):
    assert is_text(input_s) == expected
