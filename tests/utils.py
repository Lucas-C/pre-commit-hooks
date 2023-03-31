from contextlib import contextmanager
import io
import os
import sys


@contextmanager
def chdir_to_test_resources():
    prev_dir = os.getcwd()
    try:
        res_dir = os.path.dirname(os.path.realpath(__file__)) + "/resources"
        os.chdir(res_dir)
        yield
    finally:
        os.chdir(prev_dir)


@contextmanager
def capture_stdout():
    try:
        captured = io.StringIO()
        sys.stdout = captured
        yield captured
    finally:
        sys.stdout = sys.__stdout__
