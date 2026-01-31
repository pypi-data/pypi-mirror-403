"""
Tests for CAN-001 Fixes: Neoclassical Canon Ratio Corrections

These tests validate the corrections made to the neoclassical canons analyzer for:
1. Fixed expected_ratio values for Canon 3 and Canon 6 (1.0 instead of 0.20/0.25)
2. Deviation percentages are now in reasonable ranges (<200%)
3. All 8 canons are properly returned

Issue: Canons 3, 6, 8 had >150% deviation due to mismatched expected_ratio values.
"""

import pytest
import numpy as np


class TestCanonDefinitions:
    """Test canon definitions are correctly configured."""

    def test_canon_3_expected_ratio(self):
        """Test Canon 3 (Facial Fifths) has expected_ratio of 1.0."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        canon_3 = analyzer.CANONS.get('canon_3_facial_fifths')
        assert canon_3 is not None, "Canon 3 should be defined"

        # FIX CAN-001: expected_ratio should be 1.0 (was 0.20)
        assert canon_3['expected_ratio'] == 1.0, \
               f"Canon 3 expected_ratio should be 1.0, got {canon_3['expected_ratio']}"

    def test_canon_6_expected_ratio(self):
        """Test Canon 6 (Nose = 1/4 Face Width) has expected_ratio of 1.0."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        canon_6 = analyzer.CANONS.get('canon_6_nose_face_ratio')
        assert canon_6 is not None, "Canon 6 should be defined"

        # FIX CAN-001: expected_ratio should be 1.0 (was 0.25)
        assert canon_6['expected_ratio'] == 1.0, \
               f"Canon 6 expected_ratio should be 1.0, got {canon_6['expected_ratio']}"

    def test_all_8_standard_canons_defined(self):
        """Test all 8 standard canons are defined."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        standard_canons = [
            'canon_1_facial_thirds',
            'canon_2_facial_quarters',
            'canon_3_facial_fifths',
            'canon_4_intercanthal_nose',
            'canon_5_eye_nose_width',
            'canon_6_nose_face_ratio',
            'canon_7_mouth_nose_ratio',
            'canon_8_interocular_nose',
        ]

        for canon_name in standard_canons:
            assert canon_name in analyzer.CANONS, f"Missing canon: {canon_name}"

    def test_ear_canons_marked_as_unvalidated(self):
        """Test ear-related canons are marked as not validated."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        ear_canons = ['canon_nasoaural', 'canon_orbitoaural']

        for canon_name in ear_canons:
            if canon_name in analyzer.CANONS:
                canon = analyzer.CANONS[canon_name]
                assert canon.get('validated') == False, \
                       f"Ear canon {canon_name} should be marked as not validated"
                assert canon.get('requires_profile') == True, \
                       f"Ear canon {canon_name} should require profile image"


class TestCanonMeasurementExtraction:
    """Test canon measurement extraction."""

    def test_extract_all_standard_canons(self):
        """Test that all 8 standard canons are extracted."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        # Create mock landmarks (68 points)
        landmarks = np.zeros((68, 2))

        # Set up realistic face proportions
        # Jawline (0-16)
        for i in range(17):
            landmarks[i] = [100 + i * 25, 350 - abs(i - 8) * 5]

        # Eyebrows (17-26)
        for i in range(17, 27):
            landmarks[i] = [150 + (i - 17) * 25, 150]

        # Nose (27-35)
        landmarks[27] = [250, 180]  # Nose bridge top
        landmarks[30] = [250, 240]  # Nose tip
        landmarks[33] = [250, 260]  # Subnasale
        for i in [28, 29]:
            landmarks[i] = [250, 180 + (i - 27) * 30]
        for i in [31, 32, 34, 35]:
            landmarks[i] = [230 + (i - 31) * 13, 260]

        # Eyes (36-47)
        for i in range(36, 42):  # Right eye
            landmarks[i] = [180 + (i - 36) * 8, 200]
        for i in range(42, 48):  # Left eye
            landmarks[i] = [290 + (i - 42) * 8, 200]

        # Mouth (48-67)
        for i in range(48, 60):
            landmarks[i] = [200 + (i - 48) * 8, 310]
        for i in range(60, 68):
            landmarks[i] = [210 + (i - 60) * 10, 310]

        # Extract measurements
        measurements = analyzer.extract_canon_measurements(landmarks, include_ear_canons=False)

        # Should have 8 standard canons
        standard_canon_keys = [
            'canon_1_facial_thirds',
            'canon_2_facial_quarters',
            'canon_3_facial_fifths',
            'canon_4_intercanthal_nose',
            'canon_5_eye_nose_width',
            'canon_6_nose_face_ratio',
            'canon_7_mouth_nose_ratio',
            'canon_8_interocular_nose',
        ]

        for key in standard_canon_keys:
            assert key in measurements, f"Missing measurement for {key}"
            assert 'ratio' in measurements[key], f"Missing ratio for {key}"
            assert 'confidence' in measurements[key], f"Missing confidence for {key}"


class TestCanonDeviationRanges:
    """Test canon deviation percentages are in reasonable ranges."""

    def test_canon_3_deviation_under_200_percent(self):
        """Test Canon 3 deviation is under 200% with fix."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        # Simulate measurement where eye width is 90% of expected (1/5 face)
        measurement_data = {
            'ratio': 0.9,  # 90% of expected
            'confidence': 0.9
        }

        result = analyzer.analyze_canon_validity(
            'canon_3_facial_fifths',
            measurement_data
        )

        # With expected_ratio=1.0, deviation should be |0.9 - 1.0| / 1.0 * 100 = 10%
        assert result.deviation_percentage < 200, \
               f"Canon 3 deviation should be <200%, got {result.deviation_percentage}%"

    def test_canon_6_deviation_under_200_percent(self):
        """Test Canon 6 deviation is under 200% with fix."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        # Simulate measurement where nose is 110% of expected (1/4 face)
        measurement_data = {
            'ratio': 1.1,  # 110% of expected
            'confidence': 0.9
        }

        result = analyzer.analyze_canon_validity(
            'canon_6_nose_face_ratio',
            measurement_data
        )

        # With expected_ratio=1.0, deviation should be |1.1 - 1.0| / 1.0 * 100 = 10%
        assert result.deviation_percentage < 200, \
               f"Canon 6 deviation should be <200%, got {result.deviation_percentage}%"

    def test_realistic_deviations_for_all_canons(self):
        """Test all canons have realistic deviation ranges."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        # Simulate realistic measurements (ratios between 0.7 and 1.3)
        test_ratios = {
            'canon_1_facial_thirds': 0.95,
            'canon_2_facial_quarters': 0.88,
            'canon_3_facial_fifths': 0.85,
            'canon_4_intercanthal_nose': 1.1,
            'canon_5_eye_nose_width': 0.9,
            'canon_6_nose_face_ratio': 1.15,
            'canon_7_mouth_nose_ratio': 1.0,
            'canon_8_interocular_nose': 1.05,
        }

        for canon_name, ratio in test_ratios.items():
            measurement_data = {'ratio': ratio, 'confidence': 0.9}
            result = analyzer.analyze_canon_validity(canon_name, measurement_data)

            assert result.deviation_percentage < 200, \
                   f"{canon_name} deviation should be <200%, got {result.deviation_percentage}%"


class TestCanonValidity:
    """Test canon validity calculations."""

    def test_perfect_ratio_is_valid(self):
        """Test that a perfect ratio (1.0) is marked as valid."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        measurement_data = {
            'ratio': 1.0,  # Perfect match
            'confidence': 0.9
        }

        result = analyzer.analyze_canon_validity(
            'canon_3_facial_fifths',
            measurement_data
        )

        assert result.is_valid == True, "Perfect ratio should be valid"
        assert result.validity_score > 0.9, "Perfect ratio should have high validity score"
        assert result.deviation_percentage < 1, "Perfect ratio should have ~0% deviation"

    def test_slight_deviation_still_valid(self):
        """Test that slight deviations within tolerance are valid."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        # 5% deviation should be within 15% tolerance
        measurement_data = {
            'ratio': 1.05,
            'confidence': 0.9
        }

        result = analyzer.analyze_canon_validity(
            'canon_3_facial_fifths',
            measurement_data
        )

        # With 15% tolerance, 5% deviation should be valid
        assert result.is_valid == True, \
               f"5% deviation should be valid with 15% tolerance, got is_valid={result.is_valid}"

    def test_large_deviation_is_invalid(self):
        """Test that large deviations are marked as invalid."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        # 50% deviation should exceed tolerance
        measurement_data = {
            'ratio': 1.5,
            'confidence': 0.9
        }

        result = analyzer.analyze_canon_validity(
            'canon_3_facial_fifths',
            measurement_data
        )

        assert result.is_valid == False, "50% deviation should be invalid"


class TestCanonResult:
    """Test CanonResult dataclass."""

    def test_canon_result_has_all_fields(self):
        """Test CanonResult has all required fields."""
        from capa.modules.neoclassical_canons import CanonResult

        result = CanonResult(
            canon_name="Test Canon",
            measured_ratio=0.95,
            expected_ratio=1.0,
            validity_score=0.8,
            deviation_percentage=5.0,
            is_valid=True,
            confidence=0.9
        )

        assert result.canon_name == "Test Canon"
        assert result.measured_ratio == 0.95
        assert result.expected_ratio == 1.0
        assert result.validity_score == 0.8
        assert result.deviation_percentage == 5.0
        assert result.is_valid == True
        assert result.confidence == 0.9


class TestNeoclassicalAnalysisResult:
    """Test NeoclassicalAnalysisResult structure."""

    def test_result_to_dict_has_all_canons(self):
        """Test to_dict includes all canon results."""
        from capa.modules.neoclassical_canons import (
            NeoclassicalAnalysisResult,
            CanonResult
        )

        canon_results = [
            CanonResult(f"Canon {i}", 0.95, 1.0, 0.8, 5.0, True, 0.9)
            for i in range(1, 9)
        ]

        result = NeoclassicalAnalysisResult(
            canons=canon_results,
            overall_validity_score=0.75,
            beauty_score=0.6,
            proportion_balance=0.7,
            confidence=0.85,
            landmarks=np.zeros((68, 2)),
            recommendations=["Good proportions"]
        )

        result_dict = result.to_dict()

        assert 'canons' in result_dict
        assert len(result_dict['canons']) == 8
        assert 'overall_validity_score' in result_dict
        assert 'beauty_score' in result_dict
        assert 'confidence' in result_dict


class TestToleranceValues:
    """Test tolerance values are appropriate."""

    def test_canon_3_has_reasonable_tolerance(self):
        """Test Canon 3 has increased tolerance (0.15)."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()
        canon = analyzer.CANONS.get('canon_3_facial_fifths')

        tolerance = canon.get('tolerance_ratio', 0)
        assert tolerance >= 0.10, \
               f"Canon 3 tolerance should be at least 0.10, got {tolerance}"

    def test_canon_6_has_reasonable_tolerance(self):
        """Test Canon 6 has increased tolerance (0.15)."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()
        canon = analyzer.CANONS.get('canon_6_nose_face_ratio')

        tolerance = canon.get('tolerance_ratio', 0)
        assert tolerance >= 0.10, \
               f"Canon 6 tolerance should be at least 0.10, got {tolerance}"


class TestPaperValidityData:
    """Test paper validity data is preserved."""

    def test_canons_have_paper_validity(self):
        """Test standard canons include paper validity data."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()

        standard_canons = [
            'canon_1_facial_thirds',
            'canon_3_facial_fifths',
            'canon_7_mouth_nose_ratio',
        ]

        for canon_name in standard_canons:
            canon = analyzer.CANONS.get(canon_name)
            assert 'paper_validity' in canon, \
                   f"{canon_name} should have paper_validity data"
            assert 'male' in canon['paper_validity'], \
                   f"{canon_name} should have male validity data"
            assert 'female' in canon['paper_validity'], \
                   f"{canon_name} should have female validity data"

    def test_canon_7_low_validity_documented(self):
        """Test Canon 7 (mouth width) has documented low validity."""
        from capa.modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()
        canon = analyzer.CANONS.get('canon_7_mouth_nose_ratio')

        # Paper found only 2.4% validity for Canon 7
        assert canon['paper_validity']['male'] < 0.05, \
               "Canon 7 should have documented low validity"
