import argparse, os, sys

# pylint: disable=unused-wildcard-import, wildcard-import
from stat import *

SUPPORTED_BITS = (
    S_ISUID  # set UID bit
    | S_ISGID  # set GID bit
    | S_ISVTX  # sticky bit
    | S_IREAD  # Unix V7 synonym for S_IRUSR
    | S_IWRITE  # Unix V7 synonym for S_IWUSR
    | S_IEXEC  # Unix V7 synonym for S_IXUSR
    | S_IRWXU  # mask for owner permissions
    | S_IRUSR  # read by owner
    | S_IWUSR  # write by owner
    | S_IXUSR  # execute by owner
    | S_IRWXG  # mask for group permissions
    | S_IRGRP  # read by group
    | S_IWGRP  # write by group
    | S_IXGRP  # execute by group
    | S_IRWXO  # mask for others (not in group) permissions
    | S_IROTH  # read by others
    | S_IWOTH  # write by others
    | S_IXOTH  # execute by others
)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "perms", type=str, help="Octal permissions to set on target files"
    )
    parser.add_argument("filenames", nargs="*", help="filenames to check")
    args = parser.parse_args(argv)
    try:
        # TODO: add support for +rwx syntax
        new_mode = int(args.perms, 8)
    except ValueError as error:
        print(f"Incorrect octal permissions provided in configuration: {error}")
        return 2
    result = 0
    for filename in args.filenames:
        current_mode = os.stat(filename).st_mode
        # We ignore S_IFREG and other similar unsupported bits:
        current_mode &= SUPPORTED_BITS
        if current_mode != new_mode:
            print(
                f"Fixing file permissions on {filename}:"
                f" 0o{current_mode:o} -> 0o{new_mode:o}"
            )
            os.chmod(filename, new_mode)
            result = 1
    return result


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))  # pragma: no cover
