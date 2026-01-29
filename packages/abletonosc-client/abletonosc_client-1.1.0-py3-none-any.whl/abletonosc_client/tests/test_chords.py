"""Tests for chords module - no Ableton connection required."""

import pytest
from abletonosc_client.chords import (
    get_chord,
    get_chord_in_key,
    get_progression,
    invert,
    voice_lead,
    spread,
    drop2,
    list_chord_types,
    list_progressions,
    CHORD_FORMULAS,
    PROGRESSIONS,
)


class TestGetChord:
    def test_c_major(self):
        chord = get_chord('C', 'major', 4)
        assert chord == [60, 64, 67]  # C E G

    def test_a_minor(self):
        chord = get_chord('A', 'minor', 4)
        assert chord == [69, 72, 76]  # A C E

    def test_g_dom7(self):
        chord = get_chord('G', 'dom7', 4)
        assert chord == [67, 71, 74, 77]  # G B D F

    def test_c_maj7(self):
        chord = get_chord('C', 'maj7', 4)
        assert chord == [60, 64, 67, 71]  # C E G B

    def test_power_chord(self):
        chord = get_chord('E', 'power', 2)
        assert chord == [40, 47]  # E B

    def test_sus4(self):
        chord = get_chord('D', 'sus4', 4)
        assert chord == [62, 67, 69]  # D G A

    def test_invalid_chord_type(self):
        with pytest.raises(ValueError) as exc:
            get_chord('C', 'nonexistent')
        assert 'Unknown chord type' in str(exc.value)


class TestGetChordInKey:
    def test_c_major_I(self):
        # I chord in C major = C major
        chord = get_chord_in_key('C', 0, 'major', 4)
        assert chord == [60, 64, 67]

    def test_c_major_V(self):
        # V chord in C major = G major
        chord = get_chord_in_key('C', 4, 'major', 4)
        assert chord == [67, 71, 74]

    def test_c_major_vi(self):
        # vi chord in C major = A minor
        chord = get_chord_in_key('C', 5, 'minor', 4)
        assert chord == [69, 72, 76]

    def test_invalid_degree(self):
        with pytest.raises(ValueError):
            get_chord_in_key('C', 7, 'major')


class TestGetProgression:
    def test_I_IV_V_I_in_C(self):
        prog = get_progression('C', 'I-IV-V-I', 4)
        assert len(prog) == 4
        assert prog[0] == [60, 64, 67]  # C major
        assert prog[1] == [65, 69, 72]  # F major
        assert prog[2] == [67, 71, 74]  # G major
        assert prog[3] == [60, 64, 67]  # C major

    def test_I_V_vi_IV(self):
        # "Axis progression" - very common
        prog = get_progression('G', 'I-V-vi-IV', 4)
        assert len(prog) == 4

    def test_invalid_progression(self):
        with pytest.raises(ValueError) as exc:
            get_progression('C', 'nonexistent')
        assert 'Unknown progression' in str(exc.value)


class TestInvert:
    def test_first_inversion(self):
        c_major = [60, 64, 67]
        inverted = invert(c_major, 1)
        assert inverted == [64, 67, 72]  # E G C

    def test_second_inversion(self):
        c_major = [60, 64, 67]
        inverted = invert(c_major, 2)
        assert inverted == [67, 72, 76]  # G C E

    def test_no_inversion(self):
        c_major = [60, 64, 67]
        inverted = invert(c_major, 0)
        assert inverted == [60, 64, 67]

    def test_original_unchanged(self):
        c_major = [60, 64, 67]
        invert(c_major, 1)
        assert c_major == [60, 64, 67]  # Original not modified


class TestVoiceLead:
    def test_c_to_f_voice_leading(self):
        c_major = [60, 64, 67]  # C E G
        f_major = [65, 69, 72]  # F A C
        led = voice_lead(c_major, f_major)
        # Should minimize movement - all notes should be close
        assert len(led) == 3
        # Check that movement is minimized
        for orig, new in zip(c_major, led):
            assert abs(orig - new) <= 12  # No voice moves more than octave

    def test_same_chord_unchanged(self):
        c_major = [60, 64, 67]
        led = voice_lead(c_major, c_major.copy())
        assert sorted(led) == sorted(c_major)


class TestSpread:
    def test_spread_triad(self):
        c_major = [60, 64, 67]
        spread_chord = spread(c_major)
        assert spread_chord[0] == 60  # Root unchanged
        assert spread_chord[1] == 64  # 3rd unchanged
        assert spread_chord[2] == 79  # 5th up octave

    def test_spread_two_notes(self):
        power = [60, 67]
        spread_chord = spread(power)
        assert spread_chord == [60, 67]  # Unchanged


class TestDrop2:
    def test_drop2_maj7(self):
        cmaj7 = [60, 64, 67, 71]  # C E G B
        dropped = drop2(cmaj7)
        # Second from top (G=67) drops an octave to 55
        assert 55 in dropped
        assert len(dropped) == 4

    def test_drop2_triad_unchanged(self):
        c_major = [60, 64, 67]
        dropped = drop2(c_major)
        assert dropped == [60, 64, 67]


class TestListFunctions:
    def test_list_chord_types(self):
        types = list_chord_types()
        assert 'major' in types
        assert 'minor' in types
        assert 'dom7' in types
        assert len(types) > 10

    def test_list_progressions(self):
        progs = list_progressions()
        assert 'I-IV-V-I' in progs
        assert 'I-V-vi-IV' in progs
        assert 'ii-V-I' in progs


class TestChordFormulas:
    def test_triads_have_3_notes(self):
        triads = ['major', 'minor', 'diminished', 'augmented']
        for name in triads:
            assert len(CHORD_FORMULAS[name]) == 3

    def test_seventh_chords_have_4_notes(self):
        sevenths = ['maj7', 'min7', 'dom7', 'dim7']
        for name in sevenths:
            assert len(CHORD_FORMULAS[name]) == 4

    def test_power_chord_has_2_notes(self):
        assert len(CHORD_FORMULAS['power']) == 2
