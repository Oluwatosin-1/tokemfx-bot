"""
Permission Middleware
====================
Access control and permission management for dashboard features.
"""

from typing import Dict, List, Set, Any

class PermissionMiddleware:
    """Permission-based access control middleware."""
    
    def __init__(self):
        self.role_hierarchy = {
            "viewer": {"permissions": ["view_positions", "view_performance"]},
            "trader": {"permissions": ["execute_trades", "modify_strategies", "view_positions", "risk_management"]},
            "analyst": {"permissions": ["view_positions", "view_alerts", "configure_alerts", "risk_management"]}, 
            "admin": {"permissions": ["full_access", "system_controls", "user_management", "emergency_controls"]}
        }
        
        self.component_permissions = {
            "dashboard": ["view_positions"],
            "backtesting": ["run_backtests"],
            "optimize": ["optimize_strategies"],
            "live_trading": ["execute_trades"],
            "performance": ["view_performance"],
            "ai_health": ["view_ai"],
            "system_audit": ["view_audit"],
            "production_monitor": ["view_system"],
            "alert_dashboard": ["manage_alerts"],
            "infrastructure": ["manage_infrastructure"]
        }
    
    def get_role_permissions(self, role: str) -> Set[str]:
        """Get all permissions for a role."""
        return set(self.role_hierarchy.get(role, {}).get("permissions", []))
    
    def has_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        """Check if user has required permission."""
        return required_permission in user_permissions or "full_access" in user_permissions
    
    def can_access_component(self, user_permissions: List[str], component_name: str) -> bool:
        """Check if user can access specific component."""
        required_permissions = self.component_permissions.get(component_name, [])
        
        if not required_permissions:  # No specific permissions required
            return True
            
        return any(self.has_permission(user_permissions, perm) for perm in required_permissions)
    
    def filter_accessible_components(self, user_permissions: List[str], components: Dict[str, Any]) -> Dict[str, Any]:
        """Filter components user can access."""
        accessible = {}
        for name, component in components.items():
            if self.can_access_component(user_permissions, name):
                accessible[name] = component
        return accessible
    
    def get_accessible_tabs(self, user_role: str, template_tabs: List[str]) -> List[str]:
        """Get tabs user can access based on role and template."""
        user_permissions = list(self.get_role_permissions(user_role))
        accessible_tabs = []
        
        for tab in template_tabs:
            if self.can_access_component(user_permissions, tab):
                accessible_tabs.append(tab)
                
        return accessible_tabs

# Global permission middleware instance
permission_middleware = PermissionMiddleware()

def check_component_access(user_permissions: List[str], component_name: str) -> bool:
    """Convenience function to check component access."""
    return permission_middleware.can_access_component(user_permissions, component_name)

def get_accessible_tabs_for_role(user_role: str, template_tabs: List[str]) -> List[str]:
    """Convenience function to get accessible tabs."""
    return permission_middleware.get_accessible_tabs(user_role, template_tabs)
