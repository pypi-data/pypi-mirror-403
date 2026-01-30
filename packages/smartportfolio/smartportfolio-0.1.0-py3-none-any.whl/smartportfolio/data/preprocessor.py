"""
Data Preprocessor

Handles data normalization, missing value handling, and train/test splitting.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Preprocesses financial data for ML models.
    
    Handles normalization, missing values, and data alignment.
    """
    
    def __init__(
        self,
        scaling_method: str = "minmax",
        fill_method: str = "ffill",
    ):
        """
        Initialize preprocessor.
        
        Args:
            scaling_method: 'minmax' or 'standard'
            fill_method: Method for filling missing values
        """
        self.scaling_method = scaling_method
        self.fill_method = fill_method
        self.scalers: Dict[str, Union[MinMaxScaler, StandardScaler]] = {}
    
    def handle_missing_values(
        self,
        df: pd.DataFrame,
        method: str = None,
    ) -> pd.DataFrame:
        """
        Handle missing values in DataFrame.
        
        Args:
            df: Input DataFrame
            method: Fill method ('ffill', 'bfill', 'mean', 'zero')
            
        Returns:
            DataFrame with missing values handled
        """
        method = method or self.fill_method
        df = df.copy()
        
        if method == "ffill":
            df = df.ffill().bfill()
        elif method == "bfill":
            df = df.bfill().ffill()
        elif method == "mean":
            df = df.fillna(df.mean())
        elif method == "zero":
            df = df.fillna(0)
        elif method == "drop":
            df = df.dropna()
        else:
            raise ValueError(f"Unknown fill method: {method}")
        
        return df
    
    def normalize(
        self,
        data: np.ndarray,
        name: str = "default",
        fit: bool = True,
    ) -> np.ndarray:
        """
        Normalize data using specified scaling method.
        
        Args:
            data: Data to normalize (2D array)
            name: Name for scaler (for inverse transform)
            fit: Whether to fit the scaler
            
        Returns:
            Normalized data
        """
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)
        
        if fit or name not in self.scalers:
            if self.scaling_method == "minmax":
                scaler = MinMaxScaler(feature_range=(0, 1))
            else:
                scaler = StandardScaler()
            
            scaler.fit(data)
            self.scalers[name] = scaler
        else:
            scaler = self.scalers[name]
        
        return scaler.transform(data)
    
    def denormalize(
        self,
        data: np.ndarray,
        name: str = "default",
    ) -> np.ndarray:
        """
        Inverse transform normalized data.
        
        Args:
            data: Normalized data
            name: Name of scaler to use
            
        Returns:
            Original scale data
        """
        if name not in self.scalers:
            raise ValueError(f"No scaler found with name: {name}")
        
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)
        
        return self.scalers[name].inverse_transform(data)
    
    def normalize_features(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
        group_by: str = None,
    ) -> pd.DataFrame:
        """
        Normalize specified feature columns in DataFrame.
        
        Args:
            df: Input DataFrame
            feature_cols: Columns to normalize
            group_by: Optional column to group by (e.g., 'ticker')
            
        Returns:
            DataFrame with normalized features
        """
        df = df.copy()
        
        if group_by is not None:
            # Normalize within each group
            for group_val in df[group_by].unique():
                mask = df[group_by] == group_val
                for col in feature_cols:
                    if col in df.columns:
                        values = df.loc[mask, col].values.reshape(-1, 1)
                        scaler = MinMaxScaler() if self.scaling_method == "minmax" else StandardScaler()
                        df.loc[mask, col] = scaler.fit_transform(values).flatten()
        else:
            # Normalize across all data
            for col in feature_cols:
                if col in df.columns:
                    values = df[col].values.reshape(-1, 1)
                    normalized = self.normalize(values, name=col)
                    df[col] = normalized.flatten()
        
        return df
    
    def create_sequences(
        self,
        data: np.ndarray,
        seq_length: int,
        target_length: int = 1,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for time series modeling.
        
        Args:
            data: Input data array
            seq_length: Length of input sequences
            target_length: Length of target sequences
            
        Returns:
            Tuple of (sequences, targets)
        """
        sequences = []
        targets = []
        
        for i in range(len(data) - seq_length - target_length + 1):
            seq = data[i:i + seq_length]
            target = data[i + seq_length:i + seq_length + target_length]
            sequences.append(seq)
            targets.append(target)
        
        return np.array(sequences), np.array(targets)
    
    def train_test_split(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        train_ratio: float = 0.8,
        validation_ratio: float = 0.1,
    ) -> Tuple[Any, Any, Any]:
        """
        Split data into train, validation, and test sets.
        
        Uses chronological split for time series data.
        
        Args:
            data: Input data
            train_ratio: Proportion for training
            validation_ratio: Proportion for validation
            
        Returns:
            Tuple of (train, validation, test)
        """
        n = len(data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + validation_ratio))
        
        if isinstance(data, pd.DataFrame):
            train = data.iloc[:train_end]
            val = data.iloc[train_end:val_end]
            test = data.iloc[val_end:]
        else:
            train = data[:train_end]
            val = data[train_end:val_end]
            test = data[val_end:]
        
        return train, val, test
    
    def align_data(
        self,
        data_dict: Dict[str, pd.DataFrame],
        date_col: str = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Align multiple DataFrames to same date range.
        
        Args:
            data_dict: Dictionary of DataFrames
            date_col: Date column name (if None, uses index)
            
        Returns:
            Dictionary with aligned DataFrames
        """
        if not data_dict:
            return {}
        
        # Find common date range
        all_dates = None
        for ticker, df in data_dict.items():
            if date_col:
                dates = set(df[date_col])
            else:
                dates = set(df.index)
            
            if all_dates is None:
                all_dates = dates
            else:
                all_dates = all_dates.intersection(dates)
        
        # Filter to common dates
        aligned = {}
        for ticker, df in data_dict.items():
            if date_col:
                mask = df[date_col].isin(all_dates)
                aligned[ticker] = df[mask].copy()
            else:
                aligned[ticker] = df[df.index.isin(all_dates)].copy()
        
        return aligned
    
    def prepare_rl_state(
        self,
        feature_matrix: np.ndarray,
        current_weights: np.ndarray,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Prepare state vector for RL agent.
        
        Args:
            feature_matrix: Features for all assets (n_assets, n_features)
            current_weights: Current portfolio weights
            normalize: Whether to normalize features
            
        Returns:
            Flattened state vector
        """
        if normalize:
            # Normalize features per-asset
            feature_matrix = (feature_matrix - np.nanmean(feature_matrix, axis=0)) / (
                np.nanstd(feature_matrix, axis=0) + 1e-10
            )
        
        # Replace NaN with 0
        feature_matrix = np.nan_to_num(feature_matrix, 0)
        
        # Flatten and concatenate with weights
        flat_features = feature_matrix.flatten()
        state = np.concatenate([flat_features, current_weights])
        
        return state.astype(np.float32)
