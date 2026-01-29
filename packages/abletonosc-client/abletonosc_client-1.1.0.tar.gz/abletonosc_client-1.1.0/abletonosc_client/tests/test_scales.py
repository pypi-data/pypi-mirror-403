"""Tests for scales module - no Ableton connection required."""

import pytest
from abletonosc_client.scales import (
    note_to_midi,
    midi_to_note,
    get_scale,
    get_scale_range,
    in_scale,
    snap_to_scale,
    list_scales,
    SCALE_PATTERNS,
)


class TestNoteConversion:
    def test_note_to_midi_middle_c(self):
        assert note_to_midi('C', 4) == 60

    def test_note_to_midi_a440(self):
        assert note_to_midi('A', 4) == 69

    def test_note_to_midi_sharps(self):
        assert note_to_midi('C#', 4) == 61
        assert note_to_midi('F#', 4) == 66

    def test_note_to_midi_flats(self):
        assert note_to_midi('Db', 4) == 61
        assert note_to_midi('Bb', 4) == 70

    def test_note_to_midi_octaves(self):
        assert note_to_midi('C', 0) == 12
        assert note_to_midi('C', 3) == 48
        assert note_to_midi('C', 5) == 72

    def test_note_to_midi_invalid(self):
        with pytest.raises(ValueError):
            note_to_midi('X', 4)

    def test_midi_to_note_middle_c(self):
        assert midi_to_note(60) == ('C', 4)

    def test_midi_to_note_a440(self):
        assert midi_to_note(69) == ('A', 4)

    def test_midi_to_note_sharps(self):
        assert midi_to_note(61) == ('C#', 4)
        assert midi_to_note(66) == ('F#', 4)


class TestGetScale:
    def test_c_major(self):
        scale = get_scale('C', 'major', 4)
        assert scale == [60, 62, 64, 65, 67, 69, 71]

    def test_a_minor(self):
        scale = get_scale('A', 'minor', 4)
        assert scale == [69, 71, 72, 74, 76, 77, 79]

    def test_c_pentatonic_minor(self):
        scale = get_scale('C', 'pentatonic_minor', 4)
        assert scale == [60, 63, 65, 67, 70]

    def test_invalid_scale(self):
        with pytest.raises(ValueError) as exc:
            get_scale('C', 'nonexistent')
        assert 'Unknown scale' in str(exc.value)


class TestGetScaleRange:
    def test_c_major_range(self):
        notes = get_scale_range('C', 'major', 60, 72)
        assert notes == [60, 62, 64, 65, 67, 69, 71, 72]

    def test_pentatonic_range(self):
        notes = get_scale_range('C', 'pentatonic_major', 60, 72)
        # C D E G A C
        assert notes == [60, 62, 64, 67, 69, 72]


class TestInScale:
    def test_c_in_c_major(self):
        assert in_scale(60, 'C', 'major') is True

    def test_csharp_not_in_c_major(self):
        assert in_scale(61, 'C', 'major') is False

    def test_all_c_major_notes(self):
        c_major = [60, 62, 64, 65, 67, 69, 71]
        for midi in c_major:
            assert in_scale(midi, 'C', 'major') is True

    def test_chromatic_out_of_c_major(self):
        not_in_c_major = [61, 63, 66, 68, 70]
        for midi in not_in_c_major:
            assert in_scale(midi, 'C', 'major') is False


class TestSnapToScale:
    def test_already_in_scale(self):
        assert snap_to_scale(60, 'C', 'major') == 60

    def test_snap_nearest_up(self):
        # C# snaps to D (nearest)
        assert snap_to_scale(61, 'C', 'major') == 62

    def test_snap_down(self):
        # C# snaps down to C
        assert snap_to_scale(61, 'C', 'major', 'down') == 60

    def test_snap_up(self):
        # C# snaps up to D
        assert snap_to_scale(61, 'C', 'major', 'up') == 62


class TestListScales:
    def test_list_scales_returns_list(self):
        scales = list_scales()
        assert isinstance(scales, list)
        assert len(scales) > 0

    def test_common_scales_present(self):
        scales = list_scales()
        assert 'major' in scales
        assert 'minor' in scales
        assert 'pentatonic_major' in scales
        assert 'blues' in scales


class TestScalePatterns:
    def test_major_has_7_notes(self):
        assert len(SCALE_PATTERNS['major']) == 7

    def test_pentatonic_has_5_notes(self):
        assert len(SCALE_PATTERNS['pentatonic_major']) == 5

    def test_chromatic_has_12_notes(self):
        assert len(SCALE_PATTERNS['chromatic']) == 12

    def test_blues_has_6_notes(self):
        assert len(SCALE_PATTERNS['blues']) == 6
