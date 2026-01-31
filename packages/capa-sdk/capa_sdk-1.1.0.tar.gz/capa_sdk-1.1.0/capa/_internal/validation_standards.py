"""
CAPA Validation Standards
=========================

Defines defendible performance standards based on measurability,
consistency, and calibration rather than inflated metrics.

CAPA - Craniofacial Analysis & Prediction Architecture
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


class PerformanceGrade(Enum):
    """Defendible performance grades"""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    INVALID = "INVALID"


@dataclass
class ValidationStandards:
    """Defendible validation standards for A/A+ grading"""
    
    # Landmark accuracy standards (NME - Normalized Mean Error)
    LANDMARK_NME_A_PLUS = 0.025  # ≤2.5% for A+
    LANDMARK_NME_A = 0.035       # ≤3.5% for A
    LANDMARK_NME_B = 0.045       # ≤4.5% for B
    
    # WD Analysis standards
    WD_CONFIDENCE_A_PLUS = 0.92  # ≥92% confidence for A+
    WD_CONFIDENCE_A = 0.85       # ≥85% confidence for A
    WD_ERROR_THRESHOLD = 0.05    # ≤5% test-retest error
    
    # Neoclassical standards
    NEO_VALID_CANONS_A_PLUS = 0.875  # ≥87.5% (7/8) valid canons for A+
    NEO_VALID_CANONS_A = 0.75        # ≥75% (6/8) valid canons for A
    NEO_DEVIATION_THRESHOLD = 80.0   # >80% deviation = invalid
    
    # Calibration standards (ECE - Expected Calibration Error)
    ECE_A_PLUS = 0.03     # <3% miscalibration for A+
    ECE_A = 0.05          # <5% miscalibration for A
    
    # Overall system standards
    OVERALL_CONFIDENCE_A_PLUS = 0.92
    OVERALL_CONFIDENCE_A = 0.85
    
    # Confidence interval standards
    CI95_WIDTH_TARGET = 0.10  # Target CI95 width relative to mean


class DefendibleValidator:
    """Validator for defendible A/A+ standards"""
    
    def __init__(self):
        self.standards = ValidationStandards()
    
    def validate_wd_analysis(self, wd_result, test_retest_data: Optional[List] = None) -> Dict:
        """
        Validate WD analysis with defendible standards
        
        Returns:
            Dict with grade, confidence, and validation metrics
        """
        confidence = getattr(wd_result, 'measurement_confidence', 0.0)
        
        # Conservative grading - no inflation
        if confidence >= self.standards.WD_CONFIDENCE_A_PLUS:
            grade = PerformanceGrade.A_PLUS
        elif confidence >= self.standards.WD_CONFIDENCE_A:
            grade = PerformanceGrade.A
        elif confidence >= 0.75:
            grade = PerformanceGrade.B_PLUS
        elif confidence >= 0.65:
            grade = PerformanceGrade.B
        elif confidence >= 0.55:
            grade = PerformanceGrade.C_PLUS
        else:
            grade = PerformanceGrade.C
        
        # Test-retest validation if available
        test_retest_error = None
        if test_retest_data and len(test_retest_data) > 1:
            values = [float(x) for x in test_retest_data]
            test_retest_error = np.std(values) / np.mean(values)  # Coefficient of variation
            
            # Penalize if test-retest error too high
            if test_retest_error > self.standards.WD_ERROR_THRESHOLD:
                grade = PerformanceGrade.C_PLUS  # Demote for poor reproducibility
        
        return {
            'grade': grade.value,
            'confidence': confidence,
            'test_retest_error': test_retest_error,
            'passes_defendible_standard': grade.value in ['A+', 'A'],
            'limitations': self._get_wd_limitations(wd_result)
        }
    
    def validate_neoclassical_analysis(self, neo_result, pose_data: Optional[Dict] = None) -> Dict:
        """
        Validate neoclassical analysis with measurability focus
        
        Returns:
            Dict with grade, valid canon ratio, and measurability assessment
        """
        canons = getattr(neo_result, 'canons', [])
        total_canons = len(canons)
        
        # Count actually valid canons (not just computed)
        valid_canons = sum(1 for canon in canons if getattr(canon, 'is_valid', False))
        
        if total_canons == 0:
            return {
                'grade': PerformanceGrade.INVALID.value,
                'valid_ratio': 0.0,
                'measurable_canons': 0,
                'passes_defendible_standard': False
            }
        
        valid_ratio = valid_canons / total_canons
        
        # Conservative grading based on valid ratio
        if valid_ratio >= self.standards.NEO_VALID_CANONS_A_PLUS:
            grade = PerformanceGrade.A_PLUS
        elif valid_ratio >= self.standards.NEO_VALID_CANONS_A:
            grade = PerformanceGrade.A
        elif valid_ratio >= 0.625:  # 5/8 canons
            grade = PerformanceGrade.B_PLUS
        elif valid_ratio >= 0.5:    # 4/8 canons
            grade = PerformanceGrade.B
        elif valid_ratio >= 0.375:  # 3/8 canons
            grade = PerformanceGrade.C_PLUS
        else:
            grade = PerformanceGrade.C
        
        # Check measurability constraints
        measurable_assessment = self._assess_canon_measurability(canons, pose_data)
        
        return {
            'grade': grade.value,
            'valid_ratio': valid_ratio,
            'valid_canons': valid_canons,
            'total_canons': total_canons,
            'measurable_canons': measurable_assessment['measurable_count'],
            'passes_defendible_standard': grade.value in ['A+', 'A'],
            'measurability_assessment': measurable_assessment
        }
    
    def validate_overall_system(self, analysis_result) -> Dict:
        """
        Validate overall system performance with conservative standards
        
        Returns:
            Dict with overall grade and module breakdown
        """
        module_validations = {}
        
        # Validate each module
        if hasattr(analysis_result, 'wd_result') and analysis_result.wd_result:
            module_validations['wd'] = self.validate_wd_analysis(analysis_result.wd_result)
        
        if hasattr(analysis_result, 'neoclassical_result') and analysis_result.neoclassical_result:
            pose_data = getattr(analysis_result, 'pose_validation', None)
            module_validations['neoclassical'] = self.validate_neoclassical_analysis(
                analysis_result.neoclassical_result, pose_data
            )
        
        # Overall grade = min of all module grades (conservative)
        module_grades = []
        for module, validation in module_validations.items():
            grade_str = validation['grade']
            if grade_str in ['A+', 'A', 'B+', 'B', 'C+', 'C']:
                module_grades.append(self._grade_to_numeric(grade_str))
        
        if not module_grades:
            overall_grade = PerformanceGrade.INVALID
        else:
            # Take minimum grade (most conservative)
            min_grade_num = min(module_grades)
            overall_grade = self._numeric_to_grade(min_grade_num)
        
        # Overall confidence = minimum of module confidences (conservative)
        confidences = []
        if 'wd' in module_validations:
            confidences.append(module_validations['wd']['confidence'])
        if hasattr(analysis_result, 'morphology_result') and analysis_result.morphology_result:
            confidences.append(getattr(analysis_result.morphology_result, 'measurement_confidence', 0.0))
        if hasattr(analysis_result, 'forehead_result') and analysis_result.forehead_result:
            confidences.append(getattr(analysis_result.forehead_result, 'measurement_confidence', 0.0))
        
        overall_confidence = min(confidences) if confidences else 0.0
        
        return {
            'overall_grade': overall_grade.value,
            'overall_confidence': overall_confidence,
            'module_validations': module_validations,
            'passes_a_plus_standard': overall_grade == PerformanceGrade.A_PLUS,
            'passes_a_standard': overall_grade.value in ['A+', 'A'],
            'defendible_for_production': overall_grade.value in ['A+', 'A', 'B+']
        }
    
    def _get_wd_limitations(self, wd_result) -> List[str]:
        """Get limitations for WD analysis"""
        limitations = []
        
        confidence = getattr(wd_result, 'measurement_confidence', 0.0)
        
        if confidence < 0.7:
            limitations.append("Confidence insufficient for categorical labels")
        if confidence < 0.85:
            limitations.append("Use only for exploratory analysis")
        if not hasattr(wd_result, 'demographic_reference'):
            limitations.append("No population reference for percentiles")
        
        return limitations
    
    def _assess_canon_measurability(self, canons: List, pose_data: Optional[Dict]) -> Dict:
        """Assess which canons are actually measurable given constraints"""
        
        measurable_count = 0
        projection_canons = ['Orbitonasal Proportion', 'Chin Projection', 'Nasal Projection']
        
        for canon in canons:
            canon_name = getattr(canon, 'canon_name', '')
            
            # Check if 3D projection canons are measurable from current pose
            if canon_name in projection_canons:
                if pose_data and abs(pose_data.get('yaw', 0)) < 15:
                    continue  # Not measurable from frontal pose
            
            measurable_count += 1
        
        return {
            'measurable_count': measurable_count,
            'total_canons': len(canons),
            'measurability_ratio': measurable_count / len(canons) if canons else 0.0
        }
    
    def _grade_to_numeric(self, grade_str: str) -> float:
        """Convert grade string to numeric for comparison"""
        grade_map = {
            'A+': 4.0,
            'A': 3.7,
            'B+': 3.3,
            'B': 3.0,
            'C+': 2.3,
            'C': 2.0,
            'D': 1.0
        }
        return grade_map.get(grade_str, 0.0)
    
    def _numeric_to_grade(self, numeric: float) -> PerformanceGrade:
        """Convert numeric back to grade"""
        if numeric >= 4.0:
            return PerformanceGrade.A_PLUS
        elif numeric >= 3.7:
            return PerformanceGrade.A
        elif numeric >= 3.3:
            return PerformanceGrade.B_PLUS
        elif numeric >= 3.0:
            return PerformanceGrade.B
        elif numeric >= 2.3:
            return PerformanceGrade.C_PLUS
        elif numeric >= 2.0:
            return PerformanceGrade.C
        else:
            return PerformanceGrade.D