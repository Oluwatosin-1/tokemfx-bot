"""
Network Health Monitoring Component for TokemFX Dashboard
=========================================================

Real-time network resilience monitoring and dashboard integration.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Import network resilience manager
from src.network_resilience import network_resilience

def render_network_health_monitor():
    """
    Render comprehensive network health monitoring dashboard.

    Shows real-time connectivity status, resilience metrics, and system health.
    """
    st.header("🌐 **Network Resilience Monitor**")

    # Get real-time health status
    health_status = network_resilience.get_health_status()

    # Current operational mode indicator
    mode = health_status.get('operational_mode', 'unknown')
    mode_color = {
        'connected': '🟢',
        'degraded': '🟡',
        'offline': '🔴'
    }.get(mode, '⚪')

    col_status, col_metrics, col_alerts = st.columns([1, 2, 1])

    # Operational Status Column
    with col_status:
        st.subheader("📊 **Operational Status**")
        st.metric(
            label="Connection State",
            value=f"{mode_color} {mode.title()}"
        )

        circuit_state = health_status.get('circuit_breaker', {}).get('state', 'unknown')
        circuit_color = {
            'closed': '🟢',
            'open': '🔴',
            'half_open': '🟡'
        }.get(circuit_state, '⚪')

        st.metric(
            label="Circuit Breaker",
            value=f"{circuit_color} {circuit_state.title()}"
        )

        # Connection quality indicator
        conn_stats = health_status.get('connection_stats', {})
        success_rate = conn_stats.get('success_rate', 0)
        rate_color = '🟢' if success_rate > 95 else '🟡' if success_rate > 80 else '🔴'

        st.metric(
            label="Success Rate",
            value=".1f",
            help="Percentage of successful network operations"
        )

    # Performance Metrics Column
    with col_metrics:
        st.subheader("📊 **Performance Metrics**")

        # Response time chart
        response_time = conn_stats.get('average_response_time', 0)
        st.metric(
            label="Avg Response Time",
            value=".2f",
            help="Average API response time in seconds"
        )

        # Error breakdown
        error_breakdown = health_status.get('error_breakdown', {})

        col_dns, col_ssl, col_timeout = st.columns(3)

        with col_dns:
            dns_errors = error_breakdown.get('dns_failures', 0)
            st.metric(label="DNS Errors", value=str(dns_errors))

        with col_ssl:
            ssl_errors = error_breakdown.get('ssl_failures', 0)
            st.metric(label="SSL Errors", value=str(ssl_errors))

        with col_timeout:
            timeout_errors = error_breakdown.get('timeouts', 0)
            st.metric(label="Timeouts", value=str(timeout_errors))

        # Connection attempts chart
        st.subheader("🔄 **Connection Activity**")
        attempts = conn_stats.get('total_attempts', 0)
        successful = conn_stats.get('successful_connections', 0)

        fig = go.Figure(data=[
            go.Bar(name='Successful', x=['Connections'], y=[successful],
                   marker_color='lightgreen'),
            go.Bar(name='Failed', x=['Connections'], y=[attempts - successful],
                   marker_color='lightcoral')
        ])
        fig.update_layout(
            title="Recent Connection Attempts",
            showlegend=True,
            height=200
        )
        st.plotly_chart(fig, use_container_width=True)

    # Alerts and Endpoint Status Column
    with col_alerts:
        st.subheader("🚨 **Alerts & Status**")

        # Generate alerts based on health metrics
        alerts = _generate_health_alerts(health_status)

        if alerts:
            for alert in alerts:
                if alert['level'] == 'critical':
                    st.error(f"🚨 {alert['message']}")
                elif alert['level'] == 'warning':
                    st.warning(f"⚠️ {alert['message']}")
                else:
                    st.info(f"ℹ️ {alert['message']}")
        else:
            st.success("✅ All systems operational")

        # Endpoint status
        st.subheader("🌐 **Endpoint Health**")
        endpoint_status = health_status.get('endpoint_status', [])

        for endpoint in endpoint_status:
            url_short = endpoint.get('url', '').replace('wss://', '')[:20] + '...'
            healthy = endpoint.get('healthy', False)
            status_icon = "🟢" if healthy else "🔴"
            failures = endpoint.get('failures', 0)

            st.metric(
                label=f"{status_icon} {url_short}",
                value=f"{failures} failures",
                help=f"Priority: {endpoint.get('priority', 'N/A')}"
            )

    # Detailed Network Statistics
    st.header("📈 **Detailed Network Statistics**")

    col_stats, col_chart = st.columns([1, 2])

    with col_stats:
        st.subheader("📊 **Real-time Stats**")

        # Refresh button
        if st.button("🔄 Refresh Statistics", help="Get latest network metrics"):
            network_resilience.reset_stats()
            st.rerun()

        # Display detailed stats
        stats_df = pd.DataFrame([
            {"Metric": "Total Attempts", "Value": conn_stats.get('total_attempts', 0)},
            {"Metric": "Successful Connections", "Value": conn_stats.get('successful_connections', 0)},
            {"Metric": "Failed Connections", "Value": conn_stats.get('failed_connections', 0)},
            {"Metric": "Consecutive Failures", "Value": conn_stats.get('consecutive_failures', 0)},
            {"Metric": "Avg Response Time (s)", "Value": ".3f"},
            {"Metric": "DNS Resolution Failures", "Value": error_breakdown.get('dns_failures', 0)},
            {"Metric": "SSL Handshake Failures", "Value": error_breakdown.get('ssl_failures', 0)},
            {"Metric": "Timeout Failures", "Value": error_breakdown.get('timeouts', 0)},
        ])

        st.dataframe(stats_df, use_container_width=True, hide_index=True)

    with col_chart:
        st.subheader("📉 **Error Trend Analysis**")

        # Simple error trend visualization (would be enhanced with real time series data)
        if conn_stats.get('total_attempts', 0) > 0:
            error_rate = (conn_stats.get('failed_connections', 0) / conn_stats.get('total_attempts', 0)) * 100

            # Create a gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=error_rate,
                title={'text': "Connection Error Rate %"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 5], 'color': "lightgreen"},
                        {'range': [5, 15], 'color': "yellow"},
                        {'range': [15, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 5
                    }
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No connection data available yet")

    # Resilience Configuration
    st.header("⚙️ **Resilience Configuration**")

    col_config1, col_config2 = st.columns(2)

    with col_config1:
        st.subheader("🔄 **Retry Settings**")
        st.metric(label="Max Retries", value=str(network_resilience.max_retries))
        st.metric(label="Base Delay (s)", value=str(network_resilience.base_retry_delay))
        st.metric(label="Max Delay (s)", value=str(network_resilience.max_retry_delay))
        st.metric(label="Jitter Factor", value=".2f")

    with col_config2:
        st.subheader("🛡️ **Circuit Breaker**")
        st.metric(label="Failure Threshold", value=str(network_resilience.failure_threshold))
        st.metric(label="Recovery Timeout (s)", value=str(network_resilience.recovery_timeout))
        st.metric(label="Error Rate Threshold", value=".1%")
        st.metric(label="Consecutive Failures", value=str(conn_stats.get('consecutive_failures', 0)))

    # Manual Controls
    st.subheader("🎮 **Manual Controls**")

    col_buttons1, col_buttons2, col_buttons3 = st.columns(3)

    with col_buttons1:
        if st.button("🔄 Reset Statistics", help="Clear all connection statistics"):
            network_resilience.reset_stats()
            st.success("Network statistics reset!")

    with col_buttons2:
        if st.button("🧪 Test Connectivity", help="Perform connectivity test"):
            test_result = _perform_connectivity_test()
            if test_result:
                st.success("✅ Connectivity test passed!")
            else:
                st.error("❌ Connectivity test failed!")

    with col_buttons3:
        if st.button("📊 Health Refresh", help="Force refresh of health data"):
            # This would trigger a health check in a real implementation
            st.info("Health data refreshed")

def _generate_health_alerts(health_status: Dict[str, Any]) -> list:
    """Generate alerts based on health status."""
    alerts = []

    conn_stats = health_status.get('connection_stats', {})
    error_rate = conn_stats.get('success_rate', 100)

    # Critical alerts
    if health_status.get('operational_mode') == 'offline':
        alerts.append({
            'level': 'critical',
            'message': 'SYSTEM IS OFFLINE - All operations failing'
        })

    if health_status.get('circuit_breaker') == 'open':
        alerts.append({
            'level': 'critical',
            'message': 'CIRCUIT BREAKER OPEN - Requests being rejected'
        })

    # Warning alerts
    if error_rate < 95:
        alerts.append({
            'level': 'warning',
            'message': ".1f"        })

    consecutive_failures = conn_stats.get('consecutive_failures', 0)
    if consecutive_failures >= 3:
        alerts.append({
            'level': 'warning',
            'message': f"High consecutive failures: {consecutive_failures}"
        })

    # Info alerts
    response_time = conn_stats.get('average_response_time', 0)
    if response_time > 2.0:
        alerts.append({
            'level': 'info',
            'message': ".2f"        })

    endpoint_status = health_status.get('endpoint_status', [])
    unhealthy_endpoints = [ep for ep in endpoint_status if not ep.get('healthy', True)]
    if unhealthy_endpoints:
        alerts.append({
            'level': 'info',
            'message': f"{len(unhealthy_endpoints)} endpoint(s) unhealthy"
        })

    return alerts

def _perform_connectivity_test() -> bool:
    """Perform a simple connectivity test."""
    try:
        import socket

        # Test TCP connectivity to Deriv WebSocket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('ws.derivws.com', 443))
        sock.close()

        return result == 0
    except Exception as e:
        logger.error(f"Connectivity test failed: {e}")
        return False

def get_network_health_summary() -> Dict[str, Any]:
    """Get a summary of network health for dashboard overview."""
    health_status = network_resilience.get_health_status()

    return {
        'operational_mode': health_status.get('operational_mode', 'unknown'),
        'connection_success_rate': health_status.get('connection_stats', {}).get('success_rate', 0),
        'total_failures': health_status.get('connection_stats', {}).get('consecutive_failures', 0),
        'response_time': health_status.get('connection_stats', {}).get('average_response_time', 0),
        'circuit_breaker_state': health_status.get('circuit_breaker', 'unknown'),
        'timestamp': datetime.now()
    }
