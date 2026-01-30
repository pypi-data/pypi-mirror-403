"""
NumPy-based Graph Attention Network

Lightweight GAT implementation using pure NumPy operations.
No PyTorch or TensorFlow dependencies.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import sparse

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class NumpyGAT:
    """
    Graph Attention Network implemented in pure NumPy.
    
    This is a lightweight alternative to PyTorch Geometric for
    environments with limited resources or installation constraints.
    
    Implements:
    - Linear transformation of node features
    - Attention score calculation with LeakyReLU
    - Softmax normalization of attention weights
    - Weighted aggregation of neighbor features
    - Multi-head attention (optional)
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int = None,
        num_heads: int = None,
        dropout: float = None,
        alpha: float = 0.2,
        seed: int = 42,
    ):
        """
        Initialize GAT layer.
        
        Args:
            in_features: Input feature dimension
            out_features: Output feature dimension (per head)
            num_heads: Number of attention heads
            dropout: Dropout rate
            alpha: LeakyReLU negative slope
            seed: Random seed for reproducibility
        """
        self.in_features = in_features
        self.out_features = out_features or config.model.gat_embedding_dim
        self.num_heads = num_heads or config.model.gat_num_heads
        self.dropout = dropout or config.model.gat_dropout
        self.alpha = alpha
        
        np.random.seed(seed)
        
        # Initialize weights using Xavier initialization
        self._init_weights()
    
    def _init_weights(self):
        """Initialize learnable parameters."""
        # Weight matrix for linear transformation: W
        # Shape: (num_heads, in_features, out_features)
        std = np.sqrt(2.0 / (self.in_features + self.out_features))
        self.W = np.random.randn(
            self.num_heads, self.in_features, self.out_features
        ).astype(np.float32) * std
        
        # Attention vectors: a
        # Shape: (num_heads, 2 * out_features)
        std_a = np.sqrt(2.0 / (2 * self.out_features))
        self.a = np.random.randn(
            self.num_heads, 2 * self.out_features
        ).astype(np.float32) * std_a
        
        # Bias terms
        self.bias = np.zeros((self.num_heads, self.out_features), dtype=np.float32)
    
    def _leaky_relu(self, x: np.ndarray) -> np.ndarray:
        """LeakyReLU activation."""
        return np.where(x > 0, x, self.alpha * x)
    
    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Numerically stable softmax."""
        x_max = np.max(x, axis=axis, keepdims=True)
        exp_x = np.exp(x - x_max)
        return exp_x / (np.sum(exp_x, axis=axis, keepdims=True) + 1e-10)
    
    def _dropout(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """Apply dropout."""
        if not training or self.dropout == 0:
            return x
        mask = np.random.binomial(1, 1 - self.dropout, x.shape) / (1 - self.dropout)
        return x * mask
    
    def forward(
        self,
        node_features: np.ndarray,
        adjacency: np.ndarray,
        training: bool = False,
    ) -> np.ndarray:
        """
        Forward pass of GAT layer.
        
        Args:
            node_features: Node feature matrix (N, in_features)
            adjacency: Adjacency matrix (N, N) - can be dense or sparse
            training: Whether in training mode (for dropout)
            
        Returns:
            Output features (N, num_heads * out_features) or (N, out_features) if concat=False
        """
        N = node_features.shape[0]
        
        # Convert sparse to dense if needed
        if sparse.issparse(adjacency):
            adjacency = adjacency.toarray()
        
        # Ensure float32
        node_features = node_features.astype(np.float32)
        adjacency = adjacency.astype(np.float32)
        
        # Apply dropout to input
        if training:
            node_features = self._dropout(node_features, training)
        
        head_outputs = []
        
        for head in range(self.num_heads):
            # Linear transformation: Z = X @ W
            # Shape: (N, out_features)
            Z = node_features @ self.W[head]
            
            # Compute attention scores for all pairs
            # Split attention vector into source and target parts
            a_src = self.a[head, :self.out_features]  # (out_features,)
            a_tgt = self.a[head, self.out_features:]  # (out_features,)
            
            # Compute attention contributions
            # e_ij = LeakyReLU(a_src @ z_i + a_tgt @ z_j)
            src_scores = Z @ a_src  # (N,)
            tgt_scores = Z @ a_tgt  # (N,)
            
            # Broadcast to get pairwise scores: (N, N)
            attention_scores = src_scores[:, np.newaxis] + tgt_scores[np.newaxis, :]
            attention_scores = self._leaky_relu(attention_scores)
            
            # Mask non-edges with large negative value
            mask = (adjacency == 0)
            attention_scores = np.where(mask, -1e9, attention_scores)
            
            # Softmax normalization per node
            attention_weights = self._softmax(attention_scores, axis=1)
            
            # Apply dropout to attention weights
            if training:
                attention_weights = self._dropout(attention_weights, training)
            
            # Aggregate neighbor features
            # H' = attention_weights @ Z
            H_prime = attention_weights @ Z  # (N, out_features)
            
            # Add bias
            H_prime = H_prime + self.bias[head]
            
            head_outputs.append(H_prime)
        
        # Concatenate heads
        output = np.concatenate(head_outputs, axis=1)  # (N, num_heads * out_features)
        
        return output
    
    def forward_with_edge_index(
        self,
        node_features: np.ndarray,
        edge_index: Tuple[np.ndarray, np.ndarray],
        num_nodes: int = None,
        training: bool = False,
    ) -> np.ndarray:
        """
        Forward pass using edge index format (COO).
        
        More memory efficient for sparse graphs.
        
        Args:
            node_features: Node features (N, in_features)
            edge_index: Tuple of (source, target) index arrays
            num_nodes: Number of nodes (inferred if None)
            training: Whether in training mode
            
        Returns:
            Output features
        """
        sources, targets = edge_index
        N = num_nodes or node_features.shape[0]
        
        node_features = node_features.astype(np.float32)
        
        if training:
            node_features = self._dropout(node_features, training)
        
        head_outputs = []
        
        for head in range(self.num_heads):
            # Linear transformation
            Z = node_features @ self.W[head]  # (N, out_features)
            
            # Attention vectors
            a_src = self.a[head, :self.out_features]
            a_tgt = self.a[head, self.out_features:]
            
            # Compute attention for edges only
            src_features = Z[sources]  # (E, out_features)
            tgt_features = Z[targets]  # (E, out_features)
            
            # Attention score per edge
            edge_scores = (src_features @ a_src) + (tgt_features @ a_tgt)
            edge_scores = self._leaky_relu(edge_scores)  # (E,)
            
            # Softmax per source node
            # Group edges by source and apply softmax
            max_scores = np.full(N, -np.inf, dtype=np.float32)
            np.maximum.at(max_scores, sources, edge_scores)
            
            exp_scores = np.exp(edge_scores - max_scores[sources])
            
            sum_exp = np.zeros(N, dtype=np.float32)
            np.add.at(sum_exp, sources, exp_scores)
            
            attention_weights = exp_scores / (sum_exp[sources] + 1e-10)
            
            if training:
                attention_weights = self._dropout(attention_weights, training)
            
            # Aggregate: weighted sum of neighbor features
            H_prime = np.zeros((N, self.out_features), dtype=np.float32)
            weighted_features = attention_weights[:, np.newaxis] * tgt_features
            np.add.at(H_prime, sources, weighted_features)
            
            # Add bias
            H_prime = H_prime + self.bias[head]
            
            head_outputs.append(H_prime)
        
        output = np.concatenate(head_outputs, axis=1)
        return output
    
    def get_embeddings(
        self,
        node_features: np.ndarray,
        adjacency: np.ndarray,
        activation: str = "relu",
    ) -> np.ndarray:
        """
        Get final node embeddings with activation.
        
        Args:
            node_features: Input features
            adjacency: Adjacency matrix
            activation: Activation function ('relu', 'elu', 'none')
            
        Returns:
            Node embeddings
        """
        output = self.forward(node_features, adjacency, training=False)
        
        if activation == "relu":
            output = np.maximum(0, output)
        elif activation == "elu":
            output = np.where(output > 0, output, np.exp(output) - 1)
        
        return output
    
    def get_attention_weights(
        self,
        node_features: np.ndarray,
        adjacency: np.ndarray,
        head: int = 0,
    ) -> np.ndarray:
        """
        Get attention weights for visualization.
        
        Args:
            node_features: Node features
            adjacency: Adjacency matrix
            head: Which attention head to return
            
        Returns:
            Attention weight matrix (N, N)
        """
        if sparse.issparse(adjacency):
            adjacency = adjacency.toarray()
        
        node_features = node_features.astype(np.float32)
        
        # Linear transformation
        Z = node_features @ self.W[head]
        
        # Attention computation
        a_src = self.a[head, :self.out_features]
        a_tgt = self.a[head, self.out_features:]
        
        src_scores = Z @ a_src
        tgt_scores = Z @ a_tgt
        
        attention_scores = src_scores[:, np.newaxis] + tgt_scores[np.newaxis, :]
        attention_scores = self._leaky_relu(attention_scores)
        
        # Mask non-edges
        mask = (adjacency == 0)
        attention_scores = np.where(mask, -1e9, attention_scores)
        
        attention_weights = self._softmax(attention_scores, axis=1)
        
        return attention_weights


class MultiLayerGAT:
    """
    Multi-layer GAT with stacked attention layers.
    """
    
    def __init__(
        self,
        layer_dims: List[int],
        num_heads: List[int] = None,
        dropout: float = None,
        seed: int = 42,
    ):
        """
        Initialize multi-layer GAT.
        
        Args:
            layer_dims: List of layer dimensions [in, hidden1, ..., out]
            num_heads: Number of heads per layer
            dropout: Dropout rate
            seed: Random seed
        """
        self.layer_dims = layer_dims
        self.num_layers = len(layer_dims) - 1
        self.dropout = dropout or config.model.gat_dropout
        
        if num_heads is None:
            # Default: multi-head for hidden, single head for output
            num_heads = [config.model.gat_num_heads] * (self.num_layers - 1) + [1]
        
        self.layers = []
        for i in range(self.num_layers):
            in_dim = layer_dims[i]
            if i > 0:
                # Account for concatenated heads
                in_dim = layer_dims[i] * num_heads[i - 1]
            
            layer = NumpyGAT(
                in_features=in_dim,
                out_features=layer_dims[i + 1],
                num_heads=num_heads[i],
                dropout=self.dropout,
                seed=seed + i,
            )
            self.layers.append(layer)
    
    def forward(
        self,
        node_features: np.ndarray,
        adjacency: np.ndarray,
        training: bool = False,
    ) -> np.ndarray:
        """
        Forward pass through all layers.
        
        Args:
            node_features: Input features
            adjacency: Adjacency matrix
            training: Training mode
            
        Returns:
            Final node embeddings
        """
        x = node_features
        
        for i, layer in enumerate(self.layers):
            x = layer.forward(x, adjacency, training)
            
            # Apply activation to all but last layer
            if i < len(self.layers) - 1:
                x = np.maximum(0, x)  # ReLU
        
        return x
    
    def get_embeddings(
        self,
        node_features: np.ndarray,
        adjacency: np.ndarray,
    ) -> np.ndarray:
        """Get final embeddings."""
        return self.forward(node_features, adjacency, training=False)
