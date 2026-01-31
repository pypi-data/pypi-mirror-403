"""
CAPA Modules - Scientific Analysis Components

This package contains the scientific analysis modules that integrate
detection methods, quality assessment, and continuous learning capabilities.

Modules:
- WDAnalyzer: Bizygomatic width analysis with personality correlations
- ForeheadAnalyzer: Forehead analysis with neuroscience correlations
- MorphologyAnalyzer: Facial morphology with 3D reconstruction
- NeoclassicalCanonsAnalyzer: Classical facial proportion analysis

Version: 1.1
"""

from .wd_analyzer import (
    WDAnalyzer,
    WDResult,
    WDPersonalityProfile,
    WDClassification,
    WDLandmarkQuality
)

from .forehead_analyzer import (
    ForeheadAnalyzer,
    ForeheadResult,
    ForeheadGeometry,
    NeuroscienceCorrelations,
    ImpulsivenessProfile,
    ImpulsivenessLevel,
    NeurologicalRisk,
    ForeheadLandmarkQuality
)

from .morphology_analyzer import (
    MorphologyAnalyzer,
    MorphologyResult,
    FacialProportions,
    GeometricFeatures,
    ThreeDReconstruction,
    ShapeClassificationResult,
    FaceShape,
    MorphologyConfidence,
    MorphologyLandmarkQuality
)

from .neoclassical_canons import (
    NeoclassicalCanonsAnalyzer,
    NeoclassicalAnalysisResult
)

__all__ = [
    # WD Analysis
    'WDAnalyzer',
    'WDResult',
    'WDPersonalityProfile',
    'WDClassification',
    'WDLandmarkQuality',

    # Forehead Analysis
    'ForeheadAnalyzer',
    'ForeheadResult',
    'ForeheadGeometry',
    'NeuroscienceCorrelations',
    'ImpulsivenessProfile',
    'ImpulsivenessLevel',
    'NeurologicalRisk',
    'ForeheadLandmarkQuality',

    # Morphology Analysis
    'MorphologyAnalyzer',
    'MorphologyResult',
    'FacialProportions',
    'GeometricFeatures',
    'ThreeDReconstruction',
    'ShapeClassificationResult',
    'FaceShape',
    'MorphologyConfidence',
    'MorphologyLandmarkQuality',

    # Neoclassical Canons
    'NeoclassicalCanonsAnalyzer',
    'NeoclassicalAnalysisResult'
]

# Version information
__version__ = '1.1.0'
