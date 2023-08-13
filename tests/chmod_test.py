import sys
from pre_commit_hooks.chmod import main as chmod

from .utils import chdir_to_test_resources, capture_stdout


def test_chmod_ok():
    with chdir_to_test_resources():
        if sys.platform == "win32":
            with capture_stdout() as stdout:
                assert chmod(["755", "module_with_license.py"]) == 0
            assert (
                "This hook does nothing when executed on Windows" in stdout.getvalue()
            )
        else:
            assert chmod(["755", "module_with_license.py"]) == 1
            assert chmod(["644", "module_with_license.py"]) == 1
            assert chmod(["644", "module_with_license.py"]) == 0


def test_invalid_perms():
    assert chmod(["668", __file__]) == 2
