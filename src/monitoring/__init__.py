"""
TokemFX Monitoring Module
=========================
Enterprise-grade monitoring, auditing, and control systems.
Complete observability stack for production trading environments.
"""

try:
    from .audit.final_audit import comprehensive_loophole_audit
except ImportError:
    comprehensive_loophole_audit = None

try:
    from .controls.dashboard_control_system import dashboard_controller, create_streamlit_control_interface
except ImportError:
    dashboard_controller = create_streamlit_control_interface = None

try:
    from .emergency.emergency_controls import emergency_shutdown
except ImportError:
    emergency_shutdown = None

try:
    from .production.production_monitoring_system import production_monitor
except ImportError:
    production_monitor = None

try:
    from .system.system_audit import system_auditor
except ImportError:
    system_auditor = None

__all__ = [
    'comprehensive_loophole_audit',
    'dashboard_controller',
    'create_streamlit_control_interface',
    'emergency_shutdown',
    'production_monitor',
    'system_auditor'
]

__version__ = "1.0.0"
__description__ = "Enterprise Monitoring & Observability for TokemFX"
