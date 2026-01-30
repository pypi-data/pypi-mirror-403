
import pytest
import numpy as np
from smartportfolio.rl.agent import HierarchicalAgent

def test_agent_initialization():
    agent = HierarchicalAgent(num_assets=5, feature_dim=10)
    assert agent is not None
    assert agent.num_assets == 5

def test_agent_get_allocation():
    agent = HierarchicalAgent(num_assets=5, feature_dim=10)
    obs = np.random.randn(15)  # 10 + 5
    tickers = ["A", "B", "C", "D", "E"]
    
    alloc = agent.get_allocation(obs, tickers)
    
    assert len(alloc) == 5
    assert sum(alloc.values()) == pytest.approx(1.0)
    assert all(w >= 0 for w in alloc.values())

def test_agent_predict():
    agent = HierarchicalAgent(num_assets=5, feature_dim=10)
    obs = np.random.randn(15)
    action, info = agent.predict(obs)
    
    assert len(action) == 5
    assert "regime" in info
