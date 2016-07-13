from __future__ import print_function
import argparse, sys
from html5validator.validator import Validator

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    parser.add_argument('--error_only', dest='error_only',
                        action='store_false', default=True)
    parser.add_argument('--ignore', nargs='*', default=None,
                        type=lambda s: (s.decode('utf-8')
                                        if isinstance(s, bytes) else s),
                        help='ignore messages containing the given strings')
    parser.add_argument('--ignore-re', nargs='*', default=None,
                        type=lambda s: (s.decode('utf-8')
                                        if isinstance(s, bytes) else s),
                        dest='ignore_re',
                        help='regular expression of messages to ignore')
    parser.add_argument('-l', action='store_const', const=2048,
                        dest='stack_size',
                        help=('run on larger files: sets Java '
                              'stack size to 2048k')
                        )
    parser.add_argument('-ll', action='store_const', const=8192,
                        dest='stack_size',
                        help=('run on larger files: sets Java '
                              'stack size to 8192k')
                        )
    parser.add_argument('-lll', action='store_const', const=32768,
                        dest='stack_size',
                        help=('run on larger files: sets Java '
                              'stack size to 32768k')
                        )
    args = parser.parse_args(argv)

    validator = Validator(directory=None, match=None, ignore=args.ignore, ignore_re=args.ignore_re)
    sys.exit(validator.validate(
        args.filenames,
        errors_only=args.error_only,
        stack_size=args.stack_size,
    ))

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
