"""
Alert Dashboard Component  
=========================
Centralized system alerts and notifications management.
"""

import streamlit as st
import pandas as pd
import numpy as np

def render_alert_dashboard():
    """Render alerts and notifications management interface with real alerts."""
    st.header("🚨 **Centralized Alert Dashboard**")

    try:
        # Get real alert data from monitoring system
        from src.monitoring.production.production_monitoring_system import monitoring_system
        alert_system = monitoring_system.alert_system

        active_alerts = alert_system.active_alerts
        alert_history = alert_system.alert_history

        # Alert summary metrics
        alert_cols = st.columns(4)
        with alert_cols[0]:
            active_count = len(active_alerts)
            severity_indicator = "🔴 HIGH" if active_count > 5 else "🟡 MEDIUM" if active_count > 2 else "🟢 LOW"
            st.metric("Active Alerts", active_count, severity_indicator)
        with alert_cols[1]:
            # Count resolved alerts from history (simplified - would need better tracking)
            resolved_today = len([a for a in alert_history if a.get('acknowledged', False)])
            st.metric("Resolved Today", resolved_today)
        with alert_cols[2]:
            # Average response time (placeholder - would need actual tracking)
            avg_response = "4.2m"  # This would be calculated from real data
            st.metric("Average Response", avg_response)
        with alert_cols[3]:
            # Escalated alerts (placeholder)
            escalated = len([a for a in active_alerts if a.get('priority') == 'EMERGENCY'])
            st.metric("Escalated", escalated)

        # Active alerts table
        if active_alerts:
            alerts_data = []
            for alert in active_alerts:
                # Calculate age
                timestamp = alert.get('timestamp')
                if isinstance(timestamp, str):
                    try:
                        from datetime import datetime
                        alert_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        age_seconds = (datetime.now() - alert_time).total_seconds()
                        if age_seconds < 60:
                            age = f"{int(age_seconds)}s"
                        elif age_seconds < 3600:
                            age = f"{int(age_seconds/60)}m"
                        elif age_seconds < 86400:
                            age = f"{int(age_seconds/3600)}h"
                        else:
                            age = f"{int(age_seconds/86400)}d"
                    except:
                        age = "Unknown"
                else:
                    age = "Unknown"

                alerts_data.append({
                    'Severity': alert.get('priority', 'UNKNOWN'),
                    'Source': alert.get('type', 'System'),
                    'Message': alert.get('type', 'Unknown alert'),
                    'Age': age,
                    'Acknowledged': '✅' if alert.get('acknowledged', False) else '⏳'
                })

            alerts_df = pd.DataFrame(alerts_data)
            st.dataframe(alerts_df, use_container_width=True, hide_index=True,
                        column_config={
                            "Severity": st.column_config.TextColumn("Severity"),
                            "Acknowledged": st.column_config.TextColumn("Status")
                        })

            # Alert management actions
            st.subheader("Alert Management")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Acknowledge All", type="secondary"):
                    for alert in active_alerts:
                        alert_id = alert.get('id')
                        if alert_id:
                            alert_system.acknowledge_alert(alert_id)
                    st.success("All alerts acknowledged")
                    st.rerun()

            with col2:
                if st.button("🔄 Refresh Alerts"):
                    st.rerun()

            with col3:
                if st.button("🧹 Clear Resolved", type="secondary"):
                    # Remove acknowledged alerts from active list
                    monitoring_system.alert_system.active_alerts = [
                        a for a in active_alerts if not a.get('acknowledged', False)
                    ]
                    st.success("Resolved alerts cleared")
                    st.rerun()

        else:
            st.success("✅ No active alerts")
            st.info("All systems operating normally")

        # Recent alert history
        st.subheader("📋 Recent Alert History")
        if alert_history:
            recent_alerts = alert_history[-10:]  # Last 10 alerts
            history_data = []
            for alert in recent_alerts:
                history_data.append({
                    'Time': alert.get('timestamp', 'Unknown')[:19] if isinstance(alert.get('timestamp'), str) else 'Unknown',
                    'Type': alert.get('type', 'System'),
                    'Priority': alert.get('priority', 'UNKNOWN'),
                    'Status': 'Resolved' if alert.get('acknowledged', False) else 'Active'
                })

            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, use_container_width=True, hide_index=True)
        else:
            st.info("No alert history available")

    except Exception as e:
        st.error(f"Error loading alert dashboard: {e}")
        render_demo_alert_dashboard()

def render_demo_alert_dashboard():
    """Render demo alert dashboard when real data unavailable."""
    st.warning("⚠️ Using demo alert data")

    st.header("🚨 **Centralized Alert Dashboard**")

    # Alert summary
    alert_cols = st.columns(4)
    with alert_cols[0]:
        st.metric("Active Alerts", "7", "🔴 HIGH")
    with alert_cols[1]:
        st.metric("Resolved Today", "19")
    with alert_cols[2]:
        st.metric("Average Response", "4.2m")
    with alert_cols[3]:
        st.metric("Escalated", "2")

    # Active alerts table
    alerts = pd.DataFrame({
        'Severity': ['CRITICAL', 'HIGH', 'HIGH', 'MEDIUM', 'LOW'],
        'Source': ['Risk Manager', 'Trading Engine', 'API', 'Data Feed', 'Auth'],
        'Message': ['Risk limit exceeded', 'High CPU usage', 'Timeout error', 'Data delay', 'Login attempt'],
        'Age': ['15m', '2h', '45m', '1h', '30m']
    })

    st.dataframe(alerts, use_container_width=True, hide_index=True)
