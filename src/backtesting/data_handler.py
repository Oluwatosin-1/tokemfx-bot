"""
TokemFX Backtesting Data Handler
================================
Data preparation, validation, and preprocessing for backtesting operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DataValidationReport:
    """Data validation results"""
    is_valid: bool
    total_rows: int
    missing_data_pct: float
    gap_analysis: Dict[str, Any]
    outlier_analysis: Dict[str, Any]
    quality_score: float
    recommended_actions: List[str]


class BacktestDataHandler:
    """
    Handles data preparation and validation for backtesting operations.
    """

    def __init__(self,
                 required_columns: Optional[List[str]] = None,
                 time_column: str = 'time',
                 validation_enabled: bool = True):
        """
        Initialize data handler.

        Args:
            required_columns: Required OHLC columns
            time_column: Name of time column
            validation_enabled: Enable data validation
        """
        self.required_columns = required_columns or ['time', 'open', 'high', 'low', 'close']
        self.time_column = time_column
        self.validation_enabled = validation_enabled
        self._data_cache = {}

    def validate_and_clean_data(self, df: pd.DataFrame, instrument: str) -> Tuple[pd.DataFrame, DataValidationReport]:
        """
        Comprehensive data validation and cleaning.

        Args:
            df: Raw data DataFrame
            instrument: Instrument name for logging

        Returns:
            Tuple of (cleaned_data, validation_report)
        """
        if df is None or df.empty:
            report = DataValidationReport(
                is_valid=False,
                total_rows=0,
                missing_data_pct=100.0,
                gap_analysis={},
                outlier_analysis={},
                quality_score=0.0,
                recommended_actions=["No data provided"]
            )
            return pd.DataFrame(), report

        original_rows = len(df)
        validation_issues = []

        # Check required columns
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            validation_issues.append(f"Missing required columns: {missing_cols}")

        # Ensure time column exists and convert to datetime
        df = self._standardize_time_column(df)

        # Sort by time
        if self.time_column in df.columns:
            df = df.sort_values(self.time_column).reset_index(drop=True)

        # Remove duplicates
        before_dedup = len(df)
        df = df.drop_duplicates(subset=[self.time_column] if self.time_column in df.columns else None)
        duplicates_removed = before_dedup - len(df)
        if duplicates_removed > 0:
            validation_issues.append(f"Removed {duplicates_removed} duplicate rows")

        # Handle missing data
        missing_analysis = self._analyze_missing_data(df)
        df = self._interpolate_missing_data(df, missing_analysis)

        # Detect and handle gaps
        gap_analysis = self._analyze_gaps(df)
        df = self._handle_gaps(df, gap_analysis)

        # Outlier detection and handling
        outlier_analysis = self._detect_outliers(df)
        df = self._handle_outliers(df, outlier_analysis)

        # Final data quality assessment
        quality_score = self._calculate_data_quality_score(df, original_rows, validation_issues)

        # Generate recommendations
        recommended_actions = self._generate_recommendations(validation_issues, quality_score)

        report = DataValidationReport(
            is_valid=quality_score >= 0.7,  # 70% quality threshold
            total_rows=len(df),
            missing_data_pct=missing_analysis['percentage'],
            gap_analysis=gap_analysis,
            outlier_analysis=outlier_analysis,
            quality_score=quality_score,
            recommended_actions=recommended_actions
        )

        logger.info(f"Data validation for {instrument}: Quality score {quality_score:.2f}, {len(df)} rows processed")
        return df, report

    def _standardize_time_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize time column format"""
        df = df.copy()

        # Find time column
        time_cols = [col for col in ['time', 'timestamp', 'datetime', 'Date'] if col in df.columns]

        if not time_cols:
            logger.warning("No time column found, creating sequential timestamps")
            df['time'] = pd.date_range(start=datetime.now(), periods=len(df), freq='1min')
            return df

        time_col = time_cols[0]

        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            try:
                df[time_col] = pd.to_datetime(df[time_col])
            except Exception as e:
                logger.warning(f"Failed to convert time column {time_col}: {e}")
                df['time'] = pd.date_range(start=datetime.now(), periods=len(df), freq='1min')
                return df

        # Rename to standard 'time' if different
        if time_col != 'time':
            df = df.rename(columns={time_col: 'time'})

        return df

    def _analyze_missing_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing data patterns"""
        if df.empty:
            return {'percentage': 100.0, 'by_column': {}, 'total_missing': 0}

        # Calculate missing data by column
        missing_by_col = df.isnull().sum()
        missing_by_col_pct = (missing_by_col / len(df)) * 100

        total_missing = missing_by_col.sum()
        total_percentage = (total_missing / (len(df) * len(df.columns))) * 100

        # Find missing data patterns
        missing_patterns = {}
        for col in df.columns:
            missing_mask = df[col].isnull()
            if missing_mask.any():
                # Calculate longest gap
                longest_gap = self._find_longest_gap(missing_mask)
                missing_patterns[col] = {
                    'count': int(missing_by_col[col]),
                    'percentage': float(missing_by_col_pct[col]),
                    'longest_gap': longest_gap
                }

        return {
            'percentage': float(total_percentage),
            'by_column': missing_patterns,
            'total_missing': int(total_missing)
        }

    def _find_longest_gap(self, bool_series: pd.Series) -> int:
        """Find longest sequence of True values in boolean series"""
        if not bool_series.any():
            return 0

        # Find transitions
        transitions = bool_series.ne(bool_series.shift())

        if transitions.any():
            groups = transitions.cumsum()
            group_lengths = bool_series.groupby(groups).size()
            true_lengths = group_lengths[bool_series.groupby(groups).first()]
            return int(true_lengths.max()) if not true_lengths.empty else 0

        return int(bool_series.sum())

    def _interpolate_missing_data(self, df: pd.DataFrame, missing_analysis: Dict) -> pd.DataFrame:
        """Interpolate missing OHLC data where appropriate"""
        df = df.copy()

        # Only interpolate numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        cols_to_check = [col for col in numeric_cols if col in df.columns and col in missing_analysis['by_column']]

        for col in cols_to_check:
            missing_count = missing_analysis['by_column'][col]['count']
            col_pct = missing_analysis['by_column'][col]['percentage']

            if col_pct > 20:  # Too much missing data for reliable interpolation
                logger.warning(f"Column {col} has {col_pct:.1f}% missing data - skipping interpolation")
                continue
            elif col_pct > 10:  # Moderate missing - use forward/backward fill first
                df[col] = df[col].ffill().bfill()
            elif col_pct > 0:  # Small amount missing - linear interpolation
                df[col] = df[col].interpolate(method='linear')

        return df

    def _analyze_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze time series gaps"""
        if df.empty or 'time' not in df.columns:
            return {'total_gaps': 0, 'gap_periods': [], 'significant_gaps': []}

        # Assume 1-minute frequency for gap detection
        time_diff_series = df['time'].diff()
        if not hasattr(time_diff_series, 'dt'):
            # If not a timedelta series, skip gap analysis
            return {'total_gaps': 0, 'gap_periods': [], 'significant_gaps': [], 'error': 'Invalid time column type'}
        time_diff = time_diff_series.dt.total_seconds() / 60  # minutes
        expected_diff = 1.0  # 1 minute

        gaps = []
        significant_gaps = []

        for i, diff in enumerate(time_diff):
            if pd.notna(diff) and diff > expected_diff:
                gap_minutes = diff - expected_diff
                gap_info = {
                    'index': i,
                    'start_time': df['time'].iloc[i-1],
                    'end_time': df['time'].iloc[i],
                    'gap_minutes': gap_minutes,
                    'gap_periods': int(gap_minutes)
                }
                gaps.append(gap_info)

                # Significant gap (> 5 minutes)
                if gap_minutes > 5:
                    significant_gaps.append(gap_info)

        return {
            'total_gaps': len(gaps),
            'gap_periods': gaps,
            'significant_gaps': significant_gaps,
            'total_missing_periods': sum(g['gap_periods'] for g in significant_gaps)
        }

    def _handle_gaps(self, df: pd.DataFrame, gap_analysis: Dict) -> pd.DataFrame:
        """Handle data gaps appropriately"""
        if gap_analysis['total_gaps'] == 0:
            return df

        # For significant gaps, we can't really fill them with synthetic data
        # Just log and continue - the data quality score will reflect this
        if gap_analysis['significant_gaps']:
            significant_gap_count = len(gap_analysis['significant_gaps'])
            logger.warning(f"Found {significant_gap_count} significant data gaps (>5 minutes)")

        return df

    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers using statistical methods"""
        outlier_analysis = {}

        if df.empty:
            return outlier_analysis

        # Price outlier detection (OHLC)
        price_cols = [col for col in ['open', 'high', 'low', 'close'] if col in df.columns]

        for col in price_cols:
            if len(df[col].dropna()) < 10:  # Need minimum data for outlier detection
                continue

            # Use modified Z-score (more robust than standard Z-score)
            series = df[col].dropna()
            median = series.median()
            mad = (series - median).abs().median()  # Median Absolute Deviation

            if mad > 0:
                modified_z_scores = 0.6745 * (series - median) / mad
                outliers = modified_z_scores.abs() > 3.5  # Outlier threshold
                outlier_count = outliers.sum()

                if outlier_count > 0:
                    outlier_values = series[outliers]
                    outlier_analysis[col] = {
                        'count': int(outlier_count),
                        'percentage': float((outlier_count / len(series)) * 100),
                        'values': outlier_values.tolist()[:10],  # First 10 outliers
                        'method': 'modified_z_score'
                    }

        # Volume outlier detection (if available)
        if 'volume' in df.columns and not df['volume'].empty:
            volume_series = df['volume'].dropna()
            if len(volume_series) >= 10:
                # Use IQR method for volume outliers
                Q1 = volume_series.quantile(0.25)
                Q3 = volume_series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                volume_outliers = (volume_series < lower_bound) | (volume_series > upper_bound)

                if volume_outliers.any():
                    outlier_analysis['volume'] = {
                        'count': int(volume_outliers.sum()),
                        'percentage': float((volume_outliers.sum() / len(volume_series)) * 100),
                        'bounds': [float(lower_bound), float(upper_bound)],
                        'method': 'iqr'
                    }

        return outlier_analysis

    def _handle_outliers(self, df: pd.DataFrame, outlier_analysis: Dict) -> pd.DataFrame:
        """Handle detected outliers"""
        df = df.copy()

        # For now, we log outliers but don't remove them automatically
        # Removal should be done with careful consideration of the strategy
        total_outliers = sum(col_data['count'] for col_data in outlier_analysis.values() if 'count' in col_data)

        if total_outliers > 0:
            logger.info(f"Detected {total_outliers} outliers across {len(outlier_analysis)} columns. "
                       "Consider reviewing these for strategy impact.")

        return df

    def _calculate_data_quality_score(self, df: pd.DataFrame, original_rows: int, validation_issues: List) -> float:
        """Calculate overall data quality score (0-1)"""
        if df.empty:
            return 0.0

        score = 1.0

        # Data completeness (0.4 weight)
        completeness = len(df) / original_rows if original_rows > 0 else 0
        score -= (1 - completeness) * 0.4

        # Missing data penalty (0.3 weight)
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
        score -= missing_pct * 0.3

        # Validation issues penalty (0.3 weight)
        issue_penalty = min(len(validation_issues) * 0.1, 0.3)
        score -= issue_penalty

        return max(0.0, min(1.0, score))

    def _generate_recommendations(self, validation_issues: List, quality_score: float) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if quality_score < 0.5:
            recommendations.append("CRITICAL: Data quality is too low for reliable backtesting")
        elif quality_score < 0.7:
            recommendations.append("WARNING: Review data quality issues before proceeding")

        if "Missing required columns" in str(validation_issues):
            recommendations.append("ACTION: Verify data source includes all required OHLC fields")

        if "duplicate" in str(validation_issues).lower():
            recommendations.append("INFO: Duplicate data removed - verify if this impacts strategy")

        if quality_score < 0.8:
            recommendations.append("RECOMMENDATION: Consider using higher quality data sources")

        if not recommendations:
            recommendations.append("SUCCESS: Data passed validation checks")

        return recommendations

    def prepare_data_for_backtest(self,
                                raw_df: pd.DataFrame,
                                instrument: str,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Tuple[pd.DataFrame, DataValidationReport]:
        """
        Complete data preparation pipeline for backtesting.

        Args:
            raw_df: Raw trading data
            instrument: Instrument name
            start_date: Filter start date
            end_date: Filter end date

        Returns:
            Tuple of (prepared_data, validation_report)
        """
        # Validate and clean data
        cleaned_df, validation_report = self.validate_and_clean_data(raw_df, instrument)

        if not validation_report.is_valid:
            logger.warning(f"Data validation failed for {instrument}: {validation_report.recommended_actions}")

        # Apply date filters if specified
        if start_date and 'time' in cleaned_df.columns:
            cleaned_df = cleaned_df[cleaned_df['time'] >= start_date]

        if end_date and 'time' in cleaned_df.columns:
            cleaned_df = cleaned_df[cleaned_df['time'] <= end_date]

        # Final reset of index
        if not cleaned_df.empty:
            cleaned_df = cleaned_df.reset_index(drop=True)

        return cleaned_df, validation_report

    def get_data_summary(self, df: pd.DataFrame, instrument: str) -> Dict[str, Any]:
        """
        Generate comprehensive data summary.

        Args:
            df: DataFrame to summarize
            instrument: Instrument name

        Returns:
            Data summary dictionary
        """
        if df.empty:
            return {'instrument': instrument, 'status': 'empty', 'total_rows': 0}

        # Basic statistics
        summary = {
            'instrument': instrument,
            'total_rows': len(df),
            'time_range': {
                'start': df['time'].min().isoformat() if 'time' in df.columns else None,
                'end': df['time'].max().isoformat() if 'time' in df.columns else None
            },
            'price_range': {
                'low': df['low'].min() if 'low' in df.columns else None,
                'high': df['high'].max() if 'high' in df.columns else None
            },
            'columns': list(df.columns)
        }

        # OHLC statistics
        ohlc_cols = [col for col in ['open', 'high', 'low', 'close'] if col in df.columns]
        if ohlc_cols:
            summary['ohlc_stats'] = df[ohlc_cols].describe().to_dict()

        # Volume statistics
        if 'volume' in df.columns:
            summary['volume_stats'] = df['volume'].describe().to_dict()

        # Data quality metrics
        missing_total = df.isnull().sum().sum()
        summary['data_quality'] = {
            'missing_total': int(missing_total),
            'missing_percentage': float((missing_total / (len(df) * len(df.columns))) * 100),
            'duplicate_rows': int(df.duplicated().sum())
        }

        # Time series analysis
        if 'time' in df.columns and len(df) > 1:
            time_diff_series = df['time'].diff().dropna()
            if not time_diff_series.empty and hasattr(time_diff_series, 'dt'):
                summary['time_series'] = {
                    'avg_interval_seconds': float(time_diff_series.dt.total_seconds().mean()),
                    'gaps_detected': int((time_diff_series.dt.total_seconds() > 120).sum())  # >2 min gaps
                }

        return summary

    def get_historical(self, instrument: str, granularity: str, start_date: datetime, end_date: datetime, cache_dir: str = "cache") -> pd.DataFrame:
        """
        Get historical data for backtesting.

        Args:
            instrument: Trading instrument
            granularity: Time granularity (e.g., 'M1', 'H1', 'D')
            start_date: Start date for data
            end_date: End date for data
            cache_dir: Directory to look for cached CSV files

        Returns:
            DataFrame with historical data
        """
        import os

        # Try to load from CSV cache first (as expected by tests)
        csv_filename = f"{instrument}_{granularity}_{start_date:%Y%m%d}_{end_date:%Y%m%d}.csv"
        csv_path = os.path.join(cache_dir, csv_filename)

        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, index_col=0)
                logger.info(f"Loaded historical data from CSV: {csv_path}")
                return df
            except Exception as e:
                logger.warning(f"Failed to load CSV {csv_path}: {e}")

        # Try with current working directory cache
        cwd_cache_path = os.path.join(os.getcwd(), cache_dir, csv_filename)
        if os.path.exists(cwd_cache_path):
            try:
                df = pd.read_csv(cwd_cache_path, index_col=0)
                logger.info(f"Loaded historical data from CSV: {cwd_cache_path}")
                return df
            except Exception as e:
                logger.warning(f"Failed to load CSV {cwd_cache_path}: {e}")

        # Fallback: return empty DataFrame (database/cache loading would be implemented here)
        logger.info(f"No cached data found for {instrument}, returning empty DataFrame")
        return pd.DataFrame()
