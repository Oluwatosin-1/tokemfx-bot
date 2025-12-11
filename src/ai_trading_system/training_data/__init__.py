"""
AI Training Data Module
=======================
Manages historical data pipeline for AI/ML model training and continuous learning.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import json

from .training_pipeline import training_pipeline

class AITrainingDataManager:
    """
    Manages AI training data storage and retrieval.
    """

    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)
        self.raw_data_path = self.base_path / "backtest_results" / "raw"
        self.processed_data_path = self.base_path / "backtest_results" / "processed"
        self.models_path = self.base_path / "backtest_results" / "models"
        self.patterns_path = self.base_path / "market_patterns"
        self.logs_path = self.base_path / "performance_logs"

    def store_backtest_results(self, results: List[Dict], data_type: str = "processed") -> bool:
        """
        Store backtest results for AI training.

        Args:
            results: List of backtest result dictionaries
            data_type: "raw" or "processed"

        Returns:
            Success status
        """
        try:
            if data_type == "raw":
                output_path = self.raw_data_path
            else:
                output_path = self.processed_data_path

            output_path.mkdir(parents=True, exist_ok=True)

            # Save as JSON with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{timestamp}.json"

            with open(output_path / filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            return True
        except Exception as e:
            print(f"Error storing backtest results: {e}")
            return False

    def load_training_data(self, data_type: str = "processed") -> List[Dict]:
        """
        Load historical training data.

        Args:
            data_type: Type of data to load ("raw" or "processed")

        Returns:
            Combined training data
        """
        try:
            if data_type == "raw":
                data_path = self.raw_data_path
            else:
                data_path = self.processed_data_path

            all_data = []

            if data_path.exists():
                for json_file in data_path.glob("*.json"):
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                all_data.extend(data)
                            else:
                                all_data.append(data)
                    except Exception as e:
                        print(f"Error loading {json_file}: {e}")

            return all_data
        except Exception as e:
            print(f"Error loading training data: {e}")
            return []

# Create global instance
data_manager = AITrainingDataManager()

__all__ = ['AITrainingDataManager', 'data_manager']
