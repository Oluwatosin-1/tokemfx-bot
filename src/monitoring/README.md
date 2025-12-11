# Monitoring Infrastructure

Complete observability stack for enterprise trading environments. Provides comprehensive monitoring, auditing, and control capabilities.

## Components

### audit/
- **comprehensive_system_audit.py**: Security auditing and compliance checks
- **final_audit.py**: Final system validation before deployment

### controls/
- **dashboard_control_system.py**: Dashboard control and management interfaces

### emergency/
- **emergency_controls.py**: Emergency shutdown and crisis management

### production/
- **production_monitoring_system.py**: Production environment monitoring

### system/
- **system_audit.py**: System health and performance audits

### dashboards/
- **provisioning/**: Grafana dashboard configurations
  - `backtesting_dashboards.json`: Backtesting analytics
  - `strategy_performance.json`: Strategy optimization
  - `ai_trading_intelligence.json`: AI model health
  - `live_trading_monitor.json`: Real-time trading P&L
  - `risk_management_center.json`: Risk exposure tracking
  - `system_infrastructure.json`: System performance
  - `comprehensive_overview.json`: Executive KPIs

## Dashboard Suite

7 comprehensive Grafana dashboards covering:
- **Backtesting Analytics**: Strategy performance, walk-forward analysis, optimization convergence
- **Strategy Performance**: Comparison matrix, risk-return analysis, monthly heatmaps
- **AI Trading Intelligence**: Confidence gauges, model accuracy, drift detection
- **Live Trading Monitor**: Real-time P&L, position monitoring, execution speeds
- **Risk Management Center**: VaR calculations, position limits, correlation tracking
- **System Infrastructure**: API latency, memory/CPU usage, error rates
- **Executive Overview**: Business KPIs, system health, portfolio performance

## Integration

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboard management
- **Streamlit**: Control interfaces and user interactions
- **PostgreSQL**: Audit trail and historical data storage

## Usage

```python
from src.monitoring import (
    comprehensive_system_audit,
    dashboard_controller,
    emergency_shutdown
)

# Run comprehensive system audit
results = comprehensive_system_audit()
print(f"Audit complete: {results['passed']}/{results['total']} checks passed")

# Emergency halt all trading
emergency_shutdown(reason="Critical error detected")
