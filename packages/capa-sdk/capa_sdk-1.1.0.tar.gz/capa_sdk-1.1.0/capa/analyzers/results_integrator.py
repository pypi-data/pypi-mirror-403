"""
Results Integrator - CAPA (Craniofacial Analysis & Prediction Architecture)

This module integrates results from multiple scientific analysis modules
and provides confidence-weighted combined predictions.

IMPORTANT DESIGN PRINCIPLES:
1. Weight predictions by scientific evidence level (validated vs speculative)
2. Cross-validate predictions between modules when possible
3. Clearly distinguish validated findings from extrapolations
4. Report confidence intervals and uncertainty

Integration Sources:
- WD Analyzer: Width Difference personality predictions (validated)
- Forehead Analyzer: FID impulsivity predictions (validated BIS-11 only)
- Morphology Analyzer: Face shape classification (validated)
- Neoclassical Canons: Proportion analysis (partially validated)

Version: 1.1
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EvidenceLevel(Enum):
    """Evidence level classification for predictions"""
    VALIDATED = "validated"           # Directly from peer-reviewed paper
    PARTIALLY_VALIDATED = "partial"   # Some aspects validated, others extrapolated
    EXTRAPOLATED = "extrapolated"     # Derived from validated findings
    SPECULATIVE = "speculative"       # Theoretical, no direct validation


@dataclass
class PredictionResult:
    """Single prediction with confidence and evidence level"""
    trait: str
    value: float
    confidence: float
    evidence_level: EvidenceLevel
    source_module: str
    paper_reference: Optional[str] = None
    warning: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'trait': self.trait,
            'value': float(self.value),
            'confidence': float(self.confidence),
            'evidence_level': self.evidence_level.value,
            'source_module': self.source_module,
            'paper_reference': self.paper_reference,
            'warning': self.warning
        }


@dataclass
class CrossValidationResult:
    """Result of cross-validation between modules"""
    trait: str
    module_a: str
    module_b: str
    prediction_a: float
    prediction_b: float
    agreement_score: float  # 0-1, how well they agree
    combined_confidence: float
    interpretation: str


@dataclass
class IntegratedAnalysisResult:
    """Complete integrated analysis result"""
    # Primary predictions (validated)
    validated_predictions: List[PredictionResult] = field(default_factory=list)

    # Secondary predictions (extrapolated/speculative)
    speculative_predictions: List[PredictionResult] = field(default_factory=list)

    # Cross-validation results
    cross_validations: List[CrossValidationResult] = field(default_factory=list)

    # Overall metrics
    overall_confidence: float = 0.0
    data_quality_score: float = 0.0

    # Module-specific results (raw)
    module_results: Dict[str, Any] = field(default_factory=dict)

    # Warnings and notes
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'validated_predictions': [p.to_dict() for p in self.validated_predictions],
            'speculative_predictions': [p.to_dict() for p in self.speculative_predictions],
            'cross_validations': [
                {
                    'trait': cv.trait,
                    'modules': [cv.module_a, cv.module_b],
                    'predictions': [cv.prediction_a, cv.prediction_b],
                    'agreement': cv.agreement_score,
                    'confidence': cv.combined_confidence,
                    'interpretation': cv.interpretation
                }
                for cv in self.cross_validations
            ],
            'overall_confidence': float(self.overall_confidence),
            'data_quality_score': float(self.data_quality_score),
            'warnings': self.warnings,
            'notes': self.notes
        }


class ResultsIntegrator:
    """
    Integrates multiple facial analysis modules into coherent predictions.

    This class:
    1. Collects results from WD, Forehead, Morphology, and Canon analyzers
    2. Weights predictions by evidence level and measurement confidence
    3. Cross-validates predictions where modules overlap
    4. Produces integrated results with clear uncertainty quantification

    IMPORTANT: This analyzer clearly separates:
    - VALIDATED predictions (from peer-reviewed papers)
    - SPECULATIVE predictions (theoretical extrapolations)
    """

    # ========================================================================
    # EVIDENCE WEIGHTS
    # These weights determine how much each evidence level contributes
    # to combined predictions. Validated findings are weighted heavily.
    # ========================================================================
    EVIDENCE_WEIGHTS = {
        EvidenceLevel.VALIDATED: 1.0,
        EvidenceLevel.PARTIALLY_VALIDATED: 0.7,
        EvidenceLevel.EXTRAPOLATED: 0.4,
        EvidenceLevel.SPECULATIVE: 0.2
    }

    # ========================================================================
    # TRAIT MAPPING
    # Maps traits across different modules for cross-validation
    # ========================================================================
    CROSS_VALIDATION_MAP = {
        # Impulsivity can be predicted by both WD and Forehead
        'impulsivity': {
            'wd_analyzer': 'dominance_score',  # Higher WD → more dominant → more impulsive
            'forehead_analyzer': 'bis11_total'
        },
        # Self-control is inverse of impulsivity
        'self_control': {
            'wd_analyzer': 'self_reliance',    # 16PF Q2
            'forehead_analyzer': 'behavioral_inhibition'
        },
        # Emotional traits
        'emotional_expression': {
            'wd_analyzer': 'emotional_expressivity',  # EES scale
            'forehead_analyzer': 'emotional_regulation'
        }
    }

    def __init__(self):
        """Initialize the multi-factor analyzer"""
        self.wd_analyzer = None
        self.forehead_analyzer = None
        self.morphology_analyzer = None
        self.canons_analyzer = None

        # Store last analysis results
        self._last_results = {}

    def set_analyzers(self,
                      wd_analyzer=None,
                      forehead_analyzer=None,
                      morphology_analyzer=None,
                      canons_analyzer=None):
        """
        Set the analyzer instances to use.

        Args:
            wd_analyzer: WDAnalyzer instance
            forehead_analyzer: ForeheadAnalyzer instance
            morphology_analyzer: MorphologyAnalyzer instance
            canons_analyzer: NeoclassicalCanonsAnalyzer instance
        """
        if wd_analyzer:
            self.wd_analyzer = wd_analyzer
        if forehead_analyzer:
            self.forehead_analyzer = forehead_analyzer
        if morphology_analyzer:
            self.morphology_analyzer = morphology_analyzer
        if canons_analyzer:
            self.canons_analyzer = canons_analyzer

    def analyze(self,
                frontal_image: np.ndarray = None,
                profile_image: np.ndarray = None,
                wd_result: Dict = None,
                forehead_result: Dict = None,
                morphology_result: Dict = None,
                canons_result: Dict = None) -> IntegratedAnalysisResult:
        """
        Perform integrated multi-factor analysis.

        Can accept either raw images (if analyzers are set) or pre-computed
        results from individual modules.

        Args:
            frontal_image: Frontal face image (for WD, Morphology, Canons)
            profile_image: Profile face image (for Forehead)
            wd_result: Pre-computed WD analysis result
            forehead_result: Pre-computed Forehead analysis result
            morphology_result: Pre-computed Morphology analysis result
            canons_result: Pre-computed Canons analysis result

        Returns:
            IntegratedAnalysisResult with combined predictions
        """
        result = IntegratedAnalysisResult()

        # Collect results from each module
        module_results = {}

        # WD Analysis
        if wd_result:
            module_results['wd'] = wd_result
        elif frontal_image is not None and self.wd_analyzer:
            try:
                wd_analysis = self.wd_analyzer.analyze_image(frontal_image)
                module_results['wd'] = wd_analysis.to_dict() if hasattr(wd_analysis, 'to_dict') else wd_analysis
            except Exception as e:
                result.warnings.append(f"WD analysis failed: {str(e)}")

        # Forehead Analysis
        if forehead_result:
            module_results['forehead'] = forehead_result
        elif profile_image is not None and self.forehead_analyzer:
            try:
                fh_analysis = self.forehead_analyzer.analyze_image(profile_image)
                module_results['forehead'] = fh_analysis.to_dict() if hasattr(fh_analysis, 'to_dict') else fh_analysis
            except Exception as e:
                result.warnings.append(f"Forehead analysis failed: {str(e)}")

        # Morphology Analysis
        if morphology_result:
            module_results['morphology'] = morphology_result
        elif frontal_image is not None and self.morphology_analyzer:
            try:
                morph_analysis = self.morphology_analyzer.analyze_image(frontal_image)
                module_results['morphology'] = morph_analysis.to_dict() if hasattr(morph_analysis, 'to_dict') else morph_analysis
            except Exception as e:
                result.warnings.append(f"Morphology analysis failed: {str(e)}")

        # Canons Analysis
        if canons_result:
            module_results['canons'] = canons_result
        elif frontal_image is not None and self.canons_analyzer:
            try:
                canon_analysis = self.canons_analyzer.analyze_image(frontal_image)
                module_results['canons'] = canon_analysis.to_dict() if hasattr(canon_analysis, 'to_dict') else canon_analysis
            except Exception as e:
                result.warnings.append(f"Canons analysis failed: {str(e)}")

        result.module_results = module_results
        self._last_results = module_results

        # Extract validated predictions
        result.validated_predictions = self._extract_validated_predictions(module_results)

        # Extract speculative predictions
        result.speculative_predictions = self._extract_speculative_predictions(module_results)

        # Perform cross-validation
        result.cross_validations = self._cross_validate_predictions(module_results)

        # Calculate overall metrics
        result.overall_confidence = self._calculate_overall_confidence(result)
        result.data_quality_score = self._calculate_data_quality(module_results)

        # Add notes about what was analyzed
        if 'wd' in module_results:
            result.notes.append("WD analysis: Personality traits from bizygomatic/bigonial width difference")
        if 'forehead' in module_results:
            result.notes.append("Forehead analysis: BIS-11 impulsivity from forehead inclination")
        if 'morphology' in module_results:
            result.notes.append("Morphology analysis: Face shape classification")
        if 'canons' in module_results:
            result.notes.append("Canons analysis: Neoclassical proportion assessment")

        return result

    def _extract_validated_predictions(self, module_results: Dict) -> List[PredictionResult]:
        """
        Extract only scientifically validated predictions.

        These are predictions that come directly from peer-reviewed papers
        with documented coefficients and confidence intervals.
        """
        predictions = []

        # ================================================================
        # WD ANALYZER - Validated Predictions
        # Source: Lefevre et al. (2012), etc.
        # ================================================================
        if 'wd' in module_results:
            wd = module_results['wd']

            # Self-reliance (16PF Q2) - directly validated
            if 'personality_predictions' in wd:
                pp = wd['personality_predictions']

                if 'self_reliance_16pf_q2' in pp:
                    predictions.append(PredictionResult(
                        trait='Self-Reliance (16PF Q2)',
                        value=pp['self_reliance_16pf_q2'],
                        confidence=wd.get('combined_confidence', 0.5),
                        evidence_level=EvidenceLevel.VALIDATED,
                        source_module='wd_analyzer',
                        paper_reference='Lefevre et al. (2012) - B=3.69, p<0.001'
                    ))

                if 'emotional_expressivity_ees' in pp:
                    predictions.append(PredictionResult(
                        trait='Emotional Expressivity (EES)',
                        value=pp['emotional_expressivity_ees'],
                        confidence=wd.get('combined_confidence', 0.5),
                        evidence_level=EvidenceLevel.VALIDATED,
                        source_module='wd_analyzer',
                        paper_reference='Lefevre et al. (2012) - B=-7.49, p<0.001'
                    ))

        # ================================================================
        # FOREHEAD ANALYZER - Validated Predictions
        # Source: Guerrero-Apolo et al. (2018)
        # ================================================================
        if 'forehead' in module_results:
            fh = module_results['forehead']

            if 'impulsiveness_profile' in fh:
                ip = fh['impulsiveness_profile']

                # BIS-11 Total - directly validated
                if 'bis11_total' in ip:
                    predictions.append(PredictionResult(
                        trait='BIS-11 Total Impulsivity',
                        value=ip['bis11_total'],
                        confidence=fh.get('measurement_confidence', 0.5),
                        evidence_level=EvidenceLevel.VALIDATED,
                        source_module='forehead_analyzer',
                        paper_reference='Guerrero-Apolo et al. (2018) - b=1.405, R²=0.217, p<0.001'
                    ))

                # BIS-11 Attentional
                if 'attentional_impulsiveness' in ip:
                    predictions.append(PredictionResult(
                        trait='BIS-11 Attentional Impulsivity',
                        value=ip['attentional_impulsiveness'],
                        confidence=fh.get('measurement_confidence', 0.5),
                        evidence_level=EvidenceLevel.VALIDATED,
                        source_module='forehead_analyzer',
                        paper_reference='Guerrero-Apolo et al. (2018) - b=0.389, R²=0.240, p<0.001'
                    ))

                # BIS-11 Motor
                if 'motor_impulsiveness' in ip:
                    predictions.append(PredictionResult(
                        trait='BIS-11 Motor Impulsivity',
                        value=ip['motor_impulsiveness'],
                        confidence=fh.get('measurement_confidence', 0.5),
                        evidence_level=EvidenceLevel.VALIDATED,
                        source_module='forehead_analyzer',
                        paper_reference='Guerrero-Apolo et al. (2018) - b=0.579, R²=0.166, p<0.001'
                    ))

        # ================================================================
        # MORPHOLOGY ANALYZER - Validated Face Shape
        # Source: Anthropometric standards
        # ================================================================
        if 'morphology' in module_results:
            morph = module_results['morphology']

            if 'face_shape' in morph:
                predictions.append(PredictionResult(
                    trait='Face Shape Classification',
                    value=morph['face_shape'],
                    confidence=morph.get('confidence', 0.5),
                    evidence_level=EvidenceLevel.VALIDATED,
                    source_module='morphology_analyzer',
                    paper_reference='Anthropometric classification standards'
                ))

        return predictions

    def _extract_speculative_predictions(self, module_results: Dict) -> List[PredictionResult]:
        """
        Extract speculative/extrapolated predictions.

        These are predictions derived from validated findings but not
        directly tested in the original papers.
        """
        predictions = []

        # ================================================================
        # FOREHEAD ANALYZER - Speculative Predictions
        # These are derived from BIS-11 but not directly validated
        # ================================================================
        if 'forehead' in module_results:
            fh = module_results['forehead']

            if 'impulsiveness_profile' in fh:
                ip = fh['impulsiveness_profile']

                # Derived traits (speculative)
                speculative_traits = [
                    ('risk_taking_tendency', 'Risk-Taking Tendency'),
                    ('sensation_seeking', 'Sensation Seeking'),
                    ('cognitive_control', 'Cognitive Control'),
                    ('emotional_regulation', 'Emotional Regulation'),
                    ('delay_of_gratification', 'Delay of Gratification')
                ]

                for key, name in speculative_traits:
                    if key in ip and not ip.get(f'{key}_validated', False):
                        predictions.append(PredictionResult(
                            trait=name,
                            value=ip[key],
                            confidence=fh.get('measurement_confidence', 0.3) * 0.5,
                            evidence_level=EvidenceLevel.SPECULATIVE,
                            source_module='forehead_analyzer',
                            warning='Derived from BIS-11 scores - not directly validated'
                        ))

            # Neuroscience predictions - highly speculative
            if 'neuroscience_correlations' in fh:
                nc = fh['neuroscience_correlations']
                predictions.append(PredictionResult(
                    trait='Neuroscience Predictions',
                    value=nc,
                    confidence=0.2,
                    evidence_level=EvidenceLevel.SPECULATIVE,
                    source_module='forehead_analyzer',
                    warning='THEORETICAL - No direct imaging validation exists'
                ))

        # ================================================================
        # CANONS ANALYZER - Ear-related canons are estimated
        # ================================================================
        if 'canons' in module_results:
            canons = module_results['canons']

            for canon in canons.get('canons', []):
                if 'estimated' in canon.get('canon_name', '').lower() or \
                   'aural' in canon.get('canon_name', '').lower():
                    predictions.append(PredictionResult(
                        trait=f"Canon: {canon.get('canon_name', 'Unknown')}",
                        value=canon.get('validity_score', 0),
                        confidence=canon.get('confidence', 0.3),
                        evidence_level=EvidenceLevel.EXTRAPOLATED,
                        source_module='canons_analyzer',
                        warning='Ear landmarks are estimated, not directly detected'
                    ))

        return predictions

    def _cross_validate_predictions(self, module_results: Dict) -> List[CrossValidationResult]:
        """
        Cross-validate predictions between modules where they overlap.

        This helps identify when multiple independent measurements agree,
        increasing confidence in the prediction.
        """
        cross_validations = []

        # Skip if we don't have multiple modules
        if len(module_results) < 2:
            return cross_validations

        # ================================================================
        # Cross-validate impulsivity (WD dominance vs Forehead BIS-11)
        # ================================================================
        if 'wd' in module_results and 'forehead' in module_results:
            wd = module_results['wd']
            fh = module_results['forehead']

            # Get dominance from WD (higher WD → more dominant/aggressive)
            wd_value = None
            if 'personality_predictions' in wd:
                # Use aggression/dominance as proxy for impulsivity
                if 'aggression_score' in wd['personality_predictions']:
                    wd_value = wd['personality_predictions']['aggression_score']

            # Get BIS-11 from Forehead
            fh_value = None
            if 'impulsiveness_profile' in fh:
                if 'bis11_total' in fh['impulsiveness_profile']:
                    # Normalize BIS-11 (typically 30-120) to 0-1 scale
                    raw_bis = fh['impulsiveness_profile']['bis11_total']
                    fh_value = (raw_bis - 30) / 90  # Normalized

            if wd_value is not None and fh_value is not None:
                # Calculate agreement
                agreement = 1.0 - abs(wd_value - fh_value)

                cross_validations.append(CrossValidationResult(
                    trait='Impulsivity/Dominance',
                    module_a='wd_analyzer',
                    module_b='forehead_analyzer',
                    prediction_a=wd_value,
                    prediction_b=fh_value,
                    agreement_score=agreement,
                    combined_confidence=(
                        wd.get('combined_confidence', 0.5) *
                        fh.get('measurement_confidence', 0.5) *
                        (0.5 + 0.5 * agreement)  # Boost if they agree
                    ),
                    interpretation=self._interpret_agreement(agreement)
                ))

        return cross_validations

    def _interpret_agreement(self, agreement: float) -> str:
        """Interpret the agreement score between modules"""
        if agreement >= 0.9:
            return "Excellent agreement - high confidence in prediction"
        elif agreement >= 0.7:
            return "Good agreement - moderate confidence"
        elif agreement >= 0.5:
            return "Partial agreement - predictions may differ in nuance"
        else:
            return "Low agreement - contradictory predictions, interpret with caution"

    def _calculate_overall_confidence(self, result: IntegratedAnalysisResult) -> float:
        """Calculate overall confidence in the integrated analysis"""
        if not result.validated_predictions and not result.speculative_predictions:
            return 0.0

        # Weight validated predictions more heavily
        validated_conf = np.mean([p.confidence for p in result.validated_predictions]) if result.validated_predictions else 0
        speculative_conf = np.mean([p.confidence for p in result.speculative_predictions]) if result.speculative_predictions else 0

        # Cross-validation boost
        cv_boost = 0
        if result.cross_validations:
            cv_boost = np.mean([cv.agreement_score for cv in result.cross_validations]) * 0.1

        # Weighted combination (validated matters more)
        overall = (
            validated_conf * 0.7 +
            speculative_conf * 0.2 +
            cv_boost
        )

        return min(1.0, overall)

    def _calculate_data_quality(self, module_results: Dict) -> float:
        """Calculate data quality score based on inputs"""
        quality = 0.0

        # Each module contributes to quality
        if 'wd' in module_results:
            wd = module_results['wd']
            quality += wd.get('combined_confidence', 0.5) * 0.3

        if 'forehead' in module_results:
            fh = module_results['forehead']
            quality += fh.get('measurement_confidence', 0.5) * 0.3
            # Profile validation is important for forehead
            if fh.get('profile_validated', False):
                quality += 0.1

        if 'morphology' in module_results:
            morph = module_results['morphology']
            quality += morph.get('confidence', 0.5) * 0.2

        if 'canons' in module_results:
            canons = module_results['canons']
            quality += canons.get('confidence', 0.5) * 0.1

        return min(1.0, quality)

    def get_combined_trait_prediction(self,
                                      trait: str,
                                      module_results: Dict = None) -> Tuple[float, float, str]:
        """
        Get a combined prediction for a specific trait across modules.

        Args:
            trait: Trait name to predict
            module_results: Optional results (uses last analysis if None)

        Returns:
            Tuple of (predicted_value, confidence, evidence_summary)
        """
        if module_results is None:
            module_results = self._last_results

        if not module_results:
            return (0.0, 0.0, "No analysis data available")

        predictions = []
        weights = []
        sources = []

        # Collect predictions for this trait from all modules
        for module, results in module_results.items():
            value, confidence, evidence = self._get_trait_from_module(trait, module, results)
            if value is not None:
                weight = confidence * self.EVIDENCE_WEIGHTS.get(evidence, 0.2)
                predictions.append(value)
                weights.append(weight)
                sources.append(f"{module}: {evidence.value}")

        if not predictions:
            return (0.0, 0.0, f"Trait '{trait}' not found in any module")

        # Weighted average
        total_weight = sum(weights)
        if total_weight == 0:
            return (np.mean(predictions), 0.1, "Low confidence - no weighted predictions")

        combined_value = sum(p * w for p, w in zip(predictions, weights)) / total_weight
        combined_confidence = total_weight / len(weights)  # Normalized

        return (
            combined_value,
            combined_confidence,
            f"Combined from: {', '.join(sources)}"
        )

    def _get_trait_from_module(self,
                               trait: str,
                               module: str,
                               results: Dict) -> Tuple[Optional[float], float, EvidenceLevel]:
        """Extract a trait prediction from a specific module's results"""
        # This would need to be expanded based on actual trait names
        # For now, return None to indicate trait not found
        return (None, 0.0, EvidenceLevel.SPECULATIVE)

    def generate_report(self, result: IntegratedAnalysisResult) -> str:
        """
        Generate a human-readable report of the integrated analysis.

        Args:
            result: IntegratedAnalysisResult to report on

        Returns:
            Formatted string report
        """
        lines = []
        lines.append("=" * 60)
        lines.append("CAPA - INTEGRATED RESULTS ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Overall metrics
        lines.append(f"Overall Confidence: {result.overall_confidence:.1%}")
        lines.append(f"Data Quality Score: {result.data_quality_score:.1%}")
        lines.append("")

        # Validated predictions
        if result.validated_predictions:
            lines.append("-" * 40)
            lines.append("VALIDATED PREDICTIONS (Peer-Reviewed)")
            lines.append("-" * 40)
            for pred in result.validated_predictions:
                lines.append(f"  {pred.trait}:")
                lines.append(f"    Value: {pred.value}")
                lines.append(f"    Confidence: {pred.confidence:.1%}")
                lines.append(f"    Source: {pred.source_module}")
                if pred.paper_reference:
                    lines.append(f"    Reference: {pred.paper_reference}")
            lines.append("")

        # Speculative predictions
        if result.speculative_predictions:
            lines.append("-" * 40)
            lines.append("SPECULATIVE PREDICTIONS (Use with Caution)")
            lines.append("-" * 40)
            for pred in result.speculative_predictions:
                lines.append(f"  {pred.trait}:")
                lines.append(f"    Value: {pred.value}")
                lines.append(f"    Confidence: {pred.confidence:.1%}")
                if pred.warning:
                    lines.append(f"    ⚠️ {pred.warning}")
            lines.append("")

        # Cross-validations
        if result.cross_validations:
            lines.append("-" * 40)
            lines.append("CROSS-VALIDATION RESULTS")
            lines.append("-" * 40)
            for cv in result.cross_validations:
                lines.append(f"  {cv.trait}:")
                lines.append(f"    {cv.module_a}: {cv.prediction_a:.2f}")
                lines.append(f"    {cv.module_b}: {cv.prediction_b:.2f}")
                lines.append(f"    Agreement: {cv.agreement_score:.1%}")
                lines.append(f"    {cv.interpretation}")
            lines.append("")

        # Warnings
        if result.warnings:
            lines.append("-" * 40)
            lines.append("WARNINGS")
            lines.append("-" * 40)
            for warning in result.warnings:
                lines.append(f"  ⚠️ {warning}")
            lines.append("")

        # Notes
        if result.notes:
            lines.append("-" * 40)
            lines.append("ANALYSIS NOTES")
            lines.append("-" * 40)
            for note in result.notes:
                lines.append(f"  • {note}")

        lines.append("")
        lines.append("=" * 60)
        lines.append("END OF REPORT")
        lines.append("=" * 60)

        return "\n".join(lines)
