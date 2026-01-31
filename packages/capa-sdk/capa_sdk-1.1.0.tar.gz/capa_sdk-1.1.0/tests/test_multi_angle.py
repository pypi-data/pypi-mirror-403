"""
Tests for MultiAngleAnalyzer

Unit tests for multi-angle facial analysis.
"""

import pytest
import numpy as np


class TestMultiAngleImports:
    """Test MultiAngleAnalyzer imports."""

    def test_import_multi_angle_analyzer(self):
        """Test importing MultiAngleAnalyzer."""
        from capa import MultiAngleAnalyzer
        assert MultiAngleAnalyzer is not None

    def test_import_angle_specification(self):
        """Test importing AngleSpecification."""
        from capa import AngleSpecification
        assert AngleSpecification is not None

    def test_import_multi_angle_result(self):
        """Test importing MultiAngleResult."""
        from capa import MultiAngleResult
        assert MultiAngleResult is not None


class TestAngleSpecification:
    """Test AngleSpecification dataclass."""

    def test_create_frontal_spec(self):
        """Test creating a frontal angle specification."""
        from capa import AngleSpecification

        spec = AngleSpecification(
            angle_type='frontal',
            image_path='/path/to/image.jpg'
        )
        assert spec.angle_type == 'frontal'
        assert spec.image_path == '/path/to/image.jpg'
        assert spec.weight == 1.0  # Default

    def test_create_spec_with_weight(self):
        """Test creating specification with custom weight."""
        from capa import AngleSpecification

        spec = AngleSpecification(
            angle_type='profile',
            image_path='/path/to/profile.jpg',
            weight=0.8
        )
        assert spec.weight == 0.8

    def test_create_spec_with_threshold(self):
        """Test creating specification with quality threshold."""
        from capa import AngleSpecification

        spec = AngleSpecification(
            angle_type='lateral_left',
            image_path='/path/to/left.jpg',
            quality_threshold=0.5
        )
        assert spec.quality_threshold == 0.5

    @pytest.mark.parametrize("angle_type", [
        'frontal', 'lateral_left', 'lateral_right', 'profile', 'semi_frontal'
    ])
    def test_all_angle_types(self, angle_type):
        """Test all supported angle types."""
        from capa import AngleSpecification

        spec = AngleSpecification(
            angle_type=angle_type,
            image_path=f'/path/to/{angle_type}.jpg'
        )
        assert spec.angle_type == angle_type


class TestMultiAngleAnalyzerInitialization:
    """Test MultiAngleAnalyzer initialization."""

    def test_init_default(self):
        """Test initializing MultiAngleAnalyzer with defaults."""
        from capa import MultiAngleAnalyzer

        analyzer = MultiAngleAnalyzer()
        assert analyzer is not None
        analyzer.shutdown()

    def test_init_with_config(self, default_analysis_config):
        """Test initializing with custom configuration."""
        from capa import MultiAngleAnalyzer

        analyzer = MultiAngleAnalyzer(config=default_analysis_config)
        assert analyzer.config == default_analysis_config
        analyzer.shutdown()


class TestMultiAngleAnalyzerShutdown:
    """Test MultiAngleAnalyzer shutdown."""

    def test_shutdown_releases_resources(self):
        """Test that shutdown properly releases resources."""
        from capa import MultiAngleAnalyzer

        analyzer = MultiAngleAnalyzer()
        analyzer.shutdown()
        # Should not raise any exceptions

    def test_multiple_shutdown_calls(self):
        """Test that multiple shutdown calls don't cause errors."""
        from capa import MultiAngleAnalyzer

        analyzer = MultiAngleAnalyzer()
        analyzer.shutdown()
        analyzer.shutdown()  # Should be safe


class TestMultiAngleResult:
    """Test MultiAngleResult structure."""

    def test_result_has_expected_fields(self):
        """Test that MultiAngleResult has expected fields."""
        from capa import MultiAngleResult
        from datetime import datetime

        result = MultiAngleResult(
            subject_id="test_subject",
            analysis_id="test_analysis",
            timestamp=datetime.now()
        )

        assert result.subject_id == "test_subject"
        assert result.analysis_id == "test_analysis"
        assert result.timestamp is not None
        assert hasattr(result, 'angle_results')
        assert hasattr(result, 'combined_wd_value')
        assert hasattr(result, 'combined_forehead_angle')
        assert hasattr(result, 'combined_face_shape')
        assert hasattr(result, 'combined_confidence')


class TestMultiAngleWeights:
    """Test angle weight configuration."""

    def test_default_weights(self):
        """Test that default weights are set correctly."""
        from capa import MultiAngleAnalyzer

        analyzer = MultiAngleAnalyzer()

        # Check default weights exist
        assert hasattr(analyzer, 'angle_weights')
        assert 'frontal' in analyzer.angle_weights
        assert analyzer.angle_weights['frontal'] == 1.0  # Frontal should have highest weight

        analyzer.shutdown()

    def test_frontal_highest_weight(self):
        """Test that frontal angle has highest weight."""
        from capa import MultiAngleAnalyzer

        analyzer = MultiAngleAnalyzer()

        frontal_weight = analyzer.angle_weights.get('frontal', 0)
        for angle, weight in analyzer.angle_weights.items():
            if angle != 'frontal':
                assert frontal_weight >= weight, f"Frontal should have highest weight, but {angle} has {weight}"

        analyzer.shutdown()


class TestAnalysisPreferences:
    """Test analysis type preferences for different angles."""

    def test_wd_analysis_preferences(self):
        """Test WD analysis angle preferences."""
        from capa import MultiAngleAnalyzer

        analyzer = MultiAngleAnalyzer()

        assert hasattr(analyzer, 'analysis_preferences')
        wd_prefs = analyzer.analysis_preferences.get('wd_analysis', [])
        assert 'frontal' in wd_prefs  # WD should prefer frontal

        analyzer.shutdown()

    def test_forehead_analysis_preferences(self):
        """Test forehead analysis angle preferences."""
        from capa import MultiAngleAnalyzer

        analyzer = MultiAngleAnalyzer()

        forehead_prefs = analyzer.analysis_preferences.get('forehead_analysis', [])
        # Forehead can use frontal and lateral views
        assert len(forehead_prefs) > 0

        analyzer.shutdown()
