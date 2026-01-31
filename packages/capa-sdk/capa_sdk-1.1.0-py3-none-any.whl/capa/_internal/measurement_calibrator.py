"""
Measurement Calibrator - CAPA (Craniofacial Analysis & Prediction Architecture)

Provides pixel-to-millimeter calibration for accurate craniofacial measurements.

Scientific Requirement:
Anthropometric measurements must be in standardized units (millimeters) to be
comparable with research data and population norms. This module provides multiple
calibration methods to convert pixel measurements to real-world units.

Calibration Methods:
1. Reference Object: Known-size object in the image (ruler, card, coin)
2. Interpupillary Distance (IPD): Using population average IPD
3. Facial Feature Reference: Using known average measurements
4. Manual Calibration: User-provided scale factor

Version: 1.1
"""

import numpy as np
from typing import Dict, Tuple, Optional, List, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CalibrationMethod(Enum):
    """Available calibration methods"""
    REFERENCE_OBJECT = "reference_object"      # Known-size object in image
    INTERPUPILLARY_DISTANCE = "ipd"            # Using IPD standard
    FACIAL_FEATURE = "facial_feature"          # Using facial feature averages
    MANUAL = "manual"                          # User-provided scale
    UNCALIBRATED = "uncalibrated"              # No calibration (pixels only)


@dataclass
class CalibrationResult:
    """Result of calibration process"""
    method: CalibrationMethod
    pixels_per_mm: float                       # Conversion factor
    mm_per_pixel: float                        # Inverse conversion
    confidence: float                          # Calibration confidence (0-1)
    reference_used: str                        # What was used as reference
    reference_value_mm: float                  # Known size in mm
    reference_value_px: float                  # Measured size in pixels
    metadata: Dict[str, Any]                   # Additional calibration data

    def convert_px_to_mm(self, pixels: float) -> float:
        """Convert pixel measurement to millimeters"""
        return pixels * self.mm_per_pixel

    def convert_mm_to_px(self, mm: float) -> float:
        """Convert millimeter measurement to pixels"""
        return mm * self.pixels_per_mm

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'method': self.method.value,
            'pixels_per_mm': self.pixels_per_mm,
            'mm_per_pixel': self.mm_per_pixel,
            'confidence': self.confidence,
            'reference_used': self.reference_used,
            'reference_value_mm': self.reference_value_mm,
            'reference_value_px': self.reference_value_px,
            'metadata': self.metadata
        }


class MeasurementCalibrator:
    """
    Universal measurement calibrator for craniofacial analysis.

    Provides multiple methods to establish pixel-to-millimeter conversion
    for accurate anthropometric measurements.
    """

    # Population average values from anthropometric studies
    # Sources: Farkas (1994), Doddi & Eccles (2010), various population studies
    POPULATION_AVERAGES = {
        'ipd': {  # Interpupillary Distance
            'male': {
                'mean': 64.0,      # mm
                'std': 3.5,
                'range': (58, 70)
            },
            'female': {
                'mean': 62.0,      # mm
                'std': 3.2,
                'range': (56, 68)
            },
            'average': {
                'mean': 63.0,      # mm
                'std': 3.5,
                'range': (56, 70)
            }
        },
        'bizygomatic_width': {  # Cheekbone width
            'male': {
                'mean': 137.0,    # mm
                'std': 6.5,
                'range': (125, 150)
            },
            'female': {
                'mean': 128.0,    # mm
                'std': 5.8,
                'range': (118, 140)
            }
        },
        'bigonial_width': {  # Jaw width
            'male': {
                'mean': 106.0,    # mm
                'std': 7.2,
                'range': (92, 120)
            },
            'female': {
                'mean': 97.0,     # mm
                'std': 6.1,
                'range': (85, 110)
            }
        },
        'face_height': {  # Trichion to Gnathion
            'male': {
                'mean': 182.0,    # mm
                'std': 10.5,
                'range': (165, 200)
            },
            'female': {
                'mean': 171.0,    # mm
                'std': 9.2,
                'range': (155, 190)
            }
        },
        'nasal_width': {
            'male': {
                'mean': 35.0,     # mm
                'std': 3.5,
                'range': (28, 42)
            },
            'female': {
                'mean': 31.0,     # mm
                'std': 3.0,
                'range': (25, 38)
            }
        },
        'mouth_width': {
            'male': {
                'mean': 53.0,     # mm
                'std': 4.2,
                'range': (45, 62)
            },
            'female': {
                'mean': 50.0,     # mm
                'std': 3.8,
                'range': (43, 58)
            }
        }
    }

    # Standard reference objects
    REFERENCE_OBJECTS = {
        'credit_card': {
            'width_mm': 85.6,
            'height_mm': 53.98,
            'description': 'ISO/IEC 7810 ID-1 standard credit card'
        },
        'us_quarter': {
            'diameter_mm': 24.26,
            'description': 'US Quarter dollar coin'
        },
        'euro_1': {
            'diameter_mm': 23.25,
            'description': '1 Euro coin'
        },
        'ruler_cm': {
            'unit_mm': 10.0,
            'description': 'Standard ruler centimeter marks'
        },
        'a4_paper': {
            'width_mm': 210.0,
            'height_mm': 297.0,
            'description': 'A4 paper sheet'
        }
    }

    def __init__(self):
        """Initialize calibrator"""
        self.current_calibration: Optional[CalibrationResult] = None
        self.calibration_history: List[CalibrationResult] = []
        logger.info("MeasurementCalibrator initialized")

    def calibrate_from_ipd(self, ipd_pixels: float,
                           gender: str = 'average',
                           custom_ipd_mm: Optional[float] = None) -> CalibrationResult:
        """
        Calibrate using Interpupillary Distance (IPD).

        IPD is a reliable reference because:
        1. Easy to measure from landmarks (eye centers)
        2. Relatively consistent within populations
        3. Less affected by expression than other features

        Scientific Reference:
        - Doddi & Eccles (2010): Average adult IPD 63mm (range 54-74mm)
        - Farkas (1994): Male 64mm, Female 62mm

        Args:
            ipd_pixels: Measured IPD in pixels (from eye center to eye center)
            gender: 'male', 'female', or 'average' for population norms
            custom_ipd_mm: Optional known IPD in mm (overrides population average)

        Returns:
            CalibrationResult with conversion factors
        """
        # Get reference IPD value
        if custom_ipd_mm is not None:
            ipd_mm = custom_ipd_mm
            confidence = 0.95  # High confidence with known value
            reference_note = f"User-provided IPD: {ipd_mm}mm"
        else:
            gender_key = gender.lower() if gender.lower() in self.POPULATION_AVERAGES['ipd'] else 'average'
            ipd_data = self.POPULATION_AVERAGES['ipd'][gender_key]
            ipd_mm = ipd_data['mean']
            # Confidence based on population standard deviation
            confidence = 0.75  # Moderate confidence with population average
            reference_note = f"Population average IPD ({gender_key}): {ipd_mm}mm (±{ipd_data['std']}mm)"

        # Calculate conversion factors
        if ipd_pixels <= 0:
            raise ValueError("IPD in pixels must be positive")

        pixels_per_mm = ipd_pixels / ipd_mm
        mm_per_pixel = ipd_mm / ipd_pixels

        result = CalibrationResult(
            method=CalibrationMethod.INTERPUPILLARY_DISTANCE,
            pixels_per_mm=round(pixels_per_mm, 4),
            mm_per_pixel=round(mm_per_pixel, 6),
            confidence=confidence,
            reference_used="interpupillary_distance",
            reference_value_mm=ipd_mm,
            reference_value_px=ipd_pixels,
            metadata={
                'gender': gender,
                'custom_value_used': custom_ipd_mm is not None,
                'population_std': self.POPULATION_AVERAGES['ipd'].get(gender, {}).get('std', 3.5),
                'note': reference_note
            }
        )

        self.current_calibration = result
        self.calibration_history.append(result)
        logger.info(f"IPD calibration complete: {pixels_per_mm:.2f} px/mm")

        return result

    def calibrate_from_reference_object(self, object_type: str,
                                        measured_pixels: float,
                                        measurement_type: str = 'width') -> CalibrationResult:
        """
        Calibrate using a known-size reference object in the image.

        Args:
            object_type: Type of reference object ('credit_card', 'us_quarter', etc.)
            measured_pixels: Measured size of object in pixels
            measurement_type: 'width', 'height', or 'diameter'

        Returns:
            CalibrationResult with conversion factors
        """
        if object_type not in self.REFERENCE_OBJECTS:
            available = ', '.join(self.REFERENCE_OBJECTS.keys())
            raise ValueError(f"Unknown reference object. Available: {available}")

        ref_obj = self.REFERENCE_OBJECTS[object_type]

        # Get known size in mm
        if measurement_type == 'width' and 'width_mm' in ref_obj:
            known_mm = ref_obj['width_mm']
        elif measurement_type == 'height' and 'height_mm' in ref_obj:
            known_mm = ref_obj['height_mm']
        elif measurement_type == 'diameter' and 'diameter_mm' in ref_obj:
            known_mm = ref_obj['diameter_mm']
        elif 'unit_mm' in ref_obj:
            known_mm = ref_obj['unit_mm']
        else:
            raise ValueError(f"Measurement type '{measurement_type}' not available for {object_type}")

        if measured_pixels <= 0:
            raise ValueError("Measured pixels must be positive")

        pixels_per_mm = measured_pixels / known_mm
        mm_per_pixel = known_mm / measured_pixels

        result = CalibrationResult(
            method=CalibrationMethod.REFERENCE_OBJECT,
            pixels_per_mm=round(pixels_per_mm, 4),
            mm_per_pixel=round(mm_per_pixel, 6),
            confidence=0.92,  # High confidence with known object
            reference_used=object_type,
            reference_value_mm=known_mm,
            reference_value_px=measured_pixels,
            metadata={
                'object_description': ref_obj.get('description', ''),
                'measurement_type': measurement_type,
                'note': f"Calibrated using {object_type} {measurement_type}: {known_mm}mm"
            }
        )

        self.current_calibration = result
        self.calibration_history.append(result)
        logger.info(f"Reference object calibration complete: {pixels_per_mm:.2f} px/mm")

        return result

    def calibrate_from_facial_feature(self, feature_name: str,
                                       measured_pixels: float,
                                       gender: str = 'male') -> CalibrationResult:
        """
        Calibrate using a known facial feature with population averages.

        Less accurate than reference object or known IPD, but useful when
        no other reference is available.

        Args:
            feature_name: 'bizygomatic_width', 'bigonial_width', 'face_height', etc.
            measured_pixels: Measured size in pixels
            gender: 'male' or 'female' for population norms

        Returns:
            CalibrationResult with conversion factors
        """
        if feature_name not in self.POPULATION_AVERAGES:
            available = ', '.join(self.POPULATION_AVERAGES.keys())
            raise ValueError(f"Unknown feature. Available: {available}")

        feature_data = self.POPULATION_AVERAGES[feature_name]
        gender_key = gender.lower() if gender.lower() in feature_data else 'male'

        if gender_key not in feature_data:
            raise ValueError(f"Gender '{gender}' not available for {feature_name}")

        stats = feature_data[gender_key]
        known_mm = stats['mean']

        if measured_pixels <= 0:
            raise ValueError("Measured pixels must be positive")

        pixels_per_mm = measured_pixels / known_mm
        mm_per_pixel = known_mm / measured_pixels

        # Lower confidence due to population variance
        confidence = 0.65

        result = CalibrationResult(
            method=CalibrationMethod.FACIAL_FEATURE,
            pixels_per_mm=round(pixels_per_mm, 4),
            mm_per_pixel=round(mm_per_pixel, 6),
            confidence=confidence,
            reference_used=feature_name,
            reference_value_mm=known_mm,
            reference_value_px=measured_pixels,
            metadata={
                'gender': gender_key,
                'population_std': stats['std'],
                'population_range': stats['range'],
                'note': f"Calibrated using {feature_name} ({gender_key}): {known_mm}mm (±{stats['std']}mm)",
                'warning': 'Lower confidence - based on population average, not measured reference'
            }
        )

        self.current_calibration = result
        self.calibration_history.append(result)
        logger.info(f"Facial feature calibration complete: {pixels_per_mm:.2f} px/mm (confidence: {confidence})")

        return result

    def calibrate_manual(self, pixels_per_mm: float,
                         reference_description: str = "Manual calibration") -> CalibrationResult:
        """
        Set manual calibration with user-provided scale factor.

        Args:
            pixels_per_mm: Known pixels per millimeter ratio
            reference_description: Description of how calibration was determined

        Returns:
            CalibrationResult with conversion factors
        """
        if pixels_per_mm <= 0:
            raise ValueError("Pixels per mm must be positive")

        mm_per_pixel = 1.0 / pixels_per_mm

        result = CalibrationResult(
            method=CalibrationMethod.MANUAL,
            pixels_per_mm=round(pixels_per_mm, 4),
            mm_per_pixel=round(mm_per_pixel, 6),
            confidence=0.90,  # High confidence with manual calibration
            reference_used="manual",
            reference_value_mm=1.0,
            reference_value_px=pixels_per_mm,
            metadata={
                'description': reference_description,
                'note': 'User-provided calibration'
            }
        )

        self.current_calibration = result
        self.calibration_history.append(result)
        logger.info(f"Manual calibration set: {pixels_per_mm:.2f} px/mm")

        return result

    def calibrate_from_landmarks(self, landmarks: np.ndarray,
                                  gender: str = 'average') -> CalibrationResult:
        """
        Auto-calibrate using detected facial landmarks.

        Uses IPD measured from landmarks as the primary reference.

        Args:
            landmarks: 68-point facial landmarks array
            gender: 'male', 'female', or 'average'

        Returns:
            CalibrationResult with conversion factors
        """
        if len(landmarks) < 48:
            raise ValueError("Insufficient landmarks for calibration (need at least 48 for eyes)")

        # Calculate IPD from eye landmarks
        # Left eye center (points 36-41)
        left_eye_center = np.mean(landmarks[36:42], axis=0)
        # Right eye center (points 42-47)
        right_eye_center = np.mean(landmarks[42:48], axis=0)

        ipd_pixels = np.linalg.norm(right_eye_center - left_eye_center)

        return self.calibrate_from_ipd(ipd_pixels, gender=gender)

    def convert_measurement(self, value_pixels: float,
                            calibration: Optional[CalibrationResult] = None) -> Dict[str, Any]:
        """
        Convert a pixel measurement to millimeters.

        Args:
            value_pixels: Measurement in pixels
            calibration: Calibration to use (or current if None)

        Returns:
            Dictionary with converted value and confidence
        """
        cal = calibration or self.current_calibration

        if cal is None:
            return {
                'value_mm': None,
                'value_px': value_pixels,
                'calibrated': False,
                'confidence': 0.0,
                'warning': 'No calibration available - measurement in pixels only'
            }

        value_mm = cal.convert_px_to_mm(value_pixels)

        # Estimate measurement uncertainty based on calibration confidence
        # and typical measurement error (±2%)
        measurement_error_mm = value_mm * 0.02
        calibration_error_mm = value_mm * (1 - cal.confidence) * 0.1

        total_uncertainty = np.sqrt(measurement_error_mm**2 + calibration_error_mm**2)

        return {
            'value_mm': round(value_mm, 2),
            'value_px': round(value_pixels, 1),
            'calibrated': True,
            'confidence': cal.confidence,
            'uncertainty_mm': round(total_uncertainty, 2),
            'calibration_method': cal.method.value,
            'calibration_reference': cal.reference_used
        }

    def convert_measurements_batch(self, measurements: Dict[str, float],
                                    calibration: Optional[CalibrationResult] = None) -> Dict[str, Dict[str, Any]]:
        """
        Convert multiple pixel measurements to millimeters.

        Args:
            measurements: Dictionary of {name: pixels} measurements
            calibration: Calibration to use (or current if None)

        Returns:
            Dictionary of converted measurements
        """
        results = {}
        for name, value_px in measurements.items():
            results[name] = self.convert_measurement(value_px, calibration)
        return results

    def get_uncalibrated_result(self) -> CalibrationResult:
        """
        Get an uncalibrated result (1:1 pixel mapping).

        Useful when calibration is not possible but measurements
        still need to be recorded with appropriate warnings.
        """
        return CalibrationResult(
            method=CalibrationMethod.UNCALIBRATED,
            pixels_per_mm=1.0,
            mm_per_pixel=1.0,
            confidence=0.0,
            reference_used="none",
            reference_value_mm=1.0,
            reference_value_px=1.0,
            metadata={
                'warning': 'UNCALIBRATED: Values are in pixels, not millimeters',
                'recommendation': 'Use calibrate_from_ipd() or calibrate_from_reference_object() for accurate measurements'
            }
        )

    def validate_calibration(self, calibration: CalibrationResult,
                              landmarks: np.ndarray,
                              gender: str = 'male') -> Dict[str, Any]:
        """
        Validate a calibration by checking if derived measurements
        fall within expected population ranges.

        Args:
            calibration: Calibration to validate
            landmarks: 68-point facial landmarks
            gender: 'male' or 'female' for population norms

        Returns:
            Validation result with flags and recommendations
        """
        if len(landmarks) < 68:
            return {'valid': False, 'reason': 'Insufficient landmarks'}

        validations = []
        all_valid = True

        # Check bizygomatic width
        bizygomatic_px = np.linalg.norm(landmarks[1] - landmarks[15])
        bizygomatic_mm = calibration.convert_px_to_mm(bizygomatic_px)
        bz_range = self.POPULATION_AVERAGES['bizygomatic_width'][gender]['range']

        if bz_range[0] <= bizygomatic_mm <= bz_range[1]:
            validations.append({
                'feature': 'bizygomatic_width',
                'value_mm': round(bizygomatic_mm, 1),
                'expected_range': bz_range,
                'valid': True
            })
        else:
            validations.append({
                'feature': 'bizygomatic_width',
                'value_mm': round(bizygomatic_mm, 1),
                'expected_range': bz_range,
                'valid': False,
                'deviation': 'too_low' if bizygomatic_mm < bz_range[0] else 'too_high'
            })
            all_valid = False

        # Check bigonial width
        bigonial_px = np.linalg.norm(landmarks[5] - landmarks[11])
        bigonial_mm = calibration.convert_px_to_mm(bigonial_px)
        bg_range = self.POPULATION_AVERAGES['bigonial_width'][gender]['range']

        if bg_range[0] <= bigonial_mm <= bg_range[1]:
            validations.append({
                'feature': 'bigonial_width',
                'value_mm': round(bigonial_mm, 1),
                'expected_range': bg_range,
                'valid': True
            })
        else:
            validations.append({
                'feature': 'bigonial_width',
                'value_mm': round(bigonial_mm, 1),
                'expected_range': bg_range,
                'valid': False,
                'deviation': 'too_low' if bigonial_mm < bg_range[0] else 'too_high'
            })
            all_valid = False

        return {
            'valid': all_valid,
            'calibration_confidence': calibration.confidence,
            'validations': validations,
            'recommendation': 'Calibration appears valid' if all_valid else 'Consider recalibrating with a different reference'
        }


# Export
__all__ = ['MeasurementCalibrator', 'CalibrationResult', 'CalibrationMethod']
