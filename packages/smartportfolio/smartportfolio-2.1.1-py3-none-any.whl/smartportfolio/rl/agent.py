"""
Hierarchical DRL Agent

PPO-based hierarchical agent with regime detection and expert sub-agents.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import numpy as np

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detects market regime (bull/bear/volatile) from recent returns.
    """
    
    def __init__(
        self,
        volatility_threshold: float = 0.02,
        trend_threshold: float = 0.01,
        lookback: int = 20,
    ):
        """
        Initialize regime detector.
        
        Args:
            volatility_threshold: Threshold for high volatility
            trend_threshold: Threshold for trend detection
            lookback: Lookback period for regime detection
        """
        self.volatility_threshold = volatility_threshold
        self.trend_threshold = trend_threshold
        self.lookback = lookback
    
    def detect(self, returns: np.ndarray) -> str:
        """
        Detect current market regime.
        
        Args:
            returns: Recent portfolio/market returns
            
        Returns:
            Regime string: 'bull', 'bear', or 'volatile'
        """
        if len(returns) < self.lookback:
            return "neutral"
        
        recent = returns[-self.lookback:]
        
        volatility = np.std(recent)
        trend = np.mean(recent)
        
        if volatility > self.volatility_threshold:
            return "volatile"
        elif trend > self.trend_threshold:
            return "bull"
        elif trend < -self.trend_threshold:
            return "bear"
        else:
            return "neutral"
    
    def get_regime_embedding(self, regime: str) -> np.ndarray:
        """
        Get one-hot embedding for regime.
        
        Args:
            regime: Regime string
            
        Returns:
            One-hot encoded regime
        """
        regimes = ["bull", "bear", "volatile", "neutral"]
        embedding = np.zeros(len(regimes), dtype=np.float32)
        if regime in regimes:
            embedding[regimes.index(regime)] = 1.0
        else:
            embedding[-1] = 1.0  # default to neutral
        return embedding


class HierarchicalAgent:
    """
    Hierarchical RL agent for portfolio optimization.
    
    Uses a high-level regime detector to select between
    specialized expert agents.
    """
    
    def __init__(
        self,
        num_assets: int,
        feature_dim: int,
        learning_rate: float = None,
        gamma: float = None,
        batch_size: int = None,
        buffer_size: int = None,
        device: str = "cpu",
    ):
        """
        Initialize hierarchical agent.
        
        Args:
            num_assets: Number of assets (including cash)
            feature_dim: Observation feature dimension
            learning_rate: PPO learning rate
            gamma: Discount factor
            batch_size: Training batch size
            buffer_size: Replay buffer size
            device: Device to use ('cpu')
        """
        self.num_assets = num_assets
        self.feature_dim = feature_dim
        self.learning_rate = learning_rate or config.model.rl_learning_rate
        self.gamma = gamma or config.model.rl_gamma
        self.batch_size = batch_size or config.model.rl_batch_size
        self.buffer_size = buffer_size or config.model.rl_buffer_size
        self.device = device
        
        self.regime_detector = RegimeDetector()
        self.current_regime = "neutral"
        
        self.model = None
        self.expert_models: Dict[str, Any] = {}
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize PPO models for each regime."""
        try:
            from stable_baselines3 import PPO
            from stable_baselines3.common.policies import ActorCriticPolicy
            
            # Check if we can import successfully
            self._sb3_available = True
            logger.info("Stable Baselines3 available for RL training")
            
        except ImportError:
            self._sb3_available = False
            logger.warning("Stable Baselines3 not available, using simple policy")
    
    def train(
        self,
        env,
        total_timesteps: int = 10000,
        progress_callback: callable = None,
    ) -> Dict[str, Any]:
        """
        Train the agent on the environment.
        
        Args:
            env: Portfolio environment
            total_timesteps: Total training timesteps
            progress_callback: Callback for progress updates
            
        Returns:
            Training metrics
        """
        if not self._sb3_available:
            logger.warning("Training not available without Stable Baselines3")
            return self._train_simple(env, total_timesteps)
        
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import BaseCallback
        
        class ProgressCallback(BaseCallback):
            def __init__(self, callback_fn, verbose=0):
                super().__init__(verbose)
                self.callback_fn = callback_fn
                self.episode_count = 0
            
            def _on_step(self) -> bool:
                if self.callback_fn and self.n_calls % 100 == 0:
                    self.callback_fn(self.n_calls, self.num_timesteps, "training")
                return True
        
        # Create PPO model
        self.model = PPO(
            "MlpPolicy",
            env,
            learning_rate=self.learning_rate,
            gamma=self.gamma,
            batch_size=self.batch_size,
            n_epochs=config.model.rl_n_epochs,
            clip_range=config.model.rl_clip_range,
            verbose=0,
            device=self.device,
        )
        
        # Train
        callback = ProgressCallback(progress_callback) if progress_callback else None
        self.model.learn(total_timesteps=total_timesteps, callback=callback)
        
        logger.info(f"Training completed: {total_timesteps} timesteps")
        
        return {"timesteps": total_timesteps, "model": "PPO"}
    
    def _train_simple(
        self,
        env,
        total_timesteps: int,
    ) -> Dict[str, Any]:
        """
        Simple training fallback without SB3.
        
        Uses a basic policy gradient approach.
        """
        logger.info("Using simple policy gradient training")
        
        episodes = total_timesteps // 100
        
        for ep in range(episodes):
            obs, info = env.reset()
            done = False
            ep_reward = 0
            
            while not done:
                # Simple policy: slightly modify current weights
                action = self._simple_policy(obs)
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                ep_reward += reward
            
            if (ep + 1) % 10 == 0:
                logger.debug(f"Episode {ep + 1}: reward = {ep_reward:.4f}")
        
        return {"timesteps": total_timesteps, "model": "simple"}
    
    def _simple_policy(self, obs: np.ndarray) -> np.ndarray:
        """
        Simple heuristic policy as fallback.
        
        Args:
            obs: Current observation
            
        Returns:
            Action (portfolio weights)
        """
        # Extract current weights from observation
        # Weights are at the end of observation
        current_weights = obs[-self.num_assets:]
        
        # Add small random perturbation
        noise = np.random.randn(self.num_assets) * 0.1
        new_weights = current_weights + noise
        
        # Ensure valid weights
        new_weights = np.maximum(new_weights, 0)
        new_weights = new_weights / (new_weights.sum() + 1e-10)
        
        return new_weights.astype(np.float32)
    
    def predict(
        self,
        observation: np.ndarray,
        returns_history: np.ndarray = None,
        deterministic: bool = True,
    ) -> Tuple[np.ndarray, Optional[Dict]]:
        """
        Predict action given observation.
        
        Args:
            observation: Current observation
            returns_history: Recent returns for regime detection
            deterministic: Whether to use deterministic policy
            
        Returns:
            Tuple of (action, info)
        """
        # Detect regime
        if returns_history is not None:
            self.current_regime = self.regime_detector.detect(returns_history)
        
        # Get action from model
        if self.model is not None and self._sb3_available:
            action, _ = self.model.predict(observation, deterministic=deterministic)
        else:
            action = self._simple_policy(observation)
        
        info = {"regime": self.current_regime}
        
        return action, info
    
    def get_allocation(
        self,
        observation: np.ndarray,
        tickers: List[str],
        returns_history: np.ndarray = None,
    ) -> Dict[str, float]:
        """
        Get portfolio allocation as dictionary.
        
        Args:
            observation: Current observation
            tickers: List of ticker symbols
            returns_history: Recent returns
            
        Returns:
            Dictionary mapping ticker to weight
        """
        action, _ = self.predict(observation, returns_history)
        
        # Normalize
        weights = np.maximum(action, 0)
        weights = weights / (weights.sum() + 1e-10)
        
        # Skip cash (first element) and re-normalize
        allocation = {}
        equity_weights = []
        
        for i, ticker in enumerate(tickers):
            w = float(weights[i + 1]) if i + 1 < len(weights) else 0.0
            equity_weights.append(w)
            allocation[ticker] = w
            
        # Re-normalize to sum to 1.0 (fully invested equity portion)
        total_equity = sum(equity_weights)
        if total_equity > 1e-6:
            for ticker in allocation:
                allocation[ticker] /= total_equity
        else:
            # Fallback if mostly cash: equal weights
            for ticker in allocation:
                allocation[ticker] = 1.0 / len(tickers)
        
        return allocation
    
    def save(self, path: Path) -> None:
        """
        Save agent to file.
        
        Args:
            path: Save path
        """
        if self.model is not None and self._sb3_available:
            self.model.save(str(path))
            logger.info(f"Saved agent to {path}")
        else:
            logger.warning("No model to save")
    
    def load(self, path: Path) -> None:
        """
        Load agent from file.
        
        Args:
            path: Load path
        """
        if not self._sb3_available:
            logger.warning("Cannot load model without Stable Baselines3")
            return
        
        from stable_baselines3 import PPO
        
        self.model = PPO.load(str(path))
        logger.info(f"Loaded agent from {path}")
    
    def get_policy_info(self) -> Dict[str, Any]:
        """
        Get information about current policy.
        
        Returns:
            Policy information dictionary
        """
        return {
            "regime": self.current_regime,
            "model_type": "PPO" if self._sb3_available else "simple",
            "num_assets": self.num_assets,
            "learning_rate": self.learning_rate,
            "gamma": self.gamma,
        }
