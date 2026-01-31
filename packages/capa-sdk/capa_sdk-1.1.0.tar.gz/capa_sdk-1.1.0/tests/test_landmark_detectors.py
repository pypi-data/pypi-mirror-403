"""
Tests for landmark detection system.

Verifies that multiple detectors are functional and producing consistent results.
"""

import pytest
import numpy as np
from pathlib import Path


class TestLandmarkDetectors:
    """Test suite for landmark detector functionality."""

    @pytest.fixture
    def sample_image_path(self):
        """Get path to a sample test image."""
        project_root = Path(__file__).parent.parent
        images_dir = project_root / "images" / "frontal"
        images = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.JPG"))
        if images:
            return str(images[0])
        pytest.skip("No test images available")

    def test_landmark_system_initialization(self):
        """Test that the intelligent landmark system initializes correctly."""
        from capa._internal.intelligent_landmark_system import IntelligentLandmarkSystem

        system = IntelligentLandmarkSystem()

        # Verify system has detector methods
        assert hasattr(system, '_run_mediapipe_detection')
        assert hasattr(system, '_run_dlib_detection')
        assert hasattr(system, 'detect_landmarks_intelligent')

    def test_multiple_detectors_functional(self, sample_image_path):
        """Test that at least 2 detectors produce results."""
        from capa._internal.intelligent_landmark_system import IntelligentLandmarkSystem
        import cv2

        system = IntelligentLandmarkSystem()
        image = cv2.imread(sample_image_path)

        if image is None:
            pytest.skip(f"Could not load image: {sample_image_path}")

        result = system.detect_landmarks_intelligent(image)

        # Should have results from multiple detectors
        assert result is not None
        assert hasattr(result, 'individual_results')
        assert len(result.individual_results) >= 2, \
            f"Expected at least 2 detectors, got {len(result.individual_results)}"

        # Verify each detector produced landmarks
        for i, detector_result in enumerate(result.individual_results):
            assert len(detector_result.landmarks) > 0, \
                f"Detector {i} produced no landmarks"

    def test_landmark_precision_reasonable(self, sample_image_path):
        """Test that landmark precision is reasonable (not 0%)."""
        from capa._internal.intelligent_landmark_system import IntelligentLandmarkSystem
        import cv2

        system = IntelligentLandmarkSystem()
        image = cv2.imread(sample_image_path)

        if image is None:
            pytest.skip(f"Could not load image: {sample_image_path}")

        result = system.detect_landmarks_intelligent(image)

        assert result is not None
        assert hasattr(result, 'quality_metrics')

        precision = result.quality_metrics.landmark_precision

        # Precision should be reasonable (at least 50% with valid detections)
        assert precision >= 0.5, \
            f"Landmark precision too low: {precision:.1%}. Expected >= 50%"

        # Precision should not exceed 100%
        assert precision <= 1.0, \
            f"Landmark precision invalid: {precision:.1%}. Expected <= 100%"

    def test_landmark_consistency_calculated(self, sample_image_path):
        """Test that landmark consistency is calculated properly."""
        from capa._internal.intelligent_landmark_system import IntelligentLandmarkSystem
        import cv2

        system = IntelligentLandmarkSystem()
        image = cv2.imread(sample_image_path)

        if image is None:
            pytest.skip(f"Could not load image: {sample_image_path}")

        result = system.detect_landmarks_intelligent(image)

        assert result is not None
        consistency = result.quality_metrics.landmark_consistency

        # Consistency should be a valid value
        assert 0.0 <= consistency <= 1.0, \
            f"Landmark consistency out of range: {consistency:.1%}"

    def test_ensemble_landmarks_produced(self, sample_image_path):
        """Test that ensemble (fused) landmarks are produced."""
        from capa._internal.intelligent_landmark_system import IntelligentLandmarkSystem
        import cv2

        system = IntelligentLandmarkSystem()
        image = cv2.imread(sample_image_path)

        if image is None:
            pytest.skip(f"Could not load image: {sample_image_path}")

        result = system.detect_landmarks_intelligent(image)

        assert result is not None
        assert hasattr(result, 'final_landmarks')
        assert len(result.final_landmarks) > 0, \
            "No ensemble landmarks produced"

    def test_detector_types_identified(self, sample_image_path):
        """Test that detector types are properly identified in results."""
        from capa._internal.intelligent_landmark_system import IntelligentLandmarkSystem, DetectorType
        import cv2

        system = IntelligentLandmarkSystem()
        image = cv2.imread(sample_image_path)

        if image is None:
            pytest.skip(f"Could not load image: {sample_image_path}")

        result = system.detect_landmarks_intelligent(image)

        assert result is not None

        # Check that detector qualities include known detector types
        detector_types = set(result.quality_metrics.detector_qualities.keys())
        known_types = {DetectorType.MEDIAPIPE, DetectorType.DLIB,
                       DetectorType.FACE_RECOGNITION, DetectorType.OPENCV_DNN}

        # At least 2 known detectors should be used
        intersection = detector_types & known_types
        assert len(intersection) >= 2, \
            f"Expected at least 2 known detectors, got: {detector_types}"


class TestLandmarkPrecisionCalculation:
    """Test the landmark precision calculation specifically."""

    def test_precision_with_single_detector(self):
        """Test precision calculation with single detector result."""
        from capa._internal.intelligent_landmark_system import (
            IntelligentLandmarkSystem, LandmarkResult, DetectorType
        )
        import numpy as np

        system = IntelligentLandmarkSystem()

        # Single detector result
        single_result = [
            LandmarkResult(
                detector_type=DetectorType.DLIB,
                landmarks=np.array([(100, 100), (200, 200), (300, 300)]),
                confidence=0.9,
                processing_time=0.1,
                face_rect=(50, 50, 300, 300),
                quality_score=0.9,
                detection_metadata={}
            )
        ]

        precision = system._calculate_landmark_precision(single_result)

        # Single detector should return default 0.8
        assert precision == 0.8

    def test_precision_with_agreeing_detectors(self):
        """Test precision with detectors that agree on face location."""
        from capa._internal.intelligent_landmark_system import (
            IntelligentLandmarkSystem, LandmarkResult, DetectorType
        )
        import numpy as np

        system = IntelligentLandmarkSystem()

        # Two detectors with similar face locations
        results = [
            LandmarkResult(
                detector_type=DetectorType.DLIB,
                landmarks=np.array([(100 + i, 100 + i) for i in range(68)]),
                confidence=0.9,
                processing_time=0.1,
                face_rect=(50, 50, 300, 300),
                quality_score=0.9,
                detection_metadata={}
            ),
            LandmarkResult(
                detector_type=DetectorType.MEDIAPIPE,
                landmarks=np.array([(105 + i, 105 + i) for i in range(68)]),
                confidence=0.85,
                processing_time=0.15,
                face_rect=(52, 52, 302, 302),
                quality_score=0.85,
                detection_metadata={}
            )
        ]

        precision = system._calculate_landmark_precision(results)

        # High agreement should give high precision
        assert precision >= 0.8, f"Expected high precision, got {precision:.1%}"

    def test_precision_minimum_floor(self):
        """Test that precision has a minimum floor with valid detections."""
        from capa._internal.intelligent_landmark_system import (
            IntelligentLandmarkSystem, LandmarkResult, DetectorType
        )
        import numpy as np

        system = IntelligentLandmarkSystem()

        # Two detectors with very different face locations
        results = [
            LandmarkResult(
                detector_type=DetectorType.DLIB,
                landmarks=np.array([(100 + i, 100 + i) for i in range(68)]),
                confidence=0.9,
                processing_time=0.1,
                face_rect=(50, 50, 300, 300),
                quality_score=0.9,
                detection_metadata={}
            ),
            LandmarkResult(
                detector_type=DetectorType.MEDIAPIPE,
                landmarks=np.array([(300 + i, 300 + i) for i in range(68)]),
                confidence=0.85,
                processing_time=0.15,
                face_rect=(250, 250, 500, 500),
                quality_score=0.85,
                detection_metadata={}
            )
        ]

        precision = system._calculate_landmark_precision(results)

        # Even with disagreement, floor should be 50%
        assert precision >= 0.5, f"Expected minimum floor of 50%, got {precision:.1%}"
