from pre_commit_hooks.chmod import main as chmod

from .utils import chdir_to_test_resources


def test_chmod_ok():
    with chdir_to_test_resources():
        assert chmod(["755", "module_with_license.py"]) == 1
        assert chmod(["644", "module_with_license.py"]) == 1
        assert chmod(["644", "module_with_license.py"]) == 0


def test_invalid_perms():
    assert chmod(["668", __file__]) == 2
