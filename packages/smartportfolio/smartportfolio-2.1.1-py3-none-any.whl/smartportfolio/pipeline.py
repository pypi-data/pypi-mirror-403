"""
Pipeline Module

Main pipeline for running the portfolio optimization workflow.
"""

import logging
import gc
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import numpy as np
import pandas as pd

from smartportfolio.config import config
from smartportfolio.data import TickerDataFetcher, FeatureEngineer, LocalStorage, DataPreprocessor
from smartportfolio.graph import DynamicGraphBuilder, NumpyGAT


logger = logging.getLogger(__name__)


def run_test_pipeline():
    """
    Run integration test with sample tickers.
    """
    print("SmartPortfolio Integration Test")
    print("=" * 40)
    
    # Sample tickers
    test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    
    print(f"\n1. Testing with tickers: {test_tickers}")
    
    # Initialize components
    fetcher = TickerDataFetcher()
    engineer = FeatureEngineer()
    builder = DynamicGraphBuilder()
    storage = LocalStorage()
    
    # Fetch data
    print("\n2. Fetching market data...")
    data_dict = fetcher.fetch_multiple(test_tickers)
    print(f"   Fetched data for {len(data_dict)} tickers")
    
    if not data_dict:
        print("   ERROR: No data fetched")
        return
    
    # Feature engineering
    print("\n3. Engineering features...")
    for ticker in data_dict:
        data_dict[ticker] = engineer.engineer_features(data_dict[ticker])
    print("   Features calculated: RSI, MACD, Bollinger Bands")
    
    # Build graph
    print("\n4. Building correlation graph...")
    price_matrix = fetcher.get_price_matrix(list(data_dict.keys()))
    returns = price_matrix.pct_change().dropna()
    graph = builder.build_correlation_graph(returns)
    stats = builder.get_graph_stats()
    print(f"   Nodes: {stats['num_nodes']}, Edges: {stats['num_edges']}")
    
    # GAT embeddings
    print("\n5. Computing GAT embeddings...")
    features, tickers, _ = engineer.get_feature_matrix(data_dict)
    current_features = features[:, -1, :]  # Last timestep
    
    # Handle NaN
    current_features = np.nan_to_num(current_features, 0)
    
    adj = builder.get_adjacency_matrix(sparse_format=False)
    gat = NumpyGAT(in_features=current_features.shape[1], out_features=16, num_heads=2)
    embeddings = gat.get_embeddings(current_features, adj)
    print(f"   Embedding shape: {embeddings.shape}")
    
    # Generate allocation
    print("\n6. Generating portfolio allocation...")
    recent_returns = returns.iloc[-20:].mean().values
    
    # Simple score based on returns and embedding magnitude
    scores = recent_returns + 0.1 * np.linalg.norm(embeddings, axis=1)[:len(recent_returns)]
    scores = np.maximum(scores, 0)
    weights = scores / (scores.sum() + 1e-10)
    
    allocation = dict(zip(list(data_dict.keys()), weights.tolist()))
    
    print("\n   Portfolio Allocation:")
    print("   " + "-" * 30)
    for ticker, weight in sorted(allocation.items(), key=lambda x: -x[1]):
        bar = "=" * int(weight * 30)
        print(f"   {ticker:6} [{bar:30}] {weight:6.2%}")
    
    # Save results
    print("\n7. Saving results...")
    output_path = storage.save_portfolio_weights(
        allocation,
        metadata={"test": True, "timestamp": datetime.now().isoformat()}
    )
    print(f"   Saved to: {output_path}")
    
    print("\n" + "=" * 40)
    print("Integration test completed successfully!")
    
    return allocation


def run_headless_pipeline(ticker_file: str) -> Dict[str, float]:
    """
    Run optimization pipeline in headless mode.
    
    Args:
        ticker_file: Path to ticker file (CSV/XLSX)
        
    Returns:
        Portfolio allocation dictionary
    """
    logger.info(f"Running headless pipeline with {ticker_file}")
    
    # Initialize
    fetcher = TickerDataFetcher()
    engineer = FeatureEngineer()
    builder = DynamicGraphBuilder()
    storage = LocalStorage()
    
    # Load tickers
    tickers = fetcher.load_tickers_from_file(ticker_file)
    logger.info(f"Loaded {len(tickers)} tickers")
    
    # Fetch data
    def progress(c, t, tk):
        if c % 5 == 0:
            logger.info(f"Fetching {c}/{t}: {tk}")
    
    data_dict = fetcher.fetch_multiple(tickers, progress_callback=progress)
    
    if not data_dict:
        raise ValueError("No data fetched")
    
    # Feature engineering
    logger.info("Engineering features...")
    for ticker in data_dict:
        data_dict[ticker] = engineer.engineer_features(data_dict[ticker])
    
    # Build graph
    logger.info("Building correlation graph...")
    price_matrix = fetcher.get_price_matrix(list(data_dict.keys()))
    returns = price_matrix.pct_change().dropna()
    builder.build_correlation_graph(returns)
    
    # Get embeddings
    logger.info("Computing embeddings...")
    features, tickers_list, _ = engineer.get_feature_matrix(data_dict)
    current_features = np.nan_to_num(features[:, -1, :], 0)
    
    adj = builder.get_adjacency_matrix(sparse_format=False)
    gat = NumpyGAT(in_features=current_features.shape[1])
    embeddings = gat.get_embeddings(current_features, adj)
    
    # Generate allocation
    logger.info("Generating allocation...")
    recent_returns = returns.iloc[-20:].mean().values
    
    scores = recent_returns + 0.1 * np.linalg.norm(embeddings, axis=1)[:len(recent_returns)]
    scores = np.maximum(scores, 0)
    weights = scores / (scores.sum() + 1e-10)
    
    allocation = dict(zip(tickers_list, weights.tolist()))
    
    # Save results
    output_path = storage.save_portfolio_weights(
        allocation,
        metadata={"headless": True, "timestamp": datetime.now().isoformat()}
    )
    logger.info(f"Saved results to: {output_path}")
    
    # Print summary
    print("\nPortfolio Allocation:")
    print("-" * 40)
    for ticker, weight in sorted(allocation.items(), key=lambda x: -x[1])[:10]:
        print(f"{ticker:8} {weight:8.2%}")
    print(f"\nSaved to: {output_path}")
    
    return allocation


def run_full_pipeline(
    ticker_file: str,
    train_episodes: int = 100,
    use_prophet: bool = True,
) -> Dict[str, Any]:
    """
    Run full optimization pipeline with RL training.
    
    Args:
        ticker_file: Path to ticker file
        train_episodes: Number of training episodes
        use_prophet: Whether to use Prophet for forecasting
        
    Returns:
        Results dictionary
    """
    from smartportfolio.rl import PortfolioEnv, HierarchicalAgent, RewardCalculator
    
    logger.info("Starting full optimization pipeline...")
    
    # Initialize
    fetcher = TickerDataFetcher()
    engineer = FeatureEngineer()
    builder = DynamicGraphBuilder()
    preprocessor = DataPreprocessor()
    storage = LocalStorage()
    
    # Load and fetch
    tickers = fetcher.load_tickers_from_file(ticker_file)
    data_dict = fetcher.fetch_multiple(tickers)
    
    if not data_dict:
        raise ValueError("No data fetched")
    
    # Feature engineering
    for ticker in data_dict:
        data_dict[ticker] = engineer.engineer_features(data_dict[ticker])
    
    # Build graph
    price_matrix = fetcher.get_price_matrix(list(data_dict.keys()))
    returns = price_matrix.pct_change().dropna()
    builder.build_correlation_graph(returns)
    
    # Prepare RL data
    features, tickers_list, _ = engineer.get_feature_matrix(data_dict)
    prices = price_matrix.values
    
    # Align dimensions
    min_len = min(features.shape[1], len(prices))
    features = features[:, -min_len:, :]
    prices = prices[-min_len:]
    
    # Create environment
    env = PortfolioEnv(
        prices=prices,
        features=features.transpose(1, 0, 2),  # (timesteps, assets, features)
        tickers=tickers_list,
    )
    
    # Create and train agent
    obs_dim = env.observation_space.shape[0]
    agent = HierarchicalAgent(
        num_assets=len(tickers_list) + 1,
        feature_dim=obs_dim,
    )
    
    logger.info(f"Training agent for {train_episodes * 100} timesteps...")
    agent.train(env, total_timesteps=train_episodes * 100)
    
    # Get final allocation
    obs, _ = env.reset()
    action, info = agent.predict(obs, deterministic=True)
    
    # Normalize weights
    weights = np.maximum(action, 0)
    weights = weights / (weights.sum() + 1e-10)
    
    allocation = {}
    for i, ticker in enumerate(tickers_list):
        allocation[ticker] = float(weights[i + 1]) if i + 1 < len(weights) else 0.0
    
    # Get metrics
    metrics = env.get_portfolio_metrics()
    
    # Save
    output_path = storage.save_portfolio_weights(
        allocation,
        metadata={
            "trained": True,
            "episodes": train_episodes,
            "metrics": metrics,
        }
    )
    
    return {
        "allocation": allocation,
        "metrics": metrics,
        "output_path": str(output_path),
        "regime": info.get("regime", "neutral"),
    }


if __name__ == "__main__":
    # Run test
    run_test_pipeline()
