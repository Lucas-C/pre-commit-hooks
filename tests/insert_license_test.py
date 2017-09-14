from __future__ import unicode_literals

from contextlib import contextmanager
import os, pytest, shutil

from pre_commit_hooks.insert_license import main as insert_license
from pre_commit_hooks.insert_license import find_license_header_index


@pytest.mark.parametrize(
    ('src_file_path', 'comment_prefix', 'new_src_file_expected'),
    (
        ('module_without_license.py', '#', 'module_with_license.py'),
        ('module_with_license.py', '#', False),
        ('module_with_license_and_shebang.py', '#', False),
        ('module_without_license.groovy', '//', 'module_with_license.groovy'),
        ('module_with_license.groovy', '//', False),
    ),
)
def test_insert_license(src_file_path, comment_prefix, new_src_file_expected, tmpdir):
    with chdir_to_test_resources():
        path = tmpdir.join('src_file_path')
        shutil.copy(src_file_path, path.strpath)
        assert insert_license(['--comment-style', comment_prefix, path.strpath]) == (1 if new_src_file_expected else 0)
        if new_src_file_expected:
            with open(new_src_file_expected) as expected_content_file:
                expected_content = expected_content_file.read()
            new_file_content = path.open().read()
            assert new_file_content == expected_content

@pytest.mark.parametrize(
    ('src_file_content', 'expected_index'),
    (
        (['foo\n', 'bar\n'], None),
        (['# License line 1\n', '# License line 2\n', '\n', 'foo\n', 'bar\n'], 0),
        (['\n', '# License line 1\n', '# License line 2\n', 'foo\n', 'bar\n'], 1),
    ),
)
def test_is_license_present(src_file_content, expected_index):
    prefixed_license = ['# License line 1\n', '# License line 2\n']
    assert expected_index == find_license_header_index(src_file_content, prefixed_license, 5)


@pytest.mark.parametrize(
    ('src_file_path', 'is_python', 'new_src_file_expected'),
    (
        ('module_with_license.css', False, 'module_without_license.css'),
        ('module_without_license.css', False, False),
        ('module_with_license_and_shebang.py', True, 'module_without_license_and_shebang.py'),
    ),
)
def test_remove_license(src_file_path, is_python, new_src_file_expected, tmpdir):
    with chdir_to_test_resources():
        path = tmpdir.join('src_file_path')
        shutil.copy(src_file_path, path.strpath)
        argv = ['--remove-header', path.strpath]
        if is_python:
            argv = ['--comment-style', '#'] + argv
        else:
            argv = ['--comment-style', '/*| *| */'] + argv
        assert insert_license(argv) == (1 if new_src_file_expected else 0)
        if new_src_file_expected:
            with open(new_src_file_expected) as expected_content_file:
                expected_content = expected_content_file.read()
            new_file_content = path.open().read()
            assert new_file_content == expected_content

@contextmanager
def chdir_to_test_resources():
    prev_dir = os.getcwd()
    try:
        os.chdir('tests/resources')
        yield
    finally:
        os.chdir(prev_dir)
