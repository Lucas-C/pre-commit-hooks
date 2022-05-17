from __future__ import absolute_import
from __future__ import unicode_literals
try:
    FileNotFoundError
except NameError:  # Python 2:
    FileNotFoundError = IOError
    FileNotFoundError = IOError

import pytest

from pre_commit_hooks.remove_crlf import main as remove_crlf


@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        ('foo\r\nbar', 'foo\nbar'),
        ('bar\nbaz\r\n', 'bar\nbaz\n'),
    ),
)
def test_remove_crlf(input_s, expected, tmpdir):
    path = tmpdir.join('file.txt')
    path.write(input_s)
    assert remove_crlf([path.strpath]) == 1
    assert path.read() == expected


@pytest.mark.parametrize(('arg'), ('', 'a.b', 'a/b'))
def test_badopt(arg):
    with pytest.raises((FileNotFoundError,)):
        remove_crlf([arg])


def test_nothing_to_fix():
    assert remove_crlf([__file__]) == 0
    assert remove_crlf(['--']) == 0
