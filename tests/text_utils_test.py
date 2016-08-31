from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from pre_commit_hooks.utils import is_text


@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        (b'foo \r\nbar', True),
        (b'<a>\xe9 \n</a>\n', False),
    ),
)
def test_is_text(input_s, expected):
    assert is_text(input_s) == expected
