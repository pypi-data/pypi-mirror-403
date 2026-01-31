"""
Multi-Angle Analysis System - CAPA (Craniofacial Analysis & Prediction Architecture)

Sistema para análisis de múltiples ángulos del mismo individuo.
Combina y correlaciona información de diferentes vistas faciales.

Version: 1.1
"""

import numpy as np
import cv2
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

from .core_analyzer import (
    CoreAnalyzer, ComprehensiveAnalysisResult, AnalysisConfiguration
)

logger = logging.getLogger(__name__)


@dataclass
class AngleSpecification:
    """Specification for image angle"""
    angle_type: str  # 'frontal', 'lateral_left', 'lateral_right', 'semi_frontal', 'profile'
    image_path: str
    weight: float = 1.0  # Weight for combining results
    quality_threshold: float = 0.3  # Minimum quality threshold


@dataclass
class MultiAngleResult:
    """Result from multi-angle analysis"""
    subject_id: str
    analysis_id: str
    timestamp: datetime
    
    # Individual angle results
    angle_results: Dict[str, ComprehensiveAnalysisResult] = field(default_factory=dict)
    
    # Combined analysis
    combined_wd_value: Optional[float] = None
    combined_forehead_angle: Optional[float] = None
    combined_face_shape: Optional[str] = None
    combined_confidence: Optional[float] = None
    
    # Quality metrics
    overall_quality: Optional[float] = None
    angle_qualities: Dict[str, float] = field(default_factory=dict)
    
    # Correlations between angles
    inter_angle_correlations: Dict[str, float] = field(default_factory=dict)
    consistency_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Recommendations
    best_angle_for_wd: Optional[str] = None
    best_angle_for_forehead: Optional[str] = None
    best_angle_for_morphology: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            'subject_id': self.subject_id,
            'analysis_id': self.analysis_id,
            'timestamp': self.timestamp.isoformat(),
            'combined_analysis': {
                'wd_value': self.combined_wd_value,
                'forehead_angle': self.combined_forehead_angle,
                'face_shape': self.combined_face_shape,
                'confidence': self.combined_confidence
            },
            'quality_metrics': {
                'overall_quality': self.overall_quality,
                'angle_qualities': self.angle_qualities
            },
            'correlations': self.inter_angle_correlations,
            'consistency': self.consistency_metrics,
            'recommendations': {
                'best_wd_angle': self.best_angle_for_wd,
                'best_forehead_angle': self.best_angle_for_forehead,
                'best_morphology_angle': self.best_angle_for_morphology
            },
            'individual_results': {}
        }
        
        # Add individual angle results
        for angle, analysis_result in self.angle_results.items():
            try:
                result['individual_results'][angle] = analysis_result.to_dict()
            except Exception as e:
                logger.warning(f"Could not serialize result for angle {angle}: {e}")
                result['individual_results'][angle] = {'error': str(e)}
        
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class MultiAngleAnalyzer:
    """
    Analyzer for multiple angles of the same individual
    
    Features:
    - Supports multiple angle types (frontal, lateral, profile, etc.)
    - Combines results intelligently based on angle quality
    - Provides correlation analysis between different views
    - Optimizes analysis order based on success probability
    """
    
    def __init__(self, config: Optional[AnalysisConfiguration] = None):
        self.config = config or AnalysisConfiguration()
        self.master_analyzer = CoreAnalyzer(config=self.config)
        
        # Angle specifications and weights
        self.angle_weights = {
            'frontal': 1.0,
            'lateral_left': 0.8,
            'lateral_right': 0.8,
            'semi_frontal': 0.9,
            'profile': 0.7,
            'three_quarter': 0.85
        }
        
        # Analysis type preferences for different angles
        self.analysis_preferences = {
            'wd_analysis': ['frontal', 'semi_frontal'],
            'forehead_analysis': ['frontal', 'lateral_left', 'lateral_right'],
            'morphology_analysis': ['frontal', 'semi_frontal', 'three_quarter']
        }
        
        logger.info("Multi-Angle Analyzer initialized")
    
    def analyze_multiple_angles(self, 
                              angle_specs: List[AngleSpecification],
                              subject_id: str,
                              analysis_id: Optional[str] = None) -> MultiAngleResult:
        """
        Analyze multiple angles of the same individual
        
        Args:
            angle_specs: List of angle specifications
            subject_id: Identifier for the subject
            analysis_id: Optional analysis identifier
            
        Returns:
            MultiAngleResult with combined analysis
        """
        
        if analysis_id is None:
            analysis_id = f"MULTI_ANGLE_{subject_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting multi-angle analysis for subject {subject_id}")
        
        # Initialize result
        result = MultiAngleResult(
            subject_id=subject_id,
            analysis_id=analysis_id,
            timestamp=datetime.now()
        )
        
        # Analyze each angle
        successful_analyses = {}
        failed_angles = []
        
        for angle_spec in angle_specs:
            try:
                logger.info(f"Analyzing {angle_spec.angle_type} angle: {angle_spec.image_path}")
                
                # Perform individual analysis
                individual_result = self.master_analyzer.analyze_image(
                    image=angle_spec.image_path,
                    analysis_id=f"{analysis_id}_{angle_spec.angle_type}",
                    subject_id=subject_id,
                    angle_type=angle_spec.angle_type
                )
                
                # Check quality
                quality = self._assess_angle_quality(individual_result, angle_spec.angle_type)
                result.angle_qualities[angle_spec.angle_type] = quality
                
                if quality >= angle_spec.quality_threshold:
                    successful_analyses[angle_spec.angle_type] = individual_result
                    result.angle_results[angle_spec.angle_type] = individual_result
                    logger.info(f"✅ {angle_spec.angle_type} analysis successful (quality: {quality:.3f})")
                else:
                    failed_angles.append(angle_spec.angle_type)
                    logger.warning(f"⚠️ {angle_spec.angle_type} analysis below quality threshold ({quality:.3f})")
                
            except Exception as e:
                logger.error(f"❌ {angle_spec.angle_type} analysis failed: {e}")
                failed_angles.append(angle_spec.angle_type)
                result.angle_qualities[angle_spec.angle_type] = 0.0
        
        if not successful_analyses:
            logger.error("No successful angle analyses")
            return result
        
        # Combine results
        self._combine_analysis_results(result, successful_analyses)
        
        # Calculate correlations
        self._calculate_inter_angle_correlations(result, successful_analyses)
        
        # Generate recommendations
        self._generate_angle_recommendations(result, successful_analyses)
        
        logger.info(f"Multi-angle analysis completed: {len(successful_analyses)} successful, {len(failed_angles)} failed")
        
        return result
    
    def _assess_angle_quality(self, analysis_result: ComprehensiveAnalysisResult, angle_type: str) -> float:
        """Assess quality of analysis for specific angle"""
        
        try:
            qualities = []
            
            # Landmark quality
            if analysis_result.landmark_result and hasattr(analysis_result.landmark_result, 'quality_metrics'):
                qualities.append(analysis_result.landmark_result.quality_metrics.overall_quality)
            
            # Individual analysis confidences
            if analysis_result.wd_result:
                qualities.append(analysis_result.wd_result.measurement_confidence)
            
            if analysis_result.forehead_result:
                qualities.append(analysis_result.forehead_result.measurement_confidence)
            
            if analysis_result.morphology_result:
                qualities.append(analysis_result.morphology_result.measurement_confidence)
            
            # Overall confidence from metadata
            if (analysis_result.processing_metadata and 
                analysis_result.processing_metadata.overall_confidence):
                qualities.append(analysis_result.processing_metadata.overall_confidence)
            
            if qualities:
                base_quality = np.mean(qualities)
                
                # Apply angle-specific weights
                angle_weight = self.angle_weights.get(angle_type, 0.5)
                
                return float(base_quality * angle_weight)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Could not assess quality for {angle_type}: {e}")
            return 0.0
    
    def _combine_analysis_results(self, result: MultiAngleResult, 
                                successful_analyses: Dict[str, ComprehensiveAnalysisResult]):
        """Combine results from multiple angles"""
        
        try:
            # Combine WD values
            wd_values = []
            wd_weights = []
            
            for angle, analysis in successful_analyses.items():
                if analysis.wd_result:
                    weight = self.angle_weights.get(angle, 0.5)
                    if angle in self.analysis_preferences['wd_analysis']:
                        weight *= 1.2  # Boost preferred angles
                    
                    wd_values.append(analysis.wd_result.wd_value)
                    wd_weights.append(weight)
            
            if wd_values:
                result.combined_wd_value = float(np.average(wd_values, weights=wd_weights))
            
            # Combine forehead angles
            forehead_angles = []
            forehead_weights = []
            
            for angle, analysis in successful_analyses.items():
                if analysis.forehead_result:
                    weight = self.angle_weights.get(angle, 0.5)
                    if angle in self.analysis_preferences['forehead_analysis']:
                        weight *= 1.2
                    
                    forehead_angles.append(analysis.forehead_result.forehead_geometry.slant_angle_degrees)
                    forehead_weights.append(weight)
            
            if forehead_angles:
                result.combined_forehead_angle = float(np.average(forehead_angles, weights=forehead_weights))
            
            # Combine face shapes (most frequent with weights)
            face_shapes = {}
            
            for angle, analysis in successful_analyses.items():
                if analysis.morphology_result:
                    shape = analysis.morphology_result.shape_classification.primary_shape.value
                    weight = self.angle_weights.get(angle, 0.5)
                    if angle in self.analysis_preferences['morphology_analysis']:
                        weight *= 1.2
                    
                    face_shapes[shape] = face_shapes.get(shape, 0) + weight
            
            if face_shapes:
                result.combined_face_shape = max(face_shapes, key=face_shapes.get)
            
            # Calculate combined confidence
            confidences = []
            conf_weights = []
            
            for angle, analysis in successful_analyses.items():
                if analysis.processing_metadata and analysis.processing_metadata.overall_confidence:
                    weight = self.angle_weights.get(angle, 0.5)
                    confidences.append(analysis.processing_metadata.overall_confidence)
                    conf_weights.append(weight)
            
            if confidences:
                result.combined_confidence = float(np.average(confidences, weights=conf_weights))
            
            # Calculate overall quality
            qualities = list(result.angle_qualities.values())
            if qualities:
                result.overall_quality = float(np.mean(qualities))
            
        except Exception as e:
            logger.error(f"Error combining analysis results: {e}")
    
    def _calculate_inter_angle_correlations(self, result: MultiAngleResult,
                                          successful_analyses: Dict[str, ComprehensiveAnalysisResult]):
        """Calculate correlations between different angle analyses"""
        
        try:
            angles = list(successful_analyses.keys())
            
            # WD value correlations
            wd_values = {}
            for angle, analysis in successful_analyses.items():
                if analysis.wd_result:
                    wd_values[angle] = analysis.wd_result.wd_value
            
            if len(wd_values) >= 2:
                wd_list = list(wd_values.values())
                wd_std = np.std(wd_list)
                wd_mean = np.mean(wd_list)
                if wd_mean != 0:
                    result.inter_angle_correlations['wd_consistency'] = float(1.0 - (wd_std / abs(wd_mean)))
                else:
                    result.inter_angle_correlations['wd_consistency'] = 1.0
            
            # Confidence correlations
            confidences = {}
            for angle, analysis in successful_analyses.items():
                if analysis.processing_metadata and analysis.processing_metadata.overall_confidence:
                    confidences[angle] = analysis.processing_metadata.overall_confidence
            
            if len(confidences) >= 2:
                conf_list = list(confidences.values())
                conf_std = np.std(conf_list)
                result.consistency_metrics['confidence_consistency'] = float(1.0 - conf_std)
            
            # Shape consistency
            shapes = {}
            for angle, analysis in successful_analyses.items():
                if analysis.morphology_result:
                    shape = analysis.morphology_result.shape_classification.primary_shape.value
                    shapes[angle] = shape
            
            if len(shapes) >= 2:
                unique_shapes = len(set(shapes.values()))
                total_shapes = len(shapes)
                result.consistency_metrics['shape_consistency'] = float(1.0 - (unique_shapes - 1) / total_shapes)
            
        except Exception as e:
            logger.warning(f"Error calculating correlations: {e}")
    
    def _generate_angle_recommendations(self, result: MultiAngleResult,
                                      successful_analyses: Dict[str, ComprehensiveAnalysisResult]):
        """Generate recommendations for best angles for each analysis type"""
        
        try:
            # Best angle for WD analysis
            best_wd_quality = 0
            for angle, analysis in successful_analyses.items():
                if analysis.wd_result:
                    quality = analysis.wd_result.measurement_confidence
                    if quality > best_wd_quality:
                        best_wd_quality = quality
                        result.best_angle_for_wd = angle
            
            # Best angle for forehead analysis
            best_forehead_quality = 0
            for angle, analysis in successful_analyses.items():
                if analysis.forehead_result:
                    quality = analysis.forehead_result.measurement_confidence
                    if quality > best_forehead_quality:
                        best_forehead_quality = quality
                        result.best_angle_for_forehead = angle
            
            # Best angle for morphology analysis
            best_morphology_quality = 0
            for angle, analysis in successful_analyses.items():
                if analysis.morphology_result:
                    quality = analysis.morphology_result.measurement_confidence
                    if quality > best_morphology_quality:
                        best_morphology_quality = quality
                        result.best_angle_for_morphology = angle
        
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
    
    def analyze_from_paths(self, image_paths: List[str], subject_id: str,
                          angle_types: Optional[List[str]] = None) -> MultiAngleResult:
        """
        Convenience method to analyze from image paths
        
        Args:
            image_paths: List of image file paths
            subject_id: Subject identifier
            angle_types: Optional list of angle types (auto-detected if None)
            
        Returns:
            MultiAngleResult
        """
        
        if angle_types is None:
            # Auto-detect angle types based on filename or order
            angle_types = self._auto_detect_angles(image_paths)
        
        # Create angle specifications
        angle_specs = []
        for i, (path, angle_type) in enumerate(zip(image_paths, angle_types)):
            spec = AngleSpecification(
                angle_type=angle_type,
                image_path=path,
                weight=self.angle_weights.get(angle_type, 0.5)
            )
            angle_specs.append(spec)
        
        return self.analyze_multiple_angles(angle_specs, subject_id)
    
    def _auto_detect_angles(self, image_paths: List[str]) -> List[str]:
        """Auto-detect angle types from filenames or order"""
        
        detected_angles = []
        
        for path in image_paths:
            filename = Path(path).stem.lower()
            
            if any(term in filename for term in ['frontal', 'front', 'face']):
                detected_angles.append('frontal')
            elif any(term in filename for term in ['lateral', 'side', 'left']):
                detected_angles.append('lateral_left')
            elif any(term in filename for term in ['right']):
                detected_angles.append('lateral_right')
            elif any(term in filename for term in ['profile', 'perfil']):
                detected_angles.append('profile')
            elif any(term in filename for term in ['semi', 'three', 'quarter']):
                detected_angles.append('semi_frontal')
            else:
                # Default assignment based on order
                if len(detected_angles) == 0:
                    detected_angles.append('frontal')
                elif len(detected_angles) == 1:
                    detected_angles.append('lateral_left')
                elif len(detected_angles) == 2:
                    detected_angles.append('lateral_right')
                else:
                    detected_angles.append('semi_frontal')
        
        return detected_angles
    
    def shutdown(self):
        """Shutdown the multi-angle analyzer"""
        self.master_analyzer.shutdown()
        logger.info("Multi-Angle Analyzer shutdown complete")


# Export main classes
__all__ = [
    'MultiAngleAnalyzer',
    'MultiAngleResult',
    'AngleSpecification'
]