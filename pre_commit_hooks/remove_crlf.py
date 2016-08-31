from __future__ import print_function
import argparse, sys
from .utils import is_textfile

def contains_crlf(filename):
    with open(filename, mode='rb') as file_checked:
        for line in file_checked.readlines():
            if line.endswith(b'\r\n'):
                return True
    return False

def removes_crlf_in_file(filename):
    with open(filename, mode='rb') as file_processed:
        lines = file_processed.readlines()
    lines = [line.replace(b'\r\n', b'\n') for line in lines]
    with open(filename, mode='wb') as file_processed:
        for line in lines:
            file_processed.write(line)

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    args = parser.parse_args(argv)
    text_files = [f for f in args.filenames if is_textfile(f)]
    files_with_crlf = [f for f in text_files if contains_crlf(f)]
    for file_with_crlf in files_with_crlf:
        print('Removing CRLF end-lines in: {0}'.format(file_with_crlf))
        removes_crlf_in_file(file_with_crlf)
    if files_with_crlf:
        print('')
        print('CRLF end-lines have been successfully removed. Now aborting the commit.')
        print('You can check the changes made. Then simply "git add --update ." and re-commit')
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
