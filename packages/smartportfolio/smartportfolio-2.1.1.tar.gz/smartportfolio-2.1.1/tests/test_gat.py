
import pytest
import torch
import numpy as np
from smartportfolio.graph.torch_gat import PureTorchGAT, create_torch_gat

def test_gat_initialization():
    gat = PureTorchGAT(in_features=10, hidden_features=16, out_features=8, num_heads=2)
    assert gat is not None
    assert gat.W.weight.shape == (32, 10)  # hidden * heads, in

def test_gat_forward_shape():
    gat = PureTorchGAT(in_features=10, hidden_features=8, out_features=4, num_heads=2)
    x = torch.randn(5, 10)
    adj = torch.eye(5)
    
    out = gat(x, adj)
    assert out.shape == (5, 4)

def test_factory_function():
    gat = create_torch_gat(in_features=10)
    assert gat is not None
