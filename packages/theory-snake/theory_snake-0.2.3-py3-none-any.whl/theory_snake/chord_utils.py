from .consts import SUPPORTED_CHORDS
from .scale_builder import build_scale
from .note_utils import get_flat, get_sharp,get_alt
from .models.chord_model import Chord

def build_chord(root_note, chord_type):
    scale = build_scale(root_note, 'major')
    if chord_type in SUPPORTED_CHORDS:
        chord_intervals = SUPPORTED_CHORDS[chord_type]
    else:
        raise ValueError(f"Currently only the following chord types are supported: {list(SUPPORTED_CHORDS.keys())}")

    chord = []
    for interval in chord_intervals:
        if interval.isnumeric():
            chord.append(scale[int(interval) - 1])
        elif "b" in interval:
            base_note = scale[int(interval[0]) - 1]
            chord.append(get_flat(base_note))
        elif "#" in interval:
            base_note = scale[int(interval[0]) - 1]
            chord.append(get_sharp(base_note))
    return Chord(root_note, chord_type, chord)

def recognise_chord(notes):
    # Placeholder for future implementation
    set_notes = []
    set_notes = [note for note in notes if note is not None and note not in set_notes]
    set_notes = [get_alt(note) for note in set_notes]


    possible_chords = []
    for root_note in set_notes:
        for chord_type in SUPPORTED_CHORDS.keys():
            chord = build_chord(root_note, chord_type)
            possible_chords.append((chord.root, chord.chord_type, chord.notes))



    for root_note, chord_type, chord in possible_chords:
        if all(note in set_notes for note in chord) and len(chord) == len(set_notes):
            return f"{root_note} {chord_type}"


if __name__ == "__main__":
    print(build_chord("G", "minor"))  # Expected output: ['C', 'E', 'G']
    print(build_chord("A", "minor"))  # Expected output: ['A', 'C', 'E']
     # Placeholder call


