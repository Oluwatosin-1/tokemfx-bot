#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM HEALTH CHECK
=================================
Full system validation to ensure production readiness.
"""

import sys
import os
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

class SystemHealthChecker:
    """Comprehensive system health validation."""

    def __init__(self):
        self.results = {
            'import_errors': [],
            'placeholder_usage': [],
            'missing_implementations': [],
            'module_correctness': [],
            'dashboard_components': [],
            'critical_errors': [],
            'warnings': []
        }

    def run_full_health_check(self) -> Dict[str, Any]:
        """Run complete system health assessment."""
        print("🔍 COMPREHENSIVE SYSTEM HEALTH CHECK")
        print("=" * 60)

        # Test all dashboard components
        self._test_dashboard_components()

        # Test core modules
        self._test_core_modules()

        # Scan for placeholders and demo data
        self._scan_for_placeholders()

        # Check implementation completeness
        self._check_implementation_completeness()

        # Generate report
        return self._generate_report()

    def _test_dashboard_components(self):
        """Test all dashboard component imports and basic functionality."""
        print("📊 Testing Dashboard Components...")

        dashboard_components = [
            'src.dashboard.components.ai_monitoring',
            'src.dashboard.components.ai_trading',
            'src.dashboard.components.alert_dashboard',
            'src.dashboard.components.backtesting_studio',
            'src.dashboard.components.live_trading',
            'src.dashboard.components.performance_monitor',
            'src.dashboard.components.portfolio_dashboard',
            'src.dashboard.components.production_monitor',
            'src.dashboard.components.strategy_optimizer',
            'src.dashboard.components.system_audit',
        ]

        for component in dashboard_components:
            try:
                print(f"  Testing {component}...")
                module = importlib.import_module(component)

                # Check for required functions
                required_functions = ['render_' + component.split('.')[-1]]
                for func_name in required_functions:
                    if hasattr(module, func_name):
                        print(f"    ✅ {func_name} found")
                    else:
                        self.results['missing_implementations'].append({
                            'component': component,
                            'missing': func_name,
                            'type': 'function'
                        })

                self.results['dashboard_components'].append({
                    'component': component,
                    'status': 'operational',
                    'import_success': True
                })

            except ImportError as e:
                self.results['import_errors'].append({
                    'component': component,
                    'error': str(e),
                    'type': 'import_error'
                })
                print(f"    ❌ Import error: {e}")
            except Exception as e:
                self.results['critical_errors'].append({
                    'component': component,
                    'error': str(e),
                    'type': 'runtime_error'
                })
                print(f"    ❌ Runtime error: {e}")

    def _test_core_modules(self):
        """Test core system modules."""
        print("🔧 Testing Core Modules...")

        core_modules = [
            'src.ai_trading_system.analytics.performance_analyzer',
            'src.backtesting.engine',
            'src.trading.execution.broker',
            'src.monitoring.production.production_monitoring_system',
            'src.dashboard.security',
            'src.config.settings',
        ]

        for module_name in core_modules:
            try:
                print(f"  Testing {module_name}...")
                module = importlib.import_module(module_name)

                # Test basic instantiation where applicable
                if module_name == 'src.ai_trading_system.analytics.performance_analyzer':
                    analyzer = module.performance_analyzer
                    if hasattr(analyzer, 'get_performance_summary'):
                        summary = analyzer.get_performance_summary()
                        if summary.get('data_source') == 'aggregated_backtesting':
                            print("    ✅ Using real synthetic data")
                        else:
                            print("    ⚠️ May be using demo data")

                elif module_name == 'src.backtesting.engine':
                    # Test basic engine creation
                    from src.trading.execution.data_handler import DataHandler
                    dh = DataHandler(cache_dir='cache')
                    engine = module.BacktestEngine(data_handler=dh, cash=1000)
                    print("    ✅ Engine initialized successfully")

                elif module_name == 'src.trading.execution.broker':
                    # Just test import, don't create instance
                    print("    ✅ Broker module imported")

                print(f"    ✅ {module_name} operational")

            except ImportError as e:
                self.results['import_errors'].append({
                    'component': module_name,
                    'error': str(e),
                    'type': 'import_error'
                })
                print(f"    ❌ Import error: {e}")
            except Exception as e:
                self.results['critical_errors'].append({
                    'component': module_name,
                    'error': str(e),
                    'type': 'runtime_error'
                })
                print(f"    ❌ Runtime error: {e}")

    def _scan_for_placeholders(self):
        """Scan codebase for placeholder and demo data usage."""
        print("🔍 Scanning for Placeholders and Demo Data...")

        # Directories to scan
        scan_dirs = [
            'src/dashboard/components',
            'src/ai_trading_system',
            'src/monitoring',
        ]

        placeholder_patterns = [
            r'demo.*data',
            r'placeholder',
            r'fake.*data',
            r'mock.*data',
            r'test.*data',
            r'sample.*data',
            r'example.*data',
            r'DEMO.*DATA',
            r'PLACEHOLDER',
            r'FAKE.*DATA',
            r'MOCK.*DATA',
        ]

        for scan_dir in scan_dirs:
            scan_path = Path('src') / scan_dir.split('/')[-1]
            if scan_path.exists():
                for py_file in scan_path.rglob('*.py'):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read().lower()

                            for pattern in placeholder_patterns:
                                if re.search(pattern, content):
                                    # Check if it's in comments or actual code
                                    lines = content.split('\n')
                                    for i, line in enumerate(lines):
                                        if re.search(pattern, line):
                                            # Skip if it's in a comment
                                            if '#' in line and line.find('#') < line.find(re.search(pattern, line).group()):
                                                continue

                                            self.results['placeholder_usage'].append({
                                                'file': str(py_file),
                                                'line': i + 1,
                                                'pattern': pattern,
                                                'content': line.strip()
                                            })

                    except Exception as e:
                        self.results['warnings'].append({
                            'file': str(py_file),
                            'warning': f'Could not scan file: {e}'
                        })

    def _check_implementation_completeness(self):
        """Check for missing implementations and TODO items."""
        print("📋 Checking Implementation Completeness...")

        scan_dirs = ['src']

        todo_patterns = [
            r'TODO',
            r'FIXME',
            r'XXX',
            r'HACK',
            r'NOT.*IMPLEMENTED',
            r'PLACEHOLDER',
        ]

        for scan_dir in scan_dirs:
            scan_path = Path(scan_dir)
            if scan_path.exists():
                for py_file in scan_path.rglob('*.py'):
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                            for pattern in todo_patterns:
                                matches = re.findall(f'{pattern}.*', content, re.IGNORECASE)
                                for match in matches:
                                    self.results['missing_implementations'].append({
                                        'file': str(py_file),
                                        'pattern': pattern,
                                        'content': match.strip(),
                                        'type': 'todo_item'
                                    })

                    except Exception as e:
                        continue

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report."""
        print("\n" + "=" * 60)
        print("📊 SYSTEM HEALTH REPORT")
        print("=" * 60)

        total_issues = 0

        # Import Errors
        if self.results['import_errors']:
            print(f"\n❌ IMPORT ERRORS ({len(self.results['import_errors'])}):")
            for error in self.results['import_errors']:
                print(f"  • {error['component']}: {error['error']}")
                total_issues += 1

        # Critical Errors
        if self.results['critical_errors']:
            print(f"\n🚨 CRITICAL ERRORS ({len(self.results['critical_errors'])}):")
            for error in self.results['critical_errors']:
                print(f"  • {error['component']}: {error['error']}")
                total_issues += 1

        # Missing Implementations
        if self.results['missing_implementations']:
            print(f"\n⚠️ MISSING IMPLEMENTATIONS ({len(self.results['missing_implementations'])}):")
            for item in self.results['missing_implementations'][:10]:  # Show first 10
                if item['type'] == 'todo_item':
                    print(f"  • {item['file']}: {item['content']}")
                else:
                    print(f"  • {item['file']}: Missing {item['missing']}")
                total_issues += 1

        # Placeholder Usage
        if self.results['placeholder_usage']:
            print(f"\n🔶 PLACEHOLDER USAGE ({len(self.results['placeholder_usage'])}):")
            for item in self.results['placeholder_usage'][:5]:  # Show first 5
                print(f"  • {item['file']}:{item['line']}: {item['pattern']}")
                total_issues += 1

        # Dashboard Components Status
        operational_components = len([c for c in self.results['dashboard_components']
                                    if c['status'] == 'operational'])
        total_components = len(self.results['dashboard_components'])

        print("\n📊 COMPONENT STATUS:")
        print(f"  • Dashboard Components: {operational_components}/{total_components} operational")

        # Overall Assessment
        print("\n🏆 OVERALL ASSESSMENT:")
        if total_issues == 0:
            print("  ✅ SYSTEM IS PRODUCTION READY!")
            print("  🎯 No critical errors or missing implementations found")
        elif total_issues < 5:
            print("  ⚠️ MINOR ISSUES DETECTED")
            print(f"  📊 {total_issues} issues need attention")
            print("  💡 System is mostly ready but review issues above")
        else:
            print("  ❌ SIGNIFICANT ISSUES DETECTED")
            print(f"  🚨 {total_issues} issues require immediate attention")
            print("  🛠️ Fix issues before production deployment")

        return {
            'total_issues': total_issues,
            'import_errors': len(self.results['import_errors']),
            'critical_errors': len(self.results['critical_errors']),
            'missing_implementations': len(self.results['missing_implementations']),
            'placeholder_usage': len(self.results['placeholder_usage']),
            'operational_components': operational_components,
            'total_components': total_components,
            'production_ready': total_issues == 0,
            'detailed_results': self.results
        }

def main():
    """Run the comprehensive health check."""
    try:
        checker = SystemHealthChecker()
        results = checker.run_full_health_check()

        # Exit with appropriate code
        if results['production_ready']:
            print("\n🎉 SUCCESS: System is ready for production!")
            return 0
        else:
            print(f"\n⚠️ WARNING: {results['total_issues']} issues found")
            return 1

    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
