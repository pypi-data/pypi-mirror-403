from .consts import Notes, Note_ALIASES, PREFERED_ALIASES

def get_sharp(note):
    """Returns the sharp version of the given note."""
    if note not in Notes:
        if note in Note_ALIASES:
            note = Note_ALIASES[note]
        else:
            raise ValueError("Invalid note")
    index = Notes.index(note)
    sharp_index = (index + 1) % len(Notes)
    return Notes[sharp_index]

def get_flat(note):
    """Returns the flat version of the given note."""
    if note not in Notes:
        if note in Note_ALIASES:
            note = Note_ALIASES[note]
        else:
            raise ValueError("Invalid note")
    index = Notes.index(note)
    flat_index = (index - 1) % len(Notes)
    return Notes[flat_index]

def get_alt(note):
    return PREFERED_ALIASES[note] if note in PREFERED_ALIASES else note

if __name__ == "__main__":
    print(get_sharp("G"))  # Example usage
    print(get_flat("D"))   # Example usage
