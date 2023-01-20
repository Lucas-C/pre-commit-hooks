import argparse, sys
from .utils import is_textfile

def contains_tabs(filename):
    with open(filename, mode='rb') as file_checked:
        return b'\t' in file_checked.read()

def removes_tabs_in_file(filename, whitespaces_count):
    with open(filename, mode='rb') as file_processed:
        lines = file_processed.readlines()
    lines = [subst_tabs_in_line(line, whitespaces_count) for line in lines]
    with open(filename, mode='wb') as file_processed:
        for line in lines:
            file_processed.write(line)

def subst_tabs_in_line(line: bytes, whitespaces_count: int) -> bytes:
    "Remove tabs and replace them with whitespaces_count spaces maintaining alignment"
    new_line = b''
    spaces_count = 0  # = how many consecutive space characters precede this \t
    for frag_i, frag in enumerate(line.split(b'\t')):
        if frag_i > 0 and spaces_count == 0: # case of a \t without whitespaces before
            spaces_count = 4
        else:  # we increment spaces_count to be a multiple of `whitespaces_count`:
            spaces_count += (whitespaces_count - spaces_count) % whitespaces_count
        tail_spaces_count = 0
        j = len(frag) - 1
        while j >= 0 and frag[j] == 32:
            tail_spaces_count += 1
            j -= 1
        new_line += spaces_count * (b' ') + frag[:j+1]
        spaces_count = tail_spaces_count
    return new_line

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--whitespaces-count', type=int, required=True,
                        help='number of whitespaces to substitute tabs with')
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    args = parser.parse_args(argv)
    text_files = [f for f in args.filenames if is_textfile(f)]
    files_with_tabs = [f for f in text_files if contains_tabs(f)]
    for file_with_tabs in files_with_tabs:
        print(f'Substituting tabs in: {file_with_tabs} by {args.whitespaces_count} whitespaces')
        removes_tabs_in_file(file_with_tabs, args.whitespaces_count)
    if files_with_tabs:
        print('')
        print('Tabs have been successfully removed. Now aborting the commit.')
        print('You can check the changes made. Then simply "git add --update ." and re-commit')
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
