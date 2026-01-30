"""SmartPortfolio Graph Module."""

from smartportfolio.graph.builder import DynamicGraphBuilder
from smartportfolio.graph.gat import NumpyGAT

# Try to import Pure PyTorch GAT
try:
    from smartportfolio.graph.torch_gat import PureTorchGAT, create_torch_gat, TORCH_AVAILABLE
except Exception:
    TORCH_AVAILABLE = False
    PureTorchGAT = None
    create_torch_gat = None

# Try to import DGL components, but don't fail if DGL has issues
try:
    from smartportfolio.graph.dgl_gat import DGLGATEncoder, DGLGraphWrapper, create_dgl_encoder, DGL_AVAILABLE
except Exception:
    # DGL not available or has loading issues
    DGL_AVAILABLE = False
    DGLGATEncoder = None
    DGLGraphWrapper = None
    create_dgl_encoder = None

__all__ = [
    "DynamicGraphBuilder", 
    "NumpyGAT",
    "PureTorchGAT",
    "create_torch_gat",
    "TORCH_AVAILABLE", 
    "DGLGATEncoder", 
    "DGLGraphWrapper",
    "create_dgl_encoder",
    "DGL_AVAILABLE",
]
