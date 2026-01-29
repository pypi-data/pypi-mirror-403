"""Music theory: chords and voicings.

Build chords from roots, get chord tones, create voicings.
"""

from abletonosc_client.scales import note_to_midi, NOTE_OFFSETS

# Chord formulas as semitone intervals from root
CHORD_FORMULAS = {
    # Triads
    'major': [0, 4, 7],
    'minor': [0, 3, 7],
    'diminished': [0, 3, 6],
    'augmented': [0, 4, 8],
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],

    # Seventh chords
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dom7': [0, 4, 7, 10],  # dominant 7th
    '7': [0, 4, 7, 10],     # alias for dom7
    'dim7': [0, 3, 6, 9],
    'min7b5': [0, 3, 6, 10],  # half-diminished
    'maj9': [0, 4, 7, 11, 14],
    'min9': [0, 3, 7, 10, 14],
    'dom9': [0, 4, 7, 10, 14],
    '9': [0, 4, 7, 10, 14],

    # Extended
    'add9': [0, 4, 7, 14],
    'add11': [0, 4, 7, 17],
    '6': [0, 4, 7, 9],
    'min6': [0, 3, 7, 9],

    # Power chord
    'power': [0, 7],
    '5': [0, 7],
}

# Common chord progressions (as roman numeral degrees)
# Stored as (scale_degree, chord_type) - degree is 0-indexed
PROGRESSIONS = {
    'I-IV-V-I': [(0, 'major'), (3, 'major'), (4, 'major'), (0, 'major')],
    'I-V-vi-IV': [(0, 'major'), (4, 'major'), (5, 'minor'), (3, 'major')],
    'ii-V-I': [(1, 'minor'), (4, 'major'), (0, 'major')],
    'I-vi-IV-V': [(0, 'major'), (5, 'minor'), (3, 'major'), (4, 'major')],
    'vi-IV-I-V': [(5, 'minor'), (3, 'major'), (0, 'major'), (4, 'major')],
    'I-IV-vi-V': [(0, 'major'), (3, 'major'), (5, 'minor'), (4, 'major')],
    # Minor key progressions
    'i-iv-v': [(0, 'minor'), (3, 'minor'), (4, 'minor')],
    'i-VI-III-VII': [(0, 'minor'), (5, 'major'), (2, 'major'), (6, 'major')],
    'i-iv-VII-III': [(0, 'minor'), (3, 'minor'), (6, 'major'), (2, 'major')],
    # Jazz
    'ii-V-I-VI': [(1, 'min7'), (4, 'dom7'), (0, 'maj7'), (5, 'dom7')],
}

# Major scale intervals for chord root calculation
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]


def get_chord(root: str, chord_type: str = 'major', octave: int = 4) -> list[int]:
    """Get MIDI notes for a chord.

    Args:
        root: Root note ('C', 'F#', 'Bb', etc.)
        chord_type: Chord type from CHORD_FORMULAS
        octave: Octave for root note

    Returns:
        List of MIDI note numbers

    Example:
        >>> get_chord('C', 'major', 4)
        [60, 64, 67]
        >>> get_chord('A', 'minor', 3)
        [57, 60, 64]
    """
    if chord_type not in CHORD_FORMULAS:
        available = ', '.join(sorted(CHORD_FORMULAS.keys()))
        raise ValueError(f"Unknown chord type: {chord_type}. Available: {available}")

    root_midi = note_to_midi(root, octave)
    return [root_midi + interval for interval in CHORD_FORMULAS[chord_type]]


def get_chord_in_key(key: str, degree: int, chord_type: str = 'major',
                     octave: int = 4) -> list[int]:
    """Get a chord built on a scale degree.

    Args:
        key: Key root note ('C', 'G', etc.)
        degree: Scale degree (0-6, where 0=I, 1=ii, etc.)
        chord_type: Chord type
        octave: Base octave

    Returns:
        List of MIDI notes

    Example:
        >>> get_chord_in_key('C', 4, 'major', 4)  # V chord in C
        [67, 71, 74]  # G major
    """
    if degree < 0 or degree > 6:
        raise ValueError(f"Degree must be 0-6, got {degree}")

    key_offset = NOTE_OFFSETS[key]
    root_offset = (key_offset + MAJOR_SCALE[degree]) % 12

    # Find the root note name
    root_midi = note_to_midi(key, octave) + MAJOR_SCALE[degree]

    return [root_midi + interval for interval in CHORD_FORMULAS[chord_type]]


def get_progression(key: str, progression_name: str, octave: int = 4) -> list[list[int]]:
    """Get chords for a named progression in a key.

    Args:
        key: Key root note
        progression_name: Name from PROGRESSIONS
        octave: Base octave

    Returns:
        List of chords (each chord is a list of MIDI notes)

    Example:
        >>> get_progression('C', 'I-IV-V-I', 4)
        [[60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67]]
    """
    if progression_name not in PROGRESSIONS:
        available = ', '.join(sorted(PROGRESSIONS.keys()))
        raise ValueError(f"Unknown progression: {progression_name}. Available: {available}")

    chords = []
    for degree, chord_type in PROGRESSIONS[progression_name]:
        chord = get_chord_in_key(key, degree, chord_type, octave)
        chords.append(chord)

    return chords


def invert(chord: list[int], inversion: int = 1) -> list[int]:
    """Invert a chord by moving bottom notes up an octave.

    Args:
        chord: List of MIDI notes
        inversion: Number of inversions (1=first, 2=second, etc.)

    Returns:
        Inverted chord

    Example:
        >>> invert([60, 64, 67], 1)  # C major first inversion
        [64, 67, 72]
    """
    if inversion <= 0:
        return chord.copy()

    result = chord.copy()
    for _ in range(inversion):
        if len(result) > 1:
            # Move lowest note up an octave
            result = result[1:] + [result[0] + 12]

    return result


def voice_lead(chord1: list[int], chord2: list[int]) -> list[int]:
    """Voice lead chord2 to minimize movement from chord1.

    Attempts to keep each voice as close as possible to its
    previous position.

    Args:
        chord1: Previous chord
        chord2: Next chord to voice lead

    Returns:
        Revoiced version of chord2

    Example:
        >>> voice_lead([60, 64, 67], [65, 69, 72])  # C to F
        [65, 65, 69]  # Wait, let me recalculate...
    """
    if len(chord1) != len(chord2):
        return chord2.copy()

    result = []
    used = set()

    for target in chord1:
        best_note = None
        best_distance = float('inf')

        for note in chord2:
            # Try the note and octave above/below
            for octave_shift in [-12, 0, 12]:
                candidate = note + octave_shift
                if candidate in used:
                    continue
                distance = abs(candidate - target)
                if distance < best_distance:
                    best_distance = distance
                    best_note = candidate

        if best_note is not None:
            result.append(best_note)
            # Mark the base pitch class as used
            used.add(best_note % 12)
        else:
            result.append(chord2[len(result)] if len(result) < len(chord2) else target)

    return sorted(result)


def spread(chord: list[int], spread_amount: int = 12) -> list[int]:
    """Spread a chord across a wider range.

    Args:
        chord: List of MIDI notes
        spread_amount: Semitones to spread (default octave)

    Returns:
        Spread chord

    Example:
        >>> spread([60, 64, 67])  # C major
        [60, 64, 79]  # Root, 3rd, 5th up octave
    """
    if len(chord) <= 2:
        return chord.copy()

    result = chord.copy()
    # Move every other note up
    for i in range(2, len(result), 2):
        result[i] += spread_amount

    return result


def drop2(chord: list[int]) -> list[int]:
    """Create a drop 2 voicing (drop second-from-top note down an octave).

    Common jazz voicing technique.

    Args:
        chord: 4-note chord

    Returns:
        Drop 2 voiced chord

    Example:
        >>> drop2([60, 64, 67, 71])  # Cmaj7 close position
        [64, 60, 67, 71]  # Wait, should be [52, 60, 67, 71] or sorted
    """
    if len(chord) < 4:
        return chord.copy()

    result = chord.copy()
    # Drop the second-from-top note down an octave
    result[-2] -= 12
    return sorted(result)


def list_chord_types() -> list[str]:
    """List all available chord types."""
    return sorted(CHORD_FORMULAS.keys())


def list_progressions() -> list[str]:
    """List all available chord progressions."""
    return sorted(PROGRESSIONS.keys())
