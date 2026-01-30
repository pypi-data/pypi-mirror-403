"""
DGL-based Graph Attention Network

Uses Deep Graph Library for optimized GNN operations.
Falls back to NumPy GAT if DGL is not available.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import numpy as np

from smartportfolio.config import config


logger = logging.getLogger(__name__)


# Check if DGL is available - catch ALL errors including DLL loading failures
DGL_AVAILABLE = False
try:
    import dgl
    from dgl.nn.pytorch import GATConv
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    DGL_AVAILABLE = True
    logger.info("DGL loaded successfully")
except Exception as e:
    # Catch ImportError, FileNotFoundError, OSError, etc.
    logger.warning(f"DGL not available ({type(e).__name__}), using NumPy GAT fallback")


class DGLGATEncoder(nn.Module if DGL_AVAILABLE else object):
    """
    Graph Attention Network using DGL's GATConv.
    
    Features:
    - Multi-head attention with configurable heads
    - Feature and attention dropout
    - Residual connections
    - GPU acceleration when available
    """
    
    def __init__(
        self,
        in_feats: int,
        hidden_feats: int = None,
        out_feats: int = None,
        num_heads: int = None,
        feat_drop: float = None,
        attn_drop: float = None,
        negative_slope: float = 0.2,
        residual: bool = True,
        activation: str = "elu",
    ):
        """
        Initialize DGL GAT encoder.
        
        Args:
            in_feats: Input feature dimension
            hidden_feats: Hidden layer dimension
            out_feats: Output feature dimension
            num_heads: Number of attention heads
            feat_drop: Feature dropout rate
            attn_drop: Attention dropout rate
            negative_slope: LeakyReLU negative slope
            residual: Whether to use residual connections
            activation: Activation function ('elu', 'relu', 'leaky_relu')
        """
        if not DGL_AVAILABLE:
            raise ImportError("DGL is required for DGLGATEncoder. Install with: pip install dgl")
        
        super().__init__()
        
        self.in_feats = in_feats
        self.hidden_feats = hidden_feats or config.model.gat_embedding_dim
        self.out_feats = out_feats or config.model.gat_embedding_dim
        self.num_heads = num_heads or config.model.gat_num_heads
        self.feat_drop = feat_drop or config.model.gat_dropout
        self.attn_drop = attn_drop or config.model.gat_dropout
        
        # First GAT layer: multi-head
        self.gat1 = GATConv(
            in_feats=in_feats,
            out_feats=self.hidden_feats,
            num_heads=self.num_heads,
            feat_drop=self.feat_drop,
            attn_drop=self.attn_drop,
            negative_slope=negative_slope,
            residual=residual,
            activation=None,  # Apply activation after
            allow_zero_in_degree=True,
        )
        
        # Second GAT layer: concatenated heads -> single output
        self.gat2 = GATConv(
            in_feats=self.hidden_feats * self.num_heads,  # Concatenated heads
            out_feats=self.out_feats,
            num_heads=1,  # Single head for final output
            feat_drop=self.feat_drop,
            attn_drop=self.attn_drop,
            negative_slope=negative_slope,
            residual=False,
            activation=None,
            allow_zero_in_degree=True,
        )
        
        # Activation
        if activation == "elu":
            self.activation = F.elu
        elif activation == "relu":
            self.activation = F.relu
        elif activation == "leaky_relu":
            self.activation = lambda x: F.leaky_relu(x, negative_slope)
        else:
            self.activation = lambda x: x
        
        # Move to device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.to(self.device)
        
        logger.info(f"DGLGATEncoder initialized on {self.device}")
    
    def forward(
        self,
        g: 'dgl.DGLGraph',
        features: torch.Tensor,
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            g: DGL graph
            features: Node features (num_nodes, in_feats)
            
        Returns:
            Output embeddings (num_nodes, out_feats)
        """
        # First GAT layer
        h = self.gat1(g, features)  # (num_nodes, num_heads, hidden_feats)
        h = h.flatten(1)  # (num_nodes, num_heads * hidden_feats)
        h = self.activation(h)
        
        # Second GAT layer
        h = self.gat2(g, h)  # (num_nodes, 1, out_feats)
        h = h.squeeze(1)  # (num_nodes, out_feats)
        
        return h
    
    def get_embeddings(
        self,
        g: 'dgl.DGLGraph',
        features: np.ndarray,
    ) -> np.ndarray:
        """
        Get node embeddings from graph and features.
        
        Args:
            g: DGL graph
            features: Node features as numpy array
            
        Returns:
            Embeddings as numpy array
        """
        self.eval()
        
        with torch.no_grad():
            # Convert to tensor
            if isinstance(features, np.ndarray):
                features = torch.FloatTensor(features).to(self.device)
            
            # Move graph to device
            g = g.to(self.device)
            
            # Forward pass
            embeddings = self.forward(g, features)
            
            return embeddings.cpu().numpy()
    
    def get_attention_weights(
        self,
        g: 'dgl.DGLGraph',
        features: np.ndarray,
    ) -> np.ndarray:
        """
        Get attention weights for visualization.
        
        Args:
            g: DGL graph
            features: Node features
            
        Returns:
            Attention weights as numpy array
        """
        self.eval()
        
        with torch.no_grad():
            if isinstance(features, np.ndarray):
                features = torch.FloatTensor(features).to(self.device)
            
            g = g.to(self.device)
            
            # Get attention from first layer
            _, attention = self.gat1(g, features, get_attention=True)
            
            return attention.cpu().numpy()


class DGLGraphWrapper:
    """
    Wrapper for DGL graph operations with fallback to NumPy.
    """
    
    def __init__(self):
        self.dgl_available = DGL_AVAILABLE
        self.encoder = None
    
    def create_encoder(self, in_feats: int, **kwargs) -> Any:
        """
        Create GAT encoder (DGL if available, NumPy fallback).
        
        Args:
            in_feats: Input feature dimension
            **kwargs: Additional arguments
            
        Returns:
            GAT encoder instance
        """
        if self.dgl_available:
            self.encoder = DGLGATEncoder(in_feats, **kwargs)
            return self.encoder
        else:
            # Fallback to NumPy implementation
            from smartportfolio.graph.gat import NumpyGAT
            self.encoder = NumpyGAT(in_feats, **kwargs)
            return self.encoder
    
    def networkx_to_dgl(self, nx_graph) -> 'dgl.DGLGraph':
        """
        Convert NetworkX graph to DGL graph.
        
        Args:
            nx_graph: NetworkX graph
            
        Returns:
            DGL graph
        """
        if not self.dgl_available:
            raise ImportError("DGL required for graph conversion")
        
        # Create DGL graph from NetworkX
        g = dgl.from_networkx(nx_graph)
        
        # Add self-loops if not present
        g = dgl.add_self_loop(g)
        
        return g
    
    def adjacency_to_dgl(
        self,
        adjacency: np.ndarray,
        add_self_loops: bool = True,
    ) -> 'dgl.DGLGraph':
        """
        Create DGL graph from adjacency matrix.
        
        Args:
            adjacency: Adjacency matrix (N, N)
            add_self_loops: Whether to add self-loops
            
        Returns:
            DGL graph
        """
        if not self.dgl_available:
            raise ImportError("DGL required for graph creation")
        
        # Get edges from adjacency
        src, dst = np.nonzero(adjacency)
        
        # Create graph
        g = dgl.graph((src, dst))
        
        # Add edge weights
        edge_weights = adjacency[src, dst]
        g.edata["weight"] = torch.FloatTensor(edge_weights)
        
        # Add self-loops
        if add_self_loops:
            g = dgl.add_self_loop(g)
        
        return g
    
    def get_embeddings(
        self,
        graph,
        features: np.ndarray,
    ) -> np.ndarray:
        """
        Get embeddings from graph and features.
        
        Handles both DGL and NumPy backends.
        
        Args:
            graph: DGL graph or adjacency matrix
            features: Node features
            
        Returns:
            Node embeddings
        """
        if self.encoder is None:
            self.create_encoder(features.shape[1])
        
        if self.dgl_available:
            # DGL path
            if not isinstance(graph, dgl.DGLGraph):
                graph = self.adjacency_to_dgl(graph)
            return self.encoder.get_embeddings(graph, features)
        else:
            # NumPy fallback
            return self.encoder.get_embeddings(features, graph)


# Export
def create_dgl_encoder(in_feats: int, **kwargs):
    """Factory function to create DGL encoder."""
    wrapper = DGLGraphWrapper()
    return wrapper.create_encoder(in_feats, **kwargs)
