from __future__ import print_function
import argparse, sys


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    parser.add_argument('--license-filepath', default='LICENSE.txt')
    parser.add_argument('--comment-style', default='#',
                        help='Can be a single prefix or a triplet: <comment-sart>|<comment-prefix>|<comment-end>'
                             'E.g.: /*| *| */')
    parser.add_argument('--detect-license-in-X-top-lines', type=int, default=5)
    parser.add_argument('--remove-header', action='store_true')
    args = parser.parse_args(argv)

    if '|' in args.comment_style:
        comment_start, comment_prefix, comment_end = args.comment_style.split('|')
    else:
        comment_start, comment_prefix, comment_end = None, args.comment_style, None

    with open(args.license_filepath) as license_file:
        prefixed_license = ['{}{}{}'.format(comment_prefix, ' ' if line.strip() else '', line)
                            for line in license_file.readlines()]
    eol = '\r\n' if prefixed_license[0][-2:] == '\r\n' else '\n'
    if not prefixed_license[-1].endswith(eol):
        prefixed_license[-1] += eol
    if comment_start:
        prefixed_license = [comment_start + eol] + prefixed_license
    if comment_end:
        prefixed_license = prefixed_license + [comment_end + eol]

    changes_made = False
    for src_filepath in args.filenames:
        with open(src_filepath) as src_file:
            src_file_content = src_file.readlines()
        license_header_index = find_license_header_index(src_file_content, prefixed_license, args.detect_license_in_X_top_lines)
        if license_header_index is not None:
            if args.remove_header:
                if src_file_content[license_header_index+len(prefixed_license)].strip():
                    src_file_content = src_file_content[:license_header_index] + src_file_content[license_header_index+len(prefixed_license):]
                else:
                    src_file_content = src_file_content[:license_header_index] + src_file_content[license_header_index+len(prefixed_license)+1:]
                with open(src_filepath, 'w') as src_file:
                    src_file.write(''.join(src_file_content))
                changes_made = True
        elif not args.remove_header:
            src_file_content = prefixed_license + [eol] + src_file_content
            with open(src_filepath, 'w') as src_file:
                src_file.write(''.join(src_file_content))
            changes_made = True

    if changes_made:
        print('')
        print('The license has been added to some source files. Now aborting the commit.')
        print('You can check the changes made. Then simply "git add --update ." and re-commit')
        return 1
    return 0

def find_license_header_index(src_file_content, prefixed_license, top_lines_count):
    '''
    Returns the line number, starting from 0 and lower than `top_lines_count`,
    where the license header comment starts in this file, or else None.
    '''
    for i in range(top_lines_count):
        license_match = True
        for j, license_line in enumerate(prefixed_license):
            if i + j >= len(src_file_content) or license_line.strip() != src_file_content[i + j].strip():
                license_match = False
                break
        if license_match:
            return i
    return None

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
