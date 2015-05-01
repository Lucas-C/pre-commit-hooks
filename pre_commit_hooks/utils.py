import string

# Taken from: http://code.activestate.com/recipes/173220-test-if-a-file-or-string-is-text-or-binary/

TEXT_CHARACTERS = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
NULL_TRANS = string.maketrans("", "")

def is_textfile(filename, blocksize=512):
    return is_text(open(filename).read(blocksize))

def is_text(string):
    if "\0" in string:
        return False
    if not string:  # Empty files are considered text
        return True
    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    text_chars = string.translate(NULL_TRANS, TEXT_CHARACTERS)
    # If more than 30% non-text characters, then
    # this is considered a binary file
    return len(text_chars) / len(string) < 0.30
