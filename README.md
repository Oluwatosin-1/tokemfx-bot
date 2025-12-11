# tokemFX Enterprise Trading Platform

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A battle-ready Python forex trading bot with full backtesting, live execution, AI-powered strategies, and enterprise-grade monitoring.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Oluwatosin-1/tokemfx-bot.git
cd tokemfx-bot

# Install dependencies
pip install -r requirements.txt

# Launch the enterprise dashboard
streamlit run app.py

# Or launch with Docker
docker-compose up --build
```

## 📚 Documentation

For comprehensive documentation, see the [`docs/`](./docs/) directory:

- **[Getting Started](docs/README.md)** - Full project overview and installation guide
- **[Enterprise Architecture](docs/architecture/ARCHITECTURE.md)** - Complete system design and modules
- **[Deriv API Setup](docs/configuration/DERIV_OAUTH_SETUP.md)** - Authentication and configuration guide

## 🎯 Key Features

- **🤖 AI Trading Pipeline** with continuous learning and pattern recognition
- **📊 Enterprise Dashboards** with professional monitoring and analytics
- **💼 Industrial Backtesting** with statistical validation and optimization
- **🛡️ Advanced Risk Management** with multi-layer controls and emergency systems
- **📈 Executive Monitoring** with Grafana integration and performance metrics
- **🏗️ Scalable Architecture** designed for institutional trading environments

## 🚀 Production Templates

Launch the dashboard with different user roles:

```bash
# Administrator access (all features)
streamlit run app.py -- --template=admin

# Professional trader focus
streamlit run app.py -- --template=prop_trader

# Risk analyst monitoring
streamlit run app.py -- --template=risk_analyst

# Debug and development
streamlit run app.py -- --template=developer
```

## 📜 Project Structure

```
📂 tokemfx-bot
├── app.py                       # 🖥️ Main Streamlit application
├── docs/                        # 📚 Complete documentation
├── src/                         # 🏗️ Enterprise modular architecture
│   ├── ai_trading_system/      # 🤖 AI/ML trading pipeline
│   ├── backtesting/            # 🎲 Industrial backtesting engine
│   ├── dashboard/              # 🖥️ Unified interface system
│   ├── monitoring/             # 👁️ Enterprise observability
│   ├── trading/                # 💼 Core trading execution
│   ├── strategy/               # 🎯 Strategy architecture
│   ├── charts/                 # 📊 Visualization framework
│   └── config/                 # ⚙️ Configuration management
├── config/                      # ⚙️ External configurations
├── data/                        # 💾 Application data storage
└── logs/                        # 📝 Centralized logging
```

## 📈 Enterprise Capabilities

Designed for institutional standards with Goldman Sachs-level architecture:

- **AI-Enhanced Trading** with continuous model optimization
- **Executive Intelligence** with business KPI dashboards
- **Industrial Backtesting** with statistical significance validation
- **Production Monitoring** with 7 professional Grafana dashboards
- **Scalable Architecture** supporting unlimited expansions

## 📜 License

MIT License - see LICENSE file for details.

---

**Built for reliability, transparency, and scalability across all trading environments.**

*For detailed usage instructions and comprehensive documentation, visit the [`docs/`](./docs/) directory.*
