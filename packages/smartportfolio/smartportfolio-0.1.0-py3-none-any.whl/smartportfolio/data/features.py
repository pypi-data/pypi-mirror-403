"""
Feature Engineering Module

Calculates technical indicators (RSI, MACD, Bollinger Bands) and
correlation features for the portfolio optimization pipeline.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Calculates technical indicators and derived features for stock data.
    
    Implements RSI, MACD, Bollinger Bands, returns, volatility, and
    correlation features needed for the GNN and RL models.
    """
    
    def __init__(
        self,
        rsi_period: int = None,
        macd_fast: int = None,
        macd_slow: int = None,
        macd_signal: int = None,
        bollinger_period: int = None,
        bollinger_std: int = None,
    ):
        """
        Initialize feature engineer with technical indicator parameters.
        """
        self.rsi_period = rsi_period or config.data.rsi_period
        self.macd_fast = macd_fast or config.data.macd_fast
        self.macd_slow = macd_slow or config.data.macd_slow
        self.macd_signal = macd_signal or config.data.macd_signal
        self.bollinger_period = bollinger_period or config.data.bollinger_period
        self.bollinger_std = bollinger_std or config.data.bollinger_std
    
    def calculate_returns(
        self,
        prices: pd.Series,
        log_returns: bool = True,
    ) -> pd.Series:
        """
        Calculate price returns.
        
        Args:
            prices: Price series
            log_returns: If True, calculate log returns; else simple returns
            
        Returns:
            Returns series
        """
        if log_returns:
            return np.log(prices / prices.shift(1))
        else:
            return prices.pct_change()
    
    def calculate_rsi(self, prices: pd.Series, period: int = None) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Price series
            period: RSI period
            
        Returns:
            RSI values (0-100)
        """
        period = period or self.rsi_period
        
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int = None,
        slow: int = None,
        signal: int = None,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        fast = fast or self.macd_fast
        slow = slow or self.macd_slow
        signal = signal or self.macd_signal
        
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = None,
        num_std: int = None,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Price series
            period: Moving average period
            num_std: Number of standard deviations
            
        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        period = period or self.bollinger_period
        num_std = num_std or self.bollinger_std
        
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        
        return upper, middle, lower
    
    def calculate_volatility(
        self,
        returns: pd.Series,
        window: int = 20,
    ) -> pd.Series:
        """
        Calculate rolling volatility (standard deviation of returns).
        
        Args:
            returns: Returns series
            window: Rolling window size
            
        Returns:
            Volatility series
        """
        return returns.rolling(window=window).std()
    
    def calculate_momentum(
        self,
        prices: pd.Series,
        period: int = 10,
    ) -> pd.Series:
        """
        Calculate price momentum.
        
        Args:
            prices: Price series
            period: Momentum period
            
        Returns:
            Momentum values
        """
        return prices / prices.shift(period) - 1
    
    def engineer_features(
        self,
        df: pd.DataFrame,
        price_col: str = "close",
        volume_col: str = "volume",
    ) -> pd.DataFrame:
        """
        Calculate all technical indicators for a stock DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            price_col: Name of price column
            volume_col: Name of volume column
            
        Returns:
            DataFrame with added feature columns
        """
        df = df.copy()
        prices = df[price_col]
        
        # Returns
        df["log_return"] = self.calculate_returns(prices, log_returns=True)
        df["simple_return"] = self.calculate_returns(prices, log_returns=False)
        
        # RSI
        df["rsi"] = self.calculate_rsi(prices)
        
        # MACD
        macd, signal, hist = self.calculate_macd(prices)
        df["macd"] = macd
        df["macd_signal"] = signal
        df["macd_hist"] = hist
        
        # Bollinger Bands
        upper, middle, lower = self.calculate_bollinger_bands(prices)
        df["bb_upper"] = upper
        df["bb_middle"] = middle
        df["bb_lower"] = lower
        df["bb_width"] = (upper - lower) / middle
        df["bb_position"] = (prices - lower) / (upper - lower + 1e-10)
        
        # Volatility
        df["volatility_20"] = self.calculate_volatility(df["log_return"], 20)
        df["volatility_60"] = self.calculate_volatility(df["log_return"], 60)
        
        # Momentum
        df["momentum_5"] = self.calculate_momentum(prices, 5)
        df["momentum_10"] = self.calculate_momentum(prices, 10)
        df["momentum_20"] = self.calculate_momentum(prices, 20)
        
        # Volume features
        if volume_col in df.columns:
            df["volume_sma_20"] = df[volume_col].rolling(window=20).mean()
            df["volume_ratio"] = df[volume_col] / (df["volume_sma_20"] + 1e-10)
        
        # Price ratios
        if "high" in df.columns and "low" in df.columns:
            df["high_low_ratio"] = df["high"] / (df["low"] + 1e-10)
            df["close_open_ratio"] = df[price_col] / (df.get("open", prices) + 1e-10)
        
        return df
    
    def calculate_correlation_matrix(
        self,
        returns_df: pd.DataFrame,
        method: str = "pearson",
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between assets.
        
        Args:
            returns_df: DataFrame with returns for each asset as columns
            method: Correlation method ('pearson', 'spearman', 'kendall')
            
        Returns:
            Correlation matrix
        """
        return returns_df.corr(method=method)
    
    def calculate_rolling_correlation(
        self,
        returns_df: pd.DataFrame,
        window: int = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate rolling correlation matrices over time.
        
        Args:
            returns_df: DataFrame with returns for each asset
            window: Rolling window size
            
        Returns:
            Dictionary mapping dates to correlation matrices
        """
        window = window or config.data.correlation_window
        
        correlations = {}
        dates = returns_df.index[window:]
        
        for i, date in enumerate(dates):
            start_idx = i
            end_idx = i + window
            window_data = returns_df.iloc[start_idx:end_idx]
            corr = window_data.corr()
            correlations[date] = corr
        
        return correlations
    
    def get_feature_matrix(
        self,
        data_dict: Dict[str, pd.DataFrame],
        feature_cols: List[str] = None,
    ) -> Tuple[np.ndarray, List[str], List[str]]:
        """
        Create feature matrix for all assets.
        
        Args:
            data_dict: Dictionary mapping ticker to DataFrame
            feature_cols: List of feature columns to include
            
        Returns:
            Tuple of (feature_matrix, tickers, feature_names)
        """
        if feature_cols is None:
            feature_cols = [
                "log_return", "rsi", "macd", "macd_hist",
                "bb_position", "volatility_20", "momentum_10"
            ]
        
        tickers = list(data_dict.keys())
        matrices = []
        
        for ticker in tickers:
            df = data_dict[ticker]
            
            # Ensure features are calculated
            if "rsi" not in df.columns:
                df = self.engineer_features(df)
                data_dict[ticker] = df
            
            # Get available features
            available_cols = [c for c in feature_cols if c in df.columns]
            feature_data = df[available_cols].values
            matrices.append(feature_data)
        
        # Stack into 3D array: (num_tickers, num_timesteps, num_features)
        # Align to shortest series
        min_len = min(m.shape[0] for m in matrices)
        aligned = [m[-min_len:] for m in matrices]
        feature_matrix = np.stack(aligned, axis=0)
        
        return feature_matrix, tickers, feature_cols
