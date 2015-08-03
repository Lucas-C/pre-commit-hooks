import string

# Taken from: http://code.activestate.com/recipes/173220-test-if-a-file-or-string-is-text-or-binary/

KNOWN_BINARY_FILE_EXT = ['.pdf']
ALLOWED_NON_PRINTABLE_THRESHOLD = 0.15

def is_textfile(filename, blocksize=512):
    if any(filename.endswith(ext) for ext in KNOWN_BINARY_FILE_EXT):
        return False
    return is_text(open(filename).read(blocksize))

def is_text(stuff):
    if "\0" in stuff:
        return False
    if not stuff:  # Empty files are considered text
        return True
    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    non_printable_chars = ''.join(c for c in stuff if c not in string.printable)
    return len(non_printable_chars) / len(stuff) < ALLOWED_NON_PRINTABLE_THRESHOLD
