from __future__ import print_function

import argparse
import sys

def forbid_crlf(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    args = parser.parse_args(argv)
    retval = 0
    return retval

if __name__ == '__main__':
    sys.exit(forbid_crlf())
