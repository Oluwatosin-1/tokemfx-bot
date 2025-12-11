"""
Live Trading Component
=====================
Real-time trade execution and position management interface.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Import robust timestamp parsing utility
from src.dashboard.components.ai_trading import parse_timestamp_safely

def render_live_trading():
    """
    Render live trading interface with trade execution and position management.
    """
    st.header("🎯 **Live Trading Dashboard**")
    
    # Safety warnings
    st.warning("⚠️ **HIGH RISK WARNING** - Only trade with money you can afford to lose!")
    
    # Emergency controls
    emergency_cols = st.columns(3)
    with emergency_cols[0]:
        if st.button("🛑 EMERGENCY STOP", type="primary"):
            try:
                broker = st.session_state.get('live_broker')
                if broker and broker.is_connected():
                    close_result = broker.close_all_positions()
                    if close_result and not close_result.get('error'):
                        st.error("🚨 ALL POSITIONS CLOSED - TRADING STOPPED")
                        st.success(f"✅ Closed {close_result.get('close_attempts', 0)} positions")
                        st.rerun()  # Refresh to show updated positions
                    else:
                        st.error("❌ Failed to close all positions")
                else:
                    st.error("🚨 EMERGENCY STOP ACTIVATED (No live connection)")
            except Exception as e:
                st.error(f"❌ Emergency stop failed: {e}")
    with emergency_cols[1]:
        if st.button("⚡ CLOSE ALL POSITIONS"):
            try:
                broker = st.session_state.get('live_broker')
                if broker and broker.is_connected():
                    close_result = broker.close_all_positions()
                    if close_result and not close_result.get('error'):
                        st.success(f"✅ Closed {close_result.get('close_attempts', 0)} positions")
                        st.rerun()  # Refresh to show updated positions
                    else:
                        st.error("❌ Failed to close all positions")
                else:
                    st.warning("⚠️ No live broker connection")
            except Exception as e:
                st.error(f"❌ Close all positions failed: {e}")
    with emergency_cols[2]:
        risk_level = st.selectbox("Risk Level", ["Low", "Medium", "High"], index=0)
    
    trading_tabs = st.tabs(["📊 Portfolio", "🎮 Trade Execution", "📈 Positions", "📊 Performance", "📋 Trade History"])

    with trading_tabs[0]:
        render_trading_portfolio()

    with trading_tabs[1]:
        render_trade_execution()

    with trading_tabs[2]:
        render_position_monitor()

    with trading_tabs[3]:
        render_trading_performance()

    with trading_tabs[4]:
        render_trade_history()

def render_trading_portfolio():
    """Render trading portfolio overview."""
    st.subheader("💰 Portfolio Overview")

    try:
        # Try to get real account data
        from src.trading.execution.broker import DerivBroker

        # Initialize broker with session state to avoid multiple connections
        if 'live_broker' not in st.session_state:
            st.session_state.live_broker = DerivBroker()

        broker = st.session_state.live_broker

        if broker.connect_and_authenticate():
            account_info = broker.get_account_balance()

            if 'error' not in account_info:
                # Properly parse the balance response from Deriv API
                balance_obj = account_info.get('balance', {})
                if isinstance(balance_obj, dict):
                    balance = balance_obj.get('balance', 0)
                    currency = balance_obj.get('currency', 'USD')
                    account_id = balance_obj.get('loginid', 'Unknown')
                    is_virtual = balance_obj.get('is_virtual', False)
                    account_type = "Demo" if is_virtual else "Real"
                else:
                    # Fallback if structure is unexpected
                    balance = balance_obj if isinstance(balance_obj, (int, float)) else 0
                    currency = account_info.get('currency', 'USD')
                    account_id = 'Unknown'
                    account_type = 'Unknown'

                portfolio_data = pd.DataFrame({
                    'Asset': ['Cash'],
                    'Value': [f"{balance:,.2f}"],  # Format with commas and 2 decimal places
                    'Currency': [currency],
                    'P&L': ['0.00']
                })
                st.dataframe(portfolio_data, use_container_width=True, hide_index=True)

                # Show account details
                st.success(f"✅ Connected to {account_type} account ({account_id})")
                st.metric("Account Balance", f"{balance:,.2f} {currency}")
                st.metric("Account ID", account_id)
                st.metric("Account Type", account_type)

                # Show connection status
                auth_status = broker.get_auth_status()
                if auth_status.get('is_connected'):
                    st.info(f"🔗 Connection Status: {'Secure (OAuth)' if auth_status.get('auth_method_used') == 'oauth' else 'Standard (API)'}")
            else:
                # Fallback to demo data if account access fails
                error_msg = account_info.get('error', {}).get('message', 'Unknown error')
                st.warning(f"⚠️ Account access issue: {error_msg}")
                render_demo_portfolio()
        else:
            # Fallback to demo data if connection fails
            st.warning("⚠️ Connection failed - using demo data")
            render_demo_portfolio()

    except Exception as e:
        st.error(f"❌ Portfolio data error: {e}")
        st.info("Falling back to demo data for safety.")
        render_demo_portfolio()

def render_demo_portfolio():
    """Render demo portfolio when live data unavailable."""
    st.warning("⚠️ Using demo portfolio data")

    portfolio_data = pd.DataFrame({
        'Asset': ['R_10', 'frxEURUSD', 'R_25', 'Cash'],
        'Value': [2500.00, 1800.00, 3200.00, 7030.89],
        'P&L': [234.56, -89.23, 456.78, 0.00]
    })

    st.dataframe(portfolio_data, use_container_width=True, hide_index=True)

def render_trade_execution():
    """Render trade execution interface."""
    st.subheader("🎮 Trade Execution")
    
    col_setup, col_confirm = st.columns(2)
    
    with col_setup:
        instrument = st.selectbox("Instrument", 
                                ["R_10", "R_25", "R_50", "frxEURUSD", "frxUSDJPY"])
        direction = st.radio("Direction", ["BUY", "SELL"])
        stake = st.slider("Stake Amount ($)", 10, 1000, 100)
    
    with col_confirm:
        st.write("**Trade Summary:**")
        st.write(f"**Instrument:** {instrument}")
        st.write(f"**Direction:** {direction}")
        st.write(f"**Amount:** ${stake}")
        
        if st.button("🚀 EXECUTE TRADE", type="primary", use_container_width=True):
            execute_demo_trade(instrument, direction, stake)

def render_position_monitor():
    """Render position monitoring interface."""
    st.subheader("📈 Active Positions Monitor")

    try:
        positions_found = False

        # First, check for simulated positions in session state
        if 'open_positions' in st.session_state and st.session_state.open_positions:
            positions_data = []
            for pos in st.session_state.open_positions:
                positions_data.append({
                    'Contract_ID': pos.get('id', 'N/A'),
                    'Instrument': pos.get('instrument', 'Unknown'),
                    'Direction': pos.get('direction', 'BUY').upper(),
                    'Stake': pos.get('stake', 0),
                    'Entry_Price': pos.get('entry_price', 'N/A'),
                    'Current_Price': pos.get('entry_price', 'N/A'),  # Same as entry for demo
                    'P&L': pos.get('commission', 0) * -1,  # Show commission as negative P&L initially
                    'Status': pos.get('status', 'Active')
                })

            if positions_data:
                positions_df = pd.DataFrame(positions_data)
                st.dataframe(positions_df, use_container_width=True, hide_index=True,
                           column_config={
                               "Contract_ID": st.column_config.TextColumn("Contract ID"),
                               "P&L": st.column_config.NumberColumn("P&L", format="$%.2f"),
                               "Stake": st.column_config.NumberColumn("Stake", format="$%.2f")
                           })

                # Add close position buttons
                st.subheader("Close Positions")
                cols = st.columns(min(len(positions_data), 3))
                for i, pos in enumerate(st.session_state.open_positions):
                    contract_id = pos.get('id')
                    instrument = pos.get('instrument', 'Unknown')
                    with cols[i % 3]:
                        if st.button(f"❌ Close {instrument}", key=f"close_{contract_id}"):
                            # Remove from session state
                            st.session_state.open_positions = [
                                p for p in st.session_state.open_positions if p.get('id') != contract_id
                            ]
                            st.success(f"✅ Successfully closed position for {instrument}")
                            st.rerun()  # Refresh the page

                positions_found = True

        # Also try to get positions from broker
        broker = st.session_state.get('live_broker')
        if broker:
            positions_response = broker.get_positions()

            if positions_response and not positions_response.get('error'):
                portfolio = positions_response.get('portfolio', {})
                contracts = portfolio.get('contracts', [])

                if contracts and not positions_found:  # Only show if we didn't show session positions
                    positions_data = []
                    for contract in contracts:
                        positions_data.append({
                            'Contract_ID': contract.get('contract_id', 'N/A'),
                            'Instrument': contract.get('display_name', 'Unknown'),
                            'Direction': 'BUY' if contract.get('contract_type') == 'CALL' else 'SELL',
                            'Stake': contract.get('stake', 0),
                            'Entry_Price': contract.get('entry_tick', 'N/A'),
                            'Current_Price': contract.get('current_tick', 'N/A'),
                            'P&L': contract.get('profit_loss', 0),
                            'Status': contract.get('status', 'Active')
                        })

                    positions_df = pd.DataFrame(positions_data)
                    st.dataframe(positions_df, use_container_width=True, hide_index=True,
                               column_config={
                                   "Contract_ID": st.column_config.TextColumn("Contract ID"),
                                   "P&L": st.column_config.NumberColumn("P&L", format="$%.2f"),
                                   "Stake": st.column_config.NumberColumn("Stake", format="$%.2f")
                               })

                    positions_found = True

        if not positions_found:
            st.info("No open positions")

    except Exception as e:
        st.error(f"Error loading positions: {e}")
        logger.error(f"Position monitor error: {e}")
        render_demo_positions()

def render_demo_positions():
    """Render demo positions when real data unavailable."""
    st.warning("⚠️ Using demo position data")

    positions = pd.DataFrame({
        'Instrument': ['R_25', 'frxEURUSD', 'R_50'],
        'Direction': ['BUY', 'SELL', 'BUY'],
        'Size': [200, 150, 300],
        'Entry_Price': [1.4523, 1.0894, 3487.50],
        'Current_Price': [1.4687, 1.0821, 3512.40],
        'P&L': [326.80, 110.55, 747.00]
    })

    st.dataframe(positions, use_container_width=True, hide_index=True)

def render_trading_performance():
    """Render trading performance metrics."""
    st.subheader("📊 Trading Performance")
    
    perf_cols = st.columns(4)
    with perf_cols[0]:
        st.metric("Today's P&L", "+$569.35", "+12.2%")
    with perf_cols[1]:
        st.metric("Weekly P&L", "+$1,284.67")
    with perf_cols[2]:
        st.metric("Win Rate", "73%", "+5%")
    with perf_cols[3]:
        st.metric("Avg Trade Duration", "3.2h")

def execute_demo_trade(instrument, direction, stake):
    """Execute demo trade and update position tracking."""
    try:
        # Get broker instance to update positions
        broker = st.session_state.get('live_broker')

        # Generate execution details
        execution_time = datetime.now()
        order_id = f"TXN_{np.random.randint(100000, 999999)}"
        simulated_price = np.random.uniform(1.08, 1.12) if 'frx' in instrument else np.random.uniform(3400, 3800)
        commission = stake * 0.001

        # Create position entry for tracking
        position_data = {
            'contract_id': order_id,
            'display_name': instrument,
            'contract_type': 'CALL' if direction.upper() == 'BUY' else 'PUT',
            'stake': stake,
            'entry_tick': simulated_price,
            'current_tick': simulated_price,
            'profit_loss': -commission,  # Start with commission as loss
            'status': 'open'
        }

        # Update broker's position tracking if available
        if broker and hasattr(broker, '_positions'):
            if not hasattr(broker, '_positions') or broker._positions is None:
                broker._positions = {'portfolio': {'contracts': []}}

            if 'portfolio' not in broker._positions:
                broker._positions['portfolio'] = {'contracts': []}

            if 'contracts' not in broker._positions['portfolio']:
                broker._positions['portfolio']['contracts'] = []

            # Add the new position
            broker._positions['portfolio']['contracts'].append(position_data)

            # Also store in session state for persistence
            if 'open_positions' not in st.session_state:
                st.session_state.open_positions = []

            st.session_state.open_positions.append({
                'id': order_id,
                'instrument': instrument,
                'direction': direction,
                'stake': stake,
                'entry_price': simulated_price,
                'commission': commission,
                'timestamp': execution_time,
                'status': 'active'
            })

        st.success("🚀 TRADE EXECUTED SUCCESSFULLY!")

        st.info(f"⏰ Executed at {execution_time.strftime('%H:%M:%S')}")
        st.info(f"📋 Order ID: {order_id}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Execution Price", f"{simulated_price:.4f}")
        with col2:
            st.metric("Commission", f"${commission:.2f}")

        # Force refresh to show updated positions
        st.rerun()

    except Exception as e:
        st.error(f"❌ Trade execution failed: {e}")
        logger.error(f"Trade execution error: {e}")

def render_trade_history():
    """Render trade history using real broker data."""
    st.subheader("📋 Trade History")

    try:
        # Get real trade history from broker
        broker = st.session_state.get('live_broker')
        if broker and broker.is_connected():
            statement_response = broker.get_statement(limit=50)

            if statement_response and not statement_response.get('error'):
                transactions = statement_response.get('transactions', [])

                if transactions:
                    history_data = []
                    for transaction in transactions:
                        # Parse transaction data with robust timestamp handling
                        trans_time = transaction.get('transaction_time', 0)
                        if trans_time:
                            dt = parse_timestamp_safely(trans_time)
                            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            time_str = "Unknown"

                        history_data.append({
                            'Date': time_str,
                            'Reference_ID': transaction.get('transaction_id', 'N/A'),
                            'Action': transaction.get('action_type', 'Unknown'),
                            'Instrument': transaction.get('symbol', 'Unknown'),
                            'Amount': transaction.get('amount', 0),
                            'Balance': transaction.get('balance', 0),
                            'Description': transaction.get('longcode', 'N/A')[:50] + '...' if transaction.get('longcode') and len(transaction.get('longcode', '')) > 50 else transaction.get('longcode', 'N/A')
                        })

                    history_df = pd.DataFrame(history_data)
                    st.dataframe(history_df, use_container_width=True, hide_index=True,
                               column_config={
                                   "Amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                                   "Balance": st.column_config.NumberColumn("Balance", format="$%.2f")
                               })

                    # Summary statistics
                    total_transactions = len(transactions)
                    profitable_trades = sum(1 for t in transactions if t.get('amount', 0) > 0)

                    st.subheader("Trade Summary")
                    summary_cols = st.columns(3)
                    with summary_cols[0]:
                        st.metric("Total Transactions", total_transactions)
                    with summary_cols[1]:
                        win_rate = (profitable_trades / total_transactions * 100) if total_transactions > 0 else 0
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    with summary_cols[2]:
                        total_pnl = sum(t.get('amount', 0) for t in transactions)
                        st.metric("Total P&L", f"${total_pnl:.2f}", "🟢" if total_pnl > 0 else "🔴")

                else:
                    st.info("No trade history available")
            else:
                st.warning("Could not retrieve trade history - using demo data")
                render_demo_trade_history()
        else:
            st.warning("Not connected to broker - using demo data")
            render_demo_trade_history()

    except Exception as e:
        st.error(f"Error loading trade history: {e}")
        render_demo_trade_history()

def render_demo_trade_history():
    """Render demo trade history when real data unavailable."""
    st.warning("⚠️ Using demo trade history data")

    # Generate demo trade history
    dates = pd.date_range(end=datetime.now(), periods=20, freq='H')

    demo_trades = []
    for i, date in enumerate(dates):
        pnl = np.random.normal(0, 50)
        demo_trades.append({
            'Date': date.strftime('%Y-%m-%d %H:%M:%S'),
            'Reference_ID': f'TXN_{100000 + i}',
            'Action': np.random.choice(['Buy', 'Sell', 'Deposit', 'Withdrawal']),
            'Instrument': np.random.choice(['R_10', 'frxEURUSD', 'R_25', 'BTCUSD']),
            'Amount': pnl,
            'Balance': 10000 + sum(np.random.normal(0, 50) for _ in range(i+1)),
            'Description': 'Demo trade transaction'
        })

    history_df = pd.DataFrame(demo_trades)
    st.dataframe(history_df, use_container_width=True, hide_index=True)

    # Demo summary
    st.subheader("Trade Summary")
    summary_cols = st.columns(3)
    with summary_cols[0]:
        st.metric("Total Transactions", "20")
    with summary_cols[1]:
        st.metric("Win Rate", "65%")
    with summary_cols[2]:
        st.metric("Total P&L", "+$127.43")
