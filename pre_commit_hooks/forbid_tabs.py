import argparse, sys


def contains_tabs(filename):
    with open(filename, mode="rb") as file_checked:
        return b"\t" in file_checked.read()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="filenames to check")
    args = parser.parse_args(argv)
    files_with_tabs = [f for f in args.filenames if contains_tabs(f)]
    return_code = 0
    for file_with_tabs in files_with_tabs:
        print(f"Tabs detected in file: {file_with_tabs}")
        return_code = 1
    return return_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
