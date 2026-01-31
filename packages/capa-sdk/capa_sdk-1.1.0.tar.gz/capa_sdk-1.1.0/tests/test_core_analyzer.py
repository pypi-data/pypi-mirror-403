"""
Tests for CoreAnalyzer

Unit tests for the main CAPA orchestrator.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestCoreAnalyzerImports:
    """Test that CoreAnalyzer can be imported correctly."""

    def test_import_core_analyzer(self):
        """Test importing CoreAnalyzer from capa."""
        from capa import CoreAnalyzer
        assert CoreAnalyzer is not None

    def test_import_analysis_configuration(self):
        """Test importing AnalysisConfiguration."""
        from capa import AnalysisConfiguration
        assert AnalysisConfiguration is not None

    def test_import_analysis_mode(self):
        """Test importing AnalysisMode enum."""
        from capa import AnalysisMode
        assert hasattr(AnalysisMode, 'FAST')
        assert hasattr(AnalysisMode, 'STANDARD')
        assert hasattr(AnalysisMode, 'THOROUGH')
        assert hasattr(AnalysisMode, 'SCIENTIFIC')

    def test_import_result_format(self):
        """Test importing ResultFormat enum."""
        from capa import ResultFormat
        assert hasattr(ResultFormat, 'STRUCTURED')
        assert hasattr(ResultFormat, 'JSON')
        assert hasattr(ResultFormat, 'REPORT')


class TestAnalysisConfiguration:
    """Test AnalysisConfiguration dataclass."""

    def test_default_configuration(self):
        """Test creating configuration with defaults."""
        from capa import AnalysisConfiguration, AnalysisMode

        config = AnalysisConfiguration()
        assert config.mode == AnalysisMode.STANDARD
        assert config.enable_wd_analysis is True
        assert config.enable_forehead_analysis is True
        assert config.enable_morphology_analysis is True

    def test_custom_configuration(self):
        """Test creating configuration with custom values."""
        from capa import AnalysisConfiguration, AnalysisMode

        config = AnalysisConfiguration(
            mode=AnalysisMode.FAST,
            enable_wd_analysis=True,
            enable_forehead_analysis=False,
            enable_morphology_analysis=False,
        )
        assert config.mode == AnalysisMode.FAST
        assert config.enable_wd_analysis is True
        assert config.enable_forehead_analysis is False
        assert config.enable_morphology_analysis is False

    def test_all_modes_available(self):
        """Test that all analysis modes are available."""
        from capa import AnalysisMode

        modes = [
            AnalysisMode.FAST,
            AnalysisMode.STANDARD,
            AnalysisMode.THOROUGH,
            AnalysisMode.SCIENTIFIC,
            AnalysisMode.RESEARCH,
            AnalysisMode.REALTIME,
        ]
        assert len(modes) == 6


class TestCoreAnalyzerInitialization:
    """Test CoreAnalyzer initialization."""

    def test_init_with_default_config(self):
        """Test initializing CoreAnalyzer with default configuration."""
        from capa import CoreAnalyzer

        analyzer = CoreAnalyzer()
        assert analyzer is not None
        assert analyzer.config is not None
        analyzer.shutdown()

    def test_init_with_custom_config(self, default_analysis_config):
        """Test initializing CoreAnalyzer with custom configuration."""
        from capa import CoreAnalyzer

        analyzer = CoreAnalyzer(config=default_analysis_config)
        assert analyzer.config == default_analysis_config
        analyzer.shutdown()

    def test_init_fast_mode(self):
        """Test initializing in FAST mode."""
        from capa import CoreAnalyzer, AnalysisConfiguration, AnalysisMode

        config = AnalysisConfiguration(mode=AnalysisMode.FAST)
        analyzer = CoreAnalyzer(config=config)
        assert analyzer.config.mode == AnalysisMode.FAST
        analyzer.shutdown()


class TestCoreAnalyzerAnalysis:
    """Test CoreAnalyzer analysis methods."""

    def test_analyze_blank_image(self, blank_image, tmp_path):
        """Test analyzing a blank image returns None or low confidence."""
        import cv2
        from capa import CoreAnalyzer, AnalysisConfiguration, AnalysisMode

        # Save blank image to file for analyze_image
        image_path = tmp_path / "blank.jpg"
        cv2.imwrite(str(image_path), blank_image)

        config = AnalysisConfiguration(mode=AnalysisMode.FAST)
        analyzer = CoreAnalyzer(config=config)

        try:
            result = analyzer.analyze_image(str(image_path))
            # Should either return None or a result with no valid data
            if result is not None:
                # If result exists, confidence should be very low or None
                if hasattr(result, 'processing_metadata') and result.processing_metadata:
                    confidence = result.processing_metadata.overall_confidence
                    if confidence is not None:
                        assert confidence < 0.5
        finally:
            analyzer.shutdown()

    def test_analyze_small_image(self, small_image, tmp_path):
        """Test analyzing a very small image handles edge case."""
        import cv2
        from capa import CoreAnalyzer, AnalysisConfiguration, AnalysisMode

        # Save small image to file
        image_path = tmp_path / "small.jpg"
        cv2.imwrite(str(image_path), small_image)

        config = AnalysisConfiguration(mode=AnalysisMode.FAST)
        analyzer = CoreAnalyzer(config=config)

        try:
            result = analyzer.analyze_image(str(image_path))
            # Should handle gracefully - either None or low/None confidence
            if result is not None and hasattr(result, 'processing_metadata'):
                if result.processing_metadata:
                    confidence = result.processing_metadata.overall_confidence
                    if confidence is not None:
                        assert confidence < 0.5
        finally:
            analyzer.shutdown()

    def test_analyze_returns_expected_structure(self, sample_image_rgb, tmp_path):
        """Test that analyze returns expected result structure."""
        import cv2
        from capa import CoreAnalyzer, AnalysisConfiguration, AnalysisMode

        # Save sample image to file
        image_path = tmp_path / "sample.jpg"
        cv2.imwrite(str(image_path), sample_image_rgb)

        config = AnalysisConfiguration(
            mode=AnalysisMode.FAST,
            enable_wd_analysis=True,
            enable_forehead_analysis=True,
            enable_morphology_analysis=True,
        )
        analyzer = CoreAnalyzer(config=config)

        try:
            result = analyzer.analyze_image(str(image_path))
            if result is not None:
                # Check result has expected attributes
                assert hasattr(result, 'wd_result')
                assert hasattr(result, 'forehead_result')
                assert hasattr(result, 'morphology_result')
                assert hasattr(result, 'processing_metadata')
        finally:
            analyzer.shutdown()


class TestCoreAnalyzerShutdown:
    """Test CoreAnalyzer shutdown behavior."""

    def test_shutdown_releases_resources(self):
        """Test that shutdown properly releases resources."""
        from capa import CoreAnalyzer

        analyzer = CoreAnalyzer()
        analyzer.shutdown()
        # Should not raise any exceptions

    def test_multiple_shutdown_calls(self):
        """Test that multiple shutdown calls don't cause errors."""
        from capa import CoreAnalyzer

        analyzer = CoreAnalyzer()
        analyzer.shutdown()
        analyzer.shutdown()  # Second call should be safe


class TestCoreAnalyzerModuleSelection:
    """Test module selection in CoreAnalyzer."""

    def test_wd_only_analysis(self, minimal_analysis_config, sample_image_rgb, tmp_path):
        """Test analysis with only WD module enabled."""
        import cv2
        from capa import CoreAnalyzer

        # Save sample image to file
        image_path = tmp_path / "sample_wd.jpg"
        cv2.imwrite(str(image_path), sample_image_rgb)

        analyzer = CoreAnalyzer(config=minimal_analysis_config)

        try:
            result = analyzer.analyze_image(str(image_path))
            if result is not None:
                # WD should be attempted
                assert hasattr(result, 'wd_result')
                # Others should be None or not attempted
                if hasattr(result, 'forehead_result'):
                    assert result.forehead_result is None
                if hasattr(result, 'morphology_result'):
                    assert result.morphology_result is None
        finally:
            analyzer.shutdown()


class TestAnalysisModes:
    """Test different analysis modes."""

    @pytest.mark.parametrize("mode_name", [
        "FAST", "STANDARD", "THOROUGH", "SCIENTIFIC", "RESEARCH", "REALTIME"
    ])
    def test_mode_initialization(self, mode_name):
        """Test that all modes can be used for initialization."""
        from capa import CoreAnalyzer, AnalysisConfiguration, AnalysisMode

        mode = getattr(AnalysisMode, mode_name)
        config = AnalysisConfiguration(mode=mode)
        analyzer = CoreAnalyzer(config=config)

        assert analyzer.config.mode == mode
        analyzer.shutdown()
