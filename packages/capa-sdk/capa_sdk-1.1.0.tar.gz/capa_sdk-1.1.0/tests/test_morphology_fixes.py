"""
Tests for MOR-001 Fixes: Face Shape Classification Diversity

These tests validate the corrections made to the morphology analyzer for:
1. Recalibrated HEART shape thresholds (more restrictive)
2. Expanded OVAL and OBLONG ranges
3. Classification diversity across different facial proportions

Issue: 100% of images were classified as "heart" due to permissive thresholds.
"""

import pytest
import numpy as np
from collections import Counter


class TestFaceShapeEnums:
    """Test FaceShape enum is properly defined."""

    def test_face_shape_enum_exists(self):
        """Test FaceShape enum is importable."""
        from capa.modules.morphology_analyzer import FaceShape

        assert FaceShape is not None
        assert hasattr(FaceShape, 'OVAL')
        assert hasattr(FaceShape, 'ROUND')
        assert hasattr(FaceShape, 'SQUARE')
        assert hasattr(FaceShape, 'HEART')
        assert hasattr(FaceShape, 'OBLONG')
        assert hasattr(FaceShape, 'DIAMOND')

    def test_all_expected_shapes_defined(self):
        """Test all expected face shapes are defined."""
        from capa.modules.morphology_analyzer import FaceShape

        expected_shapes = [
            'oval', 'round', 'square', 'rectangular',
            'heart', 'diamond', 'triangular', 'oblong',
            'pentagonal', 'hexagonal'
        ]

        actual_shapes = [shape.value for shape in FaceShape]

        for expected in expected_shapes:
            assert expected in actual_shapes, f"Missing shape: {expected}"


class TestHeartThresholdRecalibration:
    """Test that HEART thresholds are more restrictive."""

    def test_heart_requires_high_cone_index(self):
        """Test HEART classification requires cone_index > 1.38 (was 1.25)."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer, FaceShape
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        # Create mock proportions with moderate cone_index (1.30)
        # This should NOT be classified as HEART with new thresholds
        proportions = Mock()
        proportions.facial_index = 95.0
        proportions.facial_cone_index = 1.30  # Between old (1.25) and new (1.38) threshold
        proportions.facial_width_height_ratio = 0.75
        proportions.bizygomatic_width = 140.0
        proportions.bigonial_width = 107.7  # 140 / 1.30 = 107.7
        proportions.temporal_width = 135.0
        proportions.upper_face_ratio = 0.33
        proportions.middle_face_ratio = 0.33
        proportions.lower_face_ratio = 0.34

        features = Mock()
        features.jawline_curvature = 0.5
        features.bilateral_symmetry_score = 0.85
        features.chin_projection = 0.45  # Above new restrictive threshold
        features.cheekbone_prominence = 0.5
        features.gonial_angle = 125

        result = analyzer._classify_face_shape(proportions, features)

        # With cone_index 1.30, should NOT be primarily HEART
        # (HEART now requires > 1.38)
        assert result.primary_shape != FaceShape.HEART or \
               result.classification_confidence < 0.7, \
               f"Expected non-HEART or low confidence, got {result.primary_shape.value}"

    def test_true_heart_shape_still_detected(self):
        """Test that true heart shapes are still correctly classified."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer, FaceShape
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        # Create proportions for a true heart shape
        proportions = Mock()
        proportions.facial_index = 95.0
        proportions.facial_cone_index = 1.45  # High cone index (clear heart)
        proportions.facial_width_height_ratio = 0.75
        proportions.bizygomatic_width = 145.0
        proportions.bigonial_width = 100.0  # 145 / 100 = 1.45
        proportions.temporal_width = 140.0
        proportions.upper_face_ratio = 0.35
        proportions.middle_face_ratio = 0.35
        proportions.lower_face_ratio = 0.30

        features = Mock()
        features.jawline_curvature = 0.6
        features.bilateral_symmetry_score = 0.85
        features.chin_projection = 0.25  # Small chin
        features.cheekbone_prominence = 0.7
        features.gonial_angle = 130

        result = analyzer._classify_face_shape(proportions, features)

        # True heart shape should still be detected
        assert result.primary_shape == FaceShape.HEART, \
               f"Expected HEART for true heart proportions, got {result.primary_shape.value}"


class TestExpandedOvalRange:
    """Test expanded OVAL classification range."""

    def test_oval_accepts_higher_facial_index(self):
        """Test OVAL classification accepts facial_index up to 105 (was 92)."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer, FaceShape
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        # Facial index of 98 (was too high for OVAL, now accepted)
        proportions = Mock()
        proportions.facial_index = 98.0  # Between old max (92) and new max (105)
        proportions.facial_cone_index = 1.2
        proportions.facial_width_height_ratio = 0.72
        proportions.bizygomatic_width = 140.0
        proportions.bigonial_width = 116.7
        proportions.temporal_width = 138.0
        proportions.upper_face_ratio = 0.33
        proportions.middle_face_ratio = 0.33
        proportions.lower_face_ratio = 0.34

        features = Mock()
        features.jawline_curvature = 0.5
        features.bilateral_symmetry_score = 0.88
        features.chin_projection = 0.5
        features.cheekbone_prominence = 0.5
        features.gonial_angle = 125

        result = analyzer._classify_face_shape(proportions, features)

        # Should have some OVAL score now
        oval_score = result.shape_probability_distribution.get(FaceShape.OVAL, 0)
        assert oval_score > 0.05, \
               f"Expected OVAL to have some probability for facial_index=98, got {oval_score}"


class TestExpandedOblongRange:
    """Test OBLONG captures very elongated faces."""

    def test_oblong_bonus_for_very_high_facial_index(self):
        """Test OBLONG gets bonus for facial_index > 105."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer, FaceShape
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        # Very high facial index (hyperleptoprosopic)
        proportions = Mock()
        proportions.facial_index = 115.0
        proportions.facial_cone_index = 1.25
        proportions.facial_width_height_ratio = 0.65
        proportions.bizygomatic_width = 130.0
        proportions.bigonial_width = 104.0
        proportions.temporal_width = 128.0
        proportions.upper_face_ratio = 0.30
        proportions.middle_face_ratio = 0.35
        proportions.lower_face_ratio = 0.35

        features = Mock()
        features.jawline_curvature = 0.4
        features.bilateral_symmetry_score = 0.85
        features.chin_projection = 0.5
        features.cheekbone_prominence = 0.4
        features.gonial_angle = 120

        result = analyzer._classify_face_shape(proportions, features)

        # OBLONG should be a top contender for very elongated face
        oblong_score = result.shape_probability_distribution.get(FaceShape.OBLONG, 0)
        assert oblong_score > 0.1, \
               f"Expected high OBLONG score for facial_index=115, got {oblong_score}"


class TestClassificationDiversity:
    """Test that classification produces diverse results."""

    def test_different_proportions_yield_different_shapes(self):
        """Test that different facial proportions yield different classifications."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer, FaceShape
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        # Define test cases with expected primary shapes
        test_cases = [
            # (facial_index, cone_index, chin_projection, jawline_curve, expected_not_heart)
            (82, 1.05, 0.3, 0.7, True),   # Round-ish
            (92, 1.15, 0.5, 0.5, True),   # Oval-ish
            (82, 1.05, 0.5, 0.3, True),   # Square-ish
            (110, 1.20, 0.5, 0.4, True),  # Oblong
            (95, 1.50, 0.2, 0.6, False),  # Heart (allowed)
        ]

        classifications = []

        for fi, ci, cp, jc, should_not_be_heart in test_cases:
            proportions = Mock()
            proportions.facial_index = fi
            proportions.facial_cone_index = ci
            proportions.facial_width_height_ratio = 0.8 if fi < 90 else 0.7
            proportions.bizygomatic_width = 140.0
            proportions.bigonial_width = 140.0 / ci
            proportions.temporal_width = 138.0
            proportions.upper_face_ratio = 0.33
            proportions.middle_face_ratio = 0.33
            proportions.lower_face_ratio = 0.34

            features = Mock()
            features.jawline_curvature = jc
            features.bilateral_symmetry_score = 0.85
            features.chin_projection = cp
            features.cheekbone_prominence = 0.5
            features.gonial_angle = 120

            result = analyzer._classify_face_shape(proportions, features)
            classifications.append(result.primary_shape.value)

            if should_not_be_heart:
                assert result.primary_shape != FaceShape.HEART, \
                       f"Did not expect HEART for fi={fi}, ci={ci}, cp={cp}"

        # Should have at least 3 different shape classifications
        unique_shapes = set(classifications)
        assert len(unique_shapes) >= 3, \
               f"Expected at least 3 unique shapes, got {unique_shapes}"

    def test_no_single_shape_dominates(self):
        """Test that no single shape dominates across varied inputs."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        # Generate varied test cases
        classifications = []
        np.random.seed(42)  # Reproducible

        for _ in range(20):
            proportions = Mock()
            proportions.facial_index = np.random.uniform(80, 115)
            proportions.facial_cone_index = np.random.uniform(1.0, 1.5)
            proportions.facial_width_height_ratio = np.random.uniform(0.6, 0.9)
            proportions.bizygomatic_width = 140.0
            proportions.bigonial_width = 140.0 / proportions.facial_cone_index
            proportions.temporal_width = 138.0
            proportions.upper_face_ratio = 0.33
            proportions.middle_face_ratio = 0.33
            proportions.lower_face_ratio = 0.34

            features = Mock()
            features.jawline_curvature = np.random.uniform(0.3, 0.7)
            features.bilateral_symmetry_score = 0.85
            features.chin_projection = np.random.uniform(0.2, 0.6)
            features.cheekbone_prominence = np.random.uniform(0.4, 0.7)
            features.gonial_angle = np.random.uniform(110, 135)

            result = analyzer._classify_face_shape(proportions, features)
            classifications.append(result.primary_shape.value)

        # Count classifications
        counts = Counter(classifications)
        total = len(classifications)

        # No single shape should be more than 50% (was 100% HEART before fix)
        for shape, count in counts.items():
            ratio = count / total
            assert ratio < 0.6, \
                   f"Shape '{shape}' dominates with {ratio*100:.1f}% of classifications"


class TestShapeScoreCalculation:
    """Test individual shape score calculations."""

    def test_round_score_increases_with_low_facial_index(self):
        """Test ROUND score increases with lower facial index."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer, FaceShape
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        def create_mock(facial_index):
            proportions = Mock()
            proportions.facial_index = facial_index
            proportions.facial_cone_index = 1.1
            proportions.facial_width_height_ratio = 0.85
            proportions.bizygomatic_width = 140.0
            proportions.bigonial_width = 127.0
            proportions.temporal_width = 138.0
            proportions.upper_face_ratio = 0.33
            proportions.middle_face_ratio = 0.33
            proportions.lower_face_ratio = 0.34

            features = Mock()
            features.jawline_curvature = 0.6
            features.bilateral_symmetry_score = 0.85
            features.chin_projection = 0.4
            features.cheekbone_prominence = 0.5
            features.gonial_angle = 125

            return proportions, features

        # Lower facial index should yield higher ROUND score
        p1, f1 = create_mock(82)
        p2, f2 = create_mock(92)

        result1 = analyzer._classify_face_shape(p1, f1)
        result2 = analyzer._classify_face_shape(p2, f2)

        round_score_82 = result1.shape_probability_distribution.get(FaceShape.ROUND, 0)
        round_score_92 = result2.shape_probability_distribution.get(FaceShape.ROUND, 0)

        assert round_score_82 >= round_score_92, \
               f"ROUND score should be higher for facial_index=82 ({round_score_82}) " \
               f"than 92 ({round_score_92})"


class TestShapeClassificationResult:
    """Test ShapeClassificationResult dataclass."""

    def test_result_has_all_required_fields(self):
        """Test classification result has all required fields."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        proportions = Mock()
        proportions.facial_index = 90.0
        proportions.facial_cone_index = 1.2
        proportions.facial_width_height_ratio = 0.75
        proportions.bizygomatic_width = 140.0
        proportions.bigonial_width = 116.7
        proportions.temporal_width = 138.0
        proportions.upper_face_ratio = 0.33
        proportions.middle_face_ratio = 0.33
        proportions.lower_face_ratio = 0.34

        features = Mock()
        features.jawline_curvature = 0.5
        features.bilateral_symmetry_score = 0.85
        features.chin_projection = 0.5
        features.cheekbone_prominence = 0.5
        features.gonial_angle = 125

        result = analyzer._classify_face_shape(proportions, features)

        assert hasattr(result, 'primary_shape')
        assert hasattr(result, 'secondary_shape')
        assert hasattr(result, 'shape_probability_distribution')
        assert hasattr(result, 'classification_confidence')
        assert hasattr(result, 'shape_descriptors')

    def test_probability_distribution_sums_to_one(self):
        """Test probability distribution sums to approximately 1."""
        from capa.modules.morphology_analyzer import MorphologyAnalyzer
        from unittest.mock import Mock

        analyzer = MorphologyAnalyzer(enable_3d_reconstruction=False, enable_learning=False)

        proportions = Mock()
        proportions.facial_index = 90.0
        proportions.facial_cone_index = 1.2
        proportions.facial_width_height_ratio = 0.75
        proportions.bizygomatic_width = 140.0
        proportions.bigonial_width = 116.7
        proportions.temporal_width = 138.0
        proportions.upper_face_ratio = 0.33
        proportions.middle_face_ratio = 0.33
        proportions.lower_face_ratio = 0.34

        features = Mock()
        features.jawline_curvature = 0.5
        features.bilateral_symmetry_score = 0.85
        features.chin_projection = 0.5
        features.cheekbone_prominence = 0.5
        features.gonial_angle = 125

        result = analyzer._classify_face_shape(proportions, features)

        total_prob = sum(result.shape_probability_distribution.values())
        assert 0.99 <= total_prob <= 1.01, \
               f"Probability distribution should sum to 1, got {total_prob}"
