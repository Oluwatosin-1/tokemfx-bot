#!/usr/bin/env python3
"""
TEST ENGINE - PROPRIETARY AUTOMATED TEST HARNESS
===============================================
Black-box automated testing system for prop firm compliance and validation.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
import traceback

# Configure test logging
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger('test_engine')

class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"

class PropFirmTestSuite(Enum):
    """Prop firm compliance test categories."""
    POSITION_SIZING = "position_sizing"
    RISK_MANAGEMENT = "risk_management"
    DRAW_DOWN_LIMITS = "drawdown_limits"
    STOP_LOSS_ENFORCEMENT = "stop_loss_enforcement"
    MARGIN_REQUIREMENTS = "margin_requirements"
    CORRELATION_EXPOSURE = "correlation_exposure"
    DAILY_LOSS_LIMITS = "daily_loss_limits"
    MAXIMUM_PROFIT_LIMITS = "maximum_profit_limits"
    TRADE_FREQUENCY_LIMITS = "trade_frequency_limits"
    MARKET_HOURS_COMPLIANCE = "market_hours_compliance"

class TestResult:
    """Individual test result."""

    def __init__(self, test_name: str, test_suite: PropFirmTestSuite):
        self.test_name = test_name
        self.test_suite = test_suite
        self.status = TestStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: float = 0.0
        self.error_message: Optional[str] = None
        self.assertions_passed = 0
        self.assertions_failed = 0
        self.details: Dict[str, Any] = {}
        self.checkpoints: List[Dict[str, Any]] = []

    def start(self):
        """Mark test as started."""
        self.status = TestStatus.RUNNING
        self.start_time = datetime.now()

    def pass_test(self):
        """Mark test as passed."""
        self.status = TestStatus.PASSED
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()

    def fail_test(self, error_message: str):
        """Mark test as failed."""
        self.status = TestStatus.FAILED
        self.error_message = error_message
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()

    def error_test(self, error_message: str):
        """Mark test as having encountered an error."""
        self.status = TestStatus.ERROR
        self.error_message = error_message
        self.end_time = datetime.now()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'test_name': self.test_name,
            'test_suite': self.test_suite.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'error_message': self.error_message,
            'assertions_passed': self.assertions_passed,
            'assertions_failed': self.assertions_failed,
            'details': self.details,
            'checkpoints': self.checkpoints
        }

class AutomatedTestEngine:
    """
    Automated test execution engine for prop firm compliance validation.
    """

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.active_tests: Dict[str, TestResult] = {}
        self.test_callbacks: Dict[str, List[Callable]] = {
            'test_started': [],
            'test_completed': [],
            'suite_completed': []
        }
        self.timeout_seconds = 300  # 5 minute default timeout

        test_logger.info("🧪 Automated Test Engine initialized")

    def add_test_callback(self, event: str, callback: Callable):
        """Add callback for test events."""
        if event in self.test_callbacks:
            self.test_callbacks[event].append(callback)

    def run_prop_firm_test_suite(self, critical_tests_only: bool = False) -> Dict[str, Any]:
        """
        Run complete prop firm compliance test suite.

        Args:
            critical_tests_only: Run only critical safety tests

        Returns:
            Complete test suite results
        """
        suite_start = datetime.now()
        test_logger.info("🏦 STARTING PROP FIRM COMPLIANCE TEST SUITE")

        # Define test suite
        test_suites = [
            (PropFirmTestSuite.POSITION_SIZING, self._test_position_sizing_limits),
            (PropFirmTestSuite.RISK_MANAGEMENT, self._test_risk_management_enforcement),
            (PropFirmTestSuite.DRAW_DOWN_LIMITS, self._test_drawdown_limits),
            (PropFirmTestSuite.STOP_LOSS_ENFORCEMENT, self._test_stop_loss_enforcement),
            (PropFirmTestSuite.DAILY_LOSS_LIMITS, self._test_daily_loss_limits),
            (PropFirmTestSuite.MARGIN_REQUIREMENTS, self._test_margin_requirements),
        ]

        # Add critical/safety tests if requested
        if critical_tests_only:
            test_suites = test_suites[:4]  # Only safety-critical tests

        results_summary = {
            'suite_start': suite_start.isoformat(),
            'suite_end': None,
            'total_tests': len(test_suites),
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_error': 0,
            'tests_skipped': 0,
            'compliance_score': 0.0,
            'critical_issues': [],
            'test_results': []
        }

        # Execute test suite
        for test_suite, test_function in test_suites:
            test_name = f"{test_suite.value.replace('_', ' ').title()} Test"
            test_result = self._execute_test(test_name, test_suite, test_function)

            self.test_results.append(test_result)
            results_summary['test_results'].append(test_result.to_dict())

            # Update counters
            if test_result.status == TestStatus.PASSED:
                results_summary['tests_passed'] += 1
            elif test_result.status == TestStatus.FAILED:
                results_summary['tests_failed'] += 1
                results_summary['critical_issues'].append(f"{test_name}: {test_result.error_message}")
            elif test_result.status == TestStatus.ERROR:
                results_summary['tests_error'] += 1
                results_summary['critical_issues'].append(f"{test_name}: {test_result.error_message}")
            elif test_result.status == TestStatus.SKIPPED:
                results_summary['tests_skipped'] += 1

        # Calculate compliance score
        total_completed = results_summary['tests_passed'] + results_summary['tests_failed'] + results_summary['tests_error']
        if total_completed > 0:
            results_summary['compliance_score'] = (results_summary['tests_passed'] / total_completed) * 100.0

        results_summary['suite_end'] = datetime.now().isoformat()

        test_logger.info(".1f")
        return results_summary

    def _execute_test(self, test_name: str, test_suite: PropFirmTestSuite, test_function: Callable) -> TestResult:
        """Execute individual test with proper error handling."""
        result = TestResult(test_name, test_suite)

        # Notify test started
        for callback in self.test_callbacks['test_started']:
            try:
                callback(result)
            except Exception as e:
                test_logger.error(f"Test start callback error: {e}")

        result.start()
        self.active_tests[test_name] = result

        try:
            # Execute test function
            test_function(result)

            if result.status == TestStatus.PENDING or result.status == TestStatus.RUNNING:
                # Test completed successfully if not explicitly failed
                result.pass_test()
                test_logger.info(f"✅ {test_name}: PASSED")

        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
            result.error_test(error_message)
            test_logger.error(f"❌ {test_name}: ERROR - {error_message}")
            test_logger.debug(f"   Traceback: {traceback.format_exc()}")

        # Clean up
        if test_name in self.active_tests:
            del self.active_tests[test_name]

        # Notify test completed
        for callback in self.test_callbacks['test_completed']:
            try:
                callback(result)
            except Exception as e:
                test_logger.error(f"Test completion callback error: {e}")

        return result

    def _test_position_sizing_limits(self, result: TestResult):
        """Test position sizing limit enforcement."""
        # Import risk management tests
        try:
            from src.tests.test_risk_management import TestRiskManagementSuite
            risk_suite = TestRiskManagementSuite()

            # Create risk parameters
            risk_params = {
                'max_drawdown': 0.05,
                'max_daily_loss': 0.03,
                'max_position_size': 0.02,
                'max_portfolio_exposure': 0.10,
                'min_stop_loss': 0.005,
                'max_correlated_positions': 2,
                'required_margin': 0.10
            }

            # Run position sizing test
            risk_suite.test_position_sizing_limits_enforced(risk_params)

            result.assertions_passed += 1

        except Exception as e:
            result.fail_test(f"Position sizing test failed: {e}")

    def _test_risk_management_enforcement(self, result: TestResult):
        """Test risk management enforcement."""
        try:
            from src.tests.test_risk_management import TestRiskManagementSuite
            risk_suite = TestRiskManagementSuite()

            # Test ultimate safety - risk rules cannot be broken
            risk_suite.test_risk_rules_cannot_be_broken()

            result.assertions_passed += 1

        except Exception as e:
            result.fail_test(f"Risk management enforcement test failed: {e}")

    def _test_drawdown_limits(self, result: TestResult):
        """Test drawdown limit enforcement."""
        try:
            from src.tests.test_risk_management import TestRiskManagementSuite
            risk_suite = TestRiskManagementSuite()

            # Create mock data and risk parameters
            from src.trading.test_backtest_system import create_sample_ohlc_data
            sample_data = create_sample_ohlc_data('R_10', 500)

            risk_params = {
                'max_drawdown': 0.05,
                'max_daily_loss': 0.03,
                'max_position_size': 0.02,
                'max_portfolio_exposure': 0.10,
                'min_stop_loss': 0.005,
                'max_correlated_positions': 2,
                'required_margin': 0.10
            }

            # Run drawdown test
            risk_suite.test_max_drawdown_never_exceeded(sample_data, risk_params)

            result.assertions_passed += 1

        except Exception as e:
            result.fail_test(f"Drawdown limits test failed: {e}")

    def _test_stop_loss_enforcement(self, result: TestResult):
        """Test stop loss enforcement."""
        try:
            from src.tests.test_risk_management import TestRiskManagementSuite
            risk_suite = TestRiskManagementSuite()

            # Create mock data and risk parameters
            from src.trading.test_backtest_system import create_sample_ohlc_data
            sample_data = create_sample_ohlc_data('R_10', 500)

            risk_params = {
                'max_drawdown': 0.05,
                'max_daily_loss': 0.03,
                'max_position_size': 0.02,
                'max_portfolio_exposure': 0.10,
                'min_stop_loss': 0.005,
                'max_correlated_positions': 2,
                'required_margin': 0.10
            }

            # Run stop loss test
            risk_suite.test_stop_loss_execution_required(sample_data, risk_params)

            result.assertions_passed += 1

        except Exception as e:
            result.fail_test(f"Stop loss enforcement test failed: {e}")

    def _test_daily_loss_limits(self, result: TestResult):
        """Test daily loss limit enforcement."""
        try:
            from src.tests.test_risk_management import TestRiskManagementSuite
            risk_suite = TestRiskManagementSuite()

            # Create mock data and risk parameters
            from src.trading.test_backtest_system import create_sample_ohlc_data
            sample_data = create_sample_ohlc_data('R_10', 500)

            risk_params = {
                'max_drawdown': 0.05,
                'max_daily_loss': 0.03,
                'max_position_size': 0.02,
                'max_portfolio_exposure': 0.10,
                'min_stop_loss': 0.005,
                'max_correlated_positions': 2,
                'required_margin': 0.10
            }

            # Run daily loss test
            risk_suite.test_daily_loss_limits_enforced(sample_data, risk_params)

            result.assertions_passed += 1

        except Exception as e:
            result.fail_test(f"Daily loss limits test failed: {e}")

    def _test_margin_requirements(self, result: TestResult):
        """Test margin requirement enforcement."""
        try:
            from src.tests.test_risk_management import TestRiskManagementSuite
            risk_suite = TestRiskManagementSuite()

            # Create risk parameters
            risk_params = {
                'max_drawdown': 0.05,
                'max_daily_loss': 0.03,
                'max_position_size': 0.02,
                'max_portfolio_exposure': 0.10,
                'min_stop_loss': 0.005,
                'max_correlated_positions': 2,
                'required_margin': 0.10
            }

            # Run position sizing test which includes margin checks
            risk_suite.test_position_sizing_limits_enforced(risk_params)

            result.assertions_passed += 1

        except Exception as e:
            result.fail_test(f"Margin requirements test failed: {e}")

    def get_test_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent test execution history."""
        return [result.to_dict() for result in self.test_results[-limit:]]

    def get_active_tests(self) -> List[str]:
        """Get currently running tests."""
        return list(self.active_tests.keys())

# Global test engine instance
test_engine = AutomatedTestEngine()

# Convenience functions
def run_prop_firm_tests(critical_only: bool = False) -> Dict[str, Any]:
    """Run prop firm compliance test suite."""
    return test_engine.run_prop_firm_test_suite(critical_only)

def get_test_status() -> Dict[str, Any]:
    """Get current testing status."""
    return {
        'active_tests': test_engine.get_active_tests(),
        'recent_tests': test_engine.get_test_history(10),
        'total_tests_run': len(test_engine.test_results)
    }

if __name__ == "__main__":
    # Quick test of the engine
    print("🧪 Test Engine Self-Test")

    # Run critical tests only
    results = run_prop_firm_tests(critical_only=True)

    print(f"Tests completed: {results['tests_passed'] + results['tests_failed'] + results['tests_error']} total")
    print(".1f")
    if results['critical_issues']:
        print("🚨 Critical Issues Found:")
        for issue in results['critical_issues'][:3]:  # Show first 3
            print(f"   • {issue}")

    print("✅ Test Engine operational")
