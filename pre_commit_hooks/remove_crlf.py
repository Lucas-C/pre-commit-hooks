from __future__ import print_function
import argparse, fileinput, re, sys
from .utils import is_textfile

def contains_crlf(filename):
    for line in fileinput.input([filename]):
        if '\r' in line:
            fileinput.close()
            return True
    return False

def removes_crlf(filename):
    for line in fileinput.input([filename], inplace=True):
        print(re.sub('\r$', '', line), end='')

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    args = parser.parse_args(argv)
    text_files = filter(is_textfile, args.filenames)
    files_with_crlf = filter(contains_crlf, text_files)
    for file_with_crlf in files_with_crlf:
        print('Removing CRLF end-lines in: {0}'.format(file_with_crlf))
        removes_crlf(file_with_crlf)
    return 1 if files_with_crlf else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
