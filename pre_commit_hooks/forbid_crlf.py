from __future__ import print_function
import argparse, fileinput, sys
from .utils import is_textfile

def contains_crlf(filename):
    for line in fileinput.input([filename]):
        if line.endswith('\r\n'):
            fileinput.close()
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
        print('CRLF end-lines detected in file: {0}'.format(file_with_crlf))
        return_code = 1
    return return_code

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
