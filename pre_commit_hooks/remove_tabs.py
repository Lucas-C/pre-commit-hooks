import argparse, sys


def contains_tabs(filename):
    with open(filename, mode="rb") as file_checked:
        return b"\t" in file_checked.read()


def removes_tabs_in_file(filename, whitespaces_count):
    with open(filename, mode="rb") as file_processed:
        lines = file_processed.readlines()
    lines = [line.expandtabs(whitespaces_count) for line in lines]
    with open(filename, mode="wb") as file_processed:
        for line in lines:
            file_processed.write(line)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--whitespaces-count",
        type=int,
        required=True,
        help="number of whitespaces to substitute tabs with",
    )
    parser.add_argument("filenames", nargs="*", help="filenames to check")
    args = parser.parse_args(argv)
    files_with_tabs = [f for f in args.filenames if contains_tabs(f)]
    for file_with_tabs in files_with_tabs:
        print(
            f"Substituting tabs in: {file_with_tabs} by {args.whitespaces_count} whitespaces"
        )
        removes_tabs_in_file(file_with_tabs, args.whitespaces_count)
    if files_with_tabs:
        print("")
        print("Tabs have been successfully removed. Now aborting the commit.")
        print(
            'You can check the changes made. Then simply "git add --update ." and re-commit'
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
