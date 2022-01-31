# Taken from: http://code.activestate.com/recipes/173220-test-if-a-file-or-string-is-text-or-binary/

KNOWN_BINARY_FILE_EXTS = ('.pdf',)

def is_textfile(filename, blocksize=512):
    if any(filename.endswith(ext) for ext in KNOWN_BINARY_FILE_EXTS):
        return False
    with open(filename, 'rb') as text_file:
        return is_text(text_file.read(blocksize))

def is_text(stuff):
    if b"\0" in stuff:
        return False
    if not stuff:  # Empty files are considered text
        return True
    # Try to decode as UTF-8
    try:
        stuff.decode('utf8')
    except UnicodeDecodeError:
        return False
    else:
        return True
