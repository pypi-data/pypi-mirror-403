"""
Local Storage Manager

Handles persistent file storage with timestamp_uuid naming convention.
"""

import logging
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

import pandas as pd
import numpy as np

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class LocalStorage:
    """
    Manages local file storage for outputs, cache, and models.
    
    All outputs are saved with timestamp_uuid naming for uniqueness.
    """
    
    def __init__(
        self,
        outputs_dir: Path = None,
        cache_dir: Path = None,
        models_dir: Path = None,
    ):
        """
        Initialize storage manager.
        
        Args:
            outputs_dir: Directory for output files
            cache_dir: Directory for cached data
            models_dir: Directory for saved models
        """
        self.outputs_dir = outputs_dir or config.outputs_dir
        self.cache_dir = cache_dir or config.cache_dir
        self.models_dir = models_dir or config.models_dir
        
        # Create directories
        for d in [self.outputs_dir, self.cache_dir, self.models_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def _generate_filename(self, prefix: str, extension: str) -> str:
        """Generate unique filename with timestamp and UUID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}_{prefix}.{extension}"
    
    def save_portfolio_weights(
        self,
        weights: Dict[str, float],
        tickers: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> Path:
        """
        Save portfolio weights to CSV.
        
        Args:
            weights: Dictionary mapping ticker to weight
            tickers: Optional list of tickers (for ordering)
            metadata: Optional metadata to include
            
        Returns:
            Path to saved file
        """
        filename = self._generate_filename("portfolio_weights", "csv")
        filepath = self.outputs_dir / filename
        
        # Create DataFrame
        if tickers is None:
            tickers = list(weights.keys())
        
        df = pd.DataFrame({
            "ticker": tickers,
            "weight": [weights.get(t, 0.0) for t in tickers],
        })
        
        # Add metadata columns if provided
        if metadata:
            for key, value in metadata.items():
                df[key] = value
        
        df.to_csv(filepath, index=False)
        logger.info(f"Saved portfolio weights to {filepath}")
        
        return filepath
    
    def save_allocation_result(
        self,
        original_df: pd.DataFrame,
        weights: Dict[str, float],
        output_path: Path = None,
    ) -> Path:
        """
        Save allocation result by adding weights column to original data.
        
        Args:
            original_df: Original ticker DataFrame
            weights: Dictionary mapping ticker to weight
            output_path: Optional custom output path
            
        Returns:
            Path to saved file
        """
        if output_path is None:
            filename = self._generate_filename("allocation_result", "csv")
            output_path = self.outputs_dir / filename
        
        df = original_df.copy()
        
        # Find ticker column
        ticker_col = None
        for col in df.columns:
            if col.lower() in ["ticker", "tickers", "symbol", "symbols"]:
                ticker_col = col
                break
        
        if ticker_col is None:
            ticker_col = df.columns[0]
        
        # Add weights column
        df["weight"] = df[ticker_col].map(weights).fillna(0.0)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved allocation result to {output_path}")
        
        return output_path
    
    def save_dataframe(
        self,
        df: pd.DataFrame,
        prefix: str,
        format: str = "csv",
    ) -> Path:
        """
        Save DataFrame to file.
        
        Args:
            df: DataFrame to save
            prefix: Filename prefix
            format: File format ('csv' or 'parquet')
            
        Returns:
            Path to saved file
        """
        filename = self._generate_filename(prefix, format)
        filepath = self.outputs_dir / filename
        
        if format == "csv":
            df.to_csv(filepath, index=True)
        elif format == "parquet":
            df.to_parquet(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved DataFrame to {filepath}")
        return filepath
    
    def save_metrics(
        self,
        metrics: Dict[str, Any],
        prefix: str = "metrics",
    ) -> Path:
        """
        Save metrics dictionary to JSON.
        
        Args:
            metrics: Dictionary of metrics
            prefix: Filename prefix
            
        Returns:
            Path to saved file
        """
        filename = self._generate_filename(prefix, "json")
        filepath = self.outputs_dir / filename
        
        # Convert numpy types to Python types
        def convert(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(v) for v in obj]
            return obj
        
        with open(filepath, "w") as f:
            json.dump(convert(metrics), f, indent=2)
        
        logger.info(f"Saved metrics to {filepath}")
        return filepath
    
    def save_model(
        self,
        model: Any,
        prefix: str = "model",
    ) -> Path:
        """
        Save model to file.
        
        Args:
            model: Model object with save() method or pickle-able
            prefix: Filename prefix
            
        Returns:
            Path to saved file
        """
        filename = self._generate_filename(prefix, "pkl")
        filepath = self.models_dir / filename
        
        if hasattr(model, "save"):
            # For SB3 models
            model.save(str(filepath.with_suffix("")))
            filepath = filepath.with_suffix(".zip")
        else:
            # Pickle fallback
            import pickle
            with open(filepath, "wb") as f:
                pickle.dump(model, f)
        
        logger.info(f"Saved model to {filepath}")
        return filepath
    
    def list_outputs(self, pattern: str = "*.csv") -> List[Path]:
        """
        List output files matching pattern.
        
        Args:
            pattern: Glob pattern
            
        Returns:
            List of matching file paths
        """
        return sorted(self.outputs_dir.glob(pattern), reverse=True)
    
    def get_latest_output(self, prefix: str = "portfolio") -> Optional[Path]:
        """
        Get most recent output file with given prefix.
        
        Args:
            prefix: Filename prefix to match
            
        Returns:
            Path to most recent file or None
        """
        files = list(self.outputs_dir.glob(f"*_{prefix}*.csv"))
        if not files:
            return None
        return max(files, key=lambda p: p.stat().st_mtime)
    
    def load_latest_weights(self) -> Optional[Dict[str, float]]:
        """
        Load most recent portfolio weights.
        
        Returns:
            Dictionary of weights or None
        """
        filepath = self.get_latest_output("portfolio_weights")
        if filepath is None:
            return None
        
        df = pd.read_csv(filepath)
        weights = dict(zip(df["ticker"], df["weight"]))
        return weights
    
    def clear_cache(self) -> int:
        """
        Clear all cached files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        for f in self.cache_dir.glob("*"):
            if f.is_file():
                f.unlink()
                count += 1
        
        logger.info(f"Cleared {count} cached files")
        return count
