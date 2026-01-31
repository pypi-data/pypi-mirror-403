"""
Pose Validation System - CAPA (Craniofacial Analysis & Prediction Architecture)

Validates pose applicability before running analysis modules to prevent
impossible measurements and improve scientific accuracy.

Version: 1.1
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PoseCompatibility(Enum):
    """Pose compatibility levels for different analysis types"""
    OPTIMAL = "optimal"        # Perfect for all measurements
    GOOD = "good"             # Good for most measurements
    ACCEPTABLE = "acceptable"  # Limited measurements possible
    POOR = "poor"             # Very limited measurements
    INVALID = "invalid"       # No reliable measurements possible


@dataclass
class PoseValidationResult:
    """Result of pose validation analysis"""
    # Pose angles
    yaw: float              # Head rotation left/right
    pitch: float            # Head rotation up/down  
    roll: float             # Head tilt left/right
    
    # Compatibility assessments
    is_frontal: bool                    # Within frontal pose range
    allows_depth_measurements: bool     # Can measure 3D projections
    allows_profile_measurements: bool   # Can measure profile features
    overall_pose_quality: float        # 0-1 quality score
    
    # Analysis module compatibility
    compatible_analyses: List[str]      # Allowed analysis modules
    disabled_analyses: List[str]        # Disabled analysis modules
    restricted_canons: List[str]        # Disabled neoclassical canons
    
    # Confidence adjustments
    pose_confidence_factor: float       # Multiplier for overall confidence
    module_confidence_adjustments: Dict[str, float]  # Per-module adjustments
    
    # Recommendations
    pose_compatibility: PoseCompatibility
    recommendations: List[str]
    warnings: List[str]


class PoseValidationSystem:
    """
    Intelligent pose validation system for CAPA analysis
    
    CRITICAL IMPROVEMENT: Prevents physically impossible measurements
    and provides transparent limitations reporting.
    """
    
    def __init__(self):
        """Initialize pose validation system"""
        self.version = "4.0.4-SCIENTIFIC"
        
        # Pose angle thresholds (based on analysis requirements)
        self.POSE_THRESHOLDS = {
            'frontal_yaw_optimal': 5.0,      # ±5° for optimal frontal
            'frontal_yaw_good': 15.0,        # ±15° for good frontal
            'frontal_yaw_limit': 25.0,       # ±25° absolute limit for frontal
            'frontal_pitch_optimal': 5.0,    # ±5° for optimal frontal
            'frontal_pitch_good': 10.0,      # ±10° for good frontal
            'frontal_pitch_limit': 20.0,     # ±20° absolute limit for frontal
            'roll_tolerance': 15.0,          # ±15° roll tolerance
            'depth_measurement_yaw_limit': 10.0,  # ±10° for depth measurements
            'profile_yaw_minimum': 30.0      # ±30° minimum for profile analysis
        }
        
        # Analysis module requirements
        self.MODULE_REQUIREMENTS = {
            'wd_analysis': {
                'max_yaw': 25.0,
                'max_pitch': 20.0,
                'max_roll': 15.0,
                'description': 'Bizygomatic width measurement'
            },
            'forehead_analysis': {
                'max_yaw': 15.0,      # Stricter for hairline visibility
                'max_pitch': 15.0,
                'max_roll': 10.0,
                'description': 'Forehead slant angle measurement'
            },
            'morphology_analysis': {
                'max_yaw': 20.0,
                'max_pitch': 15.0,
                'max_roll': 15.0,
                'description': 'Facial shape classification'
            },
            'neoclassical_analysis': {
                'max_yaw': 15.0,      # Very strict for proportional measurements
                'max_pitch': 10.0,
                'max_roll': 10.0,
                'description': 'Facial canon measurements'
            }
        }
        
        # Neoclassical canons that require specific poses
        self.CANON_POSE_REQUIREMENTS = {
            'frontal_only': [
                'facial_thirds', 'facial_fifths', 'intercanthal_distance',
                'nasofacial_proportion'
            ],
            'requires_profile': [
                'nasal_projection', 'chin_projection'
            ],
            'requires_depth': [
                'orbitonasal_proportion'  # Needs 3D depth information
            ]
        }
        
        logger.info(f"Pose Validation System v{self.version} initialized")
    
    def estimate_pose_from_landmarks(self, landmarks: np.ndarray) -> Tuple[float, float, float]:
        """
        Estimate head pose angles from facial landmarks
        
        Uses 3D head model projection for accurate pose estimation
        
        Args:
            landmarks: 68-point facial landmarks
            
        Returns:
            Tuple of (yaw, pitch, roll) angles in degrees
        """
        
        if len(landmarks) < 68:
            logger.warning("Insufficient landmarks for pose estimation")
            return 0.0, 0.0, 0.0
        
        # 3D model points (approximate head model)
        model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip (30)
            (0.0, -330.0, -65.0),        # Chin (8)
            (-225.0, 170.0, -135.0),     # Left eye left corner (36)
            (225.0, 170.0, -135.0),      # Right eye right corner (45)
            (-150.0, -150.0, -125.0),    # Left mouth corner (48)
            (150.0, -150.0, -125.0)      # Right mouth corner (54)
        ], dtype=np.float64)
        
        # 2D image points from landmarks
        image_points = np.array([
            landmarks[30],    # Nose tip
            landmarks[8],     # Chin
            landmarks[36],    # Left eye left corner
            landmarks[45],    # Right eye right corner
            landmarks[48],    # Left mouth corner
            landmarks[54]     # Right mouth corner
        ], dtype=np.float64)
        
        # Assume standard camera parameters (can be calibrated for better accuracy)
        size = (640, 480)  # Assume standard image size
        focal_length = size[1]
        center = (size[1]/2, size[0]/2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        
        # Assume no lens distortion
        dist_coeffs = np.zeros((4,1))
        
        try:
            # Solve PnP to get rotation and translation vectors
            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if not success:
                logger.warning("PnP solve failed, using geometric approximation")
                return self._geometric_pose_approximation(landmarks)
            
            # Convert rotation vector to rotation matrix
            rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
            
            # Extract Euler angles
            yaw, pitch, roll = self._rotation_matrix_to_euler_angles(rotation_matrix)
            
            # Convert to degrees and bound to reasonable ranges
            yaw_deg = np.degrees(yaw)
            pitch_deg = np.degrees(pitch)
            roll_deg = np.degrees(roll)
            
            # Bound angles to reasonable ranges
            yaw_deg = max(-90, min(90, yaw_deg))
            pitch_deg = max(-60, min(60, pitch_deg))
            roll_deg = max(-45, min(45, roll_deg))
            
            return yaw_deg, pitch_deg, roll_deg
            
        except Exception as e:
            logger.warning(f"Pose estimation failed: {e}, using geometric approximation")
            return self._geometric_pose_approximation(landmarks)
    
    def _geometric_pose_approximation(self, landmarks: np.ndarray) -> Tuple[float, float, float]:
        """Geometric approximation when 3D pose estimation fails"""
        
        # Simple geometric calculations
        # Yaw estimation from eye positions
        left_eye = np.mean(landmarks[36:42], axis=0)
        right_eye = np.mean(landmarks[42:48], axis=0)
        eye_distance = np.linalg.norm(right_eye - left_eye)
        
        # Estimate yaw from eye asymmetry
        face_center_x = (landmarks[0][0] + landmarks[16][0]) / 2
        eye_center_x = (left_eye[0] + right_eye[0]) / 2
        yaw_offset = (eye_center_x - face_center_x) / eye_distance
        yaw_approx = np.degrees(np.arcsin(np.clip(yaw_offset, -1, 1))) * 2
        
        # Pitch estimation from nose-chin relationship
        nose_tip = landmarks[30]
        chin = landmarks[8]
        nose_base = landmarks[33]
        
        face_height = np.linalg.norm(chin - nose_base)
        nose_projection = (nose_tip[1] - nose_base[1]) / face_height if face_height > 0 else 0
        pitch_approx = np.degrees(np.arcsin(np.clip(nose_projection, -1, 1))) * 3
        
        # Roll estimation from eye line angle
        eye_angle = np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0])
        roll_approx = np.degrees(eye_angle)
        
        return yaw_approx, pitch_approx, roll_approx
    
    def _rotation_matrix_to_euler_angles(self, R: np.ndarray) -> Tuple[float, float, float]:
        """Convert rotation matrix to Euler angles (yaw, pitch, roll)"""
        
        sy = np.sqrt(R[0,0] * R[0,0] + R[1,0] * R[1,0])
        singular = sy < 1e-6
        
        if not singular:
            yaw = np.arctan2(R[1,0], R[0,0])
            pitch = np.arctan2(-R[2,0], sy)
            roll = np.arctan2(R[2,1], R[2,2])
        else:
            yaw = np.arctan2(-R[1,2], R[1,1])
            pitch = np.arctan2(-R[2,0], sy)
            roll = 0
        
        return yaw, pitch, roll
    
    def validate_pose_for_analysis(self, landmarks: np.ndarray, 
                                  analysis_mode: str = 'comprehensive') -> PoseValidationResult:
        """
        Validate pose compatibility for facial analysis
        
        CRITICAL IMPROVEMENT: Prevents impossible measurements and provides
        transparent limitations reporting as recommended by GPT-5.
        
        Args:
            landmarks: 68-point facial landmarks
            analysis_mode: Type of analysis requested
            
        Returns:
            Complete pose validation result
        """
        
        # Estimate pose angles
        yaw, pitch, roll = self.estimate_pose_from_landmarks(landmarks)
        
        # Assess pose quality
        pose_quality = self._calculate_pose_quality(yaw, pitch, roll)
        
        # Determine pose compatibility
        is_frontal = (abs(yaw) <= self.POSE_THRESHOLDS['frontal_yaw_good'] and 
                     abs(pitch) <= self.POSE_THRESHOLDS['frontal_pitch_good'])
        
        allows_depth = abs(yaw) <= self.POSE_THRESHOLDS['depth_measurement_yaw_limit']
        allows_profile = abs(yaw) >= self.POSE_THRESHOLDS['profile_yaw_minimum']
        
        # Determine compatible and disabled analyses
        compatible_analyses = []
        disabled_analyses = []
        module_adjustments = {}
        
        for module, requirements in self.MODULE_REQUIREMENTS.items():
            if (abs(yaw) <= requirements['max_yaw'] and 
                abs(pitch) <= requirements['max_pitch'] and 
                abs(roll) <= requirements['max_roll']):
                compatible_analyses.append(module)
                # Calculate confidence adjustment based on pose quality
                adjustment = 1.0 - (abs(yaw) / requirements['max_yaw'] * 0.2 + 
                                  abs(pitch) / requirements['max_pitch'] * 0.2)
                module_adjustments[module] = max(0.7, adjustment)
            else:
                disabled_analyses.append(module)
                module_adjustments[module] = 0.0
        
        # Determine restricted neoclassical canons
        restricted_canons = []
        if not is_frontal:
            restricted_canons.extend(self.CANON_POSE_REQUIREMENTS['frontal_only'])
        if not allows_depth:
            restricted_canons.extend(self.CANON_POSE_REQUIREMENTS['requires_depth'])
        if not allows_profile:
            restricted_canons.extend(self.CANON_POSE_REQUIREMENTS['requires_profile'])
        
        # Determine overall pose compatibility
        if pose_quality >= 0.9 and is_frontal:
            compatibility = PoseCompatibility.OPTIMAL
        elif pose_quality >= 0.7 and is_frontal:
            compatibility = PoseCompatibility.GOOD
        elif pose_quality >= 0.5:
            compatibility = PoseCompatibility.ACCEPTABLE
        elif pose_quality >= 0.3:
            compatibility = PoseCompatibility.POOR
        else:
            compatibility = PoseCompatibility.INVALID
        
        # Generate recommendations and warnings
        recommendations, warnings = self._generate_pose_recommendations(
            yaw, pitch, roll, compatibility, disabled_analyses, restricted_canons
        )
        
        # Calculate overall confidence factor
        confidence_factor = min(1.0, pose_quality * 1.2)  # Slight boost for good poses
        
        return PoseValidationResult(
            yaw=round(yaw, 1),
            pitch=round(pitch, 1),
            roll=round(roll, 1),
            is_frontal=is_frontal,
            allows_depth_measurements=allows_depth,
            allows_profile_measurements=allows_profile,
            overall_pose_quality=round(pose_quality, 3),
            compatible_analyses=compatible_analyses,
            disabled_analyses=disabled_analyses,
            restricted_canons=restricted_canons,
            pose_confidence_factor=round(confidence_factor, 3),
            module_confidence_adjustments=module_adjustments,
            pose_compatibility=compatibility,
            recommendations=recommendations,
            warnings=warnings
        )
    
    def _calculate_pose_quality(self, yaw: float, pitch: float, roll: float) -> float:
        """Calculate overall pose quality score (0-1)"""
        
        # Calculate individual angle qualities
        yaw_quality = max(0, 1 - abs(yaw) / self.POSE_THRESHOLDS['frontal_yaw_limit'])
        pitch_quality = max(0, 1 - abs(pitch) / self.POSE_THRESHOLDS['frontal_pitch_limit'])
        roll_quality = max(0, 1 - abs(roll) / self.POSE_THRESHOLDS['roll_tolerance'])
        
        # Weighted average (yaw is most important for facial analysis)
        overall_quality = (yaw_quality * 0.5 + pitch_quality * 0.3 + roll_quality * 0.2)
        
        return max(0.0, min(1.0, overall_quality))
    
    def _generate_pose_recommendations(self, yaw: float, pitch: float, roll: float,
                                     compatibility: PoseCompatibility,
                                     disabled_analyses: List[str],
                                     restricted_canons: List[str]) -> Tuple[List[str], List[str]]:
        """Generate pose-based recommendations and warnings"""
        
        recommendations = []
        warnings = []
        
        # Angle-specific recommendations
        if abs(yaw) > self.POSE_THRESHOLDS['frontal_yaw_good']:
            if yaw > 0:
                recommendations.append("Turn head slightly to the left for better frontal view")
            else:
                recommendations.append("Turn head slightly to the right for better frontal view")
        
        if abs(pitch) > self.POSE_THRESHOLDS['frontal_pitch_good']:
            if pitch > 0:
                recommendations.append("Lower chin slightly for better frontal view")
            else:
                recommendations.append("Raise chin slightly for better frontal view")
        
        if abs(roll) > 5.0:
            if roll > 0:
                recommendations.append("Straighten head - currently tilted to the right")
            else:
                recommendations.append("Straighten head - currently tilted to the left")
        
        # Analysis-specific warnings
        if 'forehead_analysis' in disabled_analyses:
            warnings.append("Forehead analysis disabled - pose affects hairline visibility")
        
        if 'neoclassical_analysis' in disabled_analyses:
            warnings.append("Neoclassical analysis disabled - pose affects proportional measurements")
        
        if restricted_canons:
            warnings.append(f"Restricted neoclassical canons ({len(restricted_canons)}): {', '.join(restricted_canons[:3])}...")
        
        # Overall compatibility warnings
        if compatibility == PoseCompatibility.POOR:
            warnings.append("Poor pose quality - consider retaking image with better head position")
        elif compatibility == PoseCompatibility.INVALID:
            warnings.append("Invalid pose for reliable analysis - image retake strongly recommended")
        
        return recommendations, warnings


# Export main classes
__all__ = [
    'PoseValidationSystem',
    'PoseValidationResult', 
    'PoseCompatibility'
]