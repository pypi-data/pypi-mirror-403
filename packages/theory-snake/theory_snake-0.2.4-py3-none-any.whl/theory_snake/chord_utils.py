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
    # 1. Clean and normalize input
    set_notes = []
    for note in notes:
        if note is not None:
            alt_note = get_alt(note)
            if alt_note not in set_notes:
                set_notes.append(alt_note)

    best_match = None
    highest_score = 0

    # 2. Iterate through possibilities


    for root_note in set_notes:
        for chord_type in SUPPORTED_CHORDS.keys():
            chord_obj = build_chord(root_note, chord_type)
            chord_notes = chord_obj.notes

            # Calculate how many input notes exist in this chord
            matches = sum(1 for n in set_notes if n in chord_notes)

            # Scoring:
            # We want the highest number of matches, but we also want
            # to penalize chords that have too many extra notes.
            score = matches / max(len(chord_notes), len(set_notes))

            if score > highest_score:
                highest_score = score
                best_match = f"{root_note} {chord_type}"

    # 3. Return the best result if it's "close enough" (e.g., > 70% match)
    return best_match if highest_score > 0.5 else "Unknown Chord"


if __name__ == "__main__":
    print(build_chord("G", "minor"))  # Expected output: ['C', 'E', 'G']
    print(build_chord("A", "minor"))  # Expected output: ['A', 'C', 'E']
     # Placeholder call


