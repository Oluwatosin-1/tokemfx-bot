"""
Dashboard Loader System
=======================
Dynamic dashboard tab loading and configuration management.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DashboardLoader:
    """
    Dynamic dashboard loading and template management system.
    
    Supports:
    - Role-based dashboard configurations
    - Dynamic tab loading
    - Permission-based feature access
    - Template-based customization
    """
    
    def __init__(self):
        self.templates: Dict[str, Any] = {}
        self.template_path = Path(__file__).parent / "dashboard_templates.json"
        self.load_templates()
        
    def load_templates(self):
        """Load dashboard templates from configuration file."""
        try:
            if self.template_path.exists():
                with open(self.template_path, 'r') as f:
                    self.templates = json.load(f)
                logger.info(f"Loaded {len(self.templates)} dashboard templates")
            else:
                logger.warning("Dashboard templates file not found, using defaults")
                self._load_default_templates()
        except Exception as e:
            logger.error(f"Error loading dashboard templates: {e}")
            self._load_default_templates()
            
    def _load_default_templates(self):
        """Load default templates if file is missing."""
        self.templates = {
            "admin": {
                "name": "Administrator",
                "tabs": ["dashboard", "backtesting", "optimize", "live_trading", "performance", 
                        "ai_health", "system_audit", "production_monitor", "alert_dashboard", "infrastructure"],
                "permissions": ["full_access"]
            },
            "trader": {
                "name": "Trader", 
                "tabs": ["dashboard", "backtesting", "live_trading", "performance"],
                "permissions": ["execute_trades", "view_positions"]
            },
            "viewer": {
                "name": "Viewer",
                "tabs": ["dashboard", "performance"],
                "permissions": ["read_only"]
            }
        }
    
    def get_template(self, template_name: str) -> Dict[str, Any]:
        """Get dashboard template configuration."""
        return self.templates.get(template_name, self.templates.get("admin", {}))
    
    def get_available_templates(self) -> Dict[str, str]:
        """Get list of available template names with descriptions."""
        return {name: template.get("description", template["name"]) 
                for name, template in self.templates.items()}
    
    def get_tab_config_for_template(self, template_name: str) -> List[Dict[str, Any]]:
        """Get tab configurations for specific template."""
        template = self.get_template(template_name)
        tabs = template.get("tabs", [])
        
        # Map tab names to display titles and components
        tab_configurations = {
            "dashboard": {"title": "📊 Dashboard", "component": "dashboard", "icon": "📊"},
            "backtesting": {"title": "🔍 Backtest Studio", "component": "backtesting", "icon": "🔍"},
            "optimize": {"title": "⚡ Strategy Optimizer", "component": "optimize", "icon": "⚡"},
            "live_trading": {"title": "🎯 Live Trading", "component": "live_trading", "icon": "🎯"},
            "ai_trading": {"title": "🤖 AI Trading", "component": "ai_trading", "icon": "🤖"},
            "performance": {"title": "📈 Performance Monitor", "component": "performance", "icon": "📈"},
            "ai_health": {"title": "🤖 AI Health Monitor", "component": "ai_health", "icon": "🤖"},
            "system_audit": {"title": "🔬 System Audit", "component": "system_audit", "icon": "🔬"},
            "production_monitor": {"title": "📊 Production Monitor", "component": "production_monitor", "icon": "📊"},
            "alert_dashboard": {"title": "🚨 Alert Dashboard", "component": "alert_dashboard", "icon": "🚨"},
            "infrastructure": {"title": "🔧 Infrastructure", "component": "infrastructure", "icon": "🔧"}
        }
        
        configurations = []
        for tab_name in tabs:
            if tab_name in tab_configurations:
                config = tab_configurations[tab_name].copy()
                config["name"] = tab_name
                configurations.append(config)
                
        return configurations
    
    def validate_template(self, template_name: str) -> bool:
        """Validate that template has valid configuration."""
        template = self.get_template(template_name)
        
        # Check required fields
        required_fields = ["name", "tabs"]
        missing_fields = [field for field in required_fields if field not in template]
        
        if missing_fields:
            logger.warning(f"Template '{template_name}' missing required fields: {missing_fields}")
            return False
            
        # Check tabs exist in valid tab list
        valid_tabs = list(self.get_available_templates().keys())
        if template_name not in valid_tabs and template_name != "admin":
            logger.warning(f"Template '{template_name}' not in valid templates list")
            return False
            
        return True

# Global instance
dashboard_loader = DashboardLoader()

def load_dashboard_template(template_name: str = "admin") -> List[Dict[str, Any]]:
    """
    Convenience function to load dashboard template configuration.
    
    Args:
        template_name: Name of dashboard template to load
        
    Returns:
        List of tab configurations for the template
    """
    return dashboard_loader.get_tab_config_for_template(template_name)

def get_available_templates() -> Dict[str, str]:
    """Get all available dashboard templates."""
    return dashboard_loader.get_available_templates()

def switch_dashboard_template(template_name: str) -> bool:
    """
    Switch active dashboard template.
    
    Args:
        template_name: Name of template to switch to
        
    Returns:
        True if template exists and was switched, False otherwise
    """
    if dashboard_loader.validate_template(template_name):
        logger.info(f"Switched to dashboard template: {template_name}")
        return True
    else:
        logger.warning(f"Failed to switch to invalid template: {template_name}")
        return False
