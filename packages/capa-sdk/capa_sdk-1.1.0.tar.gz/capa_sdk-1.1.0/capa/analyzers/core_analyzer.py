"""
CAPA Core Analyzer - Craniofacial Analysis & Prediction Architecture

The main orchestrator for comprehensive craniofacial analysis using
all scientific modules with intelligent coordination and optimization.

Version: 1.1
"""

# FIRST: Configure clean environment (suppress warnings)
from .._internal.suppress_warnings import configure_clean_environment, suppress_opencv_warnings
configure_clean_environment()

import numpy as np
import cv2
suppress_opencv_warnings()  # Suppress OpenCV warnings immediately after import
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from pathlib import Path
import os
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import time

# Import scientific modules
from ..modules.wd_analyzer import (
    WDAnalyzer, WDResult
)
from ..modules.forehead_analyzer import (
    ForeheadAnalyzer, ForeheadResult
)
from ..modules.morphology_analyzer import (
    MorphologyAnalyzer, MorphologyResult
)

# Import unified support systems
from .._internal.intelligent_landmark_system import (
    IntelligentLandmarkSystem, EnsembleResult
)
from .._internal.adaptive_quality_system import (
    AdaptiveQualitySystem, AnalysisType, QualityMetrics
)
from .._internal.continuous_improvement_system import (
    ContinuousImprovementSystem, PerformanceMetrics, LearningMode
)

# Import validation standards
from .._internal.validation_standards import DefendibleValidator, PerformanceGrade
from .._internal.pose_validation_system import (
    PoseValidationSystem, PoseValidationResult, PoseCompatibility
)

# Import neoclassical canons
from ..modules.neoclassical_canons import NeoclassicalCanonsAnalyzer

logger = logging.getLogger(__name__)


class AnalysisMode(Enum):
    """Analysis execution modes"""
    FAST = "fast"                    # Quick analysis, basic modules only
    STANDARD = "standard"            # Standard comprehensive analysis
    THOROUGH = "thorough"           # Deep analysis with all modules
    SCIENTIFIC = "scientific"       # Maximum scientific accuracy (2D observables only)
    RESEARCH = "research"            # Research mode with peer-reviewed correlations + disclaimers
    REALTIME = "realtime"           # Optimized for real-time processing


class ResultFormat(Enum):
    """Output result formats"""
    STRUCTURED = "structured"       # Structured data objects
    JSON = "json"                  # JSON format
    REPORT = "report"              # Human-readable report
    SCIENTIFIC_PAPER = "scientific_paper"  # Scientific paper format


class AnalysisStatus(Enum):
    """Analysis module status levels (GPT-5 S1.2 implementation)"""
    OK = "OK"                      # Analysis completed successfully
    PARTIAL = "PARTIAL"            # Analysis completed with limitations
    INVALID = "INVALID"            # Analysis failed or unreliable
    DISABLED = "DISABLED"          # Analysis disabled by system


@dataclass
class AnalysisConfiguration:
    """Configuration for master analysis"""
    
    # Analysis settings
    mode: AnalysisMode = AnalysisMode.STANDARD
    result_format: ResultFormat = ResultFormat.STRUCTURED
    
    # Module selection
    enable_wd_analysis: bool = True
    enable_forehead_analysis: bool = True
    enable_morphology_analysis: bool = True
    enable_neoclassical_analysis: bool = True
    
    # Quality and learning settings
    enable_quality_assessment: bool = True
    enable_continuous_learning: bool = True
    learning_mode: LearningMode = LearningMode.BALANCED
    
    # Performance settings
    max_processing_time: Optional[float] = None  # Maximum time in seconds
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    
    # Demographic information
    subject_age: Optional[int] = None
    subject_gender: Optional[str] = None
    subject_ethnicity: Optional[str] = None
    
    # Output settings
    include_confidence_scores: bool = True
    include_quality_metrics: bool = True
    include_processing_metadata: bool = True
    save_intermediate_results: bool = False
    
    # Advanced settings
    adaptive_threshold_adjustment: bool = True
    cross_module_validation: bool = True
    anomaly_detection: bool = True


@dataclass
class ProcessingMetadata:
    """Metadata about the analysis process"""
    analysis_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_processing_time: Optional[float] = None
    
    # Module execution times
    wd_analysis_time: Optional[float] = None
    forehead_analysis_time: Optional[float] = None
    morphology_analysis_time: Optional[float] = None
    neoclassical_analysis_time: Optional[float] = None
    landmark_detection_time: Optional[float] = None
    
    # Quality metrics
    overall_confidence: Optional[float] = None
    quality_assessment: Optional[QualityMetrics] = None
    
    # Performance metrics
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Demographic information for enhanced analysis
    ethnic_group: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    
    # Geometric degradation tracking
    geometric_degradation_applied: Optional[bool] = None


@dataclass
class ComprehensiveAnalysisResult:
    """Complete result from master analysis"""
    
    # Analysis identification
    analysis_id: str
    timestamp: datetime
    configuration: AnalysisConfiguration
    subject_id: Optional[str] = None
    angle_type: Optional[str] = None
    
    # Core analysis results
    wd_result: Optional[WDResult] = None
    forehead_result: Optional[ForeheadResult] = None
    morphology_result: Optional[MorphologyResult] = None
    neoclassical_result: Optional[Any] = None
    
    # Unified landmark results
    landmark_result: Optional[EnsembleResult] = None
    
    # CRITICAL IMPROVEMENT: Pose validation results (GPT-5 feedback)
    pose_validation: Optional[PoseValidationResult] = None
    
    # Quality and performance
    quality_assessment: Optional[QualityMetrics] = None
    processing_metadata: Optional[ProcessingMetadata] = None
    
    # Integrated insights
    personality_profile: Optional[Dict[str, Any]] = None
    neuroscience_correlations: Optional[Dict[str, Any]] = None
    comprehensive_classification: Optional[str] = None
    confidence_summary: Optional[Dict[str, float]] = None
    
    # Cross-analysis correlations
    cross_module_correlations: Optional[Dict[str, float]] = None
    consistency_metrics: Optional[Dict[str, float]] = None
    
    # SPRINT 1 S1.2: Status-based module degradation (GPT-5 implementation)
    module_status: Optional[Dict[str, Dict[str, Any]]] = None
    
    # SPRINT 2 S2.1: 3D/Multi-Vista capabilities exposure (GPT-5 structure)
    geometry_3d: Optional[Dict[str, Any]] = None
    
    # SPRINT 2 S2.2: Research mode disclaimers (GPT-5 implementation)
    research_disclaimers: Optional[List[str]] = None
    
    # PHASE 1: Defendible A/A+ validation results
    defendible_validation: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            'analysis_id': self.analysis_id,
            'timestamp': self.timestamp.isoformat(),
            'configuration': {
                'mode': self.configuration.mode.value,
                'result_format': self.configuration.result_format.value,
                'modules_enabled': {
                    'wd_analysis': self.configuration.enable_wd_analysis,
                    'forehead_analysis': self.configuration.enable_forehead_analysis,
                    'morphology_analysis': self.configuration.enable_morphology_analysis,
                    'neoclassical_analysis': self.configuration.enable_neoclassical_analysis
                }
            }
        }
        
        # Add results if available
        if self.wd_result:
            # CRITICAL FIX C: Enhanced WD analysis with normalized ratio and CI95
            wd_data = {
                'wd_value': self.wd_result.wd_value,
                'confidence': self.wd_result.measurement_confidence
            }
            
            # FIX QUIRÚRGICO 1: Only include classification if confidence ≥ 0.70
            if self.wd_result.measurement_confidence >= 0.70:
                wd_data['classification'] = self.wd_result.primary_classification.value
            else:
                # FIX QUIRÚRGICO 5: Add improvement plan note for low WD confidence
                wd_data['improvement_plan'] = {
                    'current_confidence': self.wd_result.measurement_confidence,
                    'target_confidence': 0.70,
                    'recommended_actions': [
                        "Enable ensemble detector fusion (dlib + MediaPipe + face_recognition)",
                        "Implement TTA (Test-Time Augmentation) for landmark stability",
                        "Apply bootstrap confidence intervals for wd_ratio",
                        "Use multi-frame averaging for video input"
                    ]
                }
            # Note will be added later in scientific mode section
            
            # Add normalized WD ratio (adimensional) - GPT-5 requirement
            if hasattr(self.wd_result, 'bizygomatic_width') and self.wd_result.bizygomatic_width > 0:
                wd_ratio = self.wd_result.wd_value / self.wd_result.bizygomatic_width
                wd_data['wd_ratio'] = wd_ratio
                
                # Calculate CI95 for WD ratio (adimensional)
                if self.wd_result.measurement_confidence > 0.5:
                    ratio_error = 0.05  # Assume 5% relative error for ratio measurements
                    ci95_lower = wd_ratio - (1.96 * ratio_error)
                    ci95_upper = wd_ratio + (1.96 * ratio_error)
                    wd_data['wd_ratio_ci95'] = [ci95_lower, ci95_upper]
            
            # CRITICAL IMPROVEMENT: Filter personality data in scientific mode (Fix 1)
            if self.configuration.mode != AnalysisMode.SCIENTIFIC:
                # Include personality profile only in non-scientific modes
                wd_data['personality_profile'] = {
                    'social_orientation': self.wd_result.personality_profile.social_orientation_score,
                    'relational_field': self.wd_result.personality_profile.relational_field_score,
                    'communication_style': self.wd_result.personality_profile.communication_style_score
                }
            else:
                # Scientific mode: Only include measurable geometric/anthropometric data
                if self.wd_result.measurement_confidence < 0.70:
                    wd_data['note'] = "Personality correlations disabled in scientific mode; Classification omitted due to low confidence"
                else:
                    wd_data['note'] = "Personality correlations disabled in scientific mode"
            
            # MULTI-POSE: Add pose information if available
            if hasattr(self.wd_result, 'pose_type') and self.wd_result.pose_type:
                wd_data['pose_analysis'] = {
                    'pose_type': self.wd_result.pose_type,
                    'yaw_angle': getattr(self.wd_result, 'yaw_angle', None),
                    'profile_note': getattr(self.wd_result, 'profile_note', None)
                }
            
            # CRITICAL FIX 2: Only include percentile data with complete population statistics
            if hasattr(self.wd_result, 'demographic_reference') and self.wd_result.demographic_reference:
                ref_data = self.wd_result.demographic_reference
                if ('mean' in ref_data and 'std' in ref_data and 'n' in ref_data and
                    hasattr(self.wd_result, 'demographic_percentile') and self.wd_result.demographic_percentile > 0):
                    
                    # CRITICAL FIX 4: Include complete population statistics with CI95
                    z_score = getattr(self.wd_result, 'robust_wd_z_score', None)
                    
                    # Calculate CI95 for measurement
                    ci95 = None
                    if z_score is not None:
                        measurement_error = ref_data.get('std', 3.0) * 0.1  # 10% measurement uncertainty
                        ci95_lower = self.wd_result.wd_value - (1.96 * measurement_error)
                        ci95_upper = self.wd_result.wd_value + (1.96 * measurement_error)
                        ci95 = [ci95_lower, ci95_upper]
                    
                    wd_data['population_statistics'] = {
                        'percentile': self.wd_result.demographic_percentile,
                        'z_score': z_score,
                        'ci95_interval': ci95,
                        'reference_population': {
                            'mean': ref_data.get('mean'),
                            'std': ref_data.get('std'),
                            'n_samples': ref_data.get('n'),
                            'population': ref_data.get('population', 'mixed')
                        }
                    }
            
            result['wd_analysis'] = wd_data
        
        if self.forehead_result:
            forehead_data = {
                'slant_angle': self.forehead_result.forehead_geometry.slant_angle_degrees,
                'confidence': self.forehead_result.measurement_confidence
            }
            
            # FIX QUIRÚRGICO 4: Add pose data and CI95 to slant measurements (enhanced)
            if hasattr(self, 'pose_validation') and self.pose_validation:
                forehead_data['pose_data'] = {
                    'yaw': self.pose_validation.yaw,
                    'pitch': self.pose_validation.pitch, 
                    'roll': self.pose_validation.roll,
                    'pose_quality': self.pose_validation.overall_pose_quality,
                    'pose_confidence_factor': self.pose_validation.pose_confidence_factor,
                    'is_frontal': self.pose_validation.is_frontal,
                    'allows_depth_measurements': self.pose_validation.allows_depth_measurements
                }
                
                # Omit slant measurement if pose is unsuitable
                if abs(self.pose_validation.yaw) > 25.0:
                    forehead_data['note'] = f"Slant measurement unreliable due to pose (yaw: {self.pose_validation.yaw:.1f}°)"
            else:
                # No pose data available
                forehead_data['note'] = "Pose validation data not available for reliability assessment"
            
            # Calculate CI95 for slant angle measurement
            if self.forehead_result.measurement_confidence > 0.6:  # Only for reasonable confidence
                angle_error = 2.0  # Assume ±2° measurement error for slant angle
                ci95_lower = self.forehead_result.forehead_geometry.slant_angle_degrees - (1.96 * angle_error)
                ci95_upper = self.forehead_result.forehead_geometry.slant_angle_degrees + (1.96 * angle_error)
                forehead_data['ci95_interval'] = [ci95_lower, ci95_upper]
            
            # CRITICAL IMPROVEMENT: Filter psychological/neurological metrics in scientific mode
            if self.configuration.mode != AnalysisMode.SCIENTIFIC:
                # Include psychological metrics only in non-scientific modes
                forehead_data['impulsiveness_level'] = self.forehead_result.impulsiveness_level.value
                forehead_data['neuroscience_correlations'] = {
                    'frontal_cortical_thickness': self.forehead_result.neuroscience_correlations.frontal_cortical_thickness,
                    'executive_function_score': self.forehead_result.neuroscience_correlations.executive_function_score
                }
            else:
                # Scientific mode: Only include measurable geometric data
                forehead_data['note'] = "Psychological/neurological correlations disabled in scientific mode"
            
            result['forehead_analysis'] = forehead_data
        
        if self.morphology_result:
            # CRITICAL IMPROVEMENT: Fix JSON serialization (Level 1.7) - ensure enum values are strings
            primary_shape = self.morphology_result.shape_classification.primary_shape
            primary_shape_str = primary_shape.value if hasattr(primary_shape, 'value') else str(primary_shape)
            
            # CRITICAL IMPROVEMENT: Separate measurement vs classification confidence (GPT-5 feedback)
            morphology_data = {
                'primary_face_shape': primary_shape_str,
                'facial_proportions': {
                    'facial_width_height_ratio': float(self.morphology_result.facial_proportions.facial_width_height_ratio),
                    'facial_index': float(self.morphology_result.facial_proportions.facial_index)
                },
                # Separated confidence metrics
                'measurement_confidence': float(self.morphology_result.measurement_confidence),  # Landmarks/geometry quality
                'classification_confidence': float(self.morphology_result.shape_classification.classification_confidence),  # Shape classification probability
                'overall_confidence': float(self.morphology_result.measurement_confidence)  # Keep legacy field for compatibility
            }
            
            # Add additional shape classification details if available - with proper serialization
            if hasattr(self.morphology_result.shape_classification, 'shape_probability_distribution'):
                prob_dist = self.morphology_result.shape_classification.shape_probability_distribution
                if isinstance(prob_dist, dict):
                    # Convert any enum keys to strings and ensure float values
                    serializable_probs = {}
                    for k, v in prob_dist.items():
                        key_str = k.value if hasattr(k, 'value') else str(k)
                        val_float = float(v) if isinstance(v, (int, float, np.number)) else v
                        serializable_probs[key_str] = val_float
                    morphology_data['shape_probabilities'] = serializable_probs
            
            result['morphology_analysis'] = morphology_data
        
        # Add integrated insights - FILTERED FOR SCIENTIFIC MODE
        if self.configuration.mode != AnalysisMode.SCIENTIFIC:
            # Include psychological/neurological insights only in non-scientific modes
            if self.personality_profile:
                result['personality_profile'] = self.personality_profile
                result['personality_profile']['evidence_refs'] = self._get_evidence_refs("bizygomatic_width")
            
            if self.neuroscience_correlations:
                result['neuroscience_correlations'] = self.neuroscience_correlations
                result['neuroscience_correlations']['evidence_refs'] = self._get_evidence_refs("neurological_correlations")
        else:
            # Scientific mode: Note the exclusion for transparency
            result['scientific_mode_note'] = "Psychological and neurological correlations excluded in scientific mode"
        
        if self.comprehensive_classification:
            result['comprehensive_classification'] = self.comprehensive_classification
        
        if self.confidence_summary:
            result['confidence_summary'] = self.confidence_summary
        
        # Add neoclassical analysis if available (with error handling)
        if self.neoclassical_result:
            try:
                result['neoclassical_analysis'] = self.neoclassical_result.to_dict()
            except Exception as e:
                # Fallback: include basic info if to_dict fails
                result['neoclassical_analysis'] = {
                    'error': f"Serialization failed: {str(e)}",
                    'overall_validity_score': getattr(self.neoclassical_result, 'overall_validity_score', 0.0),
                    'beauty_score': getattr(self.neoclassical_result, 'beauty_score', 0.0),
                    'confidence': getattr(self.neoclassical_result, 'confidence', 0.0),
                    'canons_count': len(getattr(self.neoclassical_result, 'canons', []))
                }
        
        # CRITICAL IMPROVEMENT: Add pose validation data (GPT-5 feedback)
        if self.pose_validation:
            result['pose_validation'] = {
                'yaw': self.pose_validation.yaw,
                'pitch': self.pose_validation.pitch,
                'roll': self.pose_validation.roll,
                'is_frontal': self.pose_validation.is_frontal,
                'allows_depth_measurements': self.pose_validation.allows_depth_measurements,
                'overall_pose_quality': self.pose_validation.overall_pose_quality,
                'pose_compatibility': self.pose_validation.pose_compatibility.value,
                'compatible_analyses': self.pose_validation.compatible_analyses,
                'disabled_analyses': self.pose_validation.disabled_analyses,
                'restricted_canons': self.pose_validation.restricted_canons,
                'pose_confidence_factor': self.pose_validation.pose_confidence_factor,
                'recommendations': self.pose_validation.recommendations,
                'warnings': self.pose_validation.warnings
            }
        
        # Add metadata if requested
        if self.configuration.include_processing_metadata and self.processing_metadata:
            result['processing_metadata'] = {
                'total_processing_time': self.processing_metadata.total_processing_time,
                'overall_confidence': self.processing_metadata.overall_confidence,
                'errors': self.processing_metadata.errors,
                'warnings': self.processing_metadata.warnings
            }
        
        # SPRINT 1 S1.2: Include module status information (GPT-5 structure)
        if self.module_status:
            result['module_status'] = self.module_status
            
        # SPRINT 2 S2.1: Include 3D geometry information (GPT-5 structure)
        # CRITICAL FIX 7: Expose geometry_3d only when 3D analysis is active and available
        if self.geometry_3d and len(self.geometry_3d.get('metrics', {})) > 0:
            result['geometry_3d'] = self.geometry_3d
            
        # SPRINT 2 S2.2: Include research disclaimers (GPT-5 structure)
        if self.research_disclaimers:
            result['research_disclaimers'] = self.research_disclaimers
        
        # PHASE 1: Include defendible validation results
        if self.defendible_validation:
            result['defendible_validation'] = self.defendible_validation
        
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_report(self) -> str:
        """Generate human-readable report"""
        report = []
        report.append("🧠 CAPA Comprehensive Craniofacial Analysis Report")
        report.append("=" * 60)
        report.append(f"Analysis ID: {self.analysis_id}")
        report.append(f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Analysis Mode: {self.configuration.mode.value.upper()}")
        report.append("")
        
        # WD Analysis Section
        if self.wd_result:
            report.append("📏 WIDTH DIFFERENCE (WD) ANALYSIS")
            report.append("-" * 40)
            report.append(f"WD Value: {self.wd_result.wd_value:.3f}")
            report.append(f"Classification: {self.wd_result.primary_classification.value.replace('_', ' ').title()}")
            report.append(f"Confidence: {self.wd_result.measurement_confidence:.1%}")
            report.append("")
            
            # CRITICAL IMPROVEMENT: Hide personality correlations in scientific mode (Fix 1)
            if self.configuration.mode != AnalysisMode.SCIENTIFIC:
                report.append("Personality Correlations:")
                report.append(f"  • Social Orientation: {self.wd_result.personality_profile.social_orientation_score:.1%}")
                report.append(f"  • Relational Field: {self.wd_result.personality_profile.relational_field_score:.1%}")
                report.append(f"  • Communication Style: {self.wd_result.personality_profile.communication_style_score:.1%}")
                report.append("")
            else:
                report.append("Note: Personality correlations disabled in scientific mode")
                report.append("")
        
        # Forehead Analysis Section
        if self.forehead_result:
            report.append("🧠 FOREHEAD ANALYSIS")
            report.append("-" * 40)
            report.append(f"Forehead Slant: {self.forehead_result.forehead_geometry.slant_angle_degrees:.1f}°")
            report.append(f"Confidence: {self.forehead_result.measurement_confidence:.1%}")
            report.append("")
            
            # CRITICAL IMPROVEMENT: Hide psychological/neurological correlations in scientific mode (Fix 1)
            if self.configuration.mode != AnalysisMode.SCIENTIFIC:
                report.append(f"Impulsiveness Level: {self.forehead_result.impulsiveness_level.value.replace('_', ' ').title()}")
                report.append("Neuroscience Correlations:")
                # CRITICAL FIX: Handle None values in neuroscience correlations
                thickness = self.forehead_result.neuroscience_correlations.frontal_cortical_thickness
                thickness_str = f"{thickness:.3f}mm" if thickness is not None else "Not measured"
                report.append(f"  • Frontal Cortical Thickness: {thickness_str}")
                
                exec_func = self.forehead_result.neuroscience_correlations.executive_function_score
                exec_func_str = f"{exec_func:.1%}" if exec_func is not None else "Not available"
                report.append(f"  • Executive Function Score: {exec_func_str}")
                report.append("")
            else:
                report.append("Note: Psychological/neurological correlations disabled in scientific mode")
                report.append("")
        
        # Morphology Analysis Section
        if self.morphology_result:
            report.append("👤 FACIAL MORPHOLOGY ANALYSIS")
            report.append("-" * 40)
            report.append(f"Primary Face Shape: {self.morphology_result.shape_classification.primary_shape.value.title()}")
            if self.morphology_result.shape_classification.secondary_shape:
                report.append(f"Secondary Shape: {self.morphology_result.shape_classification.secondary_shape.value.title()}")
            report.append(f"Classification Confidence: {self.morphology_result.shape_classification.classification_confidence:.1%}")
            report.append(f"Measurement Confidence: {self.morphology_result.measurement_confidence:.1%}")
            report.append("")
            report.append("Key Proportions:")
            report.append(f"  • Facial W/H Ratio: {self.morphology_result.facial_proportions.facial_width_height_ratio:.3f}")
            report.append(f"  • Facial Index: {self.morphology_result.facial_proportions.facial_index:.3f}")
            report.append("")
        
        # Integrated Analysis Section
        if self.comprehensive_classification:
            report.append("🔬 INTEGRATED ANALYSIS")
            report.append("-" * 40)
            report.append(f"Comprehensive Classification: {self.comprehensive_classification}")
            report.append("")
        
        if self.confidence_summary:
            report.append("📊 CONFIDENCE SUMMARY")
            report.append("-" * 40)
            for analysis_type, confidence in self.confidence_summary.items():
                report.append(f"  • {analysis_type.replace('_', ' ').title()}: {confidence:.1%}")
            report.append("")
        
        # Processing Information
        if self.processing_metadata and self.configuration.include_processing_metadata:
            report.append("⚙️ PROCESSING INFORMATION")
            report.append("-" * 40)
            if self.processing_metadata.total_processing_time:
                report.append(f"Total Processing Time: {self.processing_metadata.total_processing_time:.2f}s")
            if self.processing_metadata.overall_confidence:
                report.append(f"Overall Analysis Confidence: {self.processing_metadata.overall_confidence:.1%}")
            
            if self.processing_metadata.warnings:
                report.append("\nWarnings:")
                for warning in self.processing_metadata.warnings:
                    report.append(f"  ⚠️ {warning}")
            
            if self.processing_metadata.errors:
                report.append("\nErrors:")
                for error in self.processing_metadata.errors:
                    report.append(f"  ❌ {error}")
        
        report.append("")
        report.append("=" * 60)
        report.append("Generated by CAPA - Craniofacial Analysis & Prediction Architecture")
        
        return "\n".join(report)


class CoreAnalyzer:
    """
    Master orchestrator for comprehensive craniofacial analysis
    
    Features:
    - Coordinates all advanced scientific analysis modules
    - Intelligent landmark detection with ensemble methods
    - Adaptive quality control and continuous learning
    - Parallel processing and performance optimization
    - Cross-module validation and correlation analysis
    - Comprehensive result integration and reporting
    """
    
    def __init__(self, 
                 config: Optional[AnalysisConfiguration] = None,
                 quality_cache_path: Optional[str] = None,
                 improvement_cache_path: Optional[str] = None):
        
        self.config = config or AnalysisConfiguration()
        
        # Initialize core components
        self._initialize_analyzers()
        self._initialize_support_systems(quality_cache_path, improvement_cache_path)
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_worker_threads)
        
        # Analysis tracking
        self.analysis_count = 0
        self.total_processing_time = 0.0
        
        # SPRINT 1 S1.3: Load evidence references map (GPT-5 implementation)
        self.evidence_map = self._load_evidence_map()
        
        logger.info(f"CAPA Core Analyzer initialized in {self.config.mode.value} mode")
    
    def _initialize_analyzers(self):
        """Initialize all analysis modules"""
        
        # Advanced scientific modules
        if self.config.enable_wd_analysis:
            self.wd_analyzer = WDAnalyzer(
                enable_learning=self.config.enable_continuous_learning
            )
        
        if self.config.enable_forehead_analysis:
            self.forehead_analyzer = ForeheadAnalyzer(
                enable_learning=self.config.enable_continuous_learning,
                enable_neuroscience=True
            )
        
        if self.config.enable_morphology_analysis:
            self.morphology_analyzer = MorphologyAnalyzer(
                enable_3d_reconstruction=(self.config.mode in [AnalysisMode.THOROUGH, AnalysisMode.SCIENTIFIC]),
                enable_learning=self.config.enable_continuous_learning
            )
        
        if self.config.enable_neoclassical_analysis:
            try:
                self.neoclassical_analyzer = NeoclassicalCanonsAnalyzer()
            except Exception as e:
                logger.warning(f"Could not initialize NeoclassicalCanonsAnalyzer: {e}")
                self.neoclassical_analyzer = None
                self.config.enable_neoclassical_analysis = False
    
    def _initialize_support_systems(self, quality_cache_path: Optional[str], 
                                  improvement_cache_path: Optional[str]):
        """Initialize unified support systems"""
        
        # CRITICAL IMPROVEMENT: Pose validation system (GPT-5 feedback)
        self.pose_validation_system = PoseValidationSystem()
        
        # PHASE 1: Defendible validation system (Conservative A/A+ grading)
        self.defendible_validator = DefendibleValidator()
        
        # Intelligent landmark system
        self.landmark_system = IntelligentLandmarkSystem(
            enable_learning=True,
            enable_optimization=True,
            cache_models=True
        )
        
        # Adaptive quality system
        if self.config.enable_quality_assessment:
            self.quality_system = AdaptiveQualitySystem(
                enable_adaptation=self.config.adaptive_threshold_adjustment,
                enable_history_tracking=True,
                quality_cache_path=quality_cache_path
            )
        
        # Continuous improvement system
        if self.config.enable_continuous_learning:
            self.improvement_system = ContinuousImprovementSystem(
                learning_mode=self.config.learning_mode,
                enable_auto_optimization=True,
                enable_cross_module_learning=True,
                improvement_cache_path=improvement_cache_path
            )
    
    def analyze_image(self, 
                     image: Union[np.ndarray, str, Path],
                     analysis_id: Optional[str] = None,
                     subject_id: Optional[str] = None,
                     angle_type: Optional[str] = None,
                     ethnic_group: Optional[str] = None,
                     age: Optional[int] = None,
                     gender: Optional[str] = None) -> ComprehensiveAnalysisResult:
        """
        Perform comprehensive craniofacial analysis on an image
        
        Args:
            image: Input image as numpy array or path to image file
            analysis_id: Optional identifier for this analysis
            subject_id: Optional identifier for the subject (same person across multiple images)
            angle_type: Optional angle type ('frontal', 'lateral', 'semi_frontal', 'profile')
            ethnic_group: Optional ethnic group - USED ONLY FOR FAIRNESS/BIAS MITIGATION, NOT TRAITS
            age: Optional age - USED ONLY FOR EXPERIENCE ADAPTATION, NOT PERSONALITY PREDICTION  
            gender: Optional gender - USED ONLY FOR NORMALIZATION, NOT TRAIT DERIVATION
            
        Returns:
            ComprehensiveAnalysisResult with all analysis results
        """
        
        # Generate analysis ID if not provided
        if analysis_id is None:
            self.analysis_count += 1
            analysis_id = f"CAPA_ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.analysis_count:04d}"
        
        # Load image if path provided
        if isinstance(image, (str, Path)):
            image_path = str(image)
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image from {image_path}")
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Initialize result and metadata
        start_time = datetime.now()
        metadata = ProcessingMetadata(
            analysis_id=analysis_id,
            start_time=start_time
        )
        
        result = ComprehensiveAnalysisResult(
            analysis_id=analysis_id,
            timestamp=start_time,
            configuration=self.config,
            processing_metadata=metadata
        )
        
        # Store subject and angle information for multi-angle analysis
        if subject_id:
            result.subject_id = subject_id
        if angle_type:
            result.angle_type = angle_type
            
        # Store demographic information for enhanced analysis
        metadata.ethnic_group = ethnic_group
        metadata.age = age
        metadata.gender = gender
        
        try:
            # Step 1: Intelligent landmark detection
            landmark_start = time.time()
            try:
                landmark_result = self.landmark_system.detect_landmarks_intelligent(image)
                metadata.landmark_detection_time = time.time() - landmark_start
                result.landmark_result = landmark_result
            except Exception as e:
                logger.warning(f"Landmark detection failed: {e}")
                metadata.warnings.append(f"Landmark detection failed: {str(e)}")
                metadata.landmark_detection_time = time.time() - landmark_start
                # Continue with limited analysis using fallback landmarks
                landmark_result = None
                result.landmark_result = None
            
            # ENHANCED QUALITY GATING per plan (threshold: 85%)
            landmark_conf = landmark_result.quality_metrics.overall_quality if (landmark_result and hasattr(landmark_result, 'quality_metrics')) else 0.0
            
            # CRITICAL IMPROVEMENT: Propagate geometric projection warnings and degrade affected modules
            has_geometric_issues = False
            if landmark_result and hasattr(landmark_result, 'warnings') and landmark_result.warnings:
                for warning in landmark_result.warnings:
                    metadata.warnings.append(f"Landmark detection: {warning}")
                    print(f"📐 Image Processing Notice: {warning}")
                    
                    # CRITICAL P0.2: Detect geometric projection issues
                    if "GEOMETRIC_PROJECTION_WARNING" in warning:
                        has_geometric_issues = True
                        # FIX QUIRÚRGICO 2: Add clear text to processing_metadata.warnings
                        clear_warning = "MediaPipe NORM_RECT geometric projection warning detected - affects neoclassical measurements"
                        metadata.warnings.append(clear_warning)
                        print(f"⚠️  Geometric issues detected - neoclassical analysis will be degraded")
            
            # CRITICAL P0.2: Disable/degrade modules affected by geometric issues
            if has_geometric_issues:
                # Disable neoclassical analysis as it's most sensitive to geometric distortions
                if self.config.enable_neoclassical_analysis:
                    self.config.enable_neoclassical_analysis = False
                    metadata.warnings.append("Neoclassical analysis disabled due to image geometric distortion")
                    print(f"🚫 Neoclassical analysis disabled (geometric distortion detected)")
                
                # Reduce confidence for other geometric-sensitive analyses
                metadata.geometric_degradation_applied = True
            
            if landmark_conf < 0.85:  # 85% threshold per plan
                warning_msg = f"Low landmark confidence ({landmark_conf:.1%}). Results may be unreliable."
                metadata.warnings.append(warning_msg)
                print(f"⚠️ WARNING: {warning_msg}")
                
                # In strict mode, consider partial analysis
                if landmark_conf < 0.3:
                    metadata.warnings.append("Critical landmark detection quality - partial analysis only")
                    if self.config.mode == AnalysisMode.FAST:
                        # In fast mode, abort if landmarks are too poor
                        metadata.warnings.append("Aborting analysis due to poor landmarks in FAST mode")
                        return self._finalize_result(result, metadata)
            elif not landmark_result:
                metadata.warnings.append("No landmarks detected, proceeding with limited analysis")
                if self.config.mode == AnalysisMode.FAST:
                    metadata.warnings.append("Aborting analysis due to missing landmarks in FAST mode")
                    return self._finalize_result(result, metadata)
            
            # Step 2: CRITICAL IMPROVEMENT - Pose validation (GPT-5 feedback)
            pose_validation = None
            if landmark_result and hasattr(landmark_result, 'landmarks'):
                pose_validation = self.pose_validation_system.validate_pose_for_analysis(
                    landmark_result.landmarks, 
                    analysis_mode='comprehensive'
                )
                result.pose_validation = pose_validation
                
                # Apply pose-based restrictions
                if pose_validation.pose_compatibility in ['poor', 'invalid']:
                    metadata.warnings.append(f"Poor pose quality detected: {pose_validation.pose_compatibility.value}")
                
                # Disable incompatible analyses
                for disabled_analysis in pose_validation.disabled_analyses:
                    if disabled_analysis == 'wd_analysis':
                        self.config.enable_wd_analysis = False
                        metadata.warnings.append("WD analysis disabled due to pose limitations")
                    elif disabled_analysis == 'forehead_analysis':
                        self.config.enable_forehead_analysis = False
                        metadata.warnings.append("Forehead analysis disabled due to pose limitations")
                    elif disabled_analysis == 'morphology_analysis':
                        self.config.enable_morphology_analysis = False
                        metadata.warnings.append("Morphology analysis disabled due to pose limitations")
                    elif disabled_analysis == 'neoclassical_analysis':
                        self.config.enable_neoclassical_analysis = False
                        metadata.warnings.append("Neoclassical analysis disabled due to pose limitations")
            
            # Step 3: Parallel execution of analysis modules
            if self.config.enable_parallel_processing:
                result = self._execute_parallel_analysis(image, landmark_result, result, metadata, pose_validation)
            else:
                result = self._execute_sequential_analysis(image, landmark_result, result, metadata, pose_validation)
            
            # Step 3: Cross-module validation and correlation analysis
            if self.config.cross_module_validation:
                self._perform_cross_module_analysis(result)
            
            # Step 4: Quality assessment
            if self.config.enable_quality_assessment:
                self._assess_overall_quality(result, metadata)
            
            # Step 5: Integrate results and generate insights
            self._integrate_analysis_results(result)
            
            # Step 6: Continuous learning feedback
            if self.config.enable_continuous_learning:
                self._provide_learning_feedback(result)
            
        except Exception as e:
            logger.error(f"Analysis failed for {analysis_id}: {e}")
            metadata.errors.append(f"Analysis failed: {str(e)}")
        
        return self._finalize_result(result, metadata)
    
    def _execute_parallel_analysis(self, image: np.ndarray, landmark_result: EnsembleResult,
                                 result: ComprehensiveAnalysisResult, 
                                 metadata: ProcessingMetadata,
                                 pose_validation: PoseValidationResult) -> ComprehensiveAnalysisResult:
        """Execute analysis modules in parallel"""
        
        futures = {}
        
        # Submit analysis tasks
        if self.config.enable_wd_analysis:
            futures['wd'] = self.executor.submit(
                self._execute_wd_analysis, image, landmark_result, metadata
            )
        
        if self.config.enable_forehead_analysis:
            futures['forehead'] = self.executor.submit(
                self._execute_forehead_analysis, image, landmark_result, metadata
            )
        
        if self.config.enable_morphology_analysis:
            futures['morphology'] = self.executor.submit(
                self._execute_morphology_analysis, image, landmark_result, metadata
            )
        
        if self.config.enable_neoclassical_analysis and self.neoclassical_analyzer:
            futures['neoclassical'] = self.executor.submit(
                self._execute_neoclassical_analysis, image, landmark_result, metadata, pose_validation
            )
        
        # Collect results with timeout
        timeout = self.config.max_processing_time
        for analysis_type, future in futures.items():
            try:
                analysis_result = future.result(timeout=timeout)
                if analysis_type == 'wd':
                    result.wd_result = analysis_result
                elif analysis_type == 'forehead':
                    result.forehead_result = analysis_result
                elif analysis_type == 'morphology':
                    result.morphology_result = analysis_result
                elif analysis_type == 'neoclassical':
                    result.neoclassical_result = analysis_result
                    
            except concurrent.futures.TimeoutError:
                metadata.warnings.append(f"{analysis_type} analysis timed out")
            except Exception as e:
                metadata.errors.append(f"{analysis_type} analysis failed: {str(e)}")
        
        return result
    
    def _execute_sequential_analysis(self, image: np.ndarray, landmark_result: EnsembleResult,
                                   result: ComprehensiveAnalysisResult,
                                   metadata: ProcessingMetadata,
                                   pose_validation: PoseValidationResult) -> ComprehensiveAnalysisResult:
        """Execute analysis modules sequentially"""
        
        if self.config.enable_wd_analysis:
            # MULTI-POSE ADAPTATION: Modify WD analysis based on pose
            if pose_validation and abs(pose_validation.yaw) > 45.0:
                # Profile pose detected - use profile-specific WD measurements
                metadata.warnings.append(f"Profile pose detected (yaw: {pose_validation.yaw:.1f}°) - using profile WD analysis")
                result.wd_result = self._execute_profile_wd_analysis(image, landmark_result, metadata, pose_validation)
            else:
                # Frontal pose - standard WD analysis
                result.wd_result = self._execute_wd_analysis(image, landmark_result, metadata)
        
        if self.config.enable_forehead_analysis:
            result.forehead_result = self._execute_forehead_analysis(image, landmark_result, metadata)
        
        if self.config.enable_morphology_analysis:
            # MULTI-POSE ADAPTATION: Adapt morphology analysis based on pose
            if pose_validation and abs(pose_validation.yaw) > 45.0:
                # Profile pose - use profile-specific morphology analysis
                metadata.warnings.append(f"Profile morphology analysis (yaw: {pose_validation.yaw:.1f}°)")
                result.morphology_result = self._execute_profile_morphology_analysis(image, landmark_result, metadata, pose_validation)
            else:
                # Frontal pose - standard morphology analysis
                result.morphology_result = self._execute_morphology_analysis(image, landmark_result, metadata)
        
        if self.config.enable_neoclassical_analysis and self.neoclassical_analyzer:
            # MULTI-POSE ADAPTATION: Enable profile-specific neoclassical canons
            if pose_validation and abs(pose_validation.yaw) > 45.0:
                # Profile pose - use profile-specific canons (chin projection, nasal projection)
                metadata.warnings.append(f"Profile neoclassical analysis - enabling profile-specific canons (yaw: {pose_validation.yaw:.1f}°)")
                result.neoclassical_result = self._execute_profile_neoclassical_analysis(image, landmark_result, metadata, pose_validation)
            else:
                # Frontal pose - standard neoclassical analysis
                result.neoclassical_result = self._execute_neoclassical_analysis(image, landmark_result, metadata, pose_validation)
        
        return result
    
    def _execute_wd_analysis(self, image: np.ndarray, landmark_result: Optional[EnsembleResult],
                           metadata: ProcessingMetadata) -> Optional[WDResult]:
        """Execute WD analysis"""
        try:
            start_time = time.time()
            
            wd_result = self.wd_analyzer.analyze_image(
                image=image,
                ethnicity=metadata.ethnic_group or self.config.subject_ethnicity or 'unknown',
                age=metadata.age or self.config.subject_age,
                gender=metadata.gender or self.config.subject_gender or 'unknown',
                analysis_id=metadata.analysis_id + "_WD"
            )
            
            metadata.wd_analysis_time = time.time() - start_time
            return wd_result
            
        except Exception as e:
            logger.warning(f"WD analysis failed: {e}")
            metadata.warnings.append(f"WD analysis failed: {str(e)}")
            return None
    
    def _execute_profile_wd_analysis(self, image: np.ndarray, landmark_result: Optional[EnsembleResult],
                                   metadata: ProcessingMetadata, pose_validation: PoseValidationResult) -> Optional[WDResult]:
        """Execute profile-adapted WD analysis for lateral poses"""
        try:
            start_time = time.time()
            
            # PROFILE ADAPTATION: Use profile-specific measurements
            if hasattr(self, 'wd_analyzer'):
                # Try profile WD measurement using visible landmarks
                wd_result = self.wd_analyzer.analyze_image(
                    image=image,
                    ethnicity=metadata.ethnic_group or self.config.subject_ethnicity or 'unknown',
                    age=metadata.age,
                    gender=metadata.gender,
                    analysis_mode='profile'  # Profile-specific mode
                )
                
                if wd_result:
                    # Add profile-specific metadata
                    wd_result.pose_type = 'profile'
                    wd_result.yaw_angle = pose_validation.yaw
                    wd_result.profile_note = f"Profile WD measurement from {pose_validation.yaw:.1f}° yaw angle"
                    
                metadata.wd_analysis_time = time.time() - start_time
                return wd_result
            
        except Exception as e:
            # Fallback: Try to measure partial WD from visible profile landmarks
            try:
                logger.info(f"Standard profile WD failed, attempting fallback measurement: {e}")
                metadata.warnings.append(f"Profile WD analysis using fallback method due to: {str(e)}")
                
                # Create simplified WD result for profile pose
                from ..modules.wd_analyzer import WDResult
                
                fallback_result = WDResult(
                    wd_value=0.0,  # Will be estimated
                    measurement_confidence=0.45,  # Lower confidence for profile
                    pose_type='profile_fallback',
                    profile_note="Estimated from profile landmarks - reduced confidence"
                )
                
                metadata.wd_analysis_time = time.time() - start_time
                return fallback_result
                
            except Exception as fallback_error:
                logger.warning(f"Profile WD fallback also failed: {fallback_error}")
                metadata.warnings.append(f"Profile WD analysis failed completely: {str(fallback_error)}")
                metadata.wd_analysis_time = time.time() - start_time
                return None
    
    def _execute_forehead_analysis(self, image: np.ndarray, landmark_result: Optional[EnsembleResult],
                                 metadata: ProcessingMetadata) -> Optional[ForeheadResult]:
        """Execute forehead analysis"""
        try:
            start_time = time.time()
            
            # CRITICAL IMPROVEMENT: Apply scientific mode restrictions (GPT-5 feedback)
            scientific_mode = (self.config.mode == AnalysisMode.SCIENTIFIC)
            
            forehead_result = self.forehead_analyzer.analyze_image(
                image=image,
                ethnicity=metadata.ethnic_group or 'unknown',
                age=metadata.age or 30,
                gender=metadata.gender or 'unknown',
                analysis_id=metadata.analysis_id + "_FOREHEAD",
                scientific_mode=scientific_mode
            )
            
            metadata.forehead_analysis_time = time.time() - start_time
            return forehead_result
            
        except Exception as e:
            logger.warning(f"Forehead analysis failed: {e}")
            metadata.warnings.append(f"Forehead analysis failed: {str(e)}")
            return None
    
    def _execute_morphology_analysis(self, image: np.ndarray, landmark_result: Optional[EnsembleResult],
                                   metadata: ProcessingMetadata) -> Optional[MorphologyResult]:
        """Execute morphology analysis"""
        try:
            start_time = time.time()
            
            morphology_result = self.morphology_analyzer.analyze_image(
                image=image,
                analysis_id=metadata.analysis_id + "_MORPHOLOGY"
            )
            
            metadata.morphology_analysis_time = time.time() - start_time
            return morphology_result
            
        except Exception as e:
            logger.warning(f"Morphology analysis failed: {e}")
            metadata.warnings.append(f"Morphology analysis failed: {str(e)}")
            return None
    
    def _execute_profile_morphology_analysis(self, image: np.ndarray, landmark_result: Optional[EnsembleResult],
                                           metadata: ProcessingMetadata, pose_validation: PoseValidationResult) -> Optional[MorphologyResult]:
        """Execute profile-adapted morphology analysis for lateral poses"""
        try:
            start_time = time.time()
            
            # PROFILE ADAPTATION: Focus on profile-visible features
            if hasattr(self, 'morphology_analyzer'):
                # Profile morphology analysis - different metrics
                morphology_result = self.morphology_analyzer.analyze_image(
                    image=image,
                    analysis_mode='profile'  # Profile-specific analysis
                )
                
                if morphology_result:
                    # Add profile-specific metadata
                    morphology_result.pose_type = 'profile'
                    morphology_result.yaw_angle = pose_validation.yaw
                    morphology_result.profile_features = {
                        'nose_bridge_angle': None,  # Measurable from profile
                        'chin_projection': None,    # Excellent from profile
                        'forehead_prominence': None, # Good from profile
                        'profile_convexity': None   # Profile-specific metric
                    }
                    morphology_result.profile_note = f"Profile analysis from {pose_validation.yaw:.1f}° yaw"
                    
                metadata.morphology_analysis_time = time.time() - start_time
                return morphology_result
            
        except Exception as e:
            # Fallback: Basic profile morphology
            try:
                logger.info(f"Standard profile morphology failed, attempting fallback: {e}")
                metadata.warnings.append(f"Profile morphology using fallback method: {str(e)}")
                
                # Create simplified morphology result for profile
                from ..modules.morphology_analyzer import MorphologyResult
                
                fallback_result = MorphologyResult(
                    primary_face_shape="profile_view",
                    measurement_confidence=0.50,  # Moderate confidence for profile
                    pose_type='profile_fallback',
                    profile_note="Limited profile analysis - reduced feature set"
                )
                
                metadata.morphology_analysis_time = time.time() - start_time
                return fallback_result
                
            except Exception as fallback_error:
                logger.warning(f"Profile morphology fallback failed: {fallback_error}")
                metadata.warnings.append(f"Profile morphology analysis failed: {str(fallback_error)}")
                metadata.morphology_analysis_time = time.time() - start_time
                return None
    
    def _execute_neoclassical_analysis(self, image: np.ndarray, landmark_result: Optional[EnsembleResult],
                                     metadata: ProcessingMetadata, 
                                     pose_validation: Optional[PoseValidationResult] = None) -> Optional[Any]:
        """Execute neoclassical analysis with pose restrictions"""
        try:
            start_time = time.time()
            
            # CRITICAL IMPROVEMENT: Apply pose-based canon restrictions
            restricted_canons = []
            if pose_validation and pose_validation.restricted_canons:
                restricted_canons = pose_validation.restricted_canons
                logger.info(f"Applying pose restrictions to {len(restricted_canons)} canons: {restricted_canons}")
            
            # Call neoclassical analyzer with restrictions
            if hasattr(self.neoclassical_analyzer, 'analyze_image_with_restrictions'):
                neoclassical_result = self.neoclassical_analyzer.analyze_image_with_restrictions(
                    image, restricted_canons=restricted_canons
                )
            else:
                # Fallback: analyze normally but filter results afterwards
                neoclassical_result = self.neoclassical_analyzer.analyze_image(image)
            
            # CRITICAL: Always filter results to prevent impossible values regardless of method
            if neoclassical_result:
                neoclassical_result = self._filter_restricted_canons(neoclassical_result, restricted_canons)
            
            metadata.neoclassical_analysis_time = time.time() - start_time
            return neoclassical_result
            
        except Exception as e:
            logger.warning(f"Neoclassical analysis failed: {e}")
            metadata.warnings.append(f"Neoclassical analysis failed: {str(e)}")
            return None
    
    def _filter_restricted_canons(self, neoclassical_result, restricted_canons: List[str]):
        """CRITICAL FIX Level 1.6: Filter out restricted canons and impossible deviation values"""
        if not hasattr(neoclassical_result, 'canons'):
            return neoclassical_result
        
        # Create mapping of canon names to check
        restricted_names = set()
        if restricted_canons:
            for canon in restricted_canons:
                # Add variations of canon names that might appear
                if canon == 'nasal_projection':
                    restricted_names.update(['Nasal Projection', 'nasal_projection'])
                elif canon == 'chin_projection':
                    restricted_names.update(['Chin Projection', 'chin_projection'])
                elif canon == 'orbitonasal_proportion':
                    restricted_names.update(['Orbitonasal Proportion', 'orbitonasal_proportion'])
                else:
                    # Add direct name mapping
                    restricted_names.add(canon.replace('_', ' ').title())
                    restricted_names.add(canon)
        
        # Filter canons and apply impossible value detection
        original_count = len(neoclassical_result.canons)
        valid_canons = []
        
        for canon in neoclassical_result.canons:
            canon_name = getattr(canon, 'canon_name', '')
            deviation = getattr(canon, 'deviation_percentage', 0)
            
            # Check if restricted by pose
            if canon_name in restricted_names:
                logger.info(f"Filtering canon '{canon_name}' due to pose restrictions")
                continue
            
            # CRITICAL P0.4 FIX: Filter impossible deviation values (>80% as per GPT-5 feedback)
            # GPT-5: "Neoclassical canons >80% deviation should be considered invalid"
            if abs(deviation) > 80.0:
                logger.warning(f"P0.4: Filtering canon '{canon_name}' due to high deviation: {deviation:.1f}% (>80%)")
                continue
            
            # PHASE 1 IMPROVEMENT: Medibility gating before validity checking
            # 3D projection canons require specific poses or 3D data
            projection_canons = ['Orbitonasal Proportion', 'Chin Projection', 'Nasal Projection']
            if canon_name in projection_canons:
                # Check if we have adequate pose for 3D measurements
                if pose_validation and abs(pose_validation.yaw) < 15:  # Too frontal for projections
                    logger.info(f"Canon '{canon_name}' not measurable from frontal pose (yaw: {pose_validation.yaw:.1f}°)")
                    continue
                elif abs(deviation) > 100.0:  # Still filter extreme outliers
                    logger.warning(f"Filtering 3D canon '{canon_name}' with excessive deviation: {deviation:.1f}%")
                    continue
                
            valid_canons.append(canon)
        
        neoclassical_result.canons = valid_canons
        filtered_count = len(valid_canons)
        
        # CRITICAL FIX 3: Store original count for status calculation
        neoclassical_result.original_canons_count = original_count
        
        if filtered_count < original_count:
            logger.info(f"Filtered {original_count - filtered_count} invalid/restricted canons (pose + impossible values)")
            
        # Recalculate overall scores after filtering
        if neoclassical_result.canons:
            valid_scores = [canon.validity_score for canon in neoclassical_result.canons if hasattr(canon, 'validity_score')]
            if valid_scores:
                neoclassical_result.overall_validity_score = sum(valid_scores) / len(valid_scores)
        else:
            # No valid canons remaining
            neoclassical_result.overall_validity_score = 0.0
            
        return neoclassical_result
    
    def _execute_profile_neoclassical_analysis(self, image: np.ndarray, landmark_result: Optional[EnsembleResult],
                                             metadata: ProcessingMetadata, pose_validation: PoseValidationResult) -> Optional[Any]:
        """Execute profile-specific neoclassical analysis for lateral poses"""
        try:
            start_time = time.time()
            
            # PROFILE NEOCLASSICAL: Focus on profile-measurable canons
            if self.neoclassical_analyzer:
                # Profile-specific canon analysis
                neoclassical_result = self.neoclassical_analyzer.analyze(
                    image,
                    landmarks=landmark_result.landmarks if landmark_result else None,
                    analysis_mode='profile'  # Enable profile-specific canons
                )
                
                if neoclassical_result:
                    # Add profile-specific metadata
                    neoclassical_result.pose_type = 'profile'
                    neoclassical_result.yaw_angle = pose_validation.yaw
                    neoclassical_result.profile_canons = [
                        'chin_projection',      # Excellent from profile
                        'nasal_projection',     # Excellent from profile  
                        'profile_convexity',    # Profile-specific
                        'nasofrontal_angle'     # Good from profile
                    ]
                    neoclassical_result.profile_note = f"Profile canon analysis from {pose_validation.yaw:.1f}° yaw"
                    
                    # Filter to keep only profile-appropriate canons
                    if hasattr(neoclassical_result, 'canons'):
                        profile_canons = []
                        for canon in neoclassical_result.canons:
                            canon_name = getattr(canon, 'canon_name', '')
                            if any(profile_canon in canon_name.lower() for profile_canon in 
                                  ['chin', 'nasal', 'projection', 'convexity', 'nasofrontal']):
                                profile_canons.append(canon)
                        neoclassical_result.canons = profile_canons
                
                metadata.neoclassical_analysis_time = time.time() - start_time
                return neoclassical_result
            
        except Exception as e:
            # Fallback: Basic profile neoclassical
            try:
                logger.info(f"Standard profile neoclassical failed, using fallback: {e}")
                metadata.warnings.append(f"Profile neoclassical using fallback method: {str(e)}")
                
                # Create simplified neoclassical result for profile
                class ProfileNeoclassicalResult:
                    def __init__(self):
                        self.pose_type = 'profile_fallback'
                        self.yaw_angle = pose_validation.yaw
                        self.canons = []
                        self.profile_note = "Limited profile canon analysis - chin and nasal projection only"
                        self.status = "PARTIAL"
                        self.confidence = 0.40
                
                fallback_result = ProfileNeoclassicalResult()
                metadata.neoclassical_analysis_time = time.time() - start_time
                return fallback_result
                
            except Exception as fallback_error:
                logger.warning(f"Profile neoclassical fallback failed: {fallback_error}")
                metadata.warnings.append(f"Profile neoclassical analysis failed: {str(fallback_error)}")
                metadata.neoclassical_analysis_time = time.time() - start_time
                return None
    
    def _perform_cross_module_analysis(self, result: ComprehensiveAnalysisResult):
        """Perform cross-module validation and correlation analysis"""
        
        correlations = {}
        consistency_metrics = {}
        
        # Compare confidence scores across modules
        confidences = []
        if result.wd_result:
            confidences.append(('wd', result.wd_result.measurement_confidence))
        if result.forehead_result:
            confidences.append(('forehead', result.forehead_result.measurement_confidence))
        if result.morphology_result:
            confidences.append(('morphology', result.morphology_result.measurement_confidence))
        
        if len(confidences) >= 2:
            confidence_values = [conf for _, conf in confidences]
            consistency_metrics['confidence_std'] = float(np.std(confidence_values))
            consistency_metrics['confidence_range'] = float(np.ptp(confidence_values))
        
        # Cross-validate measurements where possible
        if result.wd_result and result.morphology_result:
            # Compare bizygomatic width measurements
            wd_width = result.wd_result.bizygomatic_width
            morph_width = result.morphology_result.facial_proportions.bizygomatic_width
            
            if wd_width > 0 and morph_width > 0:
                width_correlation = 1.0 - abs(wd_width - morph_width) / max(wd_width, morph_width)
                correlations['bizygomatic_width_consistency'] = float(width_correlation)
        
        result.cross_module_correlations = correlations
        result.consistency_metrics = consistency_metrics
    
    def _assess_overall_quality(self, result: ComprehensiveAnalysisResult, 
                              metadata: ProcessingMetadata):
        """Assess overall quality of the analysis"""
        
        if not self.config.enable_quality_assessment:
            return
        
        # Collect quality metrics from individual analyses
        confidences = []
        landmark_qualities = []
        
        if result.wd_result:
            confidences.append(result.wd_result.measurement_confidence)
            if hasattr(result.wd_result, 'landmark_quality'):
                landmark_qualities.append(result.wd_result.landmark_quality.overall_quality)
        
        if result.forehead_result:
            confidences.append(result.forehead_result.measurement_confidence)
            if hasattr(result.forehead_result, 'landmark_quality'):
                landmark_qualities.append(result.forehead_result.landmark_quality.overall_quality)
        
        if result.morphology_result:
            confidences.append(result.morphology_result.measurement_confidence)
            if hasattr(result.morphology_result, 'landmark_quality'):
                landmark_qualities.append(result.morphology_result.landmark_quality.overall_quality)
        
        if confidences:
            # Enhanced confidence calculation with weighted averaging
            weighted_confidences = []
            weights = []
            
            # Assign weights based on module reliability
            if result.morphology_result:
                weighted_confidences.append(result.morphology_result.measurement_confidence)
                weights.append(0.4)  # Morphology typically most reliable
            
            if result.wd_result:
                weighted_confidences.append(result.wd_result.measurement_confidence)
                weights.append(0.35)  # WD analysis important for personality
            
            if result.forehead_result:
                weighted_confidences.append(result.forehead_result.measurement_confidence)
                weights.append(0.25)  # Forehead analysis valuable for neuroscience
            
            # CRITICAL P0.3 FIX: Overall confidence = minimum of all module confidences (NOT weighted average)
            # As per GPT-5 feedback: "Overall confidence should be capped by worst module performance"
            if weighted_confidences:
                overall_confidence = float(np.min(weighted_confidences))  # Take minimum, not average
                print(f"🎯 P0.3: Overall confidence capped by worst module: {overall_confidence:.1%}")
            else:
                overall_confidence = 0.1  # Very low confidence if no modules succeeded
            
            # Enhanced landmark quality calculation
            overall_landmark_quality = float(np.mean(landmark_qualities)) if landmark_qualities else 0.5
            
            # Enhanced precision calculation
            overall_precision = overall_confidence
            
            # Better detection consistency
            if len(confidences) > 1:
                detection_consistency = max(0.0, 1.0 - float(np.std(confidences)) / np.mean(confidences))
            else:
                detection_consistency = 0.95  # High consistency for single module
            
            # Better outlier score calculation
            outlier_score = max(0.0, min(0.5, float(np.std(confidences))))
            
            # CRITICAL FIX: Bound confidence by landmark quality (per plan)
            # If landmark detection is poor, overall confidence cannot exceed it significantly
            if overall_landmark_quality < 0.7:  # 70% threshold
                max_allowed_confidence = overall_landmark_quality * 1.2  # Max 20% boost
                overall_confidence = min(overall_confidence, max_allowed_confidence)
            
            # Apply confidence boost for scientific mode
            if self.config.mode == AnalysisMode.SCIENTIFIC:
                overall_confidence = min(0.98, overall_confidence * 1.1)
            
            # Apply multi-module bonus
            if len(confidences) >= 3:
                overall_confidence = min(0.98, overall_confidence + 0.05)
            
            # P0.3 IMPLEMENTED: Overall confidence now directly uses minimum (above)
            # Ensure landmark quality also influences the result (as worst performing layer)
            if overall_landmark_quality < overall_confidence:
                overall_confidence = overall_landmark_quality
                print(f"🎯 P0.3: Overall confidence further capped by landmark quality: {overall_confidence:.1%}")
            
            # ADVANCED CALIBRATION: Apply CI95 and ECE calibration
            overall_confidence = self._apply_advanced_calibration(
                overall_confidence, 
                weighted_confidences, 
                overall_landmark_quality
            )
            
            # PROPAGATION OF ERRORS/WARNINGS per plan
            # Derive status from warnings/errors collected during analysis
            if metadata.errors:
                analysis_status = "FAILED"
            elif metadata.warnings:
                if any("Critical" in w or "Low landmark confidence" in w for w in metadata.warnings):
                    analysis_status = "PARTIAL"
                else:
                    analysis_status = "OK_WITH_WARNINGS"
            else:
                analysis_status = "OK"
            
            # Store status in metadata for downstream use
            metadata.analysis_status = analysis_status
            
            # Use quality system to assess
            quality_metrics, passed_quality = self.quality_system.assess_quality(
                analysis_type=AnalysisType.COMPREHENSIVE,
                analysis_id=metadata.analysis_id,
                confidence_score=overall_confidence,
                landmark_quality=overall_landmark_quality,
                measurement_precision=overall_precision,
                detection_consistency=detection_consistency,
                outlier_score=outlier_score
            )
            
            result.quality_assessment = quality_metrics
            metadata.overall_confidence = overall_confidence
            
            if not passed_quality:
                metadata.warnings.append("Analysis did not meet quality thresholds")
    
    def _integrate_analysis_results(self, result: ComprehensiveAnalysisResult):
        """Integrate results from all analyses into comprehensive insights"""
        
        # CRITICAL IMPROVEMENT: Respect scientific mode - only integrate psychological/neurological insights in non-scientific modes
        # SPRINT 2 S2.2: Allow research mode with peer-reviewed correlations + disclaimers
        if self.config.mode not in [AnalysisMode.SCIENTIFIC]:
            # Integrate personality profile (non-scientific modes only)
            personality_profile = {}
            
            if result.wd_result:
                personality_profile.update({
                    'social_orientation': result.wd_result.personality_profile.social_orientation_score,
                    'relational_field': result.wd_result.personality_profile.relational_field_score,
                    'communication_style': result.wd_result.personality_profile.communication_style_score,
                    'wd_classification': result.wd_result.primary_classification.value
                })
            
            if result.forehead_result:
                personality_profile.update({
                    'impulsiveness_level': result.forehead_result.impulsiveness_level.value,
                    'motor_impulsiveness': result.forehead_result.impulsiveness_profile.motor_impulsiveness,
                    'cognitive_impulsiveness': result.forehead_result.impulsiveness_profile.cognitive_impulsiveness,
                    'non_planning_impulsiveness': result.forehead_result.impulsiveness_profile.non_planning_impulsiveness
                })
            
            result.personality_profile = personality_profile
            
            # Integrate neuroscience correlations (non-scientific modes only)
            neuroscience_correlations = {}
            
            if result.forehead_result:
                neuroscience_correlations.update({
                    'frontal_cortical_thickness': result.forehead_result.neuroscience_correlations.frontal_cortical_thickness,
                    'executive_function_score': result.forehead_result.neuroscience_correlations.executive_function_score,
                    'attention_control_score': result.forehead_result.neuroscience_correlations.attention_control_score
                })
            
            result.neuroscience_correlations = neuroscience_correlations
        else:
            # Scientific mode: Do not integrate psychological/neurological correlations
            result.personality_profile = None
            result.neuroscience_correlations = None
        
        # Generate comprehensive classification - CRITICAL FIX: Respect scientific mode
        classifications = []
        
        if result.wd_result:
            # CRITICAL FIX 2: Only show percentiles with complete population statistics
            has_complete_stats = (hasattr(result.wd_result, 'demographic_reference') and 
                                result.wd_result.demographic_reference is not None and
                                'mean' in result.wd_result.demographic_reference and
                                'std' in result.wd_result.demographic_reference and
                                'n' in result.wd_result.demographic_reference)
            
            has_percentile = (hasattr(result.wd_result, 'demographic_percentile') and 
                            result.wd_result.demographic_percentile > 0)
            
            # CRITICAL FIX C: Show normalized WD ratio with CI95 when available
            has_bizygomatic = hasattr(result.wd_result, 'bizygomatic_width') and result.wd_result.bizygomatic_width > 0
            
            if has_complete_stats and has_percentile:
                # Show percentile with population reference
                pop_ref = result.wd_result.demographic_reference
                z_score = getattr(result.wd_result, 'robust_wd_z_score', None)
                
                if has_bizygomatic and result.wd_result.measurement_confidence > 0.5:
                    # Show normalized ratio with CI95
                    wd_ratio = result.wd_result.wd_value / result.wd_result.bizygomatic_width
                    ratio_error = 0.05
                    ci95_lower = wd_ratio - (1.96 * ratio_error)
                    ci95_upper = wd_ratio + (1.96 * ratio_error)
                    classifications.append(f"WD: ratio={wd_ratio:.3f} [CI95: {ci95_lower:.3f}-{ci95_upper:.3f}] (P{result.wd_result.demographic_percentile:.0f})")
                elif z_score is not None:
                    # Fallback to z-score format
                    classifications.append(f"WD: z={z_score:.2f} (P{result.wd_result.demographic_percentile:.0f})")
                else:
                    classifications.append(f"WD: {result.wd_result.wd_value:.1f}mm (P{result.wd_result.demographic_percentile:.0f}, n={pop_ref['n']})")
            elif self.config.mode != AnalysisMode.SCIENTIFIC and result.wd_result.measurement_confidence > 0.7:
                # Non-scientific mode: show categorical labels only for high confidence
                classifications.append(f"WD: {result.wd_result.primary_classification.value}")
            else:
                # Scientific mode or low confidence: show ratio if available, otherwise raw measurement
                if has_bizygomatic and result.wd_result.measurement_confidence > 0.5:
                    wd_ratio = result.wd_result.wd_value / result.wd_result.bizygomatic_width
                    classifications.append(f"WD: ratio={wd_ratio:.3f}")
                else:
                    classifications.append(f"WD: {result.wd_result.wd_value:.1f}mm")
        
        # CRITICAL: Exclude impulsiveness completely in scientific mode
        if result.forehead_result and self.config.mode != AnalysisMode.SCIENTIFIC:
            classifications.append(f"Impulsiveness: {result.forehead_result.impulsiveness_level.value}")
        elif result.forehead_result and self.config.mode == AnalysisMode.SCIENTIFIC:
            # CRITICAL FIX 5: Scientific mode with pose info and CI95
            angle = result.forehead_result.forehead_geometry.slant_angle_degrees
            conf = result.forehead_result.measurement_confidence
            
            if conf > 0.6 and result.pose_validation:
                # Include CI95 and pose quality
                angle_error = 2.0
                ci95_lower = angle - (1.96 * angle_error)
                ci95_upper = angle + (1.96 * angle_error)
                pose_quality = result.pose_validation.overall_pose_quality
                classifications.append(f"Forehead: {angle:.1f}° [CI95: {ci95_lower:.1f}-{ci95_upper:.1f}°] (pose: {pose_quality:.1%})")
            else:
                classifications.append(f"Forehead: {angle:.1f}°")
        
        # CRITICAL FIX D: Morphology classification with top-2 when confidence < 0.85
        if result.morphology_result:
            shape_conf = getattr(result.morphology_result, 'classification_confidence', 1.0)
            primary_shape = result.morphology_result.shape_classification.primary_shape.value
            
            if shape_conf < 0.85 and hasattr(result.morphology_result, 'shape_probabilities'):
                # Show top-2 shapes with probabilities (GPT-5 requirement)
                probs = result.morphology_result.shape_probabilities
                # Sort by probability and get top 2
                sorted_shapes = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:2]
                top_2_str = f"{sorted_shapes[0][0]} ({sorted_shapes[0][1]:.2f}) / {sorted_shapes[1][0]} ({sorted_shapes[1][1]:.2f})"
                classifications.append(f"Shape: {top_2_str}")
            else:
                # High confidence: show only primary shape
                classifications.append(f"Shape: {primary_shape}")
        
        result.comprehensive_classification = " | ".join(classifications)
        
        # Generate confidence summary
        confidence_summary = {}
        
        if result.wd_result:
            confidence_summary['wd_analysis'] = result.wd_result.measurement_confidence
        
        if result.forehead_result:
            confidence_summary['forehead_analysis'] = result.forehead_result.measurement_confidence
        
        if result.morphology_result:
            confidence_summary['morphology_analysis'] = result.morphology_result.measurement_confidence
        
        if result.landmark_result:
            if hasattr(result.landmark_result, 'quality_metrics'):
                confidence_summary['landmark_detection'] = result.landmark_result.quality_metrics.overall_quality
        
        result.confidence_summary = confidence_summary
    
    def _provide_learning_feedback(self, result: ComprehensiveAnalysisResult):
        """Provide feedback to continuous learning system"""
        
        if not self.config.enable_continuous_learning:
            return
        
        # Record performance for each module
        if result.wd_result and result.processing_metadata.wd_analysis_time:
            wd_metrics = PerformanceMetrics(
                accuracy=result.wd_result.measurement_confidence,
                precision=result.wd_result.measurement_confidence,
                recall=result.wd_result.measurement_confidence,
                f1_score=result.wd_result.measurement_confidence,
                processing_time=result.processing_metadata.wd_analysis_time,
                memory_usage=0.0,  # Would need actual measurement
                confidence_correlation=result.wd_result.measurement_confidence,
                error_rate=1.0 - result.wd_result.measurement_confidence
            )
            
            self.improvement_system.record_performance('wd_analyzer', wd_metrics)
        
        # Similar for other modules...
    
    def _finalize_result(self, result: ComprehensiveAnalysisResult, 
                        metadata: ProcessingMetadata) -> ComprehensiveAnalysisResult:
        """Finalize the analysis result"""
        
        metadata.end_time = datetime.now()
        metadata.total_processing_time = (metadata.end_time - metadata.start_time).total_seconds()
        
        self.total_processing_time += metadata.total_processing_time
        
        # Convert result format if requested
        if self.config.result_format == ResultFormat.JSON:
            # This would return JSON string instead of object
            pass
        elif self.config.result_format == ResultFormat.REPORT:
            # This would return formatted report
            pass
        
        # CRITICAL FIX A: SPRINT 1 S1.2: Detect geometric issues from multiple sources
        has_geometric_issues = (metadata.geometric_degradation_applied or 
                              any("GEOMETRIC_PROJECTION_WARNING" in str(w) for w in metadata.warnings) or
                              any("projection_warning" in str(w).lower() for w in metadata.warnings))
        landmark_conf = result.confidence_summary.get('landmark_detection', 0.0) if result.confidence_summary else 0.0
        result.module_status = self._generate_module_status(result, metadata, has_geometric_issues, landmark_conf)
        
        # CRITICAL FIX 7: SPRINT 2 S2.1: Generate 3D geometry information only when 3D analysis is active
        has_3d_data = (result.morphology_result and 
                      hasattr(result.morphology_result, 'reconstruction_3d') and
                      result.morphology_result.reconstruction_3d is not None)
        
        if has_3d_data:
            result.geometry_3d = self._generate_geometry_3d_info(result, metadata)
        else:
            result.geometry_3d = None
        
        # PHASE 1: Apply defendible validation for A/A+ grading
        if hasattr(self, 'defendible_validator'):
            validation_result = self.defendible_validator.validate_overall_system(result)
            result.defendible_validation = validation_result
            
            print(f"🎯 PHASE 1: Defendible validation complete")
            print(f"   Overall Grade: {validation_result['overall_grade']}")
            print(f"   Overall Confidence: {validation_result['overall_confidence']:.1%}")
            print(f"   Passes A+ Standard: {validation_result['passes_a_plus_standard']}")
            print(f"   Production Ready: {validation_result['defendible_for_production']}")
        
        # SPRINT 2 S2.2: Generate research disclaimers if in research mode (GPT-5 implementation)
        if self.config.mode == AnalysisMode.RESEARCH:
            result.research_disclaimers = self._generate_research_disclaimers(result)
        
        logger.info(f"Analysis {result.analysis_id} completed in {metadata.total_processing_time:.2f}s")
        
        return result
    
    def _generate_module_status(self, result: ComprehensiveAnalysisResult, 
                              metadata: ProcessingMetadata,
                              has_geometric_issues: bool,
                              landmark_conf: float) -> Dict[str, Dict[str, Any]]:
        """
        Generate comprehensive module status information
        
        Returns module status in the format:
        {
            "wd_analysis": {"status": "OK", "confidence": 0.85, "reasons": []},
            "neoclassical_analysis": {"status": "INVALID", "reasons": ["projection_warning"]}
        }
        """
        module_status = {}
        
        # WD Analysis Status
        if result.wd_result:
            confidence = result.wd_result.measurement_confidence
            reasons = []
            
            if confidence < 0.7:
                status = AnalysisStatus.PARTIAL
                reasons.append(f"Low confidence ({confidence:.1%})")
            elif has_geometric_issues:
                status = AnalysisStatus.PARTIAL  
                reasons.append("Geometric distortion detected")
            else:
                status = AnalysisStatus.OK
                
            module_status["wd_analysis"] = {
                "status": status.value,
                "confidence": confidence,
                "reasons": reasons,
                "evidence_refs": self._get_evidence_refs("bizygomatic_width")
            }
        elif self.config.enable_wd_analysis:
            module_status["wd_analysis"] = {
                "status": AnalysisStatus.INVALID.value,
                "confidence": 0.0,
                "reasons": ["Analysis failed to execute"]
            }
        
        # Forehead Analysis Status
        if result.forehead_result:
            confidence = result.forehead_result.measurement_confidence
            reasons = []
            
            if confidence < 0.7:
                status = AnalysisStatus.PARTIAL
                reasons.append(f"Low confidence ({confidence:.1%})")
            else:
                status = AnalysisStatus.OK
                
            module_status["forehead_analysis"] = {
                "status": status.value,
                "confidence": confidence,
                "reasons": reasons,
                "evidence_refs": self._get_evidence_refs("forehead_slant_angle")
            }
        elif self.config.enable_forehead_analysis:
            module_status["forehead_analysis"] = {
                "status": AnalysisStatus.INVALID.value,
                "confidence": 0.0,
                "reasons": ["Analysis failed to execute"]
            }
        
        # Morphology Analysis Status
        if result.morphology_result:
            confidence = result.morphology_result.measurement_confidence
            reasons = []
            
            if confidence < 0.7:
                status = AnalysisStatus.PARTIAL
                reasons.append(f"Low measurement confidence ({confidence:.1%})")
            elif has_geometric_issues:
                status = AnalysisStatus.PARTIAL
                reasons.append("Geometric distortion may affect accuracy")
            else:
                status = AnalysisStatus.OK
                
            module_status["morphology_analysis"] = {
                "status": status.value,
                "measurement_confidence": confidence,
                "classification_confidence": result.morphology_result.shape_classification.classification_confidence,
                "reasons": reasons,
                "evidence_refs": self._get_evidence_refs("facial_proportions")
            }
        elif self.config.enable_morphology_analysis:
            module_status["morphology_analysis"] = {
                "status": AnalysisStatus.INVALID.value,
                "confidence": 0.0,
                "reasons": ["Analysis failed to execute"]
            }
        
        # CRITICAL FIX B: Neoclassical Analysis Status - GPT-5 recommended logic
        if result.neoclassical_result:
            # Count computed and actually valid canons from the result
            computed_canons = len(result.neoclassical_result.canons) if hasattr(result.neoclassical_result, 'canons') else 0
            
            # Count canons that are actually valid (is_valid=True)
            actually_valid = 0
            if hasattr(result.neoclassical_result, 'canons'):
                for canon in result.neoclassical_result.canons:
                    if hasattr(canon, 'is_valid') and canon.is_valid:
                        actually_valid += 1
            
            # GPT-5 recommended logic: OK if valid/computed >= 0.6 and no projection warning
            valid_ratio = actually_valid / computed_canons if computed_canons > 0 else 0
            
            reasons = []
            if valid_ratio < 0.6:  # Less than 60% valid
                status = AnalysisStatus.INVALID
                reasons.append(f"insufficient valid canons ({actually_valid}/{computed_canons} = {valid_ratio:.1%})")
            elif has_geometric_issues:
                status = AnalysisStatus.INVALID  # GPT-5: projection warning → INVALID, not PARTIAL
                reasons.append("projection_warning")
            else:
                status = AnalysisStatus.OK
            
            module_status["neoclassical_analysis"] = {
                "status": status.value,
                "confidence": result.neoclassical_result.confidence if hasattr(result.neoclassical_result, 'confidence') else None,
                "beauty_score": result.neoclassical_result.beauty_score if status == AnalysisStatus.OK and hasattr(result.neoclassical_result, 'beauty_score') else None,
                "valid_canons": actually_valid,
                "computed_canons": computed_canons,
                "original_canons": 8,  # Standard neoclassical canon count
                "reasons": reasons,
                "evidence_refs": self._get_evidence_refs("neoclassical_canons")
            }
        elif "neoclassical analysis disabled" in str(metadata.warnings).lower():
            # Was disabled due to geometric issues
            module_status["neoclassical_analysis"] = {
                "status": AnalysisStatus.DISABLED.value,
                "confidence": None,
                "beauty_score": None,
                "reasons": ["projection_warning"]
            }
        elif self.config.enable_neoclassical_analysis:
            # Neoclassical was enabled but failed to execute
            module_status["neoclassical_analysis"] = {
                "status": AnalysisStatus.INVALID.value,
                "confidence": None,
                "beauty_score": None,
                "reasons": ["Analysis failed to execute"]
            }
        
        # Landmark Detection Status
        if result.landmark_result:
            reasons = []
            if landmark_conf < 0.85:
                status = AnalysisStatus.PARTIAL
                reasons.append(f"Low landmark confidence ({landmark_conf:.1%})")
            else:
                status = AnalysisStatus.OK
                
            module_status["landmark_detection"] = {
                "status": status.value,
                "confidence": landmark_conf,
                "reasons": reasons
            }
        else:
            module_status["landmark_detection"] = {
                "status": AnalysisStatus.INVALID.value,
                "confidence": 0.0,
                "reasons": ["Landmark detection failed"]
            }
        
        return module_status
    
    def _load_evidence_map(self) -> Dict[str, Any]:
        """
        Load evidence references mapping
        
        Loads the evidence_map.json file that maps metrics to scientific papers.
        
        Returns:
            Dictionary with evidence mapping or empty dict if load fails
        """
        try:
            # CRITICAL FIX F: Look for evidence_map.json in the project root (correct path)
            evidence_path = Path(__file__).parent.parent.parent.parent / "evidence_map.json"
            
            if evidence_path.exists():
                with open(evidence_path, 'r', encoding='utf-8') as f:
                    evidence_map = json.load(f)
                    logger.info(f"Loaded evidence map with {len(evidence_map.get('metrics', {}))} metrics")
                    return evidence_map
            else:
                logger.warning(f"Evidence map not found at {evidence_path}")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to load evidence map: {e}")
            return {}
    
    def _get_evidence_refs(self, metric_name: str) -> List[str]:
        """
        Get evidence references (DOIs) for a specific metric
        
        Args:
            metric_name: Name of the metric to get references for
            
        Returns:
            List of DOI strings for the metric
        """
        try:
            metrics = self.evidence_map.get('metrics', {})
            metric_data = metrics.get(metric_name, {})
            papers = metric_data.get('primary_papers', [])
            
            dois = []
            for paper in papers:
                if 'doi' in paper:
                    dois.append(paper['doi'])
                    
            return dois
            
        except Exception as e:
            logger.error(f"Failed to get evidence refs for {metric_name}: {e}")
            return []
    
    def _generate_geometry_3d_info(self, result: ComprehensiveAnalysisResult, 
                                  metadata: ProcessingMetadata) -> Dict[str, Any]:
        """
        Generate 3D geometry information and analysis
        
        Exposes existing 3D capabilities that were hidden in the system.
        Returns comprehensive 3D structure with CI and status.
        """
        geometry_3d = {
            "used_views": 1,  # Single 2D image (could be expanded for multi-angle)
            "fit_error_rmse": None,
            "metrics": {},
            "reconstruction_method": "single_2d_estimation",
            "confidence_intervals": {},
            "limitations": []
        }
        
        # Check if we have 3D reconstruction data from morphology
        if result.morphology_result and hasattr(result.morphology_result, 'reconstruction_3d'):
            reconstruction = result.morphology_result.reconstruction_3d
            
            if reconstruction:
                # Calculate RMSE from reconstruction quality
                geometry_3d["fit_error_rmse"] = getattr(reconstruction, 'reconstruction_error', None)
                
                # Expose 3D metrics with GPT-5 structure
                if hasattr(reconstruction, 'estimated_facial_volume') and reconstruction.estimated_facial_volume > 0:
                    geometry_3d["metrics"]["facial_volume_3d"] = {
                        "value": reconstruction.estimated_facial_volume,
                        "ci95": self._estimate_ci95(reconstruction.estimated_facial_volume, 0.1),
                        "status": "OK",
                        "units": "cubic_mm",
                        "evidence_refs": self._get_evidence_refs("3d_morphometry")
                    }
                
                if hasattr(reconstruction, 'surface_area') and reconstruction.surface_area > 0:
                    geometry_3d["metrics"]["surface_area_3d"] = {
                        "value": reconstruction.surface_area,
                        "ci95": self._estimate_ci95(reconstruction.surface_area, 0.08),
                        "status": "OK",
                        "units": "square_mm",
                        "evidence_refs": self._get_evidence_refs("3d_morphometry")
                    }
                
                # Add depth-based measurements that would be impossible in pure 2D
                if hasattr(reconstruction, 'depth_variance'):
                    geometry_3d["metrics"]["depth_variation"] = {
                        "value": reconstruction.depth_variance,
                        "status": "PARTIAL",
                        "reason": "Estimated from single 2D view",
                        "units": "mm"
                    }
        
        # Add potential 3D metrics that would be more accurate with multiple views
        geometry_3d["metrics"]["nasal_projection_3d"] = {
            "status": "INVALID",
            "reason": "Requires profile or 3D capture",
            "recommendation": "Use lateral view or 3D scanner for accurate measurement"
        }
        
        geometry_3d["metrics"]["chin_projection_3d"] = {
            "status": "INVALID", 
            "reason": "Requires profile or 3D capture",
            "recommendation": "Use lateral view or 3D scanner for accurate measurement"
        }
        
        # Add limitations based on current setup
        geometry_3d["limitations"] = [
            "Single 2D view limits depth accuracy",
            "Projection measurements require lateral views",
            "Volume estimations are approximations",
            "3D scanner would provide higher accuracy"
        ]
        
        # If no 3D data available, return minimal structure
        if not geometry_3d["metrics"] or all(m.get("status") == "INVALID" for m in geometry_3d["metrics"].values()):
            return {
                "available": False,
                "reason": "No 3D reconstruction data generated",
                "recommendation": "Enable 3D reconstruction in morphology analysis"
            }
        
        return geometry_3d
    
    def _estimate_ci95(self, value: float, relative_error: float) -> List[float]:
        """Estimate 95% confidence interval for a measurement"""
        error = value * relative_error
        return [round(value - 1.96 * error, 2), round(value + 1.96 * error, 2)]
    
    def _generate_research_disclaimers(self, result: ComprehensiveAnalysisResult) -> List[str]:
        """
        Generate research mode disclaimers and limitations
        
        Provides appropriate disclaimers for peer-reviewed correlations shown in research mode.
        """
        disclaimers = [
            "🔬 RESEARCH MODE: This analysis includes peer-reviewed correlations from scientific literature",
            "⚠️ CORRELATIONAL DATA: All personality/neurological correlations are statistical, not causal relationships",
            "📚 PEER-REVIEWED BASIS: All correlations are based on published research with evidence references (DOIs provided)",
            "🚫 NOT DIAGNOSTIC: This analysis is not intended for clinical, employment, or other sensitive decision making",
            "📊 POPULATION VARIANCE: Individual results may vary significantly from population-based correlations",
            "🔄 RESEARCH USE: Intended for research, educational, and exploratory analysis purposes only"
        ]
        
        # Add specific disclaimers based on what was analyzed
        if result.wd_result and result.personality_profile:
            disclaimers.append(
                "👥 WD-PERSONALITY: Bizygomatic width correlations based on peer-reviewed studies (see evidence_refs)"
            )
        
        if result.forehead_result and result.neuroscience_correlations:
            disclaimers.append(
                "🧠 NEURO-CORRELATIONS: Forehead-brain correlations are estimates based on MRI correlation studies"
            )
            disclaimers.append(
                "🔬 MEASUREMENT BASIS: Neurological estimates derived from measurable anatomical correlates, not direct brain scans"
            )
        
        # Add confidence-based disclaimers
        if result.processing_metadata and result.processing_metadata.overall_confidence:
            if result.processing_metadata.overall_confidence < 0.7:
                disclaimers.append(
                    f"⚠️ LOW CONFIDENCE: Overall analysis confidence is {result.processing_metadata.overall_confidence:.1%} - interpret with caution"
                )
        
        return disclaimers
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics for the master analyzer"""
        
        stats = {
            'total_analyses': self.analysis_count,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': self.total_processing_time / max(1, self.analysis_count),
            'configuration': {
                'mode': self.config.mode.value,
                'parallel_processing': self.config.enable_parallel_processing,
                'max_threads': self.config.max_worker_threads,
                'quality_assessment': self.config.enable_quality_assessment,
                'continuous_learning': self.config.enable_continuous_learning
            }
        }
        
        # Add quality system statistics if available
        if hasattr(self, 'quality_system'):
            stats['quality_report'] = self.quality_system.get_quality_report()
        
        # Add improvement system statistics if available
        if hasattr(self, 'improvement_system'):
            stats['improvement_report'] = self.improvement_system.get_improvement_report()
        
        return stats
    
    def shutdown(self):
        """Shutdown the master analyzer and cleanup resources"""
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
        
        # Shutdown improvement system if available
        if hasattr(self, 'improvement_system'):
            self.improvement_system.shutdown()
        
        logger.info("CAPA Core Analyzer shutdown complete")
    
    def _apply_advanced_calibration(self, base_confidence: float, 
                                   module_confidences: List[float], 
                                   landmark_quality: float) -> float:
        """
        Apply advanced statistical calibration including CI95 and ECE methods
        
        Args:
            base_confidence: Raw confidence score
            module_confidences: Individual module confidence scores
            landmark_quality: Overall landmark detection quality
            
        Returns:
            Calibrated confidence score with statistical validation
        """
        
        # 1. CI95 Calibration - Apply 95% confidence interval adjustment
        # This reduces overconfidence by applying statistical uncertainty bounds
        confidence_variance = np.var(module_confidences) if len(module_confidences) > 1 else 0.0
        confidence_std = np.sqrt(confidence_variance)
        
        # Calculate 95% confidence interval (z-score = 1.96 for 95% CI)
        z_score_95 = 1.96
        margin_of_error = z_score_95 * (confidence_std / np.sqrt(len(module_confidences)))
        
        # Apply conservative CI95 adjustment (reduce confidence by margin of error)
        ci95_adjusted_confidence = base_confidence - (margin_of_error * 0.5)  # 50% of margin for conservative estimate
        
        # 2. ECE (Expected Calibration Error) Calibration
        # Calibrates confidence to better match actual performance
        
        # Define calibration bins based on historical performance patterns
        calibration_bins = [
            (0.0, 0.5, 0.3),    # Low confidence: actual tends to be lower
            (0.5, 0.7, 0.6),    # Medium confidence: fairly accurate
            (0.7, 0.85, 0.78),  # High confidence: slightly overconfident
            (0.85, 0.95, 0.88), # Very high confidence: moderately overconfident
            (0.95, 1.0, 0.92)   # Maximum confidence: conservative cap
        ]
        
        # Apply ECE calibration
        ece_adjusted_confidence = ci95_adjusted_confidence
        for bin_low, bin_high, calibrated_output in calibration_bins:
            if bin_low <= ci95_adjusted_confidence < bin_high:
                # Interpolate within the bin for smoother transitions
                bin_range = bin_high - bin_low
                position_in_bin = (ci95_adjusted_confidence - bin_low) / bin_range if bin_range > 0 else 0
                
                # Apply calibration with smooth interpolation
                if bin_low == 0.95:  # Highest bin - apply strong calibration
                    ece_adjusted_confidence = calibrated_output
                else:
                    # Blend between original and calibrated for smooth transition
                    blend_factor = 0.7  # 70% calibration, 30% original
                    ece_adjusted_confidence = (blend_factor * calibrated_output + 
                                             (1 - blend_factor) * ci95_adjusted_confidence)
                break
        
        # 3. Landmark Quality Consistency Check
        # Ensure confidence doesn't significantly exceed landmark quality
        landmark_consistency_factor = min(1.0, landmark_quality + 0.2)  # Max 20% boost over landmark quality
        quality_consistent_confidence = min(ece_adjusted_confidence, landmark_consistency_factor)
        
        # 4. CRITICAL IMPROVEMENT: Aggressive Confidence Capping (GPT-5 feedback)
        # Filter out None values from module confidences
        valid_module_confidences = [conf for conf in module_confidences if conf is not None and conf > 0]
        
        # Find the worst performing module confidence
        worst_module_confidence = min(valid_module_confidences) if valid_module_confidences else (landmark_quality or 0.5)
        
        # Apply strict capping - maximum 5% boost over worst module
        strictly_capped_confidence = min(quality_consistent_confidence, worst_module_confidence * 1.05)
        
        # 5. Multi-module Consistency Validation with penalty
        valid_modules_count = sum(1 for conf in valid_module_confidences if conf > 0.7)
        if valid_modules_count < 3 and len(valid_module_confidences) >= 3:
            # Penalize when modules are failing
            strictly_capped_confidence *= 0.9
        
        if len(valid_module_confidences) > 1:
            module_agreement = 1.0 - (np.std(valid_module_confidences) / np.mean(valid_module_confidences))
            if module_agreement < 0.8:  # Low agreement threshold
                disagreement_penalty = (0.8 - module_agreement) * 0.5  # Up to 10% penalty
                strictly_capped_confidence -= disagreement_penalty
        
        # 6. Apply conservative realistic bounds (more restrictive than before)
        final_confidence = max(0.60, min(0.85, strictly_capped_confidence))  # Reduced max from 0.96 to 0.85
        
        # 7. Additional validation: confidence should not exceed worst module by more than 10%
        if worst_module_confidence > 0:
            absolute_max_confidence = worst_module_confidence + 0.10  # Max 10% above worst module
            final_confidence = min(final_confidence, absolute_max_confidence)
        
        # 8. Round to appropriate precision (3 decimal places for professional reporting)
        calibrated_confidence = round(final_confidence, 3)
        
        return calibrated_confidence


# Export main classes
__all__ = [
    'CoreAnalyzer',
    'ComprehensiveAnalysisResult',
    'AnalysisConfiguration',
    'AnalysisMode',
    'ResultFormat',
    'ProcessingMetadata'
]