import argparse, sys


def contains_tabs(filename, chunk_size=4096):
    with open(filename, mode="rb") as file_checked:
        chunk = True
        while chunk:
            chunk = file_checked.read(chunk_size)
            if not chunk:
                break
            if b"\t" in chunk:
                return True
        return False


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="filenames to check")
    parser.add_argument(
        "--chunk-size",type=int,default=1024*1024,
        help=f"Size of chunks to read at a time (default: %(default)s bytes)")
    args = parser.parse_args(argv)
    files_with_tabs = [f for f in args.filenames if contains_tabs(f)]
    return_code = 0
    for file_with_tabs in files_with_tabs:
        print(f"Tabs detected in file: {file_with_tabs}")
        return_code = 1
    return return_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
