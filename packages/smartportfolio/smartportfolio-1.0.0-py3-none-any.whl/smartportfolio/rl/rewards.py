"""
Reward Calculation Module

Implements various reward functions for portfolio optimization.
"""

import logging
from typing import Dict, List, Optional

import numpy as np

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class RewardCalculator:
    """
    Calculates rewards for portfolio optimization RL.
    
    Supports multiple reward formulations:
    - Sharpe ratio based
    - Log returns
    - Risk-adjusted returns
    - Custom combinations
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.0,
        transaction_cost_rate: float = None,
        risk_penalty: float = 0.1,
        turnover_penalty: float = 0.01,
    ):
        """
        Initialize reward calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate
            transaction_cost_rate: Transaction cost rate
            risk_penalty: Penalty for volatility
            turnover_penalty: Penalty for portfolio turnover
        """
        self.risk_free_rate = risk_free_rate
        self.transaction_cost_rate = (
            transaction_cost_rate or config.model.transaction_cost_rate
        )
        self.risk_penalty = risk_penalty
        self.turnover_penalty = turnover_penalty
        
        self.returns_buffer: List[float] = []
        self.buffer_size = 60  # For rolling calculations
    
    def calculate_portfolio_return(
        self,
        weights: np.ndarray,
        asset_returns: np.ndarray,
    ) -> float:
        """
        Calculate portfolio return from weights and asset returns.
        
        Args:
            weights: Portfolio weights (excluding cash)
            asset_returns: Return for each asset
            
        Returns:
            Portfolio return
        """
        return float(np.sum(weights * asset_returns))
    
    def calculate_transaction_cost(
        self,
        old_weights: np.ndarray,
        new_weights: np.ndarray,
    ) -> float:
        """
        Calculate transaction cost from portfolio rebalancing.
        
        Args:
            old_weights: Previous portfolio weights
            new_weights: New portfolio weights
            
        Returns:
            Transaction cost
        """
        turnover = np.sum(np.abs(new_weights - old_weights))
        return float(turnover * self.transaction_cost_rate)
    
    def simple_return_reward(
        self,
        portfolio_return: float,
        transaction_cost: float = 0.0,
    ) -> float:
        """
        Simple net return reward.
        
        Args:
            portfolio_return: Portfolio return
            transaction_cost: Transaction cost
            
        Returns:
            Reward value
        """
        return portfolio_return - transaction_cost
    
    def log_return_reward(
        self,
        portfolio_return: float,
        transaction_cost: float = 0.0,
    ) -> float:
        """
        Log return reward (more stable for multiplicative growth).
        
        Args:
            portfolio_return: Portfolio return
            transaction_cost: Transaction cost
            
        Returns:
            Log return reward
        """
        net_return = portfolio_return - transaction_cost
        return float(np.log(1 + net_return + 1e-10))
    
    def sharpe_reward(
        self,
        portfolio_return: float,
        transaction_cost: float = 0.0,
    ) -> float:
        """
        Sharpe ratio based reward using rolling statistics.
        
        Args:
            portfolio_return: Portfolio return
            transaction_cost: Transaction cost
            
        Returns:
            Sharpe-based reward
        """
        net_return = portfolio_return - transaction_cost
        
        # Add to buffer
        self.returns_buffer.append(net_return)
        if len(self.returns_buffer) > self.buffer_size:
            self.returns_buffer.pop(0)
        
        # Calculate rolling Sharpe
        if len(self.returns_buffer) < 5:
            return net_return
        
        returns = np.array(self.returns_buffer)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Daily Sharpe (not annualized for reward signal)
        sharpe = mean_return / (std_return + 1e-10)
        
        return float(sharpe)
    
    def risk_adjusted_reward(
        self,
        portfolio_return: float,
        portfolio_volatility: float,
        transaction_cost: float = 0.0,
    ) -> float:
        """
        Risk-adjusted reward with volatility penalty.
        
        Args:
            portfolio_return: Portfolio return
            portfolio_volatility: Rolling portfolio volatility
            transaction_cost: Transaction cost
            
        Returns:
            Risk-adjusted reward
        """
        net_return = portfolio_return - transaction_cost
        risk_penalty = self.risk_penalty * portfolio_volatility
        
        return float(net_return - risk_penalty)
    
    def combined_reward(
        self,
        portfolio_return: float,
        old_weights: np.ndarray,
        new_weights: np.ndarray,
        volatility: float = None,
    ) -> float:
        """
        Combined reward with all penalties.
        
        Args:
            portfolio_return: Portfolio return
            old_weights: Previous weights
            new_weights: New weights
            volatility: Portfolio volatility (optional)
            
        Returns:
            Combined reward
        """
        # Transaction cost
        tx_cost = self.calculate_transaction_cost(old_weights, new_weights)
        
        # Turnover penalty
        turnover = np.sum(np.abs(new_weights - old_weights))
        turnover_pen = self.turnover_penalty * turnover
        
        # Base reward
        reward = portfolio_return - tx_cost - turnover_pen
        
        # Volatility penalty
        if volatility is not None:
            reward -= self.risk_penalty * volatility
        
        return float(reward)
    
    def calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        annualize: bool = True,
    ) -> float:
        """
        Calculate Sharpe ratio from returns array.
        
        Args:
            returns: Array of returns
            annualize: Whether to annualize (assumes daily data)
            
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        daily_sharpe = (mean_return - self.risk_free_rate / 252) / (std_return + 1e-10)
        
        if annualize:
            return float(daily_sharpe * np.sqrt(252))
        return float(daily_sharpe)
    
    def calculate_sortino_ratio(
        self,
        returns: np.ndarray,
        annualize: bool = True,
    ) -> float:
        """
        Calculate Sortino ratio (downside risk adjusted).
        
        Args:
            returns: Array of returns
            annualize: Whether to annualize
            
        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return float("inf")
        
        downside_std = np.std(downside_returns)
        daily_sortino = (mean_return - self.risk_free_rate / 252) / (downside_std + 1e-10)
        
        if annualize:
            return float(daily_sortino * np.sqrt(252))
        return float(daily_sortino)
    
    def calculate_max_drawdown(
        self,
        portfolio_values: np.ndarray,
    ) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            portfolio_values: Array of portfolio values
            
        Returns:
            Maximum drawdown (as positive number)
        """
        if len(portfolio_values) < 2:
            return 0.0
        
        running_max = np.maximum.accumulate(portfolio_values)
        drawdowns = (running_max - portfolio_values) / running_max
        
        return float(np.max(drawdowns))
    
    def get_performance_metrics(
        self,
        returns: np.ndarray,
        portfolio_values: np.ndarray,
    ) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            returns: Array of returns
            portfolio_values: Array of portfolio values
            
        Returns:
            Dictionary of metrics
        """
        return {
            "total_return": float((portfolio_values[-1] / portfolio_values[0]) - 1),
            "sharpe_ratio": self.calculate_sharpe_ratio(returns),
            "sortino_ratio": self.calculate_sortino_ratio(returns),
            "max_drawdown": self.calculate_max_drawdown(portfolio_values),
            "volatility": float(np.std(returns) * np.sqrt(252)),
            "mean_return": float(np.mean(returns) * 252),
        }
    
    def reset(self):
        """Reset internal buffers."""
        self.returns_buffer = []
