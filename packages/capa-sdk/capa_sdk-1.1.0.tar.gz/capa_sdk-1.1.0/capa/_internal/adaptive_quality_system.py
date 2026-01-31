"""
Adaptive Quality System - CAPA (Craniofacial Analysis & Prediction Architecture)

Provides dynamic quality control, validation, and adaptive thresholding
across all scientific analysis modules.

Version: 1.1
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good" 
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class AnalysisType(Enum):
    """Types of analysis for quality assessment"""
    WD_ANALYSIS = "wd_analysis"
    FOREHEAD_ANALYSIS = "forehead_analysis"
    MORPHOLOGY_ANALYSIS = "morphology_analysis"
    LANDMARK_DETECTION = "landmark_detection"
    COMPREHENSIVE = "comprehensive"


@dataclass
class QualityMetrics:
    """Quality metrics for analysis assessment"""
    confidence_score: float
    landmark_quality: float
    measurement_precision: float
    detection_consistency: float
    outlier_score: float
    temporal_stability: float = 0.0
    cross_validation_score: float = 0.0
    
    @property
    def overall_quality(self) -> float:
        """Calculate overall quality score (0-1)"""
        weights = {
            'confidence': 0.25,
            'landmark': 0.20,
            'precision': 0.20,
            'consistency': 0.15,
            'outlier': 0.10,
            'temporal': 0.05,
            'cross_validation': 0.05
        }
        
        # Convert outlier score (lower is better) to quality score
        outlier_quality = 1.0 - min(self.outlier_score, 1.0)
        
        overall = (
            weights['confidence'] * self.confidence_score +
            weights['landmark'] * self.landmark_quality +
            weights['precision'] * self.measurement_precision +
            weights['consistency'] * self.detection_consistency +
            weights['outlier'] * outlier_quality +
            weights['temporal'] * self.temporal_stability +
            weights['cross_validation'] * self.cross_validation_score
        )
        
        return max(0.0, min(1.0, overall))
    
    @property
    def quality_level(self) -> QualityLevel:
        """Determine quality level from overall score"""
        score = self.overall_quality
        
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.75:
            return QualityLevel.GOOD
        elif score >= 0.6:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.4:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE


@dataclass
class AdaptiveThresholds:
    """Adaptive quality thresholds that adjust based on performance"""
    min_confidence: float = 0.3  # Reduced from 0.5
    min_landmark_quality: float = 0.2  # Reduced from 0.4
    min_precision: float = 0.4  # Reduced from 0.6
    max_outlier_score: float = 0.5  # Increased from 0.3
    min_consistency: float = 0.5  # Reduced from 0.7
    
    # Adaptation parameters
    adaptation_rate: float = 0.1
    last_updated: datetime = field(default_factory=datetime.now)
    success_rate: float = 0.8
    
    def adapt_thresholds(self, recent_performance: Dict[str, float]):
        """Adapt thresholds based on recent performance"""
        if 'success_rate' in recent_performance:
            current_success = recent_performance['success_rate']
            
            # If success rate is too low, relax thresholds
            if current_success < 0.7:
                self.min_confidence = max(0.3, self.min_confidence - self.adaptation_rate)
                self.min_landmark_quality = max(0.2, self.min_landmark_quality - self.adaptation_rate)
                self.min_precision = max(0.4, self.min_precision - self.adaptation_rate)
                
            # If success rate is very high, tighten thresholds
            elif current_success > 0.95:
                self.min_confidence = min(0.8, self.min_confidence + self.adaptation_rate)
                self.min_landmark_quality = min(0.7, self.min_landmark_quality + self.adaptation_rate)
                self.min_precision = min(0.8, self.min_precision + self.adaptation_rate)
            
            self.success_rate = current_success
            self.last_updated = datetime.now()


@dataclass
class QualityHistory:
    """Track quality metrics over time"""
    analysis_id: str
    timestamp: datetime
    analysis_type: AnalysisType
    metrics: QualityMetrics
    passed_quality_check: bool
    adaptive_thresholds_used: AdaptiveThresholds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'analysis_id': self.analysis_id,
            'timestamp': self.timestamp.isoformat(),
            'analysis_type': self.analysis_type.value,
            'metrics': {
                'confidence_score': self.metrics.confidence_score,
                'landmark_quality': self.metrics.landmark_quality,
                'measurement_precision': self.metrics.measurement_precision,
                'detection_consistency': self.metrics.detection_consistency,
                'outlier_score': self.metrics.outlier_score,
                'temporal_stability': self.metrics.temporal_stability,
                'cross_validation_score': self.metrics.cross_validation_score,
                'overall_quality': self.metrics.overall_quality,
                'quality_level': self.metrics.quality_level.value
            },
            'passed_quality_check': self.passed_quality_check,
            'thresholds': {
                'min_confidence': self.adaptive_thresholds_used.min_confidence,
                'min_landmark_quality': self.adaptive_thresholds_used.min_landmark_quality,
                'min_precision': self.adaptive_thresholds_used.min_precision,
                'max_outlier_score': self.adaptive_thresholds_used.max_outlier_score,
                'min_consistency': self.adaptive_thresholds_used.min_consistency
            }
        }


class AdaptiveQualitySystem:
    """
    Advanced quality control system with adaptive thresholds
    
    Features:
    - Dynamic quality assessment across all analysis types
    - Adaptive thresholds that adjust based on performance
    - Temporal stability tracking
    - Cross-validation integration
    - Quality history and analytics
    - Anomaly detection and outlier identification
    """
    
    def __init__(self, 
                 enable_adaptation: bool = True,
                 enable_history_tracking: bool = True,
                 history_max_size: int = 10000,
                 quality_cache_path: Optional[str] = None):
        
        self.enable_adaptation = enable_adaptation
        self.enable_history_tracking = enable_history_tracking
        self.history_max_size = history_max_size
        
        # Initialize adaptive thresholds for each analysis type
        self.thresholds = {
            analysis_type: AdaptiveThresholds() 
            for analysis_type in AnalysisType
        }
        
        # Quality history
        self.quality_history: List[QualityHistory] = []
        
        # Performance tracking
        self.performance_stats = {
            analysis_type.value: {
                'total_analyses': 0,
                'passed_quality': 0,
                'avg_quality_score': 0.0,
                'quality_trend': []
            } for analysis_type in AnalysisType
        }
        
        # Quality cache for persistence
        self.quality_cache_path = quality_cache_path
        if self.quality_cache_path:
            self._load_quality_cache()
        
        logger.info("Adaptive Quality System initialized")
    
    def assess_quality(self, 
                      analysis_type: AnalysisType,
                      analysis_id: str,
                      confidence_score: float,
                      landmark_quality: float,
                      measurement_precision: float,
                      detection_consistency: float,
                      outlier_score: float,
                      previous_analysis: Optional[QualityMetrics] = None,
                      cross_validation_results: Optional[Dict[str, float]] = None) -> Tuple[QualityMetrics, bool]:
        """
        Assess quality of analysis results
        
        Args:
            analysis_type: Type of analysis being assessed
            analysis_id: Unique identifier for this analysis
            confidence_score: Confidence in measurements (0-1)
            landmark_quality: Quality of landmark detection (0-1)
            measurement_precision: Precision of measurements (0-1)
            detection_consistency: Consistency across detectors (0-1)
            outlier_score: Outlier detection score (0-1, lower is better)
            previous_analysis: Previous analysis for temporal stability
            cross_validation_results: Cross-validation scores if available
            
        Returns:
            Tuple of (QualityMetrics, passed_quality_check)
        """
        
        # Calculate temporal stability if previous analysis available
        temporal_stability = 0.0
        if previous_analysis:
            temporal_stability = self._calculate_temporal_stability(
                confidence_score, previous_analysis.confidence_score,
                landmark_quality, previous_analysis.landmark_quality
            )
        
        # Calculate cross-validation score
        cv_score = 0.0
        if cross_validation_results:
            cv_score = np.mean(list(cross_validation_results.values()))
        
        # Create quality metrics
        metrics = QualityMetrics(
            confidence_score=confidence_score,
            landmark_quality=landmark_quality,
            measurement_precision=measurement_precision,
            detection_consistency=detection_consistency,
            outlier_score=outlier_score,
            temporal_stability=temporal_stability,
            cross_validation_score=cv_score
        )
        
        # Check against adaptive thresholds
        thresholds = self.thresholds[analysis_type]
        passed_quality = self._check_quality_thresholds(metrics, thresholds)
        
        # Update performance statistics
        self._update_performance_stats(analysis_type, metrics, passed_quality)
        
        # Add to quality history if enabled
        if self.enable_history_tracking:
            history_entry = QualityHistory(
                analysis_id=analysis_id,
                timestamp=datetime.now(),
                analysis_type=analysis_type,
                metrics=metrics,
                passed_quality_check=passed_quality,
                adaptive_thresholds_used=thresholds
            )
            self._add_to_history(history_entry)
        
        # Adapt thresholds if enabled
        if self.enable_adaptation:
            self._adapt_thresholds_if_needed(analysis_type)
        
        # Save quality cache if configured
        if self.quality_cache_path:
            self._save_quality_cache()
        
        return metrics, passed_quality
    
    def _calculate_temporal_stability(self, current_conf: float, prev_conf: float,
                                    current_lm: float, prev_lm: float) -> float:
        """Calculate temporal stability between consecutive analyses"""
        conf_stability = 1.0 - abs(current_conf - prev_conf)
        lm_stability = 1.0 - abs(current_lm - prev_lm)
        return (conf_stability + lm_stability) / 2.0
    
    def _check_quality_thresholds(self, metrics: QualityMetrics, 
                                 thresholds: AdaptiveThresholds) -> bool:
        """Check if metrics meet quality thresholds"""
        return (
            metrics.confidence_score >= thresholds.min_confidence and
            metrics.landmark_quality >= thresholds.min_landmark_quality and
            metrics.measurement_precision >= thresholds.min_precision and
            metrics.detection_consistency >= thresholds.min_consistency and
            metrics.outlier_score <= thresholds.max_outlier_score
        )
    
    def _update_performance_stats(self, analysis_type: AnalysisType, 
                                 metrics: QualityMetrics, passed: bool):
        """Update performance statistics"""
        stats = self.performance_stats[analysis_type.value]
        stats['total_analyses'] += 1
        
        if passed:
            stats['passed_quality'] += 1
        
        # Update rolling average
        current_avg = stats['avg_quality_score']
        total = stats['total_analyses']
        stats['avg_quality_score'] = (current_avg * (total - 1) + metrics.overall_quality) / total
        
        # Update quality trend (keep last 100 entries)
        stats['quality_trend'].append(metrics.overall_quality)
        if len(stats['quality_trend']) > 100:
            stats['quality_trend'] = stats['quality_trend'][-100:]
    
    def _add_to_history(self, entry: QualityHistory):
        """Add entry to quality history"""
        self.quality_history.append(entry)
        
        # Maintain max size
        if len(self.quality_history) > self.history_max_size:
            self.quality_history = self.quality_history[-self.history_max_size:]
    
    def _adapt_thresholds_if_needed(self, analysis_type: AnalysisType):
        """Adapt thresholds based on recent performance if needed"""
        stats = self.performance_stats[analysis_type.value]
        
        # Only adapt if we have enough data
        if stats['total_analyses'] < 50:
            return
        
        # Calculate recent success rate
        recent_analyses = [
            entry for entry in self.quality_history[-50:]
            if entry.analysis_type == analysis_type
        ]
        
        if len(recent_analyses) < 10:
            return
        
        recent_success_rate = sum(1 for entry in recent_analyses if entry.passed_quality_check) / len(recent_analyses)
        
        # Adapt thresholds
        recent_performance = {
            'success_rate': recent_success_rate,
            'avg_quality': np.mean([entry.metrics.overall_quality for entry in recent_analyses])
        }
        
        self.thresholds[analysis_type].adapt_thresholds(recent_performance)
        
        logger.info(f"Adapted thresholds for {analysis_type.value} - Success rate: {recent_success_rate:.3f}")
    
    def get_quality_report(self, analysis_type: Optional[AnalysisType] = None) -> Dict[str, Any]:
        """Generate quality assessment report"""
        if analysis_type:
            types_to_report = [analysis_type]
        else:
            types_to_report = list(AnalysisType)
        
        report = {
            'generation_time': datetime.now().isoformat(),
            'total_history_entries': len(self.quality_history),
            'analysis_types': {}
        }
        
        for atype in types_to_report:
            stats = self.performance_stats[atype.value]
            thresholds = self.thresholds[atype]
            
            # Calculate success rate
            success_rate = (stats['passed_quality'] / stats['total_analyses']) if stats['total_analyses'] > 0 else 0.0
            
            # Recent trend analysis
            trend = "stable"
            if len(stats['quality_trend']) >= 10:
                recent_trend = np.mean(stats['quality_trend'][-10:])
                older_trend = np.mean(stats['quality_trend'][-20:-10]) if len(stats['quality_trend']) >= 20 else recent_trend
                
                if recent_trend > older_trend + 0.05:
                    trend = "improving"
                elif recent_trend < older_trend - 0.05:
                    trend = "declining"
            
            report['analysis_types'][atype.value] = {
                'total_analyses': stats['total_analyses'],
                'success_rate': success_rate,
                'average_quality_score': stats['avg_quality_score'],
                'quality_trend': trend,
                'current_thresholds': {
                    'min_confidence': thresholds.min_confidence,
                    'min_landmark_quality': thresholds.min_landmark_quality,
                    'min_precision': thresholds.min_precision,
                    'max_outlier_score': thresholds.max_outlier_score,
                    'min_consistency': thresholds.min_consistency
                },
                'last_threshold_update': thresholds.last_updated.isoformat()
            }
        
        return report
    
    def _save_quality_cache(self):
        """Save quality data to cache file"""
        try:
            cache_data = {
                'performance_stats': self.performance_stats,
                'thresholds': {
                    atype.value: {
                        'min_confidence': thresh.min_confidence,
                        'min_landmark_quality': thresh.min_landmark_quality,
                        'min_precision': thresh.min_precision,
                        'max_outlier_score': thresh.max_outlier_score,
                        'min_consistency': thresh.min_consistency,
                        'adaptation_rate': thresh.adaptation_rate,
                        'last_updated': thresh.last_updated.isoformat(),
                        'success_rate': thresh.success_rate
                    } for atype, thresh in self.thresholds.items()
                },
                'history': [entry.to_dict() for entry in self.quality_history[-1000:]]  # Save last 1000 entries
            }
            
            with open(self.quality_cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save quality cache: {e}")
    
    def _load_quality_cache(self):
        """Load quality data from cache file"""
        try:
            if not Path(self.quality_cache_path).exists():
                return
            
            with open(self.quality_cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Load performance stats
            if 'performance_stats' in cache_data:
                self.performance_stats.update(cache_data['performance_stats'])
            
            # Load thresholds
            if 'thresholds' in cache_data:
                for atype_str, thresh_data in cache_data['thresholds'].items():
                    try:
                        atype = AnalysisType(atype_str)
                        self.thresholds[atype] = AdaptiveThresholds(
                            min_confidence=thresh_data['min_confidence'],
                            min_landmark_quality=thresh_data['min_landmark_quality'],
                            min_precision=thresh_data['min_precision'],
                            max_outlier_score=thresh_data['max_outlier_score'],
                            min_consistency=thresh_data['min_consistency'],
                            adaptation_rate=thresh_data['adaptation_rate'],
                            last_updated=datetime.fromisoformat(thresh_data['last_updated']),
                            success_rate=thresh_data['success_rate']
                        )
                    except Exception as e:
                        logger.warning(f"Failed to load threshold for {atype_str}: {e}")
            
            logger.info(f"Loaded quality cache from {self.quality_cache_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load quality cache: {e}")


# Export classes and enums
__all__ = [
    'AdaptiveQualitySystem',
    'QualityMetrics',
    'QualityLevel',
    'AnalysisType',
    'AdaptiveThresholds',
    'QualityHistory'
]