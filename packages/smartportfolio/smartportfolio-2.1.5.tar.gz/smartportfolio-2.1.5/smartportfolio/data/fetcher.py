"""
Yahoo Finance Data Fetcher

Fetches OHLCV data for stock tickers with caching and error handling.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import yfinance as yf

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class TickerDataFetcher:
    """
    Fetches historical market data from Yahoo Finance.
    
    Includes caching to avoid repeated API calls and batch processing
    for memory efficiency on 8GB RAM devices.
    """
    
    def __init__(
        self,
        period: str = None,
        interval: str = None,
        cache_dir: Path = None,
    ):
        """
        Initialize the data fetcher.
        
        Args:
            period: Data period (e.g., '2y', '5y')
            interval: Data interval (e.g., '1d', '1h')
            cache_dir: Directory for caching downloaded data
        """
        self.period = period or config.data.default_period
        self.interval = interval or config.data.default_interval
        self.cache_dir = cache_dir or config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def load_tickers_from_file(self, file_path: Union[str, Path]) -> List[str]:
        """
        Load ticker symbols from a CSV or XLSX file.
        
        Args:
            file_path: Path to the ticker file
            
        Returns:
            List of ticker symbols
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Ticker file not found: {file_path}")
        
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Try to find ticker column
        ticker_columns = ["ticker", "tickers", "symbol", "symbols", "stock", "stocks"]
        ticker_col = None
        
        for col in df.columns:
            if col.lower() in ticker_columns:
                ticker_col = col
                break
        
        if ticker_col is None:
            # Use first column if no matching column name
            ticker_col = df.columns[0]
            logger.warning(f"Using first column '{ticker_col}' as ticker column")
        
        tickers = df[ticker_col].dropna().astype(str).str.strip().str.upper().tolist()
        tickers = [t for t in tickers if t and t != "NAN"]
        
        logger.info(f"Loaded {len(tickers)} tickers from {file_path}")
        return tickers
    
    def _get_cache_path(self, ticker: str) -> Path:
        """Get cache file path for a ticker."""
        return self.cache_dir / f"{ticker}_{self.period}_{self.interval}.parquet"
    
    def _is_cache_valid(self, cache_path: Path, max_age_hours: int = 24) -> bool:
        """Check if cached data is still valid."""
        if not cache_path.exists():
            return False
        
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=max_age_hours)
    
    def fetch_single(
        self,
        ticker: str,
        use_cache: bool = True,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data for a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cached data if available
            
        Returns:
            DataFrame with OHLCV data or None if fetch failed
        """
        cache_path = self._get_cache_path(ticker)
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_path):
            try:
                df = pd.read_parquet(cache_path)
                logger.debug(f"Loaded {ticker} from cache")
                return df
            except Exception as e:
                logger.warning(f"Failed to load cache for {ticker}: {e}")
        
        # Fetch from Yahoo Finance
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=self.period, interval=self.interval)
            
            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return None
            
            # Clean column names
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]
            
            # Add ticker column
            df["ticker"] = ticker
            
            # Save to cache
            try:
                df.to_parquet(cache_path)
                logger.debug(f"Cached {ticker} data")
            except Exception as e:
                logger.warning(f"Failed to cache {ticker}: {e}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch {ticker}: {e}")
            return None
    
    def fetch_multiple(
        self,
        tickers: List[str],
        use_cache: bool = True,
        progress_callback: callable = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple tickers with chunked processing.
        
        Args:
            tickers: List of ticker symbols
            use_cache: Whether to use cached data
            progress_callback: Callback function(current, total, ticker)
            
        Returns:
            Dictionary mapping ticker to DataFrame
        """
        results = {}
        chunk_size = config.data.chunk_size
        total = len(tickers)
        
        for i, ticker in enumerate(tickers):
            if progress_callback:
                progress_callback(i + 1, total, ticker)
            
            df = self.fetch_single(ticker, use_cache=use_cache)
            if df is not None:
                results[ticker] = df
            
            # Memory management: process in chunks
            if (i + 1) % chunk_size == 0:
                import gc
                gc.collect()
        
        logger.info(f"Fetched data for {len(results)}/{total} tickers")
        return results
    
    def fetch_to_combined(
        self,
        tickers: List[str],
        use_cache: bool = True,
        progress_callback: callable = None,
    ) -> pd.DataFrame:
        """
        Fetch data for multiple tickers and combine into single DataFrame.
        
        Args:
            tickers: List of ticker symbols
            use_cache: Whether to use cached data
            progress_callback: Callback function
            
        Returns:
            Combined DataFrame with all tickers
        """
        data_dict = self.fetch_multiple(tickers, use_cache, progress_callback)
        
        if not data_dict:
            return pd.DataFrame()
        
        # Combine all dataframes
        dfs = []
        for ticker, df in data_dict.items():
            df = df.reset_index()
            dfs.append(df)
        
        combined = pd.concat(dfs, ignore_index=True)
        combined = combined.sort_values(["ticker", "date" if "date" in combined.columns else "Date"])
        
        return combined
    
    def get_price_matrix(
        self,
        tickers: List[str],
        price_col: str = "close",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Get price matrix with tickers as columns.
        
        Args:
            tickers: List of ticker symbols
            price_col: Price column to use
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with dates as index and tickers as columns
        """
        data_dict = self.fetch_multiple(tickers, use_cache)
        
        if not data_dict:
            return pd.DataFrame()
        
        # Create price matrix
        price_dfs = []
        for ticker, df in data_dict.items():
            if price_col in df.columns:
                s = df[price_col].copy()
                s.name = ticker
                price_dfs.append(s)
        
        if not price_dfs:
            return pd.DataFrame()
        
        price_matrix = pd.concat(price_dfs, axis=1)
        price_matrix = price_matrix.dropna(how="all")
        
        return price_matrix
