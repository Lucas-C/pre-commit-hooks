from __future__ import print_function
import argparse, sys
from lxml.etree import iterparse
from lxml.html import defs

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    parser.add_argument('--extra-known-attributes', type=lambda s: s.split(','), default=[],
                        help='Comma-separated list of extra valid attribute names')
    args = parser.parse_args(argv)
    non_std_attr_matches = list(iterate_non_std_attributes(args.filenames, args.extra_known_attributes))
    return_error_code = 0
    for filename, attribute in non_std_attr_matches:
        print('Non-standard HTML attribute found in {}: {}'.format(filename, attribute))
        return_error_code = 1
    return return_error_code

def iterate_non_std_attributes(html_filenames, extra_known_attributes):
    known_html_attrs = defs.link_attrs | defs.event_attrs | defs.safe_attrs | set(extra_known_attributes)
    for html_filename in html_filenames:
        with open(html_filename, 'rb') as html_file:
            for _, elem in iterparse(html_file, html=True, remove_comments=True):
                for attribute_name in elem.attrib.keys():
                    if not any([attribute_name in known_html_attrs,
                                attribute_name.startswith('data-'),
                                attribute_name.startswith('aria-')]):
                        yield html_filename, attribute_name

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
