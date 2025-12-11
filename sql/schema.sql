-- TokemFX Database Schema
-- Professional forex trading system data storage

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- 'long' or 'short'
    size INTEGER NOT NULL,
    entry_price DECIMAL(10,5) NOT NULL,
    exit_price DECIMAL(10,5),
    pnl DECIMAL(10,2),
    commission DECIMAL(8,2) DEFAULT 0,
    entry_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exit_timestamp TIMESTAMPTZ,
    strategy VARCHAR(50),
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'closed', 'cancelled'
    risk_percentage DECIMAL(5,4),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    size INTEGER NOT NULL DEFAULT 0,
    direction VARCHAR(10),
    avg_price DECIMAL(10,5),
    current_price DECIMAL(10,5),
    unrealized_pnl DECIMAL(10,2),
    max_drawdown DECIMAL(8,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol)
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_equity DECIMAL(12,2),
    daily_pnl DECIMAL(10,2),
    drawdown DECIMAL(8,4),
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    win_rate DECIMAL(5,4),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date)
);

CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5,4),
    avg_pnl DECIMAL(8,2),
    total_pnl DECIMAL(10,2),
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(strategy_name, date)
);

CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    granularity VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(10,5) NOT NULL,
    high DECIMAL(10,5) NOT NULL,
    low DECIMAL(10,5) NOT NULL,
    close DECIMAL(10,5) NOT NULL,
    volume BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, granularity, timestamp)
);

CREATE TABLE IF NOT EXISTS risk_limits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    value DECIMAL(10,4) NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_entry_timestamp ON trades(entry_timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_strategy_performance_strategy_date ON strategy_performance(strategy_name, date);

-- Insert default risk limits
INSERT INTO risk_limits (name, value, description) VALUES
    ('max_drawdown', 0.05, 'Maximum portfolio drawdown (5%)'),
    ('max_position_size', 0.02, 'Maximum position size as % of equity'),
    ('max_daily_trades', 10.0, 'Maximum trades per day'),
    ('max_open_positions', 5.0, 'Maximum concurrent open positions')
ON CONFLICT (name) DO NOTHING;
