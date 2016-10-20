from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from pre_commit_hooks.detect_missing_css_classes import main as detect_missing_css_classes


@pytest.mark.parametrize('html_ext', ('hbs', 'html'))
def test_detect_missing_css_classes_ok(html_ext, tmpdir):
    html_path = tmpdir.join('file.' + html_ext)
    html_path.write('<html class="dummy"></html>')
    css_path = tmpdir.join('file.css')
    css_path.write('.dummy{margin:auto}')
    assert detect_missing_css_classes([
        '--css-files-dir', tmpdir.strpath,
        '--html-files-dir', tmpdir.strpath
    ]) == 0


def test_fail_on_missing_css_classes(tmpdir):
    html_path = tmpdir.join('file.html')
    html_path.write('<html class="dummy"></html>')
    css_path = tmpdir.join('file.css')
    css_path.write('')
    assert detect_missing_css_classes([
        '--css-files-dir', tmpdir.strpath,
        '--html-files-dir', tmpdir.strpath
    ]) == 1


def test_warn_on_unused_css_class(capsys, tmpdir):
    html_path = tmpdir.join('file.html')
    html_path.write('<html></html>')
    css_path = tmpdir.join('file.css')
    css_path.write('.dummy{margin:auto}')
    assert detect_missing_css_classes([
        '--css-files-dir', tmpdir.strpath,
        '--html-files-dir', tmpdir.strpath
    ]) == 0
    out, err = capsys.readouterr()
    assert out.splitlines()[-1] == 'WARNING: No usage found for CSS class dummy'


def test_ignored_missing_css_class(tmpdir):
    html_path = tmpdir.join('file.html')
    html_path.write('<html class="dummy"></html>')
    css_path = tmpdir.join('file.css')
    css_path.write('')
    assert detect_missing_css_classes([
        '--css-files-dir', tmpdir.strpath,
        '--html-files-dir', tmpdir.strpath,
        '--ignored-missing-class-defs-pattern', 'dummy'
    ]) == 0


def test_ignored_unused_css_class(capsys, tmpdir):
    html_path = tmpdir.join('file.html')
    html_path.write('<html></html>')
    css_path = tmpdir.join('file.css')
    css_path.write('.dummy{margin:auto}')
    assert detect_missing_css_classes([
        '--css-files-dir', tmpdir.strpath,
        '--html-files-dir', tmpdir.strpath,
        '--ignored-unused-class-defs-pattern', 'dummy'
    ]) == 0
    out, err = capsys.readouterr()
    assert 'WARNING' not in out
