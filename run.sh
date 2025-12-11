#!/bin/bash

# TokemFX Enterprise Trading System - Advanced Run Script
set -e

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Default values
INSTRUMENT="R_10"
STRATEGY="MA"
ENVIRONMENT="development"

# Authentication and environment detection
check_authentication() {
    echo -e "${CYAN}🔐 Checking authentication setup...${NC}"

    # Load environment variables from .env file safely
    if [ -f ".env" ]; then
        # Export valid environment variables (skip comments and malformed lines)
        while IFS='=' read -r key value; do
            # Skip lines that start with # or don't have a value
            [[ $key =~ ^# ]] && continue
            [[ -z "$key" ]] && continue
            # Remove inline comments and trim whitespace
            value=$(echo "$value" | sed 's/#.*//' | xargs)
            # Export if key and value are valid
            if [[ -n "$key" && -n "$value" ]]; then
                export "$key=$value"
            fi
        done < .env
        echo -e "${GREEN}✓ Environment variables loaded safely${NC}"
    else
        echo -e "${RED}❌ .env file not found!${NC}"
        return 1
    fi

    # Check API token
    if [ -z "$DERIV_API_TOKEN" ]; then
        echo -e "${RED}❌ DERIV_API_TOKEN not configured in .env${NC}"
        return 1
    else
        echo -e "${GREEN}✓ API token configured${NC}"
    fi

    # Check OAuth token for production
    if [ -z "$DERIV_OAUTH_TOKEN" ]; then
        echo -e "${YELLOW}⚠️  No OAuth token - using API mode (limited functionality)${NC}"
        export AUTH_MODE="api"
        export BALANCE_ACCESS="limited"
    else
        echo -e "${GREEN}✓ OAuth token configured - full balance access${NC}"
        export AUTH_MODE="oauth"
        export BALANCE_ACCESS="full"
    fi

    # Check if we're in production environment
    if [ "$ENVIRONMENT" = "production" ]; then
        if ! command -v ngrok &> /dev/null; then
            echo -e "${RED}❌ ngrok required for production but not installed${NC}"
            return 1
        fi
        # Check ngrok authentication
        if ! ngrok config check &> /dev/null; then
            echo -e "${YELLOW}⚠️  ngrok not authenticated. Please run: ngrok config add-authtoken YOUR_TOKEN${NC}"
            return 1
        else
            echo -e "${GREEN}✓ ngrok authenticated${NC}"
        fi
    fi

    return 0
}

# Check if running in virtual environment or activate it
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✓ Virtual environment detected: $VIRTUAL_ENV${NC}"
else
    # Check for common virtual environment locations
    if [[ -f ".venv/bin/activate" ]]; then
        echo -e "${CYAN}🔧 Activating virtual environment: .venv/bin/activate${NC}"
        source .venv/bin/activate
        if [[ "$VIRTUAL_ENV" != "" ]]; then
            echo -e "${GREEN}✅ Virtual environment activated${NC}"
        else
            echo -e "${YELLOW}⚠️  Failed to activate .venv${NC}"
        fi
    elif [[ -f "venv/bin/activate" ]]; then
        echo -e "${CYAN}🔧 Activating virtual environment: venv/bin/activate${NC}"
        source venv/bin/activate
        if [[ "$VIRTUAL_ENV" != "" ]]; then
            echo -e "${GREEN}✅ Virtual environment activated${NC}"
        else
            echo -e "${YELLOW}⚠️  Failed to activate venv${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No virtual environment detected. Some commands may fail.${NC}"
        echo -e "${YELLOW}💡 Consider creating a virtual environment with: python -m venv .venv${NC}"
    fi
fi

# Default values
INSTRUMENT="R_10"
STRATEGY="MA"

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_menu() {
    echo
    echo -e "${CYAN}🚀 TokemFX Enterprise Trading System${NC}"
    echo "=========================================="
    echo
    echo -e "${GREEN}Environment:${NC} $ENVIRONMENT"
    echo -e "${GREEN}Authentication:${NC} $AUTH_MODE mode (${BALANCE_ACCESS} balance access)"
    echo -e "${GREEN}Current instrument:${NC} $INSTRUMENT"
    echo -e "${GREEN}Current strategy:${NC} $STRATEGY"
    echo
    echo -e "${MAGENTA}Select an option:${NC}"
    echo "1) 🎛️  Enterprise Trading Dashboard (Streamlit)"
    echo "2) 📊 Backtesting UI (Legacy)"
    echo "3) 🤖 AI Health Monitor"
    echo "4) 🔬 System Audit"
    echo "5) 📊 Production Monitor"
    echo "6) ▶️  Production Mode (with OAuth/ngrok)"
    echo "7) 🔧 Run Tests"
    echo "8) 🐳 Docker Deploy"
    echo "9) ⚙️  Configuration"
    echo "10) Change Instrument"
    echo "11) Change Strategy"
    echo "12) 🔐 Re-authenticate OAuth"
    echo "13) 📖 Help"
    echo "14) Exit"
    echo
}

run_enterprise_dashboard() {
    echo -e "${GREEN}🚀 Launching TokemFX Enterprise Dashboard...${NC}"
    echo -e "${CYAN}This opens the full professional trading platform:${NC}"
    echo "   🚀 Enterprise-grade trading dashboard"
    echo "   📊 Professional analytics and monitoring"
    echo "   🤖 AI-powered trading features"
    echo "   🔍 Advanced backtesting capabilities"
    echo "   ⚡ Strategy optimization with real engines"
    echo "   🎯 Live trading execution"
    echo "   🧠 AI trading dashboard with trade monitoring"
    echo
    echo -e "${CYAN}Features:${NC}"
    echo "   ✅ No initialization conflicts resolved"
    echo "   ✅ All components load with real data integration"
    echo "   ✅ Strategy optimizer fully functional"
    echo "   ✅ AI trading dashboard with trade monitoring"
    echo "   ✅ Enterprise security and performance"
    echo "   ✅ Professional trading interface"
    echo "   ✅ Complete routing and navigation system"
    echo
    PYTHONPATH="${PYTHONPATH}:$(pwd)/src" python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
}

run_backtest() {
    echo -e "${GREEN}Starting backtesting UI...${NC}"
    python3 -m streamlit run app.py --server.headless true --server.port 8501
}

run_ai_health() {
    echo -e "${GREEN}🤖 Starting Enterprise Dashboard (AI Health tab)${NC}"
    echo -e "${CYAN}Launch the main dashboard, then switch to 'AI Trading' tab for AI Health features${NC}"
    run_enterprise_dashboard
}

run_system_audit() {
    echo -e "${GREEN}🔬 Running Comprehensive System Audit...${NC}"
    python3 final_system_audit.py
}

run_production_monitor() {
    echo -e "${GREEN}📊 Starting Enterprise Dashboard (Production Monitor tab)${NC}"
    echo -e "${CYAN}Launch the main dashboard, then switch to 'Production Monitor' tab${NC}"
    run_enterprise_dashboard
}

run_production_mode() {
    echo -e "${YELLOW}▶️  Starting PRODUCTION MODE with OAuth...${NC}"
    echo -e "${RED}⚠️  PRODUCTION WARNING:${NC}"
    echo "   • This starts ngrok tunnel for live server"
    echo "   • Full balance access enabled"
    echo "   • Live trading capabilities activated"
    echo
    read -p "Are you sure you want to start production mode? (yes/no): " confirm

    if [[ $confirm == "yes" ]]; then
        ENVIRONMENT="production"

        if ! check_authentication; then
            echo -e "${RED}❌ Authentication check failed. Cannot start production mode.${NC}"
            return 1
        fi

        echo -e "${GREEN}🏭 Starting production environment...${NC}"
        echo -e "${CYAN}Step 1: Starting ngrok tunnel (port 8080)${NC}"
        # Start ngrok in background
        ngrok http 8080 &
        NGROK_PID=$!
        echo "ngrok started (PID: $NGROK_PID)"

        # Wait for ngrok to initialize and get URL
        sleep 3
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o '[^"]*$')

        if [ -z "$NGROK_URL" ]; then
            echo -e "${RED}❌ Failed to get ngrok URL${NC}"
            kill $NGROK_PID 2>/dev/null
            return 1
        fi

        echo -e "${GREEN}✓ ngrok URL: ${NGROK_URL}${NC}"

        echo -e "${CYAN}Step 2: Starting Enterprise Dashboard in production mode${NC}"
        export PRODUCTION_URL="$NGROK_URL"
        python3 -m streamlit run app.py --server.port 8080 --server.address 0.0.0.0

        # Cleanup ngrok when dashboard exits
        kill $NGROK_PID 2>/dev/null
        echo -e "${GREEN}🏭 Production mode shutdown${NC}"

    else
        echo "Production mode cancelled."
    fi
}

run_paper() {
    echo -e "${GREEN}Starting paper trading with $STRATEGY strategy on $INSTRUMENT${NC}"
    python3 -m tokemfx.main --instrument "$INSTRUMENT" --strategy "$STRATEGY"
}

run_live() {
    echo -e "${YELLOW}Starting LIVE trading with $STRATEGY strategy on $INSTRUMENT${NC}"
    echo -e "${YELLOW}⚠️  WARNING: This will use real money! ⚠️${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [[ $confirm == "yes" ]]; then
        python3 -m tokemfx.main --instrument "$INSTRUMENT" --strategy "$STRATEGY" --live
    else
        echo "Operation cancelled."
    fi
}

run_oauth_reauth() {
    echo -e "${CYAN}🔐 Re-authenticating OAuth Token...${NC}"

    if ! check_authentication; then
        echo -e "${RED}❌ Basic authentication check failed${NC}"
        return 1
    fi

    # Start ngrok for OAuth if in development
    if [ "$ENVIRONMENT" = "development" ]; then
        echo "Starting temporary ngrok for OAuth setup..."
        ngrok http 8080 &
        NGROK_PID=$!
        sleep 3
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o '[^"]*$')

        if [ -n "$NGROK_URL" ]; then
            echo -e "${GREEN}✓ ngrok URL for OAuth: ${NGROK_URL}${NC}"
            export OAUTH_CALLBACK_URL="${NGROK_URL}/oauth/callback"
        fi
    fi

    echo "Running OAuth setup..."
    python3 src/oauth_setup.py

    # Save any new OAuth tokens if obtained
    if [ -f ".oauth_tokens" ]; then
        echo -e "${GREEN}✓ New OAuth tokens detected and available${NC}"
        # You could add code here to update the .env file from .oauth_tokens
    fi

    # Cleanup ngrok if started
    if [ -n "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null
    fi

    echo -e "${GREEN}✓ OAuth re-authentication complete${NC}"
}

run_tests() {
    echo -e "${GREEN}Running unit tests${NC}"
    PYTHONPATH="${PYTHONPATH}:src" pytest src/tests/ --maxfail=1 -q
}

run_docker() {
    echo -e "${GREEN}Starting with Docker Compose${NC}"
    if command -v docker-compose &> /dev/null; then
        docker-compose up --build
    else
        docker compose up --build
    fi
}

change_instrument() {
    local instruments=("R_10" "R_25" "R_50" "R_75" "R_100" "frxEURUSD" "frxUSDJPY" "frxGBPUSD" "frxEURCAD")
    echo
    echo "Available instruments:"
    select new_inst in "${instruments[@]}"; do
        if [[ -n $new_inst ]]; then
            INSTRUMENT=$new_inst
            echo -e "${GREEN}Instrument changed to: $INSTRUMENT${NC}"
            break
        else
            echo "Invalid choice. Please select a number from 1-${#instruments[@]}"
        fi
    done
}

change_strategy() {
    local strategies=("MA (Moving Average)" "RSI" "BB (Bollinger Bands)" "ATR" "EMA" "ST (SuperTrend)" "MACD")
    echo
    echo "Available strategies:"
    select choice in "${strategies[@]}"; do
        case $choice in
            "MA (Moving Average)")
                STRATEGY="MA"
                break
                ;;
            "RSI")
                STRATEGY="RSI"
                ;;
            "BB (Bollinger Bands)")
                STRATEGY="BB"
                ;;
            "ATR")
                STRATEGY="ATR"
                ;;
            "EMA")
                STRATEGY="EMA"
                ;;
            "ST (SuperTrend)")
                STRATEGY="ST"
                ;;
            "MACD")
                STRATEGY="MACD"
                ;;
            *)
                echo "Invalid choice. Please select 1-${#strategies[@]}"
                continue
                ;;
        esac
        echo -e "${GREEN}Strategy changed to: $STRATEGY${NC}"
        break
    done
}

show_help() {
    echo "TokemFX Interactive Launcher"
    echo ""
    echo "This script helps you run the TokemFX trading bot with interactive menus."
    echo "Use the menu options to:"
    echo "  - Select trading mode (backtest/paper/live)"
    echo "  - Choose trading instrument (volatile CFD indices or major pairs)"
    echo "  - Pick trading strategy (multiple technical indicators)"
    echo "  - Run tests or use Docker deployment"
    echo ""
    echo "WARNING: Live trading uses real Deriv account funds!"
    echo "Ensure your .env file contains valid DERIV_API_TOKEN and DERIV_ACCOUNT_ID"
}

main_menu() {
    # Run initial authentication check
    check_authentication

    while true; do
        print_menu
        read -p "Enter choice (1-14): " choice
        echo

        case $choice in
            1) run_enterprise_dashboard ;;
            2) run_backtest ;;
            3) run_ai_health ;;
            4) run_system_audit ;;
            5) run_production_monitor ;;
            6) run_production_mode ;;
            7) run_tests ;;
            8) run_docker ;;
            9) echo -e "${CYAN}⚙️  Configuration: Check .env file for settings${NC}" ;;
            10) change_instrument ;;
            11) change_strategy ;;
            12) run_oauth_reauth ;;
            13) show_help ;;
            14) echo "Goodbye!"; exit 0 ;;
            *) echo "Invalid choice. Please select 1-14." ;;
        esac

        echo
        read -p "Press Enter to continue..."
    done
}

# Start the interactive menu
main_menu




i know we can t be perfect but if peradventure we still have the app using monolithics apporahc to display the dashboard can we converrt this gracefully to ensur the dashboard for the backtest infastructure ,dashboard, backttesting, strategy optimiser, live trading, performance monitor, ai helth monitor, system audit, production monitor and the alert dashboard are all correctly linked to use the modules created for them and fetcht the real data from each of them and display the accurate data from the engine and system not just placeholders and i think i cant still see the ai traging dahsboard to monitor the trade taken by the ai the strategy it use and the ability to see the trade result
and also i think the dashboard should have the well enhnaced amnd full details of the route to the different function and advanced details to be aware of fo the system navigagion correctly fix any loop holes we might be having
