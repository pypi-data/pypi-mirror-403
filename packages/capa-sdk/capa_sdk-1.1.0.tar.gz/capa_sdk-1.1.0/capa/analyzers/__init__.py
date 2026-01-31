"""
Analyzers - CAPA (Craniofacial Analysis & Prediction Architecture)

This package contains the analysis orchestrators that coordinate all scientific
modules and provide unified, comprehensive analysis capabilities.

Components:
- CoreAnalyzer: Main orchestrator for comprehensive facial analysis
- MultiAngleAnalyzer: Multi-angle analysis for same individual
- ResultsIntegrator: Combines results from multiple analysis modules

Version: 1.1
"""

from .core_analyzer import (
    CoreAnalyzer,
    ComprehensiveAnalysisResult,
    AnalysisConfiguration,
    AnalysisMode,
    ResultFormat,
    ProcessingMetadata
)

from .multi_angle_analyzer import (
    MultiAngleAnalyzer,
    MultiAngleResult,
    AngleSpecification
)

from .results_integrator import (
    ResultsIntegrator,
    IntegratedAnalysisResult,
    PredictionResult,
    EvidenceLevel
)

__all__ = [
    # Core Analyzer
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
    'EvidenceLevel'
]

# Version information
__version__ = '1.1.0'
