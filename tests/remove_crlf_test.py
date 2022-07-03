from __future__ import absolute_import
from __future__ import unicode_literals
from pathlib import Path

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
    input_file = Path(tmpdir.join('file.txt'))
    input_file.write_bytes(bytes(input_s, 'UTF-8'))
    assert remove_crlf([str(input_file)]) == 1
    assert input_file.read_bytes() == bytes(expected, 'UTF-8')


@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        ('foo\r\nbar', 'foo\r\nbar'),
        ('bar\nbaz\r\n', 'bar\nbaz\r\n'),
    ),
)
def test_noremove_crlf(input_s, expected, tmpdir):
    input_file = Path(tmpdir.join('file.pdf'))
    input_file.write_bytes(bytes(input_s, 'UTF-8'))
    assert remove_crlf([str(input_file)]) == 0
    assert input_file.read_bytes() == bytes(expected, 'UTF-8')


@pytest.mark.parametrize(('arg'), ('', 'a.b', 'a/b'))
def test_badopt(arg):
    with pytest.raises((FileNotFoundError, NotADirectoryError,)):
        remove_crlf([arg])


def test_nothing_to_fix():
    assert remove_crlf([__file__]) == 0
    assert remove_crlf(['--']) == 0
