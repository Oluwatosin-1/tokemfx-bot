#!/usr/bin/env python3
"""
Synthetic Data Generation Utility
=================================
Generate realistic market data for backtesting when live data is unavailable.

This utility provides:
- Bulk synthetic data generation for multiple instruments
- Realistic price movements and volatility patterns
- Quality validation and statistical checks
- CSV export for offline backtesting

Usage:
    python src/generate_synthetic_data.py --instruments R_10 frxEURUSD --granularities D H1 --days 365
"""

import argparse
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any
import numpy as np

# Import synthetic data generator
from src.backtesting.engine import SyntheticDataGenerator

logger = logging.getLogger(__name__)

def main():
    """Main entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic market data for backtesting")
    parser.add_argument('--instruments', nargs='+', default=['R_10', 'frxEURUSD', 'frxBTCUSD'],
                       help='Instruments to generate data for')
    parser.add_argument('--granularities', nargs='+', default=['D', 'H1'],
                       help='Time granularities to generate')
    parser.add_argument('--days', type=int, default=365,
                       help='Number of days of historical data to generate')
    parser.add_argument('--output-dir', type=str, default='data/synthetic',
                       help='Output directory for synthetic data')
    parser.add_argument('--validate-quality', action='store_true', default=True,
                       help='Validate data quality after generation')
    parser.add_argument('--verbose', action='store_true', default=False,
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    logger.info("🧪 Synthetic Data Generation Utility")
    logger.info("=" * 60)

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=args.days)

    logger.info(f"📅 Generating data from {start_date.date()} to {end_date.date()} ({args.days} days)")
    logger.info(f"📊 Instruments: {', '.join(args.instruments)}")
    logger.info(f"⏰ Granularities: {', '.join(args.granularities)}")
    logger.info(f"📁 Output directory: {args.output_dir}")
    logger.info("")

    # Initialize synthetic data generator
    generator = SyntheticDataGenerator()

    # Generate bulk synthetic data
    generated_files = generator.generate_bulk_synthetic_data(
        instruments=args.instruments,
        granularities=args.granularities,
        start_date=start_date,
        end_date=end_date,
        output_dir=args.output_dir
    )

    # Summary
    logger.info("")
    logger.info("🎉 SYNTHETIC DATA GENERATION COMPLETE")
    logger.info("=" * 60)

    total_files = len(generated_files)
    total_instruments = len(args.instruments)
    total_granularities = len(args.granularities)

    logger.info(f"✅ Generated {total_files} data files")
    logger.info(f"📊 Instruments: {total_instruments}")
    logger.info(f"⏰ Granularities: {total_granularities}")
    logger.info(f"📅 Date range: {args.days} days")
    logger.info(f"📁 Output directory: {args.output_dir}")
    logger.info("")

    # Quality validation if requested
    if args.validate_quality and generated_files:
        logger.info("🔍 QUALITY VALIDATION")
        logger.info("-" * 30)

        quality_scores = {}
        for key, filepath in generated_files.items():
            try:
                df = pd.read_csv(filepath, index_col='timestamp', parse_dates=True)
                quality_score = generator.quality_validator.validate_synthetic_data(df, key.split('_')[0])
                quality_scores[key] = quality_score

                status = "✅ Excellent" if quality_score >= 0.9 else \
                        "✅ Good" if quality_score >= 0.7 else \
                        "⚠️ Fair" if quality_score >= 0.5 else "❌ Poor"

                logger.info(f"   {key}: {status} ({quality_score:.2f}) - {len(df)} rows")

            except Exception as e:
                logger.error(f"   {key}: ❌ Validation failed - {e}")

        # Quality summary
        excellent = sum(1 for s in quality_scores.values() if s >= 0.9)
        good = sum(1 for s in quality_scores.values() if 0.7 <= s < 0.9)
        fair = sum(1 for s in quality_scores.values() if 0.5 <= s < 0.7)
        poor = sum(1 for s in quality_scores.values() if s < 0.5)

        logger.info("")
        logger.info("📈 QUALITY SUMMARY:")
        logger.info(f"   Excellent (≥0.9): {excellent}")
        logger.info(f"   Good (0.7-0.9): {good}")
        logger.info(f"   Fair (0.5-0.7): {fair}")
        logger.info(f"   Poor (<0.5): {poor}")

    logger.info("")
    logger.info("💡 USAGE:")
    logger.info("   • Use these files for offline backtesting when API is unavailable")
    logger.info("   • Quality validated synthetic data ensures realistic testing")
    logger.info("   • Files are stored in standard OHLCV CSV format")
    logger.info("   • Compatible with backtesting engine and data handlers")

    if generated_files:
        logger.info("")
        logger.info("📋 GENERATED FILES:")
        for key, filepath in generated_files.items():
            logger.info(f"   {key}: {filepath}")

if __name__ == "__main__":
    main()
