from __future__ import absolute_import
from __future__ import unicode_literals

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
    input_b = bytes(input_s, 'UTF-8')
    expected_b = bytes(expected, 'UTF-8')
    with open(path, 'wb') as test_file:
        test_file.write(input_b)
    with open(path, 'rb') as test_file:
        assert test_file.read() == input_b
    assert remove_crlf([path.strpath]) == 1
    with open(path, 'rb') as test_file:
        assert test_file.read() == expected_b


@pytest.mark.parametrize(
    ('input_s', 'expected'),
    (
        ('foo\r\nbar', 'foo\r\nbar'),
        ('bar\nbaz\r\n', 'bar\nbaz\r\n'),
    ),
)
def test_noremove_crlf(input_s, expected, tmpdir):
    path = tmpdir.join('file.pdf')
    input_b = bytes(input_s, 'UTF-8')
    expected_b = bytes(expected, 'UTF-8')
    with open(path, 'wb') as test_file:
        test_file.write(input_b)
    with open(path, 'rb') as test_file:
        assert test_file.read() == input_b
    assert remove_crlf([path.strpath]) == 0
    with open(path, 'rb') as test_file:
        assert test_file.read() == expected_b


@pytest.mark.parametrize(('arg'), ('', 'a.b', 'a/b'))
def test_badopt(arg):
    with pytest.raises((FileNotFoundError, NotADirectoryError,)):
        remove_crlf([arg])


def test_nothing_to_fix():
    assert remove_crlf([__file__]) == 0
    assert remove_crlf(['--']) == 0
