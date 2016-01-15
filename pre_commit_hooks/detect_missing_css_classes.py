from __future__ import print_function
import argparse, os, re, sys
from lxml.etree import iterparse
from tinycss2 import parse_stylesheet_bytes

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='filenames to check')
    parser.add_argument('--css-files-dir', required=True,
                        help='Root directory for CSS files to check')
    parser.add_argument('--html-files-dir', required=True,
                        help='Root directory for HTML files to check')
    parser.add_argument('--ignored-missing-class-defs-pattern',
                        help='Regular expression matching CSS class names')
    parser.add_argument('--ignored-unused-class-defs-pattern',
                        help='Regular expression matching CSS class names')
    args = parser.parse_args(argv)

    html_files = list(scandir(args.html_files_dir, '.html'))
    print('{} HTML files found in directory {}'.format(len(html_files), args.html_files_dir))
    css_files = list(scandir(args.css_files_dir, '.css'))
    print('{} CSS files found in directory {}'.format(len(css_files), args.css_files_dir))

    css_classes_used = sum([list(extract_css_classes_usages(html_file)) for html_file in html_files], [])
    print('Found {} CSS classes usages in HTML files'.format(len(css_classes_used)))
    css_classes_defined = sum([list(extract_css_classes_definitions(css_file)) for css_file in css_files], [])
    print('Found {} CSS classes definitions in CSS files'.format(len(css_classes_defined)))

    css_classes_defined = set(css_classes_defined)
    css_classes_used = set(css_classes_used)
    unused_css_classes = css_classes_defined - css_classes_used
    if args.ignored_unused_class_defs_pattern:
        unused_css_classes = sorted(css_class for css_class in unused_css_classes
                                    if not re.search(args.ignored_unused_class_defs_pattern, css_class))
    missing_css_classes = css_classes_used - css_classes_defined
    if args.ignored_missing_class_defs_pattern:
        missing_css_classes = sorted(css_class for css_class in missing_css_classes
                                     if not re.search(args.ignored_missing_class_defs_pattern, css_class))

    return_error_code = 0
    for css_class in unused_css_classes:
        print('WARNING: No usage found for CSS class {}'.format(css_class))
    for css_class in missing_css_classes:
        print('ERROR: Missing definition for CSS class {}'.format(css_class))
        return_error_code = 1
    return return_error_code

def scandir(dirname, file_extension):
    for dirpath, _, fnames in os.walk(dirname):
        for file_path in [os.path.join(dirpath, fname) for fname in fnames if fname.endswith(file_extension)]:
            yield file_path

def extract_css_classes_definitions(css_file):
    with open(css_file, 'rb') as open_file:
        rules, _ = parse_stylesheet_bytes(open_file.read())
    next_is_class_name = False
    while rules:
        rule = rules.pop(0)
        if rule.type == 'at-rule' and rule.content:
            rules.extend(rule.content)
        elif rule.type == 'qualified-rule':
            rules.extend(rule.prelude)
        elif rule.type == 'ident' and next_is_class_name:
            yield rule.value
        next_is_class_name = (rule.type == 'literal' and rule.value == '.')

def extract_css_classes_usages(html_file):
    # TODO: extract (data-)ng-class & (data-)ng-style
    for _, elem in iterparse(html_file, html=True, remove_comments=True):
        if 'class' not in elem.attrib.keys():
            continue
        for css_class in elem.attrib['class'].split(' '):
            if css_class:
                yield css_class

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
