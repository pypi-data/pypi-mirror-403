"""
Portfolio Trading Environment

Custom Gymnasium environment for portfolio optimization with
action masking and transaction cost modeling.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class PortfolioEnv(gym.Env):
    """
    Portfolio optimization environment for RL training.
    
    State: Asset features + current portfolio weights
    Action: Target portfolio weights (continuous)
    Reward: Risk-adjusted returns with transaction costs
    """
    
    metadata = {"render_modes": ["human"]}
    
    def __init__(
        self,
        prices: np.ndarray,
        features: np.ndarray,
        tickers: List[str],
        initial_cash: float = 100000.0,
        transaction_cost: float = None,
        window_size: int = 20,
        reward_type: str = "sharpe",
    ):
        """
        Initialize portfolio environment.
        
        Args:
            prices: Price matrix (num_timesteps, num_assets)
            features: Feature matrix (num_timesteps, num_assets, num_features)
            tickers: List of ticker symbols
            initial_cash: Starting portfolio value
            transaction_cost: Transaction cost rate
            window_size: Lookback window for features
            reward_type: Reward calculation method
        """
        super().__init__()
        
        self.prices = prices.astype(np.float32)
        self.features = features.astype(np.float32)
        self.tickers = tickers
        self.num_assets = len(tickers)
        self.num_timesteps = len(prices)
        self.num_features = features.shape[-1] if len(features.shape) > 2 else 1
        
        self.initial_cash = initial_cash
        self.transaction_cost = transaction_cost or config.model.transaction_cost_rate
        self.window_size = window_size
        self.reward_type = reward_type
        
        # Action space: portfolio weights (continuous, sum to 1)
        # Add cash as first asset
        self.action_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(self.num_assets + 1,),
            dtype=np.float32,
        )
        
        # Observation space: flattened features + current weights
        obs_dim = self.num_assets * self.num_features + self.num_assets + 1
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_dim,),
            dtype=np.float32,
        )
        
        # State variables
        self.current_step = 0
        self.portfolio_value = initial_cash
        self.weights = np.zeros(self.num_assets + 1, dtype=np.float32)
        self.weights[0] = 1.0  # Start with all cash
        
        self.returns_history = []
        self.weights_history = []
        self.value_history = []
        
        # Action mask (which assets are tradeable)
        self.action_mask = np.ones(self.num_assets + 1, dtype=np.float32)
    
    def _get_observation(self) -> np.ndarray:
        """Get current observation."""
        # Get current features
        if len(self.features.shape) == 3:
            # (timesteps, assets, features)
            current_features = self.features[self.current_step]
        else:
            # (timesteps, assets) - single feature
            current_features = self.features[self.current_step].reshape(-1, 1)
        
        # Flatten features
        flat_features = current_features.flatten()
        
        # Combine with current weights
        obs = np.concatenate([flat_features, self.weights]).astype(np.float32)
        
        # Handle NaN
        obs = np.nan_to_num(obs, 0.0)
        
        return obs
    
    def _normalize_action(self, action: np.ndarray) -> np.ndarray:
        """Normalize action to valid portfolio weights."""
        # Apply action mask
        action = action * self.action_mask
        
        # Ensure non-negative
        action = np.maximum(action, 0)
        
        # Normalize to sum to 1
        action_sum = action.sum()
        if action_sum > 0:
            action = action / action_sum
        else:
            # Default to all cash
            action = np.zeros_like(action)
            action[0] = 1.0
        
        return action.astype(np.float32)
    
    def _calculate_returns(
        self,
        old_prices: np.ndarray,
        new_prices: np.ndarray,
    ) -> np.ndarray:
        """Calculate simple returns."""
        returns = (new_prices - old_prices) / (old_prices + 1e-10)
        return returns.astype(np.float32)
    
    def _calculate_transaction_cost(
        self,
        old_weights: np.ndarray,
        new_weights: np.ndarray,
    ) -> float:
        """Calculate transaction cost for rebalancing."""
        turnover = np.abs(new_weights - old_weights).sum()
        cost = turnover * self.transaction_cost
        return float(cost)
    
    def _calculate_reward(
        self,
        portfolio_return: float,
        transaction_cost: float,
    ) -> float:
        """Calculate step reward."""
        net_return = portfolio_return - transaction_cost
        
        if self.reward_type == "sharpe":
            # Approximate Sharpe contribution
            self.returns_history.append(net_return)
            if len(self.returns_history) >= 5:
                recent_returns = np.array(self.returns_history[-20:])
                mean_ret = np.mean(recent_returns)
                std_ret = np.std(recent_returns) + 1e-10
                reward = mean_ret / std_ret
            else:
                reward = net_return
        elif self.reward_type == "return":
            reward = net_return
        elif self.reward_type == "log_return":
            reward = np.log(1 + net_return + 1e-10)
        else:
            reward = net_return
        
        return float(reward)
    
    def step(
        self,
        action: np.ndarray,
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.
        
        Args:
            action: Target portfolio weights
            
        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        # Normalize action to valid weights
        target_weights = self._normalize_action(action)
        
        # Current prices (before action)
        current_prices = self.prices[self.current_step]
        
        # Calculate transaction cost
        tx_cost = self._calculate_transaction_cost(self.weights, target_weights)
        
        # Update weights
        old_weights = self.weights.copy()
        self.weights = target_weights
        
        # Move to next step
        self.current_step += 1
        terminated = self.current_step >= self.num_timesteps - 1
        
        # Get new prices
        new_prices = self.prices[self.current_step]
        
        # Calculate asset returns
        asset_returns = self._calculate_returns(current_prices, new_prices)
        
        # Portfolio return (weighted sum of asset returns)
        # Skip cash (index 0) in return calculation
        portfolio_return = np.sum(self.weights[1:] * asset_returns)
        
        # Update portfolio value
        self.portfolio_value *= (1 + portfolio_return - tx_cost)
        
        # Calculate reward
        reward = self._calculate_reward(portfolio_return, tx_cost)
        
        # Record history
        self.weights_history.append(self.weights.copy())
        self.value_history.append(self.portfolio_value)
        
        # Get observation
        obs = self._get_observation()
        
        # Info dict
        info = {
            "portfolio_value": self.portfolio_value,
            "portfolio_return": portfolio_return,
            "transaction_cost": tx_cost,
            "weights": self.weights.copy(),
            "step": self.current_step,
        }
        
        return obs, reward, terminated, False, info
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset environment to initial state.
        
        Args:
            seed: Random seed
            options: Reset options
            
        Returns:
            Tuple of (observation, info)
        """
        super().reset(seed=seed)
        
        # Reset state
        self.current_step = self.window_size  # Start after warmup
        self.portfolio_value = self.initial_cash
        self.weights = np.zeros(self.num_assets + 1, dtype=np.float32)
        self.weights[0] = 1.0  # All cash
        
        self.returns_history = []
        self.weights_history = [self.weights.copy()]
        self.value_history = [self.portfolio_value]
        
        obs = self._get_observation()
        info = {"step": self.current_step}
        
        return obs, info
    
    def set_action_mask(self, mask: np.ndarray) -> None:
        """
        Set action mask to restrict tradeable assets.
        
        Args:
            mask: Binary mask (1 = tradeable, 0 = not tradeable)
        """
        mask = np.array(mask, dtype=np.float32)
        if len(mask) == self.num_assets:
            # Add cash position
            self.action_mask = np.concatenate([[1.0], mask])
        else:
            self.action_mask = mask
    
    def get_portfolio_metrics(self) -> Dict[str, float]:
        """
        Calculate portfolio performance metrics.
        
        Returns:
            Dictionary of metrics
        """
        if len(self.value_history) < 2:
            return {}
        
        values = np.array(self.value_history)
        returns = np.diff(values) / values[:-1]
        
        total_return = (values[-1] - values[0]) / values[0]
        
        # Annualized metrics (assuming daily data)
        trading_days = len(returns)
        annual_factor = 252 / max(trading_days, 1)
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Sharpe ratio (assuming 0 risk-free rate)
        sharpe = np.sqrt(252) * mean_return / (std_return + 1e-10)
        
        # Maximum drawdown
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (running_max - cumulative) / running_max
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_drawdown),
            "volatility": float(std_return * np.sqrt(252)),
            "num_trades": len(self.weights_history),
        }
    
    def render(self) -> None:
        """Render environment state."""
        print(f"Step: {self.current_step}")
        print(f"Portfolio Value: ${self.portfolio_value:,.2f}")
        print(f"Weights: {dict(zip(['Cash'] + self.tickers, self.weights))}")
