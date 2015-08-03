from __future__ import print_function
import argparse, fileinput, re, sys
from .utils import is_textfile

def contains_crlf(filename):
    for line in fileinput.input([filename]):
        if line.endswith('\r\n'):
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
    text_files = [f for f in args.filenames if is_textfile(f)]
    files_with_crlf = [f for f in text_files if contains_crlf(f)]
    for file_with_crlf in files_with_crlf:
        print('Removing CRLF end-lines in: {0}'.format(file_with_crlf))
        removes_crlf(file_with_crlf)
    if files_with_crlf:
        print('')
        print('CRLF end-lines have been successfully removed. Now aborting the commit.')
        print('You can check the changes made. Then simply "git add --update ." and re-commit')
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
