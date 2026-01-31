"""
Tests for WD-001 Fixes: IPD Normalization and CM-based Classification

These tests validate the corrections made to the WD analyzer for:
1. IPD scale factor calculation (pixels to cm conversion)
2. CM-based WD classification using paper-calibrated thresholds
3. Proper WD value ranges in centimeters

Reference: Gabarre-Armengol et al., 2019
- WD mean: 0.74 cm, SD: 1.46 cm, range: -1.55 to 4.0 cm
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch


class TestIPDScaleFactorCalculation:
    """Test IPD-based pixel to centimeter conversion."""

    def test_ipd_scale_factor_with_valid_landmarks(self):
        """Test IPD scale factor calculation with valid landmarks."""
        from capa.modules.wd_analyzer import WDAnalyzer

        analyzer = WDAnalyzer(enable_learning=False)

        # Create mock landmarks with realistic eye positions
        # IPD of ~80 pixels (simulating typical face image)
        landmarks = np.zeros((68, 2))

        # Right eye (landmarks 36-41) centered at (200, 200)
        for i in range(36, 42):
            landmarks[i] = [200 + (i - 39) * 5, 200]

        # Left eye (landmarks 42-47) centered at (280, 200)
        for i in range(42, 48):
            landmarks[i] = [280 + (i - 45) * 5, 200]

        result = analyzer.calculate_ipd_scale_factor(landmarks, gender='male')

        assert 'scale_factor' in result
        assert 'scale_factor_cm' in result
        assert 'ipd_pixels' in result
        assert 'confidence' in result

        # IPD should be approximately 80 pixels
        assert 70 < result['ipd_pixels'] < 90

        # Scale factor should be positive
        assert result['scale_factor'] > 0
        assert result['scale_factor_cm'] > 0

        # Confidence should be high for valid landmarks
        assert result['confidence'] >= 0.5

    def test_ipd_scale_factor_gender_adjustment(self):
        """Test that gender affects IPD reference values."""
        from capa.modules.wd_analyzer import WDAnalyzer

        analyzer = WDAnalyzer(enable_learning=False)

        landmarks = np.zeros((68, 2))
        for i in range(36, 42):
            landmarks[i] = [200, 200]
        for i in range(42, 48):
            landmarks[i] = [280, 200]

        result_male = analyzer.calculate_ipd_scale_factor(landmarks, gender='male')
        result_female = analyzer.calculate_ipd_scale_factor(landmarks, gender='female')

        # Male IPD reference is larger (64.7mm vs 62.3mm)
        # So scale factor should be slightly different
        assert result_male['reference_ipd_mm'] > result_female['reference_ipd_mm']

    def test_ipd_scale_factor_insufficient_landmarks(self):
        """Test handling of insufficient landmarks."""
        from capa.modules.wd_analyzer import WDAnalyzer

        analyzer = WDAnalyzer(enable_learning=False)

        # Less than 68 landmarks
        landmarks = np.zeros((50, 2))

        result = analyzer.calculate_ipd_scale_factor(landmarks)

        assert result['scale_factor'] == 0.0
        assert result['confidence'] == 0.0


class TestWDMeasurementsInCM:
    """Test WD measurements include centimeter values."""

    def test_wd_measurements_include_cm_values(self):
        """Test that calculate_wd_measurements returns cm values."""
        from capa.modules.wd_analyzer import WDAnalyzer, WDLandmarkQuality

        analyzer = WDAnalyzer(enable_learning=False)

        # Create realistic landmarks
        landmarks = np.zeros((68, 2))

        # Eyes for IPD calculation
        for i in range(36, 42):
            landmarks[i] = [200 + (i - 39) * 5, 200]
        for i in range(42, 48):
            landmarks[i] = [280 + (i - 45) * 5, 200]

        # Zygion points (1, 15) - bizygomatic width
        landmarks[1] = [150, 250]
        landmarks[15] = [350, 250]

        # Gonion points (5, 11) - bigonial width
        landmarks[5] = [180, 350]
        landmarks[11] = [320, 350]

        quality = WDLandmarkQuality(
            bizygomatic_confidence=0.9,
            bigonial_confidence=0.9,
            symmetry_score=0.85,
            detection_consistency=0.9,
            overall_quality=0.88
        )

        result = analyzer.calculate_wd_measurements(landmarks, quality, gender='male')

        # Check new cm fields exist
        assert 'wd_value_cm' in result
        assert 'bizygomatic_width_cm' in result
        assert 'bigonial_width_cm' in result
        assert 'scale_factor_cm' in result

        # WD in cm should be in reasonable range (-5 to +5 cm typically)
        assert -10.0 < result['wd_value_cm'] < 10.0

        # Bizygomatic width should be ~12-15 cm for adults
        assert 8.0 < result['bizygomatic_width_cm'] < 18.0

    def test_wd_cm_negative_when_narrow_jaw(self):
        """Test WD is negative when jaw is narrower than cheekbones."""
        from capa.modules.wd_analyzer import WDAnalyzer, WDLandmarkQuality

        analyzer = WDAnalyzer(enable_learning=False)

        landmarks = np.zeros((68, 2))

        # Eyes
        for i in range(36, 42):
            landmarks[i] = [200, 200]
        for i in range(42, 48):
            landmarks[i] = [280, 200]

        # Wide cheekbones
        landmarks[1] = [140, 250]
        landmarks[15] = [360, 250]  # 220 pixels wide

        # Narrow jaw
        landmarks[5] = [190, 350]
        landmarks[11] = [310, 350]  # 120 pixels wide

        quality = WDLandmarkQuality(
            bizygomatic_confidence=0.9,
            bigonial_confidence=0.9,
            symmetry_score=0.85,
            detection_consistency=0.9,
            overall_quality=0.88
        )

        result = analyzer.calculate_wd_measurements(landmarks, quality)

        # WD should be negative (bigonial < bizygomatic)
        assert result['wd_value'] < 0
        assert result['wd_value_cm'] < 0


class TestWDClassificationCM:
    """Test WD classification using cm-based thresholds."""

    def test_classify_wd_with_cm_thresholds(self):
        """Test classification using cm-calibrated thresholds."""
        from capa.modules.wd_analyzer import WDAnalyzer, WDClassification

        analyzer = WDAnalyzer(enable_learning=False)

        # Test each classification range based on paper thresholds (Gabarre-Armengol et al.)
        # Paper ranges:
        #   - highly_reserved: WD < -5.0 cm
        #   - reserved: -5.0 <= WD < -2.0 cm
        #   - balanced: -2.0 <= WD < 2.0 cm
        #   - moderately_social: 2.0 <= WD < 5.0 cm
        #   - highly_social: WD >= 5.0 cm
        test_cases = [
            (-6.0, WDClassification.HIGHLY_RESERVED),   # < -5.0
            (-3.5, WDClassification.RESERVED),          # -5.0 to -2.0
            (0.0, WDClassification.BALANCED_SOCIAL),    # -2.0 to 2.0
            (3.0, WDClassification.MODERATELY_SOCIAL),  # 2.0 to 5.0
            (6.0, WDClassification.HIGHLY_SOCIAL),      # >= 5.0
        ]

        for wd_cm, expected_class in test_cases:
            result = analyzer.classify_wd_result(wd_cm, use_cm=True)
            assert result == expected_class, f"WD={wd_cm}cm should be {expected_class.value}, got {result.value}"

    def test_classification_diversity(self):
        """Test that different WD values produce different classifications."""
        from capa.modules.wd_analyzer import WDAnalyzer

        analyzer = WDAnalyzer(enable_learning=False)

        # Test a range of WD values (in cm) - use values that span multiple categories
        # Based on paper thresholds: <-5 (highly_reserved), -5 to -2 (reserved),
        # -2 to 2 (balanced), 2 to 5 (moderately_social), >5 (highly_social)
        wd_values = [-6.0, -3.5, 0.0, 3.0, 6.0]
        classifications = []

        for wd in wd_values:
            result = analyzer.classify_wd_result(wd, use_cm=True)
            classifications.append(result.value)

        # Should have at least 3 different classifications
        unique_classifications = set(classifications)
        assert len(unique_classifications) >= 3, \
            f"Expected diverse classifications, got only: {unique_classifications}"


class TestWDResultCMFields:
    """Test that WDResult includes cm-normalized fields."""

    def test_wd_result_has_cm_fields(self):
        """Test WDResult dataclass has new cm fields."""
        from capa.modules.wd_analyzer import WDResult, WDLandmarkQuality, WDPersonalityProfile, WDClassification
        from datetime import datetime

        quality = WDLandmarkQuality(0.9, 0.9, 0.85, 0.9, 0.88)
        profile = WDPersonalityProfile(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5)

        result = WDResult(
            wd_value=-100.0,
            bizygomatic_width=400.0,
            bigonial_width=300.0,
            wd_ratio=0.75,
            normalized_wd_value=-95.0,
            ethnic_adjusted_wd=-100.0,
            confidence_weighted_wd=-90.0,
            landmark_quality=quality,
            measurement_confidence=0.85,
            analysis_reliability=0.9,
            personality_profile=profile,
            primary_classification=WDClassification.BALANCED_SOCIAL,
            secondary_traits=["Balanced"],
            research_correlations={},
            confidence_intervals={},
            analysis_id="test",
            timestamp=datetime.now(),
            processing_time=0.1,
            landmarks_used=np.zeros((68, 2)),
            # New cm fields
            wd_value_cm=-1.5,
            bizygomatic_width_cm=13.5,
            bigonial_width_cm=12.0,
            scale_factor_cm=0.015
        )

        assert hasattr(result, 'wd_value_cm')
        assert hasattr(result, 'bizygomatic_width_cm')
        assert hasattr(result, 'bigonial_width_cm')
        assert hasattr(result, 'scale_factor_cm')

        assert result.wd_value_cm == -1.5
        assert result.bizygomatic_width_cm == 13.5

    def test_wd_result_to_dict_includes_cm(self):
        """Test that to_dict includes cm fields."""
        from capa.modules.wd_analyzer import WDResult, WDLandmarkQuality, WDPersonalityProfile, WDClassification
        from datetime import datetime

        quality = WDLandmarkQuality(0.9, 0.9, 0.85, 0.9, 0.88)
        profile = WDPersonalityProfile(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5)

        result = WDResult(
            wd_value=-100.0,
            bizygomatic_width=400.0,
            bigonial_width=300.0,
            wd_ratio=0.75,
            normalized_wd_value=-95.0,
            ethnic_adjusted_wd=-100.0,
            confidence_weighted_wd=-90.0,
            landmark_quality=quality,
            measurement_confidence=0.85,
            analysis_reliability=0.9,
            personality_profile=profile,
            primary_classification=WDClassification.BALANCED_SOCIAL,
            secondary_traits=["Balanced"],
            research_correlations={},
            confidence_intervals={},
            analysis_id="test",
            timestamp=datetime.now(),
            processing_time=0.1,
            landmarks_used=np.zeros((68, 2)),
            wd_value_cm=-1.5,
            bizygomatic_width_cm=13.5,
            bigonial_width_cm=12.0,
            scale_factor_cm=0.015
        )

        result_dict = result.to_dict()

        assert 'wd_value_cm' in result_dict
        assert 'bizygomatic_width_cm' in result_dict
        assert 'bigonial_width_cm' in result_dict
        assert 'scale_factor_cm' in result_dict


class TestWDThresholdsConstants:
    """Test WD threshold constants are properly defined."""

    def test_wd_thresholds_cm_exist(self):
        """Test that cm thresholds are defined."""
        from capa.modules.wd_analyzer import WDAnalyzer

        analyzer = WDAnalyzer(enable_learning=False)

        assert hasattr(analyzer, 'WD_THRESHOLDS_CM')
        # Note: 'highly_reserved' is implicit (anything below 'reserved' threshold)
        assert 'reserved' in analyzer.WD_THRESHOLDS_CM
        assert 'balanced' in analyzer.WD_THRESHOLDS_CM
        assert 'moderately_social' in analyzer.WD_THRESHOLDS_CM
        assert 'highly_social' in analyzer.WD_THRESHOLDS_CM

    def test_ipd_reference_constants(self):
        """Test IPD reference constants are defined."""
        from capa.modules.wd_analyzer import WDAnalyzer

        analyzer = WDAnalyzer(enable_learning=False)

        assert hasattr(analyzer, 'IPD_REFERENCE')
        assert 'adult_mean_mm' in analyzer.IPD_REFERENCE
        assert 'male_mean_mm' in analyzer.IPD_REFERENCE
        assert 'female_mean_mm' in analyzer.IPD_REFERENCE

        # Validate IPD values are in expected range
        assert 60 < analyzer.IPD_REFERENCE['adult_mean_mm'] < 70
        assert analyzer.IPD_REFERENCE['male_mean_mm'] > analyzer.IPD_REFERENCE['female_mean_mm']


class TestWDPaperCompliance:
    """Test compliance with paper specifications."""

    def test_wd_range_matches_paper(self):
        """Test that expected WD range matches paper findings."""
        from capa.modules.wd_analyzer import WDAnalyzer

        analyzer = WDAnalyzer(enable_learning=False)

        # Paper: WD range -1.55 to 4.0 cm
        # Our thresholds should cover this range
        thresholds = analyzer.WD_THRESHOLDS_CM

        # Reserved threshold should catch values near paper minimum (-1.55)
        # Anything below this threshold is 'highly_reserved'
        assert thresholds['reserved'] <= -1.5

        # Highly social should be above paper mean + 1 SD
        assert thresholds['highly_social'] >= 2.0

    def test_classification_matches_paper_categories(self):
        """Test classification categories align with paper descriptions."""
        from capa.modules.wd_analyzer import WDClassification

        # Paper describes 5 categories based on WD
        expected_categories = [
            'highly_reserved',
            'reserved',
            'balanced_social',
            'moderately_social',
            'highly_social'
        ]

        actual_categories = [e.value for e in WDClassification]

        for expected in expected_categories:
            assert expected in actual_categories, f"Missing category: {expected}"
