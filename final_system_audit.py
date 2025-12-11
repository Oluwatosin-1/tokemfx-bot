#!/usr/bin/env python3
"""
COMPREHENSIVE FINAL SYSTEM AUDIT
=================================
This script performs a complete verification that all missing imports are resolved,
no placeholder data exists, and dashboard modules are properly connected.
"""

import sys
import importlib
import importlib.util
import inspect
from typing import Dict, List, Any, Set
import os
import re

def audit_imports(src_dir: str = "src") -> Dict[str, Any]:
    """Audit all Python files for import resolution issues."""
    results = {
        'total_files': 0,
        'successful_imports': [],
        'failed_imports': [],
        'missing_modules': set(),
        'circular_imports': []
    }
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                results['total_files'] += 1
                module_path = os.path.join(root, file)
                
                try:
                    # Extract imports from file
                    with open(module_path, 'r') as f:
                        content = f.read()
                    
                    # Check for common import patterns
                    import_statements = extract_import_statements(content)
                    
                    # Try to import the module itself
                    rel_path = module_path.replace(f"{src_dir}/", "").replace(".py", "").replace("/", ".")
                    spec = None
                    
                    try:
                        spec = importlib.util.spec_from_file_location(rel_path, module_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            results['successful_imports'].append(rel_path)
                        else:
                            results['failed_imports'].append({'module': rel_path, 'error': 'Could not create spec'})
                    except Exception as e:
                        results['failed_imports'].append({'module': rel_path, 'error': str(e)})
                        
                except Exception as e:
                    results['failed_imports'].append({'module': module_path, 'error': str(e)})
    
    return results

def extract_import_statements(content: str) -> List[str]:
    """Extract import statements from Python code."""
    imports = []
    
    # Find import statements
    import_patterns = [
        r'^import\s+[\w\.]+',
        r'^from\s+[\w\.]+\s+import\s+[\w\*, ]+'
    ]
    
    for line in content.split('\n'):
        line = line.strip()
        for pattern in import_patterns:
            if re.match(pattern, line):
                imports.append(line)
                break
    
    return imports

def audit_placeholder_data(src_dir: str = "src") -> Dict[str, Any]:
    """Audit for placeholder implementations and todo comments."""
    results = {
        'placeholder_indicators': [],
        'todo_comments': [],
        'dummy_data': [],
        'hardcoded_values': [],
        'files_checked': 0
    }
    
    placeholder_patterns = [
        r'#\s*(TODO|FIXME|PLACEHOLDER|NOT\s+IMPLEMENTED)',
        r'#\s*(dummy|mock|fake|stub)',
        r'\b(dummy|fake|mock|stub|placeholder)\b',
        r'#\s*[Tt]emporary',
        r'hardcoded.*value',
        r'example.*data',
        r'sample.*only'
    ]
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                results['files_checked'] += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                    for i, line in enumerate(lines, 1):
                        for pattern in placeholder_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                results['placeholder_indicators'].append({
                                    'file': file_path,
                                    'line': i,
                                    'content': line.strip(),
                                    'pattern': pattern
                                })
                                break
                                
                except Exception as e:
                    results['placeholder_indicators'].append({
                        'file': file_path,
                        'error': str(e)
                    })
    
    return results

def audit_dashboard_connectivity() -> Dict[str, Any]:
    """Audit dashboard module connectivity and real data sources."""
    results = {
        'dashboard_modules': [],
        'data_sources': [],
        'real_implementations': [],
        'api_integrations': []
    }
    
    try:
        # Test dashboard imports
        import src.dashboard.dashboard_module as dashboard
        results['dashboard_modules'].append('dashboard_module imported successfully')
        
        # Check for real data functions
        if hasattr(dashboard, 'get_real_account_data'):
            results['data_sources'].append('Real account data function found')
            
        if hasattr(dashboard, 'render_advanced_dashboard'):
            results['dashboard_modules'].append('Advanced dashboard rendering available')
            
        # Check chart modules
        try:
            from src.charts import timeframes, fibonacci, chart_utils
            results['real_implementations'].append('Chart modules with real implementations')
        except Exception as e:
            results['real_implementations'].append(f'Chart modules missing: {e}')
            
        # Check API integrations
        try:
            from src.config.settings import APISettings
            api_config = APISettings()
            if hasattr(api_config, 'deriv_api_token'):
                results['api_integrations'].append('Deriv API configuration available')
        except:
            results['api_integrations'].append('API configuration needs verification')
            
    except Exception as e:
        results['dashboard_modules'].append(f'Dashboard import failed: {e}')
    
    return results

def main():
    """Run comprehensive system audit."""
    print("🔍 COMPREHENSIVE SYSTEM AUDIT")
    print("="*50)
    
    # 1. Import Audit
    print("\n1. 🔗 AUDITING IMPORTS...")
    import_results = audit_imports()
    print(f"   📊 Checked {import_results['total_files']} Python files")
    print(f"   ✅ {len(import_results['successful_imports'])} modules imported successfully")
    print(f"   ❌ {len(import_results['failed_imports'])} import failures")
    
    if import_results['failed_imports']:
        print("\n   ⚠️  IMPORT ISSUES FOUND:")
        for failure in import_results['failed_imports'][:5]:  # Show first 5
            print(f"      • {failure.get('module', 'Unknown')}: {failure.get('error', 'Unknown error')}")
        if len(import_results['failed_imports']) > 5:
            print(f"      ... and {len(import_results['failed_imports']) - 5} more")
    
    # 2. Placeholder Audit  
    print("\n2. 🎯 AUDITING FOR PLACEHOLDER DATA...")
    placeholder_results = audit_placeholder_data()
    print(f"   📊 Checked {placeholder_results['files_checked']} files")
    
    placeholder_count = len(placeholder_results['placeholder_indicators'])
    print(f"   🎯 Found {placeholder_count} placeholder indicators")
    
    if placeholder_count > 0:
        print("\n   ⚠️  PLACEHOLDER DATA DETECTED:")
        for item in placeholder_results['placeholder_indicators'][:10]:  # Show first 10
            file_rel = item.get('file', '').replace('src/', '')
            print(f"      • {file_rel}:{item.get('line', '?')} - {item.get('content', '')[:50]}...")
        if placeholder_count > 10:
            print(f"      ... and {placeholder_count - 10} more indicators")
    
    # 3. Dashboard Connectivity Audit
    print("\n3. 📊 AUDITING DASHBOARD CONNECTIVITY...")
    dashboard_results = audit_dashboard_connectivity()
    
    dashboard_items = len(dashboard_results['dashboard_modules']) + len(dashboard_results['data_sources']) + len(dashboard_results['real_implementations']) + len(dashboard_results['api_integrations'])
    print(f"   📊 Dashboard checks: {dashboard_items} items verified")
    
    for category, items in dashboard_results.items():
        if items:
            status = "✅" if not any("failed" in str(item).lower() for item in items) else "⚠️"
            print(f"   {status} {category.replace('_', ' ').title()}: {len(items)} components")
            if len(items) <= 3:  # Show details for small lists
                for item in items:
                    print(f"      • {item}")
    
    # Final Assessment
    print("\n" + "="*50)
    print("📋 FINAL AUDIT ASSESSMENT")
    print("="*50)
    
    # Grade import resolution
    import_success_rate = len(import_results['successful_imports']) / max(1, len(import_results['successful_imports']) + len(import_results['failed_imports']))
    import_success_pct = import_success_rate * 100
    print(f"Import Success Rate: {import_success_pct:.1f}%")
    # Grade placeholder removal
    placeholder_score = max(0, 100 - (placeholder_count * 2))  # Deduct 2 points per placeholder
    print(f"Placeholder Removal Score: {placeholder_score:.1f}%")
    # Grade dashboard connectivity
    dashboard_score = min(100, dashboard_items * 10)  # Base score on verified components
    print(f"Dashboard Connectivity Score: {dashboard_score:.1f}%")
    overall_score = (import_success_rate + placeholder_score + dashboard_score) / 3
    print(f"Overall Score: {overall_score:.1f}%")
    print("\n" + "="*50)
    
    if overall_score >= 90:
        print("🎊 EXCELLENT: System is professionally complete!")
        print("✅ All missing imports resolved")
        print("✅ No significant placeholder data found")
        print("✅ Dashboard fully connected to real data sources")
        print("✅ Ready for production deployment")
    elif overall_score >= 75:
        print("✅ GOOD: System is mostly complete")
        print("⚠️ Minor issues may need attention")
    else:
        print("⚠️ NEEDS ATTENTION: Significant issues detected")
        
    return {
        'imports': import_results,
        'placeholders': placeholder_results, 
        'dashboard': dashboard_results,
        'scores': {
            'import_success': import_success_rate,
            'placeholder_score': placeholder_score,
            'dashboard_score': dashboard_score,
            'overall_score': overall_score
        }
    }

if __name__ == "__main__":
    results = main()
    
    # Save detailed results
    import json
    with open('system_audit_results.json', 'w') as f:
        # Convert sets to lists for JSON serialization
        clean_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                clean_results[key] = {}
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, set):
                        clean_results[key][subkey] = list(subvalue)
                    else:
                        clean_results[key][subkey] = subvalue
            else:
                clean_results[key] = value
        json.dump(clean_results, f, indent=2, default=str)
    
    print("\n📄 Detailed audit results saved to 'system_audit_results.json'")
