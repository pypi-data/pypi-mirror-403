#Notes
Notes = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
Note_ALIASES = {
    'C#': 'Db',
    'D#': 'Eb',
    'F#': 'Gb',
    'G#': 'Ab',
    'A#': 'Bb',
    'Db': 'C#',
    'Eb': 'D#',
    'Gb': 'F#',
    'Ab': 'G#',
    'Bb': 'A#'
}
PREFERED_ALIASES = {
    'Db': 'C#',
    'D#': 'Eb',
    'Gb': 'F#',
    'G#': 'Ab',
    'A#': 'Bb'
}

#Scale Intervals
MAJOR_SCALE_INTERVALS = [2, 2, 1, 2, 2, 2, 1]
MINOR_SCALE_INTERVALS = [2, 1, 2, 2, 1, 2, 2]

# Chord Types
SUPPORTED_CHORDS = {
    'MAJOR_CHORD': ['1','3','5'],
    'MINOR_CHORD': ['1','3b','5'],
    'DIMINISHED_CHORD': ['1','3b','5b'],
    'AUGMENTED_CHORD': ['1','3','5#'],
    'SUSPENDED4_CHORD': ['1','4','5'],
    'SUSPENDED2_CHORD': ['1','2','5'],
    'MAJOR_7th_CHORD': ['1','3','5','7'],
    'DOMINANT_7th_CHORD': ['1','3','5','7b']
    }

CHORD_WEIGHTS = {
    'MAJOR_CHORD': 1.2,        # Highest priority
    'MINOR_CHORD': 1.2,
    'MAJOR_7th_CHORD': 1.1,
    'DOMINANT_7th_CHORD': 1.1,
    'SUSPENDED4_CHORD': 0.9,   # Lower priority than triads
    'SUSPENDED2_CHORD': 0.9,
    'DIMINISHED_CHORD': 0.8,
    'AUGMENTED_CHORD': 0.8
}

#Guitar constants
FRET_COUNT = 18
COMMON_TUNNINGS = {
    "Standard": ["E", "A", "D", "G", "B", "E"],
    "Drop D": ["D", "A", "D", "G", "B", "E"],
    "DADGAD": ["D", "A", "D", "G", "A", "D"],
    "Open G": ["D", "G", "D", "G", "B", "D"],
    "Open D": ["D", "A", "D", "F#", "A", "D"],
}

__info__  = f"""
    Notes: {Notes}

    Supported Intervals:
        - Major Scale Intervals (major)
        - Minor Scale Intervals (minor)

    Supported Chord Types:
        - Major Chord
        - Minor Chord

    Supported Guitar Tunings:
        - Standard
        - Drop D
        - DADGAD
        - Open G
        - Open D
    """

