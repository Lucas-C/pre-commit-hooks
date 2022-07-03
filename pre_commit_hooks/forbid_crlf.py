from __future__ import print_function
import argparse, sys
from .utils import is_textfile

def contains_crlf(filename):
    with open(filename, mode='rb') as file_checked:
        for line in file_checked.readlines():
            if line.endswith(b'\r\n'):
                return True
    return False

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    args = parser.parse_args(argv)
    text_files = [f for f in args.filenames if is_textfile(f)]
    files_with_crlf = [f for f in text_files if contains_crlf(f)]
    return_code = 0
    for file_with_crlf in files_with_crlf:
        print(f'CRLF end-lines detected in file: {file_with_crlf}')
        return_code = 1
    return return_code

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
