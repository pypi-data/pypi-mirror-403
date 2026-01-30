"""
Prophet Time Series Forecasting Module

Uses Facebook Prophet for per-asset time series forecasting and
state representation generation for the RL agent.
"""

import logging
import gc
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from smartportfolio.config import config


logger = logging.getLogger(__name__)


# Suppress Prophet logging
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)


class ProphetEncoder:
    """
    Prophet-based time series encoder for portfolio assets.
    
    Provides forecasting and trend decomposition features
    for the RL state representation.
    """
    
    def __init__(
        self,
        yearly_seasonality: bool = None,
        weekly_seasonality: bool = None,
        daily_seasonality: bool = None,
        changepoint_prior_scale: float = None,
        forecast_horizon: int = 5,
    ):
        """
        Initialize Prophet encoder.
        
        Args:
            yearly_seasonality: Include yearly seasonality
            weekly_seasonality: Include weekly seasonality
            daily_seasonality: Include daily seasonality
            changepoint_prior_scale: Flexibility of trend
            forecast_horizon: Days to forecast ahead
        """
        self.yearly_seasonality = (
            yearly_seasonality if yearly_seasonality is not None 
            else config.model.prophet_yearly_seasonality
        )
        self.weekly_seasonality = (
            weekly_seasonality if weekly_seasonality is not None
            else config.model.prophet_weekly_seasonality
        )
        self.daily_seasonality = (
            daily_seasonality if daily_seasonality is not None
            else config.model.prophet_daily_seasonality
        )
        self.changepoint_prior_scale = (
            changepoint_prior_scale or config.model.prophet_changepoint_prior_scale
        )
        self.forecast_horizon = forecast_horizon
        
        self.models: Dict[str, Any] = {}
        self.forecasts: Dict[str, pd.DataFrame] = {}
    
    def _prepare_data(
        self,
        df: pd.DataFrame,
        date_col: str = None,
        value_col: str = "close",
    ) -> pd.DataFrame:
        """
        Prepare data for Prophet format (ds, y columns).
        
        Args:
            df: Input DataFrame
            date_col: Date column name
            value_col: Value column name
            
        Returns:
            Prophet-formatted DataFrame
        """
        df = df.copy()
        
        # Handle date column
        if date_col and date_col in df.columns:
            df["ds"] = pd.to_datetime(df[date_col])
        elif "date" in df.columns:
            df["ds"] = pd.to_datetime(df["date"])
        elif "Date" in df.columns:
            df["ds"] = pd.to_datetime(df["Date"])
        elif isinstance(df.index, pd.DatetimeIndex):
            df["ds"] = df.index
        else:
            raise ValueError("Could not find date column")
        
        # Handle value column
        if value_col in df.columns:
            df["y"] = df[value_col].astype(float)
        else:
            raise ValueError(f"Value column '{value_col}' not found")
        
        # Select and clean
        prophet_df = df[["ds", "y"]].copy()
        prophet_df = prophet_df.dropna()
        prophet_df = prophet_df.sort_values("ds").reset_index(drop=True)
        
        return prophet_df
    
    def fit_single(
        self,
        ticker: str,
        df: pd.DataFrame,
        value_col: str = "close",
    ) -> bool:
        """
        Fit Prophet model for single ticker.
        
        Args:
            ticker: Ticker symbol
            df: Price data DataFrame
            value_col: Column to forecast
            
        Returns:
            True if successful
        """
        try:
            from prophet import Prophet
            
            prophet_df = self._prepare_data(df, value_col=value_col)
            
            if len(prophet_df) < 30:
                logger.warning(f"Insufficient data for {ticker}: {len(prophet_df)} rows")
                return False
            
            # Create and fit model
            model = Prophet(
                yearly_seasonality=self.yearly_seasonality,
                weekly_seasonality=self.weekly_seasonality,
                daily_seasonality=self.daily_seasonality,
                changepoint_prior_scale=self.changepoint_prior_scale,
            )
            
            # Suppress fitting output
            model.fit(prophet_df)
            
            self.models[ticker] = model
            logger.debug(f"Fitted Prophet model for {ticker}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fit Prophet for {ticker}: {e}")
            return False
    
    def fit_multiple(
        self,
        data_dict: Dict[str, pd.DataFrame],
        value_col: str = "close",
        progress_callback: callable = None,
    ) -> Dict[str, bool]:
        """
        Fit Prophet models for multiple tickers.
        
        Memory-efficient: fits one at a time and runs GC.
        
        Args:
            data_dict: Dictionary mapping ticker to DataFrame
            value_col: Column to forecast
            progress_callback: Callback(current, total, ticker)
            
        Returns:
            Dictionary of fit results
        """
        results = {}
        total = len(data_dict)
        
        for i, (ticker, df) in enumerate(data_dict.items()):
            if progress_callback:
                progress_callback(i + 1, total, ticker)
            
            success = self.fit_single(ticker, df, value_col)
            results[ticker] = success
            
            # Memory management
            if (i + 1) % 5 == 0:
                gc.collect()
        
        fitted = sum(results.values())
        logger.info(f"Fitted Prophet models: {fitted}/{total}")
        
        return results
    
    def forecast_single(
        self,
        ticker: str,
        periods: int = None,
    ) -> Optional[pd.DataFrame]:
        """
        Generate forecast for single ticker.
        
        Args:
            ticker: Ticker symbol
            periods: Number of periods to forecast
            
        Returns:
            Forecast DataFrame or None
        """
        if ticker not in self.models:
            logger.warning(f"No model found for {ticker}")
            return None
        
        periods = periods or self.forecast_horizon
        model = self.models[ticker]
        
        try:
            future = model.make_future_dataframe(periods=periods)
            forecast = model.predict(future)
            
            self.forecasts[ticker] = forecast
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to forecast {ticker}: {e}")
            return None
    
    def forecast_all(
        self,
        periods: int = None,
        progress_callback: callable = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate forecasts for all fitted models.
        
        Args:
            periods: Forecast horizon
            progress_callback: Callback function
            
        Returns:
            Dictionary of forecasts
        """
        results = {}
        tickers = list(self.models.keys())
        total = len(tickers)
        
        for i, ticker in enumerate(tickers):
            if progress_callback:
                progress_callback(i + 1, total, ticker)
            
            forecast = self.forecast_single(ticker, periods)
            if forecast is not None:
                results[ticker] = forecast
            
            # Memory management
            if (i + 1) % 5 == 0:
                gc.collect()
        
        logger.info(f"Generated forecasts: {len(results)}/{total}")
        return results
    
    def get_forecast_features(
        self,
        ticker: str,
        num_periods: int = 5,
    ) -> Optional[np.ndarray]:
        """
        Extract forecast-based features for RL state.
        
        Returns:
            - trend: Current trend value
            - trend_change: Trend change rate
            - yhat: Predicted value
            - yhat_lower: Lower confidence bound
            - yhat_upper: Upper confidence bound
            - forecast_return: Expected return
        
        Args:
            ticker: Ticker symbol
            num_periods: Number of forecast periods to consider
            
        Returns:
            Feature array or None
        """
        if ticker not in self.forecasts:
            forecast = self.forecast_single(ticker)
            if forecast is None:
                return None
        
        forecast = self.forecasts[ticker]
        
        try:
            # Get last historical and forecast values
            last_idx = len(forecast) - self.forecast_horizon
            
            # Current values
            current = forecast.iloc[last_idx - 1]
            
            # Future predictions
            future = forecast.iloc[last_idx:last_idx + num_periods]
            
            features = [
                current["trend"],
                future["trend"].mean() - current["trend"],  # trend change
                future["yhat"].mean(),  # mean prediction
                future["yhat_lower"].mean(),  # lower bound
                future["yhat_upper"].mean(),  # upper bound
                (future["yhat"].iloc[-1] - current["yhat"]) / (current["yhat"] + 1e-10),  # expected return
            ]
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Failed to extract features for {ticker}: {e}")
            return None
    
    def get_state_vector(
        self,
        tickers: List[str],
    ) -> np.ndarray:
        """
        Get combined state vector for all tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            State vector (num_tickers, num_features)
        """
        features_list = []
        num_features = 6  # from get_forecast_features
        
        for ticker in tickers:
            features = self.get_forecast_features(ticker)
            if features is not None:
                features_list.append(features)
            else:
                # Default features if forecast failed
                features_list.append(np.zeros(num_features, dtype=np.float32))
        
        return np.array(features_list, dtype=np.float32)
    
    def get_trend_signals(
        self,
        tickers: List[str],
    ) -> Dict[str, str]:
        """
        Get trend signals (bullish/bearish/neutral) for tickers.
        
        Args:
            tickers: List of tickers
            
        Returns:
            Dictionary mapping ticker to signal
        """
        signals = {}
        
        for ticker in tickers:
            features = self.get_forecast_features(ticker)
            if features is None:
                signals[ticker] = "neutral"
                continue
            
            trend_change = features[1]
            expected_return = features[5]
            
            if expected_return > 0.02 and trend_change > 0:
                signals[ticker] = "bullish"
            elif expected_return < -0.02 and trend_change < 0:
                signals[ticker] = "bearish"
            else:
                signals[ticker] = "neutral"
        
        return signals
    
    def clear_models(self):
        """Clear all models and forecasts to free memory."""
        self.models.clear()
        self.forecasts.clear()
        gc.collect()
        logger.info("Cleared Prophet models and forecasts")
