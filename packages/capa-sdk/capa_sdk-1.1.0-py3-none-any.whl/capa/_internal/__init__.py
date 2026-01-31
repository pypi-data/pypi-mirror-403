"""
CAPA Internal Components

This module contains internal implementation details that are not part of the public API.
These components may change without notice between versions.

Components:
- IntelligentLandmarkSystem: Multi-detector ensemble for landmarks
- AdaptiveQualitySystem: Dynamic quality control
- ContinuousImprovementSystem: Automated learning
- PoseValidationSystem: Pose assessment
- MeasurementCalibrator: Pixel-to-mm calibration
- DefendibleValidator: Performance standards
"""

# Intelligent Landmark System
from .intelligent_landmark_system import (
    IntelligentLandmarkSystem,
    EnsembleResult,
    LandmarkQuality,
    DetectorType,
    LandmarkResult,
    QualityMetrics as LandmarkQualityMetrics
)

# Adaptive Quality System
from .adaptive_quality_system import (
    AdaptiveQualitySystem,
    QualityMetrics,
    QualityLevel,
    AnalysisType
)

# Continuous Improvement System
from .continuous_improvement_system import (
    ContinuousImprovementSystem,
    PerformanceMetrics,
    LearningMode,
    ImprovementStrategy
)

# Pose Validation System
from .pose_validation_system import (
    PoseValidationSystem,
    PoseValidationResult,
    PoseCompatibility
)

# Measurement Calibrator
from .measurement_calibrator import (
    MeasurementCalibrator,
    CalibrationResult,
    CalibrationMethod
)

# Validation Standards
from .validation_standards import (
    DefendibleValidator,
    PerformanceGrade
)

# Warning Suppression Utilities
from .suppress_warnings import (
    configure_clean_environment,
    suppress_opencv_warnings,
    suppress_mediapipe_warnings
)

__all__ = [
    # Landmark System
    'IntelligentLandmarkSystem',
    'EnsembleResult',
    'LandmarkQuality',
    'DetectorType',
    'LandmarkResult',
    'LandmarkQualityMetrics',

    # Quality System
    'AdaptiveQualitySystem',
    'QualityMetrics',
    'QualityLevel',
    'AnalysisType',

    # Learning System
    'ContinuousImprovementSystem',
    'PerformanceMetrics',
    'LearningMode',
    'ImprovementStrategy',

    # Pose Validation
    'PoseValidationSystem',
    'PoseValidationResult',
    'PoseCompatibility',

    # Calibration
    'MeasurementCalibrator',
    'CalibrationResult',
    'CalibrationMethod',

    # Validation
    'DefendibleValidator',
    'PerformanceGrade',

    # Utilities
    'configure_clean_environment',
    'suppress_opencv_warnings',
    'suppress_mediapipe_warnings',
]
