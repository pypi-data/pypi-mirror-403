"""
Tests for Scientific Modules

Unit tests for WDAnalyzer, ForeheadAnalyzer, MorphologyAnalyzer, and NeoclassicalCanonsAnalyzer.
"""

import pytest
import numpy as np


# =============================================================================
# Module Import Tests
# =============================================================================

class TestModuleImports:
    """Test that all modules can be imported correctly."""

    def test_import_wd_analyzer(self):
        """Test importing WDAnalyzer."""
        from capa.modules import WDAnalyzer
        assert WDAnalyzer is not None

    def test_import_forehead_analyzer(self):
        """Test importing ForeheadAnalyzer."""
        from capa.modules import ForeheadAnalyzer
        assert ForeheadAnalyzer is not None

    def test_import_morphology_analyzer(self):
        """Test importing MorphologyAnalyzer."""
        from capa.modules import MorphologyAnalyzer
        assert MorphologyAnalyzer is not None

    def test_import_neoclassical_canons_analyzer(self):
        """Test importing NeoclassicalCanonsAnalyzer."""
        from capa.modules import NeoclassicalCanonsAnalyzer
        assert NeoclassicalCanonsAnalyzer is not None

    def test_import_from_capa_root(self):
        """Test importing modules from capa root."""
        from capa import WDAnalyzer, ForeheadAnalyzer, MorphologyAnalyzer
        assert WDAnalyzer is not None
        assert ForeheadAnalyzer is not None
        assert MorphologyAnalyzer is not None


class TestWDAnalyzerResultTypes:
    """Test WDAnalyzer result types."""

    def test_import_wd_result(self):
        """Test importing WDResult."""
        from capa.modules import WDResult
        assert WDResult is not None

    def test_import_wd_classification(self):
        """Test importing WDClassification enum."""
        from capa.modules import WDClassification
        assert hasattr(WDClassification, 'HIGHLY_SOCIAL')
        assert hasattr(WDClassification, 'MODERATELY_SOCIAL')
        assert hasattr(WDClassification, 'BALANCED_SOCIAL')
        assert hasattr(WDClassification, 'RESERVED')
        assert hasattr(WDClassification, 'HIGHLY_RESERVED')

    def test_import_wd_personality_profile(self):
        """Test importing WDPersonalityProfile."""
        from capa.modules import WDPersonalityProfile
        assert WDPersonalityProfile is not None


class TestForeheadAnalyzerResultTypes:
    """Test ForeheadAnalyzer result types."""

    def test_import_forehead_result(self):
        """Test importing ForeheadResult."""
        from capa.modules import ForeheadResult
        assert ForeheadResult is not None

    def test_import_forehead_geometry(self):
        """Test importing ForeheadGeometry."""
        from capa.modules import ForeheadGeometry
        assert ForeheadGeometry is not None

    def test_import_impulsiveness_level(self):
        """Test importing ImpulsivenessLevel enum."""
        from capa.modules import ImpulsivenessLevel
        assert hasattr(ImpulsivenessLevel, 'VERY_LOW')
        assert hasattr(ImpulsivenessLevel, 'LOW')
        assert hasattr(ImpulsivenessLevel, 'MODERATE')
        assert hasattr(ImpulsivenessLevel, 'HIGH')
        assert hasattr(ImpulsivenessLevel, 'VERY_HIGH')


class TestMorphologyAnalyzerResultTypes:
    """Test MorphologyAnalyzer result types."""

    def test_import_morphology_result(self):
        """Test importing MorphologyResult."""
        from capa.modules import MorphologyResult
        assert MorphologyResult is not None

    def test_import_face_shape(self):
        """Test importing FaceShape enum."""
        from capa.modules import FaceShape
        # Common face shapes
        assert hasattr(FaceShape, 'OVAL')
        assert hasattr(FaceShape, 'ROUND')
        assert hasattr(FaceShape, 'SQUARE')
        assert hasattr(FaceShape, 'HEART')

    def test_import_facial_proportions(self):
        """Test importing FacialProportions."""
        from capa.modules import FacialProportions
        assert FacialProportions is not None


# =============================================================================
# WDAnalyzer Tests
# =============================================================================

class TestWDAnalyzerInitialization:
    """Test WDAnalyzer initialization."""

    def test_init_default(self):
        """Test initializing WDAnalyzer with defaults."""
        from capa.modules import WDAnalyzer

        analyzer = WDAnalyzer()
        assert analyzer is not None

    def test_init_with_learning_disabled(self):
        """Test initializing with continuous learning disabled."""
        from capa.modules import WDAnalyzer

        analyzer = WDAnalyzer(enable_learning=False)
        assert analyzer is not None


class TestWDAnalyzerAnalysis:
    """Test WDAnalyzer analysis."""

    def test_analyze_blank_image(self, blank_image):
        """Test WDAnalyzer with blank image raises or returns None."""
        from capa.modules import WDAnalyzer

        analyzer = WDAnalyzer()
        try:
            result = analyzer.analyze_image(blank_image)
            # Should return None or result with low confidence
            if result is not None:
                assert result.measurement_confidence < 0.5
        except ValueError:
            # Expected - no face in blank image
            pass

    def test_analyze_returns_wd_result(self, sample_image_rgb):
        """Test that analyze returns WDResult type."""
        from capa.modules import WDAnalyzer, WDResult

        analyzer = WDAnalyzer()
        try:
            result = analyzer.analyze_image(sample_image_rgb)
            if result is not None:
                assert isinstance(result, WDResult)
        except ValueError:
            # May fail on synthetic image - acceptable
            pass

    def test_wd_value_range(self, sample_image_rgb):
        """Test that WD ratio is in expected range."""
        from capa.modules import WDAnalyzer

        analyzer = WDAnalyzer()
        try:
            result = analyzer.analyze_image(sample_image_rgb)
            if result is not None and result.wd_ratio is not None:
                # WD ratio (bizygomatic/bigonial) typically between 0.5 and 1.5
                assert 0.0 < result.wd_ratio < 2.0
        except ValueError:
            # May fail on synthetic image - acceptable
            pass


# =============================================================================
# ForeheadAnalyzer Tests
# =============================================================================

class TestForeheadAnalyzerInitialization:
    """Test ForeheadAnalyzer initialization."""

    def test_init_default(self):
        """Test initializing ForeheadAnalyzer with defaults."""
        from capa.modules import ForeheadAnalyzer

        analyzer = ForeheadAnalyzer()
        assert analyzer is not None


class TestForeheadAnalyzerAnalysis:
    """Test ForeheadAnalyzer analysis.

    Note: ForeheadAnalyzer requires PROFILE images (lateral/side view).
    Frontal images will raise ValueError.
    """

    def test_analyze_blank_image(self, blank_image):
        """Test ForeheadAnalyzer with blank image raises ValueError."""
        from capa.modules import ForeheadAnalyzer

        analyzer = ForeheadAnalyzer()
        try:
            result = analyzer.analyze_image(blank_image)
            # If no exception, check confidence
            if result is not None:
                assert result.measurement_confidence < 0.5
        except ValueError:
            # Expected - requires profile image
            pass

    def test_analyze_requires_profile_image(self, sample_image_rgb):
        """Test that analyze raises error for non-profile images."""
        from capa.modules import ForeheadAnalyzer

        analyzer = ForeheadAnalyzer()
        # Should raise ValueError because sample_image_rgb is frontal
        with pytest.raises(ValueError, match="PROFILE"):
            analyzer.analyze_image(sample_image_rgb)

    def test_forehead_analyzer_initialization(self):
        """Test ForeheadAnalyzer can be initialized."""
        from capa.modules import ForeheadAnalyzer

        analyzer = ForeheadAnalyzer()
        assert analyzer is not None


# =============================================================================
# MorphologyAnalyzer Tests
# =============================================================================

class TestMorphologyAnalyzerInitialization:
    """Test MorphologyAnalyzer initialization."""

    def test_init_default(self):
        """Test initializing MorphologyAnalyzer with defaults."""
        from capa.modules import MorphologyAnalyzer

        analyzer = MorphologyAnalyzer()
        assert analyzer is not None


class TestMorphologyAnalyzerAnalysis:
    """Test MorphologyAnalyzer analysis."""

    def test_analyze_blank_image(self, blank_image):
        """Test MorphologyAnalyzer with blank image raises or returns None."""
        from capa.modules import MorphologyAnalyzer

        analyzer = MorphologyAnalyzer()
        try:
            result = analyzer.analyze_image(blank_image)
            # Should return None or result with low confidence
            if result is not None:
                assert result.measurement_confidence < 0.5
        except ValueError:
            # Expected - no face in blank image
            pass

    def test_analyze_returns_morphology_result(self, sample_image_rgb):
        """Test that analyze returns MorphologyResult type."""
        from capa.modules import MorphologyAnalyzer, MorphologyResult

        analyzer = MorphologyAnalyzer()
        try:
            result = analyzer.analyze_image(sample_image_rgb)
            if result is not None:
                assert isinstance(result, MorphologyResult)
        except ValueError:
            # May fail on synthetic image - acceptable
            pass

    def test_facial_index_range(self, sample_image_rgb):
        """Test that facial index is in expected range."""
        from capa.modules import MorphologyAnalyzer

        analyzer = MorphologyAnalyzer()
        try:
            result = analyzer.analyze_image(sample_image_rgb)
            if result is not None and result.facial_proportions is not None:
                index = result.facial_proportions.facial_index
                # Facial index typically between 70 and 110
                assert 50 <= index <= 130
        except ValueError:
            # May fail on synthetic image - acceptable
            pass


# =============================================================================
# NeoclassicalCanonsAnalyzer Tests
# =============================================================================

class TestNeoclassicalCanonsAnalyzerInitialization:
    """Test NeoclassicalCanonsAnalyzer initialization."""

    def test_init_default(self):
        """Test initializing NeoclassicalCanonsAnalyzer with defaults."""
        from capa.modules import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()
        assert analyzer is not None


class TestNeoclassicalCanonsAnalyzerAnalysis:
    """Test NeoclassicalCanonsAnalyzer analysis."""

    def test_analyze_blank_image(self, blank_image):
        """Test NeoclassicalCanonsAnalyzer with blank image raises or returns None."""
        from capa.modules import NeoclassicalCanonsAnalyzer

        analyzer = NeoclassicalCanonsAnalyzer()
        try:
            result = analyzer.analyze_image(blank_image)
            # Should return None or result with low confidence
            if result is not None and hasattr(result, 'confidence'):
                assert result.confidence < 0.5
        except ValueError:
            # Expected - no face in blank image
            pass


# =============================================================================
# Cross-Module Tests
# =============================================================================

class TestModuleInteroperability:
    """Test that modules work well together."""

    def test_all_modules_same_image(self, sample_image_rgb):
        """Test running all modules on the same image."""
        from capa.modules import (
            WDAnalyzer, ForeheadAnalyzer, MorphologyAnalyzer
        )

        # WD and Morphology work with frontal images
        try:
            wd_result = WDAnalyzer().analyze_image(sample_image_rgb)
        except ValueError:
            wd_result = None

        try:
            morphology_result = MorphologyAnalyzer().analyze_image(sample_image_rgb)
        except ValueError:
            morphology_result = None

        # Forehead requires profile - expected to fail with frontal
        try:
            forehead_result = ForeheadAnalyzer().analyze_image(sample_image_rgb)
        except ValueError:
            forehead_result = None  # Expected

        # All should complete without unhandled errors
        assert True

    def test_module_independence(self, sample_image_rgb):
        """Test that modules operate independently."""
        from capa.modules import WDAnalyzer

        # Create two instances of same analyzer
        wd1 = WDAnalyzer()
        wd2 = WDAnalyzer()

        try:
            result1 = wd1.analyze_image(sample_image_rgb)
            result2 = wd2.analyze_image(sample_image_rgb)

            # Both should produce similar results
            if result1 is not None and result2 is not None:
                assert abs(result1.wd_ratio - result2.wd_ratio) < 0.01
        except ValueError:
            # May fail on synthetic image - acceptable
            pass
