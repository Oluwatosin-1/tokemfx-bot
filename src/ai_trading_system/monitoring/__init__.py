"""
AI MONITORING AND DRIFT DETECTION SYSTEM
=========================================
Prop Firm Quality: AI Model Health Surveillance

This module provides comprehensive monitoring and validation for AI/ML components
used in trading systems, ensuring model drift detection, confidence monitoring,
and automated alerts for AI decision-making reliability.

Critical for institutional-grade systems where AI decisions must be continuously
validated and model degradation detected before it impacts trading performance.
"""

import os
import sys
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
import numpy as np
import pandas as pd

# Configure AI monitoring logging
os.makedirs('logs', exist_ok=True)
ai_logger = logging.getLogger('ai_monitoring')
ai_logger.setLevel(logging.INFO)
ai_handler = logging.FileHandler('logs/ai_monitoring.log')
ai_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
ai_logger.addHandler(ai_handler)

# Import trading AI components (with error handling)
try:
    from src.trading.core.trading_intelligence import analyze_backtest_for_trading, execute_ai_trade
    from src.tests.test_pattern_reliability import test_ai_decision_consistency
    from src.monitoring.audit.final_audit import comprehensive_loophole_audit
    AI_SYSTEMS_AVAILABLE = True
except ImportError as e:
    ai_logger.error(f"⚠️ AI components not fully available: {e}")
    AI_SYSTEMS_AVAILABLE = False

class AIMonitoringDashboard:
    """
    INSTITUTIONAL AI HEALTH DASHBOARD

    Provides real-time monitoring and early warning system for AI model health,
    confidence drift, and decision-making reliability in trading systems.
    """

    def __init__(self, confidence_alert_threshold: float = 0.7,
                 drift_detection_sensitivity: float = 0.1):
        self.confidence_alert_threshold = confidence_alert_threshold
        self.drift_detection_sensitivity = drift_detection_sensitivity

        # Monitoring data structures
        self.ai_decision_history = []
        self.confidence_track = []
        self.model_performance_metrics = {}
        self.drift_detection_alerts = []

        # Reference benchmarks for comparison
        self.baseline_confidence = None
        self.baseline_accuracy = None
        self.last_calibration_date = None

        ai_logger.info("🤖 AI Monitoring Dashboard initialized")
        ai_logger.info(f"🎯 Confidence Alert Threshold: {confidence_alert_threshold}")
        ai_logger.info(f"🚨 Drift Sensitivity: {drift_detection_sensitivity}")

    def record_ai_decision(self, decision_data: Dict[str, Any]) -> bool:
        """
        Record an AI decision for continuous monitoring

        Args:
            decision_data: {
                'timestamp': str,
                'decision_type': 'ENTRY_SIGNAL'|'EXIT_SIGNAL'|'HOLD_SIGNAL',
                'confidence_score': float (0-1),
                'model_features': dict,
                'market_conditions': dict,
                'outcome_result': 'SUCCESS'|'FAILURE'|None,
                'actual_pnl': float (if outcome available)
            }

        Returns:
            True if decision recorded successfully
        """
        try:
            # Validate required fields
            required_fields = ['decision_type', 'confidence_score']
            for field in required_fields:
                if field not in decision_data:
                    ai_logger.error(f"❌ Invalid AI decision data: missing {field}")
                    return False

            # Add timestamp if not provided
            if 'timestamp' not in decision_data:
                decision_data['timestamp'] = datetime.now().isoformat()

            # Validate confidence score range
            confidence = decision_data['confidence_score']
            if not (0 <= confidence <= 1):
                ai_logger.warning(f"🚨 Suspicious confidence score: {confidence} (should be 0-1)")
                decision_data['confidence_anomaly'] = 'OUT_OF_RANGE'

            # Add to history
            self.ai_decision_history.append(decision_data)

            # Keep only last 1000 decisions for memory management
            if len(self.ai_decision_history) > 1000:
                self.ai_decision_history = self.ai_decision_history[-1000:]

            # Update confidence tracking
            self.confidence_track.append({
                'timestamp': decision_data['timestamp'],
                'confidence': confidence,
                'decision_type': decision_data.get('decision_type', 'UNKNOWN')
            })

            # Check for immediate alerts
            self._check_immediate_ai_alerts(decision_data)

            ai_logger.info(f"AI decision recorded: confidence={confidence:.3f}")
            return True

        except Exception as e:
            ai_logger.error(f"❌ Failed to record AI decision: {e}")
            return False

    def get_ai_health_status(self) -> Dict[str, Any]:
        """
        Generate comprehensive AI health status report

        Returns:
            Detailed AI system health assessment
        """
        status = {
            'assessment_timestamp': datetime.now().isoformat(),
            'system_health': 'UNKNOWN',
            'confidence_metrics': {},
            'drift_detection': {},
            'performance_metrics': {},
            'recommended_actions': [],
            'alerts': [],
            'overall_confidence': 0.5
        }

        try:
            # Analyze recent AI performance
            recent_decisions = self.ai_decision_history[-50:] if len(self.ai_decision_history) >= 50 else self.ai_decision_history

            if not recent_decisions:
                status['system_health'] = 'NO_DATA'
                status['recommended_actions'] = ['Collect more AI decision data for baseline establishment']
                return status

            # Confidence analysis
            confidences = [d.get('confidence_score', 0) for d in recent_decisions if 'confidence_score' in d]

            if confidences:
                status['confidence_metrics'] = {
                    'mean_confidence': np.mean(confidences),
                    'std_confidence': np.std(confidences),
                    'min_confidence': np.min(confidences),
                    'max_confidence': np.max(confidences),
                    'recent_trend': self._calculate_confidence_trend(confidences[-20:] if len(confidences) >= 20 else confidences)
                }

                status['overall_confidence'] = status['confidence_metrics']['mean_confidence']

            # Drift detection analysis
            status['drift_detection'] = self._analyze_model_drift()

            # Performance metrics (based on available outcomes)
            completed_decisions = [d for d in recent_decisions if d.get('outcome_result') in ['SUCCESS', 'FAILURE']]

            if completed_decisions:
                successes = sum(1 for d in completed_decisions if d['outcome_result'] == 'SUCCESS')
                total = len(completed_decisions)
                accuracy = successes / total

                status['performance_metrics'] = {
                    'total_decisions_analyzed': total,
                    'success_rate': accuracy,
                    'failure_rate': 1 - accuracy,
                    'average_confidence_in_successes': np.mean([d['confidence_score'] for d in completed_decisions if d['outcome_result'] == 'SUCCESS']),
                    'average_confidence_in_failures': np.mean([d['confidence_score'] for d in completed_decisions if d['outcome_result'] == 'FAILURE'])
                }
            else:
                status['performance_metrics'] = {
                    'status': 'INSUFFICIENT_DATA',
                    'note': 'Need completed trades with success/failure outcomes'
                }

            # Determine overall system health
            health_score = self._calculate_ai_health_score(status)

            if health_score >= 0.9:
                status['system_health'] = 'EXCELLENT'
            elif health_score >= 0.8:
                status['system_health'] = 'GOOD'
            elif health_score >= 0.7:
                status['system_health'] = 'FAIR'
            elif health_score >= 0.6:
                status['system_health'] = 'CONCERNING'
            elif health_score >= 0.5:
                status['system_health'] = 'POOR'
            else:
                status['system_health'] = 'CRITICAL'

            # Generate alerts
            status['alerts'] = self._generate_ai_health_alerts(status)

            # Recommended actions
            status['recommended_actions'] = self._generate_ai_maintenance_recommendations(status)

            return status

        except Exception as e:
            ai_logger.error(f"❌ AI health assessment failed: {e}")
            status['system_health'] = 'ASSESSMENT_FAILED'
            status['error'] = str(e)
            return status

    def _check_immediate_ai_alerts(self, decision_data: Dict[str, Any]):
        """Check for immediate AI decision alerts"""

        alerts = []
        confidence = decision_data.get('confidence_score', 0)

        # Low confidence alert
        if confidence < self.confidence_alert_threshold:
            alerts.append(f"🚨 LOW CONFIDENCE DECISION: {confidence:.3f} < {self.confidence_alert_threshold}")

        # Extreme confidence (possible overfitting)
        if confidence > 0.95:
            alerts.append(f"⚠️ EXTREME CONFIDENCE: {confidence:.3f} - possible overfitting")

        # Sudden confidence change
        if len(self.confidence_track) >= 10:
            recent_confidence = np.mean([c['confidence'] for c in self.confidence_track[-10:]])
            if abs(confidence - recent_confidence) > 0.3:
                alerts.append(f"⚠️ SUDDEN CONFIDENCE SHIFT: {confidence:.3f} vs recent {recent_confidence:.3f}")

        # Log alerts
        if alerts:
            for alert in alerts:
                ai_logger.warning(alert)
            self.drift_detection_alerts.extend(alerts)

    def _analyze_model_drift(self) -> Dict[str, Any]:
        """Analyze for model drift and distribution changes"""

        drift_analysis = {
            'drift_detected': False,
            'drift_severity': 0.0,
            'drift_indicators': {},
            'baseline_comparison': {}
        }

        try:
            if len(self.ai_decision_history) < 50:
                drift_analysis['status'] = 'INSUFFICIENT_DATA'
                return drift_analysis

            recent_decisions = self.ai_decision_history[-50:]

            # Confidence distribution analysis
            confidences = [d.get('confidence_score', 0) for d in recent_decisions if 'confidence_score' in d]
            if confidences:
                drift_analysis['drift_indicators'] = {
                    'confidence_std_dev': np.std(confidences),
                    'confidence_skewness': self._calculate_skewness(confidences),
                    'confidence_kurtosis': self._calculate_kurtosis(confidences)
                }

                # Compare against baseline (if available)
                if self.baseline_confidence:
                    drift_magnitude = abs(np.mean(confidences) - self.baseline_confidence)
                    drift_analysis['baseline_comparison'] = {
                        'baseline_confidence': self.baseline_confidence,
                        'current_mean_confidence': np.mean(confidences),
                        'drift_magnitude': drift_magnitude
                    }

                    if drift_magnitude > self.drift_detection_sensitivity:
                        drift_analysis['drift_detected'] = True
                        drift_analysis['drift_severity'] = min(drift_magnitude, 1.0)

        except Exception as e:
            ai_logger.warning(f"Drift analysis error: {e}")
            drift_analysis['analysis_error'] = str(e)

        return drift_analysis

    def _calculate_confidence_trend(self, confidences: List[float]) -> str:
        """Calculate confidence trend direction"""

        if len(confidences) < 5:
            return 'INSUFFICIENT_DATA'

        try:
            # Simple linear trend
            x = np.arange(len(confidences))
            slope = np.polyfit(x, confidences, 1)[0]

            if slope > 0.001:
                return 'INCREASING'
            elif slope < -0.001:
                return 'DECREASING'
            else:
                return 'STABLE'
        except:
            return 'CALCULATION_ERROR'

    def _calculate_ai_health_score(self, status: Dict[str, Any]) -> float:
        """Calculate overall AI health score 0-1"""

        score_components = []
        weights = []

        # Confidence metrics (40% weight)
        confidence_metrics = status.get('confidence_metrics', {})
        if 'mean_confidence' in confidence_metrics:
            mean_conf = confidence_metrics['mean_confidence']
            confidence_score = max(0, min(1, mean_conf * 2))  # Scale 0-1 based on confidence
            score_components.append(confidence_score)
            weights.append(0.4)

        # Performance metrics (30% weight)
        perf_metrics = status.get('performance_metrics', {})
        if 'success_rate' in perf_metrics:
            success_rate = perf_metrics['success_rate']
            score_components.append(success_rate)
            weights.append(0.3)

        # Drift detection (30% weight)
        drift_analysis = status.get('drift_detection', {})
        if drift_analysis.get('drift_detected', False):
            drift_penalty = 1.0 - drift_analysis.get('drift_severity', 0.0)
            score_components.append(drift_penalty)
            weights.append(0.3)
        else:
            score_components.append(0.9)  # No drift penalty
            weights.append(0.3)

        # Calculate weighted score
        if score_components and weights:
            return np.average(score_components, weights=weights)
        else:
            return 0.5  # Default neutral score

    def _generate_ai_health_alerts(self, status: Dict[str, Any]) -> List[str]:
        """Generate AI health alerts"""

        alerts = []

        # Confidence alerts
        confidence_metrics = status.get('confidence_metrics', {})
        if confidence_metrics.get('mean_confidence', 0) < self.confidence_alert_threshold:
            alerts.append(f"🚨 LOW AVERAGE CONFIDENCE: {confidence_metrics['mean_confidence']:.3f} < {self.confidence_alert_threshold}")

        # Performance alerts
        perf_metrics = status.get('performance_metrics', {})
        if perf_metrics.get('success_rate', 1.0) < 0.5 and 'success_rate' in perf_metrics:
            alerts.append(f"🚨 POOR AI PERFORMANCE: Success rate {perf_metrics['success_rate']:.1%}")

        # Drift alerts
        drift_analysis = status.get('drift_detection', {})
        if drift_analysis.get('drift_detected', False):
            severity = drift_analysis.get('drift_severity', 0)
            alerts.append(f"🚨 MODEL DRIFT DETECTED: Severity {severity:.1%}")

        # Trend alerts
        if confidence_metrics.get('recent_trend') == 'DECREASING':
            alerts.append("⚠️ CONFIDENCE TREND DECLINING: Possible model degradation")

        return alerts

    def _generate_ai_maintenance_recommendations(self, status: Dict[str, Any]) -> List[str]:
        """Generate AI maintenance and improvement recommendations"""

        recommendations = []

        health = status.get('system_health', 'UNKNOWN')

        if health in ['CRITICAL', 'POOR']:
            recommendations.extend([
                '🔴 URGENT: Complete AI model retraining required',
                '🔴 IMMEDIATE: Switch to rule-based fallback system',
                '🔴 INVESTIGATE: Full root cause analysis of model performance'
            ])

        elif health == 'CONCERNING':
            recommendations.extend([
                '🟡 HIGH PRIORITY: Calibrate AI confidence thresholds',
                '🟡 MONITOR CLOSELY: Track model performance daily',
                '🟡 CONSIDER: Model parameter tuning or feature selection'
            ])

        elif health in ['FAIR', 'GOOD']:
            recommendations.extend([
                '🟢 MAINTAIN: Regular model monitoring (weekly)',
                '🟢 OPTIMIZE: Fine-tune model parameters gradually',
                '🟢 EXPAND: Consider additional training data sources'
            ])

        else:  # EXCELLENT
            recommendations.extend([
                '✅ EXCELLENT: Model performing optimally',
                '✅ MAINTAIN: Continue standard monitoring schedule',
                '✅ ENHANCE: Consider advanced model improvements'
            ])

        # Specific recommendations based on metrics
        alerts = status.get('alerts', [])
        if any('LOW AVERAGE CONFIDENCE' in alert for alert in alerts):
            recommendations.append('🥅 REJECT LOW CONFIDENCE: Implement minimum confidence threshold for live trading')

        if any('MODEL DRIFT' in alert for alert in alerts):
            recommendations.append('♻️ MODEL RECALIBRATION: Update training data to reflect current market conditions')

        return recommendations

    def calibrate_baseline(self):
        """Establish baseline performance metrics for drift detection"""

        if len(self.ai_decision_history) < 50:
            ai_logger.warning("❌ Insufficient data for baseline calibration (need ≥50 decisions)")
            return False

        try:
            # Calculate baseline metrics
            all_confidences = [d.get('confidence_score', 0) for d in self.ai_decision_history if 'confidence_score' in d]

            if all_confidences:
                self.baseline_confidence = np.mean(all_confidences)
                ai_logger.info(f"📊 Baseline confidence established: {self.baseline_confidence:.4f}")

            # Calculate baseline accuracy
            completed_decisions = [d for d in self.ai_decision_history if d.get('outcome_result') in ['SUCCESS', 'FAILURE']]
            if completed_decisions:
                successes = sum(1 for d in completed_decisions if d['outcome_result'] == 'SUCCESS')
                self.baseline_accuracy = successes / len(completed_decisions)
                ai_logger.info(f"📊 Baseline accuracy established: {self.baseline_accuracy:.1%}")

            self.last_calibration_date = datetime.now().isoformat()
            ai_logger.info("✅ AI baseline calibration completed")
            return True

        except Exception as e:
            ai_logger.error(f"❌ Baseline calibration failed: {e}")
            return False

    @staticmethod
    def _calculate_skewness(data: List[float]) -> float:
        """Calculate skewness of distribution"""
        if len(data) < 3:
            return 0.0
        mean_val = np.mean(data)
        std_val = np.std(data)
        if std_val == 0:
            return 0.0
        return np.mean([((x - mean_val) / std_val) ** 3 for x in data])

    @staticmethod
    def _calculate_kurtosis(data: List[float]) -> float:
        """Calculate kurtosis of distribution"""
        if len(data) < 4:
            return 0.0
        mean_val = np.mean(data)
        std_val = np.std(data)
        if std_val == 0:
            return 0.0
        return np.mean([((x - mean_val) / std_val) ** 4 for x in data]) - 3

# Global AI monitoring instance
ai_monitor = AIMonitoringDashboard()

def validate_ai_decision_quality(decision_confidence: float, market_conditions: Dict[str, Any],
                               decision_type: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate individual AI decision quality

    Args:
        decision_confidence: 0-1 confidence score from AI model
        market_conditions: Current market data
        decision_type: 'ENTRY_SIGNAL', 'EXIT_SIGNAL', etc.

    Returns:
        Tuple of (approved: bool, reason: str, analysis: dict)
    """

    analysis = {
        'confidence_score': decision_confidence,
        'decision_type': decision_type,
        'market_volatility': _assess_market_volatility(market_conditions),
        'ai_health_status': ai_monitor.get_ai_health_status(),
        'approval_reason': ''
    }

    # Record decision for monitoring
    decision_record = {
        'decision_type': decision_type,
        'confidence_score': decision_confidence,
        'market_conditions': market_conditions,
        'validation_timestamp': datetime.now().isoformat()
    }
    ai_monitor.record_ai_decision(decision_record)

    # Decision approval logic
    confidence_threshold = 0.6  # Minimum confidence for approval
    health_score = analysis['ai_health_status'].get('overall_confidence', 0.5)

    # High volatility requires higher confidence
    volatility_adjustment = analysis['market_volatility'] * 0.1
    adjusted_threshold = min(confidence_threshold + volatility_adjustment, 0.8)

    if decision_confidence >= adjusted_threshold and health_score >= 0.7:
        analysis['approval_reason'] = f"Decision approved: confidence {decision_confidence:.3f} ≥ threshold {adjusted_threshold:.3f}"
        return True, "AI_DECISION_APPROVED", analysis
    else:
        reason = f"Decision rejected: "
        if decision_confidence < adjusted_threshold:
            reason += f"low confidence ({decision_confidence:.3f} < {adjusted_threshold:.3f})"
        if health_score < 0.7:
            reason += f"poor AI health (score: {health_score:.3f})"
        analysis['approval_reason'] = reason
        return False, "AI_DECISION_REJECTED", analysis

def _assess_market_volatility(market_data: Dict[str, Any]) -> float:
    """
    Assess market volatility level (0-1 scale)
    Higher values indicate more volatile conditions
    """
    try:
        # Simple volatility proxy based on price swings
        prices = market_data.get('prices', [])
        if len(prices) < 10:
            return 0.3  # Default moderate volatility

        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = abs((prices[i] - prices[i-1]) / prices[i-1])
                returns.append(ret)

        if returns:
            avg_return = np.mean(returns)
            volatility = min(avg_return * 10, 1.0)  # Scale to 0-1
            return volatility
        else:
            return 0.3

    except:
        return 0.5  # Default value

def export_ai_monitoring_report() -> Dict[str, Any]:
    """Export comprehensive AI monitoring report"""

    report = {
        'export_timestamp': datetime.now().isoformat(),
        'ai_health_status': ai_monitor.get_ai_health_status(),
        'monitoring_summary': {
            'total_decisions_recorded': len(ai_monitor.ai_decision_history),
            'baseline_confidence': ai_monitor.baseline_confidence,
            'baseline_accuracy': ai_monitor.baseline_accuracy,
            'last_calibration': ai_monitor.last_calibration_date
        },
        'recommendations': [
            'Calibrate AI baseline with recent known-good decisions',
            'Monitor confidence distribution for early drift detection',
            'Implement confidence thresholding for live trading',
            'Regular model retraining based on market condition changes',
            'Build alternative decision-making system for AI failures'
        ]
    }

    # Save report
    report_path = f'logs/ai_monitoring_report_{int(datetime.now().timestamp())}.json'
    try:
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        report['report_saved'] = report_path
        ai_logger.info(f"📄 AI monitoring report saved: {report_path}")
    except Exception as e:
        ai_logger.error(f"Failed to save AI report: {e}")
        report['save_error'] = str(e)

    return report

def run_ai_health_diagnostics() -> Dict[str, Any]:
    """Run comprehensive AI health diagnostics"""

    ai_logger.info("🔬 RUNNING AI HEALTH DIAGNOSTICS")

    diagnostics = {
        'diagnostic_timestamp': datetime.now().isoformat(),
        'health_status': ai_monitor.get_ai_health_status(),
        'diagnostic_tests': {},
        'issues_found': [],
        'actions_required': []
    }

    # Test 1: Historical decision consistency
    if len(ai_monitor.ai_decision_history) >= 20:
        recent_confidences = [d.get('confidence_score', 0) for d in ai_monitor.ai_decision_history[-20:]]
        consistency_score = 1.0 - (np.std(recent_confidences) / np.mean(recent_confidences))
        diagnostics['diagnostic_tests']['confidence_consistency'] = {
            'score': consistency_score,
            'status': 'GOOD' if consistency_score > 0.8 else 'POOR'
        }
        if consistency_score <= 0.8:
            diagnostics['issues_found'].append('Low confidence consistency')
            diagnostics['actions_required'].append('Investigate confidence scoring reliability')
    else:
        diagnostics['diagnostic_tests']['confidence_consistency'] = {
            'status': 'INSUFFICIENT_DATA',
            'minimum_required': 20,
            'currently_have': len(ai_monitor.ai_decision_history)
        }

    # Test 2: Decision pattern analysis
    decision_types = [d.get('decision_type', 'UNKNOWN') for d in ai_monitor.ai_decision_history[-100:] if 'decision_type' in d]
    if decision_types:
        type_distribution = pd.Series(decision_types).value_counts().to_dict()
        diagnostics['diagnostic_tests']['decision_distribution'] = {
            'distribution': type_distribution,
            'most_common': max(type_distribution.items(), key=lambda x: x[1])[0],
            'uniqueness_ratio': len(type_distribution) / len(decision_types)
        }

        if len(type_distribution) < 2:
            diagnostics['issues_found'].append('Limited decision variety')
            diagnostics['actions_required'].append('Expand AI decision-making options')

    # Test 3: Performance stability
    if len(ai_monitor.ai_decision_history) >= 50:
        # Check if performance is trending
        recent_successes = sum(1 for d in ai_monitor.ai_decision_history[-50:]
                              if d.get('outcome_result') == 'SUCCESS')
        older_successes = sum(1 for d in ai_monitor.ai_decision_history[-100:-50]
                             if d.get('outcome_result') == 'SUCCESS')

        if older_successes > 0:
            performance_change = (recent_successes - older_successes) / older_successes
            diagnostics['diagnostic_tests']['performance_stability'] = {
                'recent_successes': recent_successes,
                'older_successes': older_successes,
                'change_percentage': performance_change,
                'trend': 'IMPROVING' if performance_change > 0.1 else 'DECLINING' if performance_change < -0.1 else 'STABLE'
            }

            if abs(performance_change) > 0.2:
                diagnostics['issues_found'].append('Significant performance change')
                diagnostics['actions_required'].append('Investigate source of performance shift')

    ai_logger.info("✅ AI HEALTH DIAGNOSTICS COMPLETED")
    ai_logger.info(f"🔍 Issues found: {len(diagnostics['issues_found'])}")
    ai_logger.info(f"📋 Actions required: {len(diagnostics['actions_required'])}")

    return diagnostics

# Add the missing import for run_ai_health_diagnostics
if __name__ == "__main__":
    print("🤖 AI MONITORING AND DRIFT DETECTION SYSTEM")
    print("============================================")

    # Run diagnostics
    diagnostics = run_ai_health_diagnostics()
    health = ai_monitor.get_ai_health_status()

    print("📊 AI HEALTH STATUS:")
    overall_confidence = health.get('overall_confidence', 0.5)
    print(f"   Overall Confidence: {overall_confidence:.3f}")
    print(f"🏆 System Health: {health.get('system_health', 'UNKNOWN')}")

    if diagnostics['issues_found']:
        print("\n🚨 ISSUES DETECTED:")
        for issue in diagnostics['issues_found']:
            print(f"   • {issue}")

    if diagnostics['actions_required']:
        print("\n📋 RECOMMENDED ACTIONS:")
        for action in diagnostics['actions_required']:
            print(f"   • {action}")

    print("\n📄 Comprehensive report saved")
    print("\n⚠️  Note: This system requires active AI decision recording for effective monitoring")
    print("   Call ai_monitor.record_ai_decision() in your trading logic to enable full monitoring")
