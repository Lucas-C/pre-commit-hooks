from __future__ import unicode_literals

from contextlib import contextmanager
import os, pytest, shutil

from pre_commit_hooks.insert_license import main as insert_license
from pre_commit_hooks.insert_license import is_license_present


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
    default_args = ['--comment-start', '', '--comment-end', '', '--comment-prefix']
    with chdir_to_test_resources():
        path = tmpdir.join('src_file_path')
        shutil.copy(src_file_path, path.strpath)
        assert insert_license(default_args + [comment_prefix, path.strpath]) == (1 if new_src_file_expected else 0)
        if new_src_file_expected:
            with open(new_src_file_expected) as expected_content_file:
                expected_content = expected_content_file.read()
            new_file_content = path.open().read()
            assert new_file_content == expected_content

@pytest.mark.parametrize(
    ('src_file_content', 'expected'),
    (
        (['foo\n', 'bar\n'], False),
        (['# License line 1\n', '# License line 2\n', '\n', 'foo\n', 'bar\n'], True),
        (['\n', '# License line 1\n', '# License line 2\n', 'foo\n', 'bar\n'], True),
    ),
)
def test_is_license_present(src_file_content, expected):
    prefixed_license = ['# License line 1\n', '# License line 2\n']
    assert expected == is_license_present(src_file_content, prefixed_license, 5)


@contextmanager
def chdir_to_test_resources():
    prev_dir = os.getcwd()
    try:
        os.chdir('tests/resources')
        yield
    finally:
        os.chdir(prev_dir)
