"""
Fixed Dashboard Component Registry
==================================
Corrected registry with proper function name mappings.
"""

import importlib
import logging
from typing import Dict, List, Any, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ComponentRegistry:
    """Central registry for dashboard components and tab management."""
    
    def __init__(self):
        self._components: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, List[str]] = {}
        self._load_builtin_components()
        
    def _load_builtin_components(self):
        """Load all built-in dashboard components."""
        
        # Core trading components - now with correct function names
        self.register_component({
            'name': 'dashboard',
            'title': '📊 Dashboard',
            'function': self._import_component('src.dashboard.dashboard_module.render_advanced_dashboard'),
            'category': 'core',
            'permissions': ['view_positions'],
            'description': 'Main portfolio overview and account status',
            'icon': '📊'
        })
        
        self.register_component({
            'name': 'backtesting',
            'title': '🔍 Backtest Studio',
            'function': self._import_component('src.dashboard.ui_components.render_advanced_backtesting.render_advanced_backtesting'),
            'category': 'trading',
            'permissions': ['run_backtests'],
            'description': 'Advanced strategy backtesting and optimization',
            'icon': '🔍'
        })
        
        self.register_component({
            'name': 'optimize',
            'title': '⚡ Strategy Optimizer',
            'function': self._import_component('src.dashboard.components.strategy_optimizer.render_strategy_optimizer'),
            'category': 'trading',
            'permissions': ['optimize_strategies'],
            'description': 'Automated strategy parameter optimization',
            'icon': '⚡'
        })
        
        # Live trading components
        self.register_component({
            'name': 'live_trading',
            'title': '🎯 Live Trading',
            'function': self._import_component('src.dashboard.ui_components.render_live_trading.render_live_trading'),
            'category': 'trading',
            'permissions': ['execute_trades'],
            'description': 'Real-time trade execution and position management',
            'icon': '🎯'
        })
        
        # Performance monitoring
        self.register_component({
            'name': 'performance',
            'title': '📈 Performance Monitor',
            'function': self._import_component('src.dashboard.components.performance_monitor.render_performance_monitor'),
            'category': 'analysis',
            'permissions': ['view_performance'],
            'description': 'Trading performance analytics and reporting',
            'icon': '📈'
        })
        
        # AI/ML components
        self.register_component({
            'name': 'ai_health',
            'title': '🤖 AI Health Monitor',
            'function': self._import_component('src.dashboard.ui_components.render_ai_health_monitor.render_ai_monitoring'),
            'category': 'ai',
            'permissions': ['view_ai'],
            'description': 'AI model performance monitoring and analysis',
            'icon': '🤖'
        })
        
        # System monitoring
        self.register_component({
            'name': 'system_audit',
            'title': '🔬 System Audit',
            'function': self._import_component('src.dashboard.components.system_audit.render_system_audit'),
            'category': 'system',
            'permissions': ['view_audit'],
            'description': 'Comprehensive system security and compliance audit',
            'icon': '🔬'
        })

        self.register_component({
            'name': 'production_monitor',
            'title': '📊 Production Monitor',
            'function': self._import_component('src.dashboard.components.production_monitor.render_production_monitor'),
            'category': 'system',
            'permissions': ['view_system'],
            'description': 'Real-time system health and performance monitoring',
            'icon': '📊'
        })

        self.register_component({
            'name': 'alert_dashboard',
            'title': '🚨 Alert Dashboard',
            'function': self._import_component('src.dashboard.components.alert_dashboard.render_alert_dashboard'),
            'category': 'system',
            'permissions': ['manage_alerts'],
            'description': 'Centralized alert management and monitoring',
            'icon': '🚨'
        })

        self.register_component({
            'name': 'infrastructure',
            'title': '🔧 Infrastructure',
            'function': self._import_component('src.dashboard.components.infrastructure.render_infrastructure'),
            'category': 'system',
            'permissions': ['manage_infrastructure'],
            'description': 'System infrastructure configuration and management',
            'icon': '🔧'
        })
        
        logger.info(f"Loaded {len(self._components)} built-in dashboard components")
    
    def _import_component(self, module_path: str) -> Callable:
        """Dynamically import and return component function."""
        try:
            module_name, function_name = module_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            return function
        except (ImportError, AttributeError) as e:
            logger.warning(f"Failed to import component {module_path}: {e}")
            return self._create_placeholder_component
    
    def _create_placeholder_component(self):
        """Create a placeholder component for missing modules."""
        import streamlit as st
        def placeholder():
            st.warning("⚠️ This component is currently under development")
            st.info("Component will be available in the next update")
        return placeholder
    
    def register_component(self, component_config: Dict[str, Any]):
        """Register a new dashboard component."""
        component_name = component_config['name']
        self._components[component_name] = component_config
        
        category = component_config.get('category', 'other')
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(component_name)
        
        logger.debug(f"Registered component: {component_name}")
    
    def get_component(self, name: str) -> Optional[Dict[str, Any]]:
        """Get component configuration by name."""
        return self._components.get(name)
    
    def get_components_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all components in a specific category."""
        component_names = self._categories.get(category, [])
        return [self._components[name] for name in component_names if name in self._components]
    
    def get_all_components(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered components."""
        return self._components.copy()
    
    def has_component(self, name: str) -> bool:
        """Check if a component is registered."""
        return name in self._components
    
    def get_tab_configurations(self, tab_names: List[str]) -> List[Dict[str, Any]]:
        """Get configurations for specific tabs."""
        configs = []
        for name in tab_names:
            component = self.get_component(name)
            if component:
                configs.append(component)
        return configs

# Global component registry instance
component_registry = ComponentRegistry()

# Convenience functions
def get_component_registry() -> ComponentRegistry:
    """Get global component registry instance."""
    return component_registry

def register_custom_component(component_config: Dict[str, Any]):
    """Register a custom dashboard component."""
    component_registry.register_component(component_config)

def get_available_components() -> Dict[str, Dict[str, Any]]:
    """Get all available components."""
    return component_registry.get_all_components()
