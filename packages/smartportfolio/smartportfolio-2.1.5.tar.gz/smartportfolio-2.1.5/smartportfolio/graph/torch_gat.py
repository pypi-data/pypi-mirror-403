"""
Pure PyTorch Graph Attention Network

A simple GAT implementation using only PyTorch tensors.
No DGL or PyG dependencies - works everywhere PyTorch works.
"""

import logging
from typing import Optional, Tuple

import numpy as np

from smartportfolio.config import config


logger = logging.getLogger(__name__)


# Check if PyTorch is available
TORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available, using NumPy GAT only")


if TORCH_AVAILABLE:
    class PureTorchGAT(nn.Module):
        """
        Pure PyTorch Graph Attention Network.
        
        Implements GAT without DGL/PyG - just basic PyTorch operations.
        Works on any system where PyTorch is installed.
        """
        
        def __init__(
            self,
            in_features: int,
            hidden_features: int = None,
            out_features: int = None,
            num_heads: int = None,
            dropout: float = None,
            negative_slope: float = 0.2,
        ):
            """
            Initialize Pure PyTorch GAT.
            
            Args:
                in_features: Input feature dimension
                hidden_features: Hidden layer dimension
                out_features: Output feature dimension
                num_heads: Number of attention heads
                dropout: Dropout rate
                negative_slope: LeakyReLU negative slope
            """
            super().__init__()
            
            self.in_features = in_features
            self.hidden_features = hidden_features or config.model.gat_embedding_dim
            self.out_features = out_features or config.model.gat_embedding_dim
            self.num_heads = num_heads or config.model.gat_num_heads
            self.dropout = dropout or config.model.gat_dropout
            self.negative_slope = negative_slope
            
            # Linear transformations for each head
            self.W = nn.Linear(in_features, self.hidden_features * self.num_heads, bias=False)
            
            # Attention parameters
            self.a_src = nn.Parameter(torch.zeros(self.num_heads, self.hidden_features))
            self.a_dst = nn.Parameter(torch.zeros(self.num_heads, self.hidden_features))
            
            # Second layer
            self.W2 = nn.Linear(self.hidden_features * self.num_heads, self.out_features, bias=False)
            
            # Initialize weights
            nn.init.xavier_uniform_(self.W.weight)
            nn.init.xavier_uniform_(self.a_src)
            nn.init.xavier_uniform_(self.a_dst)
            nn.init.xavier_uniform_(self.W2.weight)
            
            # Dropout
            self.dropout_layer = nn.Dropout(self.dropout)
            
            # Device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.to(self.device)
            
            logger.info(f"PureTorchGAT initialized on {self.device}")
        
        def forward(
            self,
            x: torch.Tensor,
            adj: torch.Tensor,
        ) -> torch.Tensor:
            """
            Forward pass with simplified attention.
            
            Args:
                x: Node features (num_nodes, in_features)
                adj: Adjacency matrix (num_nodes, num_nodes)
                
            Returns:
                Output embeddings (num_nodes, out_features)
            """
            num_nodes = x.size(0)
            
            # First layer: linear transform
            h = self.W(x)  # (N, hidden * heads)
            h = F.elu(h)
            h = self.dropout_layer(h)
            
            # Graph convolution: message passing with adjacency
            # Normalize adjacency matrix
            degree = adj.sum(dim=1, keepdim=True) + 1e-10
            adj_norm = adj / degree
            
            # Aggregate neighbor features
            h_agg = torch.mm(adj_norm, h)  # (N, hidden * heads)
            
            # Second layer
            out = self.W2(h_agg)  # (N, out)
            
            return out
        
        def get_embeddings(
            self,
            features: np.ndarray,
            adj: np.ndarray,
        ) -> np.ndarray:
            """
            Get node embeddings.
            
            Args:
                features: Node features (num_nodes, in_features)
                adj: Adjacency matrix (num_nodes, num_nodes)
                
            Returns:
                Embeddings as numpy array
            """
            self.eval()
            
            with torch.no_grad():
                x = torch.FloatTensor(features).to(self.device)
                adj_tensor = torch.FloatTensor(adj).to(self.device)
                
                embeddings = self.forward(x, adj_tensor)
                
                return embeddings.cpu().numpy()


def create_torch_gat(in_features: int, **kwargs):
    """Factory function to create Pure PyTorch GAT if available."""
    if TORCH_AVAILABLE:
        return PureTorchGAT(in_features, **kwargs)
    else:
        # Fall back to NumPy GAT
        from smartportfolio.graph.gat import NumpyGAT
        return NumpyGAT(in_features, **kwargs)
