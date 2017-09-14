from __future__ import print_function
import argparse, sys


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    parser.add_argument('--license-filepath', default='LICENSE.txt')
    parser.add_argument('--comment-start', default='/*')
    parser.add_argument('--comment-prefix', default=' *')
    parser.add_argument('--comment-end', default=' */')
    parser.add_argument('--detect-license-in-X-top-lines', type=int, default=5)
    args = parser.parse_args(argv)

    with open(args.license_filepath) as license_file:
        prefixed_license = ['{}{}{}'.format(args.comment_prefix, ' ' if line.strip() else '', line)
                            for line in license_file.readlines()]
    if args.comment_start:
        prefixed_license = [args.comment_start] + prefixed_license
    if args.comment_end:
        prefixed_license = prefixed_license + [args.comment_end]

    changes_made = False
    for src_filepath in args.filenames:
        with open(src_filepath) as src_file:
            src_file_content = src_file.readlines()
        if not is_license_present(src_file_content, prefixed_license, args.detect_license_in_X_top_lines):
            insert_license(src_filepath, src_file_content, prefixed_license)
            changes_made = True

    if changes_made:
        print('')
        print('The license has been added to some source files. Now aborting the commit.')
        print('You can check the changes made. Then simply "git add --update ." and re-commit')
        return 1
    return 0

def is_license_present(src_file_content, prefixed_license, top_lines_count):
    for i in range(top_lines_count):
        mismatch = False
        for j, license_line in enumerate(prefixed_license):
            if i + j >= len(src_file_content) or license_line.strip() != src_file_content[i + j].strip():
                mismatch = True
                break
        if not mismatch:
            return True
    return False

def insert_license(src_filepath, src_file_content, prefixed_license):
    eol = '\r\n' if prefixed_license[0][-2:] == '\r\n' else '\n'
    with open(src_filepath, 'w') as src_file:
        src_file.write(''.join(prefixed_license))
        src_file.write(eol + eol)
        src_file.write(''.join(src_file_content))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
