"""
CAPA - Craniofacial Analysis & Prediction Architecture

A cutting-edge SDK for advanced craniofacial analysis and psychological prediction
based on 15+ peer-reviewed scientific research papers.

Features:
- CoreAnalyzer: Ultimate orchestrator for comprehensive analysis
- MultiAngleAnalyzer: Multi-angle analysis for same individual
- Scientific Modules: WD, Forehead, and Morphology analyzers
- Unified Support Systems: Intelligent landmarks, quality control, learning
- Neoclassical Canons: Classical facial proportion analysis

Quick Start:
    from capa import CoreAnalyzer

    analyzer = CoreAnalyzer()
    result = analyzer.analyze_image('image.jpg')
    print(result.to_report())
    analyzer.shutdown()

Version: 1.1.0
"""

import logging

from ._version import __version__, __version_info__

logger = logging.getLogger(__name__)

# ============================================================================
# CAPA PUBLIC API
# ============================================================================

# Analyzers - Primary recommendation
from .analyzers.core_analyzer import (
    CoreAnalyzer,
    ComprehensiveAnalysisResult,
    AnalysisConfiguration,
    AnalysisMode,
    ResultFormat,
    ProcessingMetadata
)

from .analyzers.multi_angle_analyzer import (
    MultiAngleAnalyzer,
    MultiAngleResult,
    AngleSpecification
)

from .analyzers.results_integrator import (
    ResultsIntegrator,
    IntegratedAnalysisResult,
    PredictionResult,
    EvidenceLevel
)

# Scientific Modules (public API)
from .modules.wd_analyzer import (
    WDAnalyzer,
    WDResult,
    WDPersonalityProfile,
    WDClassification,
    WDLandmarkQuality
)

from .modules.forehead_analyzer import (
    ForeheadAnalyzer,
    ForeheadResult,
    ForeheadGeometry,
    NeuroscienceCorrelations,
    ImpulsivenessProfile,
    ImpulsivenessLevel,
    NeurologicalRisk
)

from .modules.morphology_analyzer import (
    MorphologyAnalyzer,
    MorphologyResult,
    FacialProportions,
    GeometricFeatures,
    ShapeClassificationResult,
    FaceShape,
    MorphologyLandmarkQuality
)

# Neoclassical Analysis
try:
    from .modules.neoclassical_canons import (
        NeoclassicalCanonsAnalyzer,
        NeoclassicalAnalysisResult
    )
    NEOCLASSICAL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Neoclassical Canons Analyzer not available: {e}")
    NeoclassicalCanonsAnalyzer = None
    NeoclassicalAnalysisResult = None
    NEOCLASSICAL_AVAILABLE = False

# ============================================================================
# PUBLIC API EXPORTS
# ============================================================================

__all__ = [
    # Version
    '__version__',
    '__version_info__',

    # Core Analyzer (Primary Recommendation)
    'CoreAnalyzer',
    'ComprehensiveAnalysisResult',
    'AnalysisConfiguration',
    'AnalysisMode',
    'ResultFormat',
    'ProcessingMetadata',

    # Multi-Angle Analyzer
    'MultiAngleAnalyzer',
    'MultiAngleResult',
    'AngleSpecification',

    # Results Integrator
    'ResultsIntegrator',
    'IntegratedAnalysisResult',
    'PredictionResult',
    'EvidenceLevel',

    # Scientific Modules
    'WDAnalyzer',
    'WDResult',
    'WDPersonalityProfile',
    'WDClassification',
    'WDLandmarkQuality',

    'ForeheadAnalyzer',
    'ForeheadResult',
    'ForeheadGeometry',
    'NeuroscienceCorrelations',
    'ImpulsivenessProfile',
    'ImpulsivenessLevel',
    'NeurologicalRisk',

    'MorphologyAnalyzer',
    'MorphologyResult',
    'FacialProportions',
    'GeometricFeatures',
    'ShapeClassificationResult',
    'FaceShape',
    'MorphologyLandmarkQuality',
]

# Add Neoclassical components if available
if NEOCLASSICAL_AVAILABLE:
    __all__.extend([
        'NeoclassicalCanonsAnalyzer',
        'NeoclassicalAnalysisResult'
    ])

# ============================================================================
# VERSION AND STATUS INFORMATION
# ============================================================================

def get_version_info():
    """Get CAPA version and feature information"""
    return {
        'version': __version__,
        'status': 'Production Ready',
        'architecture': 'SDK',
        'scientific_papers': 15,
        'primary_analyzer': 'CoreAnalyzer',
        'features': [
            'Comprehensive craniofacial analysis',
            'Multi-angle individual analysis',
            'Intelligent multi-detector landmarks',
            'Advanced personality profiling',
            'Neuroscience correlations',
            'Adaptive quality control',
            'Continuous learning system',
            'Parallel processing optimization',
            'Cross-module validation'
        ],
        'analysis_modes': [mode.value for mode in AnalysisMode],
        'supported_angles': ['frontal', 'lateral_left', 'lateral_right', 'profile', 'semi_frontal'],
        'neoclassical_available': NEOCLASSICAL_AVAILABLE
    }

def show_status():
    """Show CAPA status and capabilities"""
    info = get_version_info()

    print("\n" + "="*70)
    print("CAPA - Craniofacial Analysis & Prediction Architecture")
    print("="*70)
    print(f"Version: {info['version']} ({info['status']})")
    print(f"Architecture: {info['architecture']}")
    print(f"Scientific Foundation: {info['scientific_papers']} peer-reviewed papers")
    print(f"Neoclassical Analysis: {'Available' if info['neoclassical_available'] else 'Not Available'}")

    print("\nPRIMARY RECOMMENDATION: CoreAnalyzer")
    print("Features:")
    for feature in info['features']:
        print(f"  - {feature}")

    print(f"\nAnalysis Modes: {', '.join(info['analysis_modes'])}")
    print(f"Supported Angles: {', '.join(info['supported_angles'])}")

    print("\nQuick Start:")
    print("  from capa import CoreAnalyzer")
    print("  analyzer = CoreAnalyzer()")
    print("  result = analyzer.analyze_image('image.jpg')")
    print("  print(result.to_report())")
    print("  analyzer.shutdown()")

    print("\nMulti-Angle Analysis:")
    print("  from capa import MultiAngleAnalyzer")
    print("  analyzer = MultiAngleAnalyzer()")
    print("  result = analyzer.analyze_from_paths(['front.jpg', 'side.jpg'], 'person1')")
    print("  analyzer.shutdown()")

    print("\n" + "="*70)

def show_scientific_papers():
    """Show integrated scientific papers"""
    papers = [
        "Bizygomatic Width and Personality Traits of the Relational Field",
        "The Slant of the Forehead as a Craniofacial Feature of Impulsiveness",
        "Correlation between Impulsiveness, Cortical Thickness and Slant of The Forehead",
        "Association between self reported impulsiveness and gray matter volume",
        "The validity of eight neoclassical facial canons in the Turkish adults",
        "Evaluation of Face Shape in Turkish Individuals",
        "Accuracy and precision of a 3D anthropometric facial analysis",
        "Determinacion del Indice Facial Total y Cono Facial",
        "Assessing Facial Beauty of Sabah Ethnic Groups Using Farkas Principles",
        "Frontonasal dysmorphology in bipolar disorder by 3D laser surface imaging",
        "And 5+ additional morphological and neuroscience research papers"
    ]

    print("\n" + "="*80)
    print("CAPA - Integrated Scientific Papers")
    print("="*80)
    print("All papers are fully integrated within the scientific modules:")
    print()

    for i, paper in enumerate(papers, 1):
        print(f"{i:2d}. {paper}")

    print("\nIntegration Status:")
    print("  - WDAnalyzer: Papers 1, 4-6 + demographic studies")
    print("  - ForeheadAnalyzer: Papers 2-4 + neuroscience correlations")
    print("  - MorphologyAnalyzer: Papers 5-11 + 3D reconstruction")
    print("  - NeoclassicalCanonsAnalyzer: Papers 5, 8-9 + classical proportions")
    print("\n" + "="*80)

# Export utility functions
__all__.extend(['get_version_info', 'show_status', 'show_scientific_papers'])

logger.info("CAPA SDK initialized successfully")
