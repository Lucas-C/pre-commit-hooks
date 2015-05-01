import string

# Taken from: http://code.activestate.com/recipes/173220-test-if-a-file-or-string-is-text-or-binary/

TEXT_CHARACTERS = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
NULL_TRANS = string.maketrans("", "")
KNOWN_BINARY_FILE_EXT = ['.pdf']
ALLOWED_NON_PRINTABLE_THRESHOLD = 0.15

def is_textfile(filename, blocksize=512):
    if any(filename.endswith(ext) for ext in KNOWN_BINARY_FILE_EXT):
        return False
    return is_text(open(filename).read(blocksize))

def is_text(string):
    if "\0" in string:
        return False
    if not string:  # Empty files are considered text
        return True
    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    non_printable_chars = string.translate(NULL_TRANS, TEXT_CHARACTERS)
    return len(non_printable_chars) / len(string) < ALLOWED_NON_PRINTABLE_THRESHOLD
