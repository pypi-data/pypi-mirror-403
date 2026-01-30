
import pytest
import numpy as np
from smartportfolio.rl.agent import RegimeDetector

def test_regime_detection_neutral():
    detector = RegimeDetector()
    # Flat returns -> Neutral
    returns = np.zeros(50)
    regime = detector.detect(returns)
    assert regime == "neutral"

def test_regime_detection_volatile():
    detector = RegimeDetector()
    # High variance -> Volatile
    returns = np.random.randn(50) * 0.05
    regime = detector.detect(returns)
    assert regime == "volatile"

def test_regime_detection_bull():
    detector = RegimeDetector()
    # Positive trend -> Bull
    returns = np.linspace(0, 0.05, 50) + np.random.randn(50) * 0.001
    regime = detector.detect(returns)
    assert regime == "bull"

def test_regime_detection_bear():
    detector = RegimeDetector()
    # Negative trend -> Bear
    returns = np.linspace(0, -0.05, 50) + np.random.randn(50) * 0.001
    regime = detector.detect(returns)
    assert regime == "bear"
