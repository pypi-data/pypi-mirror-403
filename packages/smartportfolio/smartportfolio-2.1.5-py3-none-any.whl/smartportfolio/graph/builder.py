"""
Dynamic Graph Builder

Constructs asset relationship graphs using NetworkX and scipy sparse matrices.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import networkx as nx
from scipy import sparse
from scipy.stats import pearsonr, spearmanr

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class DynamicGraphBuilder:
    """
    Builds dynamic graphs representing asset relationships.
    
    Uses NetworkX for graph structure and scipy sparse for efficient
    adjacency matrix representation.
    """
    
    def __init__(
        self,
        correlation_window: int = None,
        correlation_threshold: float = None,
        correlation_method: str = "pearson",
    ):
        """
        Initialize graph builder.
        
        Args:
            correlation_window: Window size for rolling correlation
            correlation_threshold: Minimum correlation for edge creation
            correlation_method: 'pearson' or 'spearman'
        """
        self.correlation_window = correlation_window or config.data.correlation_window
        self.correlation_threshold = correlation_threshold or config.data.correlation_threshold
        self.correlation_method = correlation_method
        
        self.graph: Optional[nx.Graph] = None
        self.tickers: List[str] = []
        self.ticker_to_idx: Dict[str, int] = {}
    
    def build_correlation_graph(
        self,
        returns_df: pd.DataFrame,
        threshold: float = None,
    ) -> nx.Graph:
        """
        Build graph based on asset return correlations.
        
        Args:
            returns_df: DataFrame with returns (dates as index, tickers as columns)
            threshold: Minimum absolute correlation for edge
            
        Returns:
            NetworkX graph with correlation edges
        """
        threshold = threshold or self.correlation_threshold
        
        self.tickers = list(returns_df.columns)
        self.ticker_to_idx = {t: i for i, t in enumerate(self.tickers)}
        n = len(self.tickers)
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr(method=self.correlation_method)
        
        # Build graph
        G = nx.Graph()
        G.add_nodes_from(self.tickers)
        
        # Add node attributes
        for ticker in self.tickers:
            G.nodes[ticker]["idx"] = self.ticker_to_idx[ticker]
        
        # Add edges for correlations above threshold
        for i in range(n):
            for j in range(i + 1, n):
                corr = corr_matrix.iloc[i, j]
                if not np.isnan(corr) and abs(corr) >= threshold:
                    G.add_edge(
                        self.tickers[i],
                        self.tickers[j],
                        weight=corr,
                        abs_weight=abs(corr),
                    )
        
        self.graph = G
        logger.info(f"Built correlation graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def build_sector_graph(
        self,
        ticker_sectors: Dict[str, str],
    ) -> nx.Graph:
        """
        Build graph based on sector relationships.
        
        Args:
            ticker_sectors: Dictionary mapping ticker to sector
            
        Returns:
            NetworkX graph with sector edges
        """
        tickers = list(ticker_sectors.keys())
        self.tickers = tickers
        self.ticker_to_idx = {t: i for i, t in enumerate(tickers)}
        
        G = nx.Graph()
        G.add_nodes_from(tickers)
        
        # Add node attributes
        for ticker in tickers:
            G.nodes[ticker]["idx"] = self.ticker_to_idx[ticker]
            G.nodes[ticker]["sector"] = ticker_sectors[ticker]
        
        # Connect stocks in same sector
        sectors = {}
        for ticker, sector in ticker_sectors.items():
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(ticker)
        
        for sector, sector_tickers in sectors.items():
            for i in range(len(sector_tickers)):
                for j in range(i + 1, len(sector_tickers)):
                    G.add_edge(
                        sector_tickers[i],
                        sector_tickers[j],
                        weight=1.0,
                        relation="sector",
                    )
        
        self.graph = G
        logger.info(f"Built sector graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def build_combined_graph(
        self,
        returns_df: pd.DataFrame,
        ticker_sectors: Dict[str, str] = None,
        correlation_weight: float = 0.7,
        sector_weight: float = 0.3,
    ) -> nx.Graph:
        """
        Build combined graph with multiple relation types.
        
        Args:
            returns_df: DataFrame with returns
            ticker_sectors: Optional sector mapping
            correlation_weight: Weight for correlation edges
            sector_weight: Weight for sector edges
            
        Returns:
            Combined NetworkX graph
        """
        # Start with correlation graph
        G = self.build_correlation_graph(returns_df)
        
        if ticker_sectors:
            # Add sector edges
            for ticker in self.tickers:
                if ticker in ticker_sectors:
                    G.nodes[ticker]["sector"] = ticker_sectors[ticker]
            
            # Add sector edges for tickers in same sector
            sectors = {}
            for ticker in self.tickers:
                if ticker in ticker_sectors:
                    sector = ticker_sectors[ticker]
                    if sector not in sectors:
                        sectors[sector] = []
                    sectors[sector].append(ticker)
            
            for sector, sector_tickers in sectors.items():
                for i in range(len(sector_tickers)):
                    for j in range(i + 1, len(sector_tickers)):
                        t1, t2 = sector_tickers[i], sector_tickers[j]
                        if G.has_edge(t1, t2):
                            # Combine weights
                            old_weight = G[t1][t2]["weight"]
                            G[t1][t2]["weight"] = (
                                correlation_weight * old_weight + sector_weight
                            )
                        else:
                            G.add_edge(t1, t2, weight=sector_weight, relation="sector")
        
        self.graph = G
        return G
    
    def get_adjacency_matrix(
        self,
        sparse_format: bool = True,
        add_self_loops: bool = True,
        normalize: bool = True,
    ) -> Any:
        """
        Get adjacency matrix from graph.
        
        Args:
            sparse_format: If True, return scipy sparse matrix
            add_self_loops: If True, add self-connections
            normalize: If True, apply symmetric normalization
            
        Returns:
            Adjacency matrix (sparse or dense)
        """
        if self.graph is None:
            raise ValueError("Graph not built yet")
        
        n = len(self.tickers)
        
        # Get weighted adjacency matrix
        A = nx.to_numpy_array(self.graph, nodelist=self.tickers, weight="weight")
        
        # Add self-loops
        if add_self_loops:
            A = A + np.eye(n)
        
        # Symmetric normalization: D^(-1/2) * A * D^(-1/2)
        if normalize:
            D = np.diag(A.sum(axis=1))
            D_inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(D.diagonal(), 1e-10)))
            A = D_inv_sqrt @ A @ D_inv_sqrt
        
        if sparse_format:
            return sparse.csr_matrix(A)
        return A
    
    def get_edge_index(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get edge index in COO format (source, target arrays).
        
        Returns:
            Tuple of (source_indices, target_indices)
        """
        if self.graph is None:
            raise ValueError("Graph not built yet")
        
        edges = list(self.graph.edges())
        if not edges:
            return np.array([], dtype=np.int64), np.array([], dtype=np.int64)
        
        sources = []
        targets = []
        
        for u, v in edges:
            u_idx = self.ticker_to_idx[u]
            v_idx = self.ticker_to_idx[v]
            # Add both directions for undirected graph
            sources.extend([u_idx, v_idx])
            targets.extend([v_idx, u_idx])
        
        return np.array(sources, dtype=np.int64), np.array(targets, dtype=np.int64)
    
    def get_edge_weights(self) -> np.ndarray:
        """
        Get edge weights array.
        
        Returns:
            Array of edge weights
        """
        if self.graph is None:
            raise ValueError("Graph not built yet")
        
        weights = []
        for u, v, data in self.graph.edges(data=True):
            w = data.get("weight", 1.0)
            # Both directions
            weights.extend([w, w])
        
        return np.array(weights, dtype=np.float32)
    
    def get_neighbor_indices(self, ticker: str) -> List[int]:
        """
        Get indices of neighbors for a ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            List of neighbor indices
        """
        if self.graph is None or ticker not in self.graph:
            return []
        
        neighbors = list(self.graph.neighbors(ticker))
        return [self.ticker_to_idx[n] for n in neighbors]
    
    def update_graph_weights(
        self,
        returns_df: pd.DataFrame,
        window: int = None,
    ) -> None:
        """
        Update edge weights with rolling correlation.
        
        Args:
            returns_df: Recent returns DataFrame
            window: Window for correlation calculation
        """
        if self.graph is None:
            return
        
        window = window or self.correlation_window
        recent_returns = returns_df.tail(window)
        corr_matrix = recent_returns.corr()
        
        for u, v in self.graph.edges():
            if u in corr_matrix.columns and v in corr_matrix.columns:
                corr = corr_matrix.loc[u, v]
                if not np.isnan(corr):
                    self.graph[u][v]["weight"] = corr
                    self.graph[u][v]["abs_weight"] = abs(corr)
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics.
        
        Returns:
            Dictionary of graph statistics
        """
        if self.graph is None:
            return {}
        
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "avg_degree": sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1),
            "is_connected": nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
        }
    
    def to_dgl_graph(self):
        """
        Convert NetworkX graph to DGL graph.
        
        Returns:
            DGL graph with edge weights
        """
        try:
            import dgl
            import torch
            
            if self.graph is None:
                raise ValueError("Graph not built yet")
            
            # Create DGL graph from NetworkX
            g = dgl.from_networkx(self.graph, edge_attrs=["weight"])
            
            # Ensure edge weights are float tensors
            if "weight" in g.edata:
                g.edata["weight"] = g.edata["weight"].float()
            
            # Add self-loops
            g = dgl.add_self_loop(g)
            
            logger.info(f"Converted to DGL graph: {g.num_nodes()} nodes, {g.num_edges()} edges")
            return g
            
        except ImportError:
            logger.error("DGL not installed. Install with: pip install dgl")
            raise
    
    def plot_graph(
        self,
        save_path: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 10),
        show_weights: bool = True,
        node_size: int = 2000,
        font_size: int = 8,
    ) -> Optional[str]:
        """
        Create and save graph visualization.
        
        Args:
            save_path: Path to save figure (auto-generated if None)
            figsize: Figure size
            show_weights: Whether to show edge weights
            node_size: Size of nodes
            font_size: Font size for labels
            
        Returns:
            Path to saved figure or None
        """
        if self.graph is None:
            logger.warning("No graph to plot")
            return None
        
        try:
            # Force Agg backend for thread safety (no Tkinter)
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from pathlib import Path
            import uuid
            from datetime import datetime
            
            fig, ax = plt.subplots(figsize=figsize, facecolor='#121212')
            ax.set_facecolor('#121212')
            
            # Layout
            pos = nx.spring_layout(self.graph, k=2, iterations=50, seed=42)
            
            # Get edge weights for coloring
            edges = self.graph.edges(data=True)
            edge_colors = []
            edge_widths = []
            
            for u, v, data in edges:
                weight = data.get("weight", 0.5)
                # Color: green for positive, red for negative
                if weight > 0:
                    edge_colors.append('#00FF41')  # Green
                else:
                    edge_colors.append('#FF433D')  # Red
                edge_widths.append(abs(weight) * 3 + 0.5)
            
            # Draw edges
            nx.draw_networkx_edges(
                self.graph, pos,
                edge_color=edge_colors,
                width=edge_widths,
                alpha=0.6,
                ax=ax,
            )
            
            # Draw nodes
            nx.draw_networkx_nodes(
                self.graph, pos,
                node_color='#0068FF',
                node_size=node_size,
                alpha=0.9,
                ax=ax,
            )
            
            # Draw labels
            nx.draw_networkx_labels(
                self.graph, pos,
                font_size=font_size,
                font_color='white',
                font_weight='bold',
                ax=ax,
            )
            
            # Title
            ax.set_title(
                f"Asset Correlation Graph ({self.graph.number_of_nodes()} assets, "
                f"{self.graph.number_of_edges()} correlations)",
                color='#FF6A00',
                fontsize=14,
                fontweight='bold',
            )
            
            ax.axis('off')
            plt.tight_layout()
            
            # Generate save path if not provided
            if save_path is None:
                from smartportfolio.config import config
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_id = str(uuid.uuid4())[:8]
                save_path = config.outputs_dir / f"{timestamp}_{unique_id}_correlation_graph.png"
            
            plt.savefig(save_path, facecolor='#121212', dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved graph visualization: {save_path}")
            return str(save_path)
            
        except Exception as e:
            logger.error(f"Failed to plot graph: {e}")
            return None

