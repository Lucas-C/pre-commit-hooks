from __future__ import print_function
import argparse, fileinput, re, sys
from .utils import is_textfile

def contains_tabs(filename):
    for line in fileinput.input([filename]):
        if '\t' in line:
            fileinput.close()
            return True
    return False

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    args = parser.parse_args(argv)
    text_files = filter(is_textfile, args.filenames)
    files_with_tabs = filter(contains_tabs, text_files)
    for file_with_tabs in files_with_tabs:
        print('Tabs detected in file: {0}'.format(file_with_tabs))
    return 1 if files_with_tabs else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
