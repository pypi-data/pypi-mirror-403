"""Music theory: scales and keys.

Provides scale patterns and utilities for generating scale-aware notes.
"""

# MIDI note numbers for C across octaves
# C0=12, C1=24, C2=36, C3=48, C4=60 (middle C), C5=72, C6=84, C7=96

# Note name to semitone offset from C
NOTE_OFFSETS = {
    'C': 0, 'C#': 1, 'Db': 1,
    'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4, 'E#': 5,
    'F': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11, 'Cb': 11, 'B#': 0,
}

# Scale patterns as semitone intervals from root
SCALE_PATTERNS = {
    # Major modes
    'major': [0, 2, 4, 5, 7, 9, 11],
    'ionian': [0, 2, 4, 5, 7, 9, 11],  # same as major
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'aeolian': [0, 2, 3, 5, 7, 8, 10],  # natural minor
    'locrian': [0, 1, 3, 5, 6, 8, 10],

    # Minor variants
    'minor': [0, 2, 3, 5, 7, 8, 10],  # natural minor
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor': [0, 2, 3, 5, 7, 9, 11],

    # Pentatonics
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10],

    # Blues
    'blues': [0, 3, 5, 6, 7, 10],

    # Other common scales
    'chromatic': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    'whole_tone': [0, 2, 4, 6, 8, 10],
    'diminished': [0, 2, 3, 5, 6, 8, 9, 11],  # whole-half
}


def note_to_midi(note: str, octave: int = 4) -> int:
    """Convert note name + octave to MIDI number.

    Args:
        note: Note name like 'C', 'F#', 'Bb'
        octave: Octave number (4 = middle C octave)

    Returns:
        MIDI note number (C4 = 60)

    Example:
        >>> note_to_midi('C', 4)
        60
        >>> note_to_midi('A', 4)
        69
    """
    if note not in NOTE_OFFSETS:
        raise ValueError(f"Unknown note: {note}. Use C, C#, Db, D, etc.")
    return 12 + (octave * 12) + NOTE_OFFSETS[note]


def midi_to_note(midi: int) -> tuple[str, int]:
    """Convert MIDI number to note name + octave.

    Args:
        midi: MIDI note number

    Returns:
        Tuple of (note_name, octave)

    Example:
        >>> midi_to_note(60)
        ('C', 4)
        >>> midi_to_note(69)
        ('A', 4)
    """
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi // 12) - 1
    note_idx = midi % 12
    return note_names[note_idx], octave


def get_scale(root: str, scale_type: str = 'major', octave: int = 4) -> list[int]:
    """Get MIDI notes for a scale in one octave.

    Args:
        root: Root note ('C', 'F#', 'Bb', etc.)
        scale_type: Scale type from SCALE_PATTERNS
        octave: Starting octave

    Returns:
        List of MIDI note numbers

    Example:
        >>> get_scale('C', 'major', 4)
        [60, 62, 64, 65, 67, 69, 71]
        >>> get_scale('A', 'minor', 4)
        [69, 71, 72, 74, 76, 77, 79]
    """
    if scale_type not in SCALE_PATTERNS:
        available = ', '.join(sorted(SCALE_PATTERNS.keys()))
        raise ValueError(f"Unknown scale: {scale_type}. Available: {available}")

    root_midi = note_to_midi(root, octave)
    return [root_midi + interval for interval in SCALE_PATTERNS[scale_type]]


def get_scale_range(root: str, scale_type: str = 'major',
                    low: int = 36, high: int = 96) -> list[int]:
    """Get all scale notes within a MIDI range.

    Args:
        root: Root note
        scale_type: Scale type
        low: Lowest MIDI note (default C2=36)
        high: Highest MIDI note (default C7=96)

    Returns:
        List of MIDI notes in the scale within range

    Example:
        >>> get_scale_range('C', 'pentatonic_major', 60, 84)
        [60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84]
    """
    if scale_type not in SCALE_PATTERNS:
        available = ', '.join(sorted(SCALE_PATTERNS.keys()))
        raise ValueError(f"Unknown scale: {scale_type}. Available: {available}")

    pattern = SCALE_PATTERNS[scale_type]
    root_offset = NOTE_OFFSETS[root]

    notes = []
    for midi in range(low, high + 1):
        # Check if this note is in the scale
        note_offset = (midi - root_offset) % 12
        if note_offset in pattern:
            notes.append(midi)

    return notes


def in_scale(midi: int, root: str, scale_type: str = 'major') -> bool:
    """Check if a MIDI note is in a given scale.

    Args:
        midi: MIDI note number to check
        root: Root note of scale
        scale_type: Scale type

    Returns:
        True if note is in scale

    Example:
        >>> in_scale(60, 'C', 'major')  # C in C major
        True
        >>> in_scale(61, 'C', 'major')  # C# not in C major
        False
    """
    if scale_type not in SCALE_PATTERNS:
        return False

    pattern = SCALE_PATTERNS[scale_type]
    root_offset = NOTE_OFFSETS[root]
    note_offset = (midi - root_offset) % 12
    return note_offset in pattern


def snap_to_scale(midi: int, root: str, scale_type: str = 'major',
                  direction: str = 'nearest') -> int:
    """Snap a MIDI note to the nearest note in a scale.

    Args:
        midi: MIDI note to snap
        root: Root note of scale
        scale_type: Scale type
        direction: 'nearest', 'up', or 'down'

    Returns:
        Nearest MIDI note that's in the scale

    Example:
        >>> snap_to_scale(61, 'C', 'major')  # C# snaps to C or D
        62
        >>> snap_to_scale(61, 'C', 'major', 'down')
        60
    """
    if in_scale(midi, root, scale_type):
        return midi

    if direction == 'up':
        for offset in range(1, 12):
            if in_scale(midi + offset, root, scale_type):
                return midi + offset
    elif direction == 'down':
        for offset in range(1, 12):
            if in_scale(midi - offset, root, scale_type):
                return midi - offset
    else:  # nearest
        for offset in range(1, 12):
            up = midi + offset
            down = midi - offset
            up_in = in_scale(up, root, scale_type)
            down_in = in_scale(down, root, scale_type)
            if up_in and down_in:
                return up  # prefer up when tied
            if up_in:
                return up
            if down_in:
                return down

    return midi  # shouldn't reach here


def list_scales() -> list[str]:
    """List all available scale types."""
    return sorted(SCALE_PATTERNS.keys())
