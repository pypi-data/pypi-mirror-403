"""
SmartPortfolio Configuration

Central configuration for colors, paths, model parameters, and constants.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Colors:
    """Neural Terminal Phosphor Color Palette."""
    
    # Backgrounds (The Void)
    DEEP_SPACE_BLACK: str = "#000000"
    TERMINAL_GREY: str = "#121212"
    ACTIVE_GREY: str = "#2e3440"
    
    # Signal Colors (Data & Action)
    BLOOMBERG_AMBER: str = "#FF6A00"
    TICK_GREEN: str = "#00FF41"
    STOP_RED: str = "#FF433D"
    NEURAL_BLUE: str = "#0068FF"
    
    # Text Colors
    TEXT_PRIMARY: str = "#f8f8f2"
    TEXT_MUTED: str = "#888888"
    TEXT_DIM: str = "#555555"
    
    # Border Colors
    BORDER_DEFAULT: str = "#333333"
    BORDER_ACTIVE: str = "#FF6A00"


@dataclass
class ModelConfig:
    """Model hyperparameters optimized for 8GB RAM."""
    
    # GAT Configuration
    gat_embedding_dim: int = 32
    gat_num_heads: int = 4
    gat_dropout: float = 0.1
    
    # Prophet Configuration
    prophet_yearly_seasonality: bool = True
    prophet_weekly_seasonality: bool = True
    prophet_daily_seasonality: bool = False
    prophet_changepoint_prior_scale: float = 0.05
    
    # RL Configuration
    rl_learning_rate: float = 3e-4
    rl_gamma: float = 0.99
    rl_batch_size: int = 64
    rl_buffer_size: int = 10000
    rl_n_epochs: int = 10
    rl_clip_range: float = 0.2
    
    # Training
    train_episodes: int = 100
    eval_episodes: int = 10
    
    # Transaction costs
    transaction_cost_rate: float = 0.001


@dataclass
class DataConfig:
    """Data fetching and processing configuration."""
    
    # Yahoo Finance
    default_period: str = "2y"
    default_interval: str = "1d"
    chunk_size: int = 10  # Process tickers in chunks for memory
    
    # Feature Engineering
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bollinger_period: int = 20
    bollinger_std: int = 2
    
    # Correlation
    correlation_window: int = 60
    correlation_threshold: float = 0.3


@dataclass
class Config:
    """Main configuration class."""
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    outputs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "outputs")
    cache_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "cache")
    models_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "models")
    
    # Sub-configs
    colors: Colors = field(default_factory=Colors)
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)
    
    # App Settings
    app_title: str = "SmartPortfolio"
    app_subtitle: str = "GNN + Prophet + DRL Portfolio Optimization"
    
    def __post_init__(self):
        """Create necessary directories."""
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def get_output_path(self, prefix: str = "portfolio") -> Path:
        """Generate unique output path with timestamp and UUID."""
        import uuid
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{prefix}.csv"
        return self.outputs_dir / filename


# Global config instance
config = Config()
