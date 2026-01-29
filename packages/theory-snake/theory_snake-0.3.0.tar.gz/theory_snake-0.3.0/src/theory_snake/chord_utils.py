from .consts import SUPPORTED_CHORDS,CHORD_WEIGHTS
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
    # notes[0] is often the intended root in simple play
    first_input_note = get_alt(notes[0]) if notes and notes[0] else None

    set_notes = []
    for note in notes:
        if note is not None:
            alt_note = get_alt(note)
            if alt_note not in set_notes:
                set_notes.append(alt_note)

    best_match = None
    highest_score = 0

    for root_note in set_notes:
        for chord_type, intervals in SUPPORTED_CHORDS.items():
            # Assuming build_chord uses your SUPPORTED_CHORDS keys
            chord_obj = build_chord(root_note, chord_type)
            chord_notes = chord_obj.notes

            # 1. Calculate Base Intersection (how many notes match)
            matches = sum(1 for n in set_notes if n in chord_notes)
            base_score = matches / max(len(chord_notes), len(set_notes))

            # 2. Apply Chord Type Weight (Major vs Sus)
            weight = CHORD_WEIGHTS.get(chord_type, 1.0)

            # 3. Root Bonus (If the root we are testing is the note the user played first)
            root_bonus = 1.1 if root_note == first_input_note else 1.0

            final_score = base_score * weight * root_bonus

            if final_score > highest_score:
                highest_score = final_score
                # Formatting the display name (e.g., "D MAJOR_CHORD")
                best_match = f"{root_note} {chord_type}"

    return best_match if highest_score > 0.4 else "Unknown Chord"


if __name__ == "__main__":
    print(build_chord("G", "minor"))  # Expected output: ['C', 'E', 'G']
    print(build_chord("A", "minor"))  # Expected output: ['A', 'C', 'E']
     # Placeholder call


