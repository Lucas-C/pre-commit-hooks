from __future__ import print_function
import argparse, sys
from lxml.etree import iterparse

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    args = parser.parse_args(argv)
    html_files_with_missing_img_alt = list(iterate_img_without_alt(args.filenames))
    return_error_code = 0
    for filename in html_files_with_missing_img_alt:
        print('<img> tag without alt text found in {}'.format(filename))
        return_error_code = 1
    return return_error_code

def iterate_img_without_alt(html_filenames):
    for html_filename in html_filenames:
        with open(html_filename, 'rb') as html_file:
            for _, elem in iterparse(html_file, html=True, remove_comments=True):
                if elem.tag != 'img':
                    continue
                attributes = elem.attrib.keys()
                if 'alt' not in attributes and 'data-ng-attr-alt' not in attributes:
                    yield html_filename

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
