# TokemFX Advanced Forex Trading System
FROM python:3.11-slim

# System Dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wait4ports \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy SQL schema
COPY sql/schema.sql ./sql/

# Copy configuration directory
COPY config/ ./config/

# Copy application code
COPY src/ ./src/

# Copy app files
COPY app.py run.sh ./

# Create non-root user
RUN useradd -m trader && chown -R trader:trader /app
USER trader

# Create directories
RUN mkdir -p cache logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/metrics || exit 1

# Default command
CMD ["python3", "-m", "tokemfx.main", "--instrument", "R_10", "--strategy", "MA"]
