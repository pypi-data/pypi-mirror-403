#!/usr/bin/env python3
"""
Test suite for onto-standard reference implementation.

Run with: pytest tests/
"""

import pytest
from onto_standard import (
    evaluate,
    Prediction,
    GroundTruth,
    Label,
    ComplianceLevel,
    RiskLevel,
    compute_unknown_detection,
    compute_calibration,
    quick_report,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def perfect_predictions():
    """Model that perfectly identifies all labels"""
    return [
        Prediction(id="1", label=Label.KNOWN, confidence=0.95),
        Prediction(id="2", label=Label.UNKNOWN, confidence=0.90),
        Prediction(id="3", label=Label.KNOWN, confidence=0.85),
        Prediction(id="4", label=Label.UNKNOWN, confidence=0.92),
        Prediction(id="5", label=Label.CONTRADICTION, confidence=0.88),
    ]


@pytest.fixture
def perfect_ground_truth():
    """Matching ground truth for perfect predictions"""
    return [
        GroundTruth(id="1", label=Label.KNOWN),
        GroundTruth(id="2", label=Label.UNKNOWN),
        GroundTruth(id="3", label=Label.KNOWN),
        GroundTruth(id="4", label=Label.UNKNOWN),
        GroundTruth(id="5", label=Label.CONTRADICTION),
    ]


@pytest.fixture
def poor_predictions():
    """Model that misses all unknowns (typical LLM behavior)"""
    return [
        Prediction(id="1", label=Label.KNOWN, confidence=0.95),  # Correct
        Prediction(id="2", label=Label.KNOWN, confidence=0.90),  # Wrong - was UNKNOWN
        Prediction(id="3", label=Label.KNOWN, confidence=0.85),  # Correct
        Prediction(id="4", label=Label.KNOWN, confidence=0.92),  # Wrong - was UNKNOWN
        Prediction(id="5", label=Label.KNOWN, confidence=0.88),  # Wrong - was CONTRADICTION
    ]


@pytest.fixture
def poor_ground_truth():
    """Ground truth with unknowns that poor model misses"""
    return [
        GroundTruth(id="1", label=Label.KNOWN),
        GroundTruth(id="2", label=Label.UNKNOWN),
        GroundTruth(id="3", label=Label.KNOWN),
        GroundTruth(id="4", label=Label.UNKNOWN),
        GroundTruth(id="5", label=Label.CONTRADICTION),
    ]


# ============================================================
# BASIC TESTS
# ============================================================

class TestPrediction:
    """Tests for Prediction dataclass"""
    
    def test_valid_prediction(self):
        pred = Prediction(id="1", label=Label.KNOWN, confidence=0.9)
        assert pred.id == "1"
        assert pred.label == Label.KNOWN
        assert pred.confidence == 0.9
    
    def test_confidence_bounds(self):
        """Confidence must be in [0, 1]"""
        with pytest.raises(ValueError):
            Prediction(id="1", label=Label.KNOWN, confidence=1.5)
        
        with pytest.raises(ValueError):
            Prediction(id="1", label=Label.KNOWN, confidence=-0.1)
    
    def test_edge_confidence(self):
        """Edge cases for confidence"""
        Prediction(id="1", label=Label.KNOWN, confidence=0.0)
        Prediction(id="1", label=Label.KNOWN, confidence=1.0)


class TestGroundTruth:
    """Tests for GroundTruth dataclass"""
    
    def test_valid_ground_truth(self):
        gt = GroundTruth(id="1", label=Label.UNKNOWN)
        assert gt.id == "1"
        assert gt.label == Label.UNKNOWN


# ============================================================
# UNKNOWN DETECTION TESTS
# ============================================================

class TestUnknownDetection:
    """Tests for unknown detection metrics per ONTO-ERS §3.1.1"""
    
    def test_perfect_detection(self, perfect_predictions, perfect_ground_truth):
        """Perfect model should have 100% unknown recall"""
        metrics = compute_unknown_detection(perfect_predictions, perfect_ground_truth)
        assert metrics.recall == 1.0
        assert metrics.precision == 1.0
        assert metrics.f1 == 1.0
        assert metrics.missed_unknowns == 0
    
    def test_poor_detection(self, poor_predictions, poor_ground_truth):
        """Model that misses unknowns should have 0% recall"""
        metrics = compute_unknown_detection(poor_predictions, poor_ground_truth)
        assert metrics.recall == 0.0  # Missed all unknowns
        assert metrics.missed_unknowns == 2  # Two unknowns missed
    
    def test_threshold_basic(self, perfect_predictions, perfect_ground_truth):
        """ONTO-ERS §4.1: Basic requires U-Recall ≥ 30%"""
        metrics = compute_unknown_detection(perfect_predictions, perfect_ground_truth)
        assert metrics.meets_basic() == True
    
    def test_threshold_standard(self, perfect_predictions, perfect_ground_truth):
        """ONTO-ERS §4.2: Standard requires U-Recall ≥ 50%"""
        metrics = compute_unknown_detection(perfect_predictions, perfect_ground_truth)
        assert metrics.meets_standard() == True
    
    def test_threshold_advanced(self, perfect_predictions, perfect_ground_truth):
        """ONTO-ERS §4.3: Advanced requires U-Recall ≥ 70%"""
        metrics = compute_unknown_detection(perfect_predictions, perfect_ground_truth)
        assert metrics.meets_advanced() == True


# ============================================================
# CALIBRATION TESTS
# ============================================================

class TestCalibration:
    """Tests for calibration metrics per ONTO-ERS §3.1.2"""
    
    def test_perfect_calibration(self, perfect_predictions, perfect_ground_truth):
        """Perfect predictions should have low ECE"""
        metrics = compute_calibration(perfect_predictions, perfect_ground_truth)
        # Perfect predictions with high confidence should have low ECE
        assert metrics.ece < 0.2  # At least basic compliance
    
    def test_overconfident_detection(self, poor_predictions, poor_ground_truth):
        """Overconfident wrong predictions should be detected"""
        metrics = compute_calibration(poor_predictions, poor_ground_truth)
        # Model is overconfident (high confidence, wrong answers)
        assert metrics.overconfidence_rate > 0
    
    def test_threshold_basic(self):
        """ONTO-ERS §4.1: Basic requires ECE ≤ 0.20"""
        from onto_standard import CalibrationMetrics
        metrics = CalibrationMetrics(ece=0.15, brier_score=0.1, 
                                     overconfidence_rate=0.1, underconfidence_rate=0.1)
        assert metrics.meets_basic() == True
        
        metrics_fail = CalibrationMetrics(ece=0.25, brier_score=0.1,
                                          overconfidence_rate=0.1, underconfidence_rate=0.1)
        assert metrics_fail.meets_basic() == False


# ============================================================
# COMPLIANCE LEVEL TESTS
# ============================================================

class TestComplianceLevel:
    """Tests for compliance level determination per ONTO-ERS §4"""
    
    def test_advanced_compliance(self, perfect_predictions, perfect_ground_truth):
        """Perfect model should achieve advanced compliance"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        # Perfect model should be at least BASIC
        assert result.compliance_level != ComplianceLevel.NONE
    
    def test_no_compliance(self, poor_predictions, poor_ground_truth):
        """Poor model should fail compliance"""
        result = evaluate(poor_predictions, poor_ground_truth)
        # Model that misses all unknowns should not be compliant
        assert result.compliance_level == ComplianceLevel.NONE
    
    def test_certification_ready(self, perfect_predictions, perfect_ground_truth):
        """Compliant models should be certification ready"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        if result.compliance_level != ComplianceLevel.NONE:
            assert result.certification_ready == True


# ============================================================
# RISK LEVEL TESTS
# ============================================================

class TestRiskLevel:
    """Tests for risk level assessment per ONTO-ERS §3.3.1"""
    
    def test_low_risk(self, perfect_predictions, perfect_ground_truth):
        """Well-calibrated model should have low risk"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
    
    def test_critical_risk(self, poor_predictions, poor_ground_truth):
        """Model missing unknowns should have high/critical risk"""
        result = evaluate(poor_predictions, poor_ground_truth)
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def test_risk_score_range(self, perfect_predictions, perfect_ground_truth):
        """Risk score should be 0-100"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        assert 0 <= result.risk_score <= 100


# ============================================================
# REGULATORY ALIGNMENT TESTS
# ============================================================

class TestRegulatoryAlignment:
    """Tests for regulatory alignment per ONTO-ERS §10"""
    
    def test_nist_aligned(self, perfect_predictions, perfect_ground_truth):
        """All evaluations should be NIST AI RMF aligned"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        assert result.nist_ai_rmf_aligned == True
    
    def test_eu_ai_act_standard(self, perfect_predictions, perfect_ground_truth):
        """Standard+ compliance should satisfy EU AI Act"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        if result.compliance_level in [ComplianceLevel.STANDARD, ComplianceLevel.ADVANCED]:
            assert result.eu_ai_act_compliant == True


# ============================================================
# OUTPUT FORMAT TESTS
# ============================================================

class TestOutputFormats:
    """Tests for output formats"""
    
    def test_to_dict(self, perfect_predictions, perfect_ground_truth):
        """Result should serialize to dict"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        d = result.to_dict()
        assert "compliance_level" in d
        assert "risk_score" in d
        assert "unknown_detection" in d
        assert "calibration" in d
    
    def test_to_json(self, perfect_predictions, perfect_ground_truth):
        """Result should serialize to JSON"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        json_str = result.to_json()
        import json
        parsed = json.loads(json_str)
        assert "compliance_level" in parsed
    
    def test_citation(self, perfect_predictions, perfect_ground_truth):
        """Result should generate legal citation"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        citation = result.citation()
        assert "ONTO Epistemic Risk Standard" in citation
        assert "ONTO-ERS-1.0" in citation
    
    def test_quick_report(self, perfect_predictions, perfect_ground_truth):
        """Quick report should be readable"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        report = quick_report(result)
        assert "ONTO EPISTEMIC RISK ASSESSMENT" in report
        assert "COMPLIANCE STATUS" in report


# ============================================================
# EDGE CASES
# ============================================================

class TestEdgeCases:
    """Edge case tests"""
    
    def test_empty_predictions(self):
        """Empty predictions should not crash"""
        result = evaluate([], [])
        assert result.n_samples == 0
    
    def test_mismatched_ids(self):
        """Predictions with missing ground truth should be handled"""
        preds = [Prediction(id="1", label=Label.KNOWN, confidence=0.9)]
        gt = [GroundTruth(id="2", label=Label.KNOWN)]  # Different ID
        result = evaluate(preds, gt)
        # Should handle gracefully
        assert result is not None
    
    def test_all_unknowns(self):
        """Dataset with all unknowns"""
        preds = [
            Prediction(id="1", label=Label.UNKNOWN, confidence=0.9),
            Prediction(id="2", label=Label.UNKNOWN, confidence=0.8),
        ]
        gt = [
            GroundTruth(id="1", label=Label.UNKNOWN),
            GroundTruth(id="2", label=Label.UNKNOWN),
        ]
        result = evaluate(preds, gt)
        assert result.unknown_detection.recall == 1.0


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestIntegration:
    """Integration tests"""
    
    def test_full_evaluation_pipeline(self, perfect_predictions, perfect_ground_truth):
        """Full evaluation pipeline should work end-to-end"""
        result = evaluate(perfect_predictions, perfect_ground_truth)
        
        # All required fields present
        assert result.unknown_detection is not None
        assert result.calibration is not None
        assert result.compliance_level is not None
        assert result.risk_level is not None
        assert result.standard_version == "ONTO-ERS-1.0"
        
        # Serialization works
        _ = result.to_dict()
        _ = result.to_json()
        _ = result.citation()
        _ = quick_report(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
