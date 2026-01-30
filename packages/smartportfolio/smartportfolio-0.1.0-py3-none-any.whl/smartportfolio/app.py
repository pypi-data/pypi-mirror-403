"""
SmartPortfolio TUI Application

Main Textual application with Neural Terminal styling.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, 
    DataTable, Label, LoadingIndicator, Log
)
from textual.reactive import reactive
from textual import work

from smartportfolio.ui.styles import NEURAL_TERMINAL_CSS
from smartportfolio.config import config


logger = logging.getLogger(__name__)


class CommandBar(Static):
    """Command input bar with amber styling."""
    
    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="Commands: LOAD, RUN, LOADWEIGHTS, STATUS, EXPORT, PLOT, HELP",
            id="command-input",
        )
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command = event.value.strip()
        if command:
            self.app.handle_command(command)
            event.input.value = ""


class Watchlist(Static):
    """Asset watchlist panel."""
    
    assets: reactive[Dict[str, Dict]] = reactive({})
    
    def compose(self) -> ComposeResult:
        yield Static("WATCHLIST", classes="sidebar-title")
        yield DataTable(id="watchlist-table")
    
    def on_mount(self) -> None:
        """Initialize watchlist table."""
        table = self.query_one("#watchlist-table", DataTable)
        table.add_columns("Ticker", "Price", "Change")
        table.cursor_type = "row"
    
    def update_assets(self, assets: Dict[str, Dict]) -> None:
        """Update watchlist with new asset data."""
        self.assets = assets
        table = self.query_one("#watchlist-table", DataTable)
        table.clear()
        
        for ticker, data in assets.items():
            price = data.get("price", 0)
            change = data.get("change", 0)
            change_str = f"{change:+.2f}%" if change else "0.00%"
            
            table.add_row(
                ticker,
                f"${price:.2f}",
                change_str,
                key=ticker,
            )


class AgentPanel(Static):
    """RL agent status panel."""
    
    regime: reactive[str] = reactive("neutral")
    
    def compose(self) -> ComposeResult:
        yield Static("AGENT STATUS", classes="sidebar-title")
        yield Static("NEUTRAL", id="regime-display", classes="regime-indicator regime-neutral")
        yield Static("Current Allocation:", classes="text-muted")
        yield Static(id="allocation-display")
        yield Static("Action Log:", classes="text-muted")
        yield Log(id="action-log", max_lines=20)
    
    def update_regime(self, regime: str) -> None:
        """Update regime display."""
        self.regime = regime
        display = self.query_one("#regime-display", Static)
        
        # Update text and class
        display.update(regime.upper())
        display.remove_class("regime-bull", "regime-bear", "regime-volatile", "regime-neutral")
        display.add_class(f"regime-{regime}")
    
    def update_allocation(self, allocation: Dict[str, float]) -> None:
        """Update allocation display."""
        display = self.query_one("#allocation-display", Static)
        
        lines = []
        for ticker, weight in sorted(allocation.items(), key=lambda x: -x[1]):
            if weight > 0.01:
                bar_len = int(weight * 20)
                bar = "[#0068FF]" + "=" * bar_len + "[/]"
                lines.append(f"{ticker:6} {bar} {weight:5.1%}")
        
        display.update("\n".join(lines) if lines else "No allocation")
    
    def log_action(self, action: str) -> None:
        """Add action to log."""
        log = self.query_one("#action-log", Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[{timestamp}] {action}")


class MainContent(Static):
    """Main content area with charts and visualizations."""
    
    def compose(self) -> ComposeResult:
        yield Static("PORTFOLIO OVERVIEW", classes="sidebar-title")
        yield Static(id="chart-display")
        yield Static(id="metrics-display")
    
    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """Update metrics display."""
        display = self.query_one("#metrics-display", Static)
        
        lines = [
            "",
            "[bold]Performance Metrics[/bold]",
            "-" * 30,
        ]
        
        for name, value in metrics.items():
            if "return" in name.lower():
                color = "#00FF41" if value > 0 else "#FF433D"
                lines.append(f"{name}: [{color}]{value:+.2%}[/]")
            elif "sharpe" in name.lower() or "sortino" in name.lower():
                color = "#00FF41" if value > 0 else "#FF433D"
                lines.append(f"{name}: [{color}]{value:.3f}[/]")
            elif "drawdown" in name.lower():
                lines.append(f"{name}: [#FF433D]{value:.2%}[/]")
            else:
                lines.append(f"{name}: {value:.4f}")
        
        display.update("\n".join(lines))
    
    def display_chart(self, title: str, data: List[float] = None) -> None:
        """Display simple ASCII chart."""
        display = self.query_one("#chart-display", Static)
        
        if not data:
            display.update(f"\n  {title}\n\n  [dim]No data to display[/dim]")
            return
        
        # Simple ASCII sparkline
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val or 1
        
        chars = " _.-~*"
        line = ""
        for val in data[-60:]:  # Last 60 points
            idx = int((val - min_val) / range_val * (len(chars) - 1))
            line += chars[idx]
        
        chart_text = f"""
  {title}
  
  [#0068FF]{line}[/]
  
  Min: {min_val:.2f}  Max: {max_val:.2f}
"""
        display.update(chart_text)


class StatusBar(Static):
    """Bottom status bar."""
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("SmartPortfolio v0.1.0", id="version"),
            Static("|", classes="text-dim"),
            Static("Ready", id="status-text"),
            Static("|", classes="text-dim"),
            Static("", id="memory-display"),
        )
    
    def update_status(self, status: str) -> None:
        """Update status text."""
        self.query_one("#status-text", Static).update(status)
    
    def update_memory(self, used_mb: float) -> None:
        """Update memory display."""
        self.query_one("#memory-display", Static).update(f"RAM: {used_mb:.0f}MB")


class SmartPortfolioApp(App):
    """
    SmartPortfolio TUI Application.
    
    Neural Terminal styled interface for portfolio optimization.
    """
    
    CSS = NEURAL_TERMINAL_CSS
    TITLE = "SmartPortfolio"
    SUB_TITLE = "GNN + Prophet + DRL Portfolio Optimization"
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "run_optimization", "Run"),
        Binding("l", "load_tickers", "Load"),
        Binding("e", "export_results", "Export"),
        Binding("h", "show_help", "Help"),
        Binding("escape", "focus_command", "Command"),
    ]
    
    # Reactive state
    tickers: reactive[List[str]] = reactive([])
    is_running: reactive[bool] = reactive(False)
    current_weights: reactive[Dict[str, float]] = reactive({})
    
    def __init__(self, ticker_file: str = None, **kwargs):
        """
        Initialize the application.
        
        Args:
            ticker_file: Optional path to ticker file
        """
        super().__init__(**kwargs)
        self.ticker_file = ticker_file
        self.data_fetcher = None
        self.feature_engineer = None
        self.graph_builder = None
        self.prophet_encoder = None
        self.agent = None
        self.storage = None
        self.visualizer = None
        self.price_data = {}  # Store fetched price data for watchlist
    
    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header(show_clock=True)
        
        with Container(id="app-container"):
            with Horizontal(id="main-layout"):
                # Left sidebar - Watchlist
                with Vertical(id="left-sidebar", classes="sidebar sidebar-left"):
                    yield Watchlist(id="watchlist")
                
                # Main content
                with Vertical(id="main-content"):
                    yield MainContent(id="content")
                
                # Right sidebar - Agent
                with Vertical(id="right-sidebar", classes="sidebar sidebar-right"):
                    yield AgentPanel(id="agent-panel")
        
        yield CommandBar(id="command-bar")
        yield StatusBar(id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize application on mount."""
        self._init_components()
        self.update_status("Ready - Enter command or press 'h' for help")
        
        # Load tickers if provided
        if self.ticker_file:
            self.handle_command(f"LOAD {self.ticker_file}")
    
    def _init_components(self) -> None:
        """Initialize pipeline components."""
        from smartportfolio.data import TickerDataFetcher, FeatureEngineer, LocalStorage
        from smartportfolio.graph import DynamicGraphBuilder
        from smartportfolio.visualization import PortfolioVisualizer
        
        self.data_fetcher = TickerDataFetcher()
        self.feature_engineer = FeatureEngineer()
        self.graph_builder = DynamicGraphBuilder()
        self.storage = LocalStorage()
        self.visualizer = PortfolioVisualizer()
    
    def handle_command(self, command: str) -> None:
        """
        Handle user command.
        
        Commands:
            LOAD <path>: Load tickers from file
            RUN: Run optimization pipeline
            STATUS: Show current status
            EXPORT: Export results
            HELP: Show help
            CLEAR: Clear state
        """
        parts = command.upper().split(maxsplit=1)
        cmd = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        
        # For file paths, use original case
        if cmd == "LOAD" and len(command.split(maxsplit=1)) > 1:
            args = command.split(maxsplit=1)[1]
        
        if cmd == "LOAD":
            self.action_load_tickers(args)
        elif cmd == "RUN":
            self.action_run_optimization()
        elif cmd == "STATUS":
            self.action_show_status()
        elif cmd == "EXPORT":
            self.action_export_results()
        elif cmd == "LOADWEIGHTS":
            self.action_load_weights(args)
        elif cmd == "PLOT":
            self.action_save_plots()
        elif cmd == "GRAPH":
            self.action_save_graph()
        elif cmd == "HELP":
            self.action_show_help()
        elif cmd == "CLEAR":
            self.action_clear()
        else:
            self.log_action(f"Unknown command: {cmd}")
    
    def update_status(self, status: str) -> None:
        """Update status bar."""
        try:
            self.query_one("#status-bar", StatusBar).update_status(status)
        except Exception:
            pass
    
    def log_action(self, action: str) -> None:
        """Log action to agent panel."""
        try:
            self.query_one("#agent-panel", AgentPanel).log_action(action)
        except Exception:
            pass
    
    @work(exclusive=True, thread=True)
    def action_load_tickers(self, file_path: str = "") -> None:
        """Load tickers from file."""
        if not file_path:
            self.log_action("Error: No file path provided")
            return
        
        self.update_status(f"Loading tickers from {file_path}...")
        self.log_action(f"Loading: {file_path}")
        
        try:
            path = Path(file_path.strip())
            self.tickers = self.data_fetcher.load_tickers_from_file(path)
            
            self.call_from_thread(
                self.log_action,
                f"Loaded {len(self.tickers)} tickers"
            )
            self.call_from_thread(
                self.update_status,
                f"Loaded {len(self.tickers)} tickers - Press 'r' to run"
            )
            
        except Exception as e:
            self.call_from_thread(self.log_action, f"Error: {e}")
            self.call_from_thread(self.update_status, "Load failed")
    
    @work(exclusive=True, thread=True)
    def action_run_optimization(self) -> None:
        """Run the optimization pipeline."""
        if not self.tickers:
            self.call_from_thread(self.log_action, "Error: No tickers loaded")
            return
        
        if self.is_running:
            self.call_from_thread(self.log_action, "Already running...")
            return
        
        self.is_running = True
        self.call_from_thread(self.update_status, "Running optimization pipeline...")
        
        try:
            # Step 1: Fetch data
            self.call_from_thread(self.log_action, "Fetching market data...")
            data_dict = self.data_fetcher.fetch_multiple(
                self.tickers,
                progress_callback=lambda c, t, tk: self.call_from_thread(
                    self.update_status, f"Fetching {tk} ({c}/{t})"
                )
            )
            
            if not data_dict:
                raise ValueError("No data fetched")
            
            # Step 2: Feature engineering
            self.call_from_thread(self.log_action, "Engineering features...")
            for ticker in data_dict:
                data_dict[ticker] = self.feature_engineer.engineer_features(data_dict[ticker])
            
            # Step 3: Build graph
            self.call_from_thread(self.log_action, "Building asset graph...")
            price_matrix = self.data_fetcher.get_price_matrix(list(data_dict.keys()))
            returns = price_matrix.pct_change().dropna()
            self.graph_builder.build_correlation_graph(returns)
            
            # Save graph visualization
            self.call_from_thread(self.log_action, "Saving graph visualization...")
            graph_path = self.graph_builder.plot_graph()
            if graph_path:
                self.call_from_thread(self.log_action, f"Graph saved: {Path(graph_path).name}")
            
            # Step 4: Get embeddings (PyTorch GAT if available, NumPy fallback)
            self.call_from_thread(self.log_action, "Computing graph embeddings...")
            from smartportfolio.graph import TORCH_AVAILABLE, create_torch_gat, NumpyGAT
            
            # Simple feature matrix
            features, tickers, _ = self.feature_engineer.get_feature_matrix(data_dict)
            current_features = features[:, -1, :]  # Last timestep
            current_features = np.nan_to_num(current_features, 0)  # Handle NaN
            
            adj = self.graph_builder.get_adjacency_matrix(sparse_format=False)
            
            if TORCH_AVAILABLE and create_torch_gat is not None:
                # Use Pure PyTorch GAT
                self.call_from_thread(self.log_action, "Using PyTorch GAT...")
                gat = create_torch_gat(in_features=current_features.shape[1])
                embeddings = gat.get_embeddings(current_features, adj)
            else:
                # Fallback to NumPy GAT
                self.call_from_thread(self.log_action, "Using NumPy GAT...")
                gat = NumpyGAT(in_features=current_features.shape[1])
                embeddings = gat.get_embeddings(current_features, adj)

            
            # Step 5: Generate allocation (simplified without full training)
            self.call_from_thread(self.log_action, "Generating allocation...")
            
            # Simple allocation using softmax of combined score
            recent_returns = returns.iloc[-20:].mean()
            embedding_scores = embeddings.mean(axis=1)[:len(recent_returns)]
            
            # Combine returns and embedding insight
            # Normalize both components
            ret_normalized = (recent_returns.values - recent_returns.values.mean()) / (recent_returns.values.std() + 1e-10)
            emb_normalized = (embedding_scores - embedding_scores.mean()) / (embedding_scores.std() + 1e-10)
            
            # Combined score
            scores = ret_normalized + 0.3 * emb_normalized
            
            # Softmax to get positive weights that sum to 1
            exp_scores = np.exp(scores - scores.max())  # subtract max for numerical stability
            weights = exp_scores / exp_scores.sum()
            
            self.current_weights = dict(zip(tickers, weights.tolist()))
            
            # Update UI - allocation
            self.call_from_thread(
                self.query_one("#agent-panel", AgentPanel).update_allocation,
                self.current_weights
            )
            
            # Update watchlist with live prices
            self.call_from_thread(self.log_action, "Updating watchlist...")
            self.call_from_thread(self.update_watchlist_prices, data_dict)
            
            # Calculate metrics
            metrics = {
                "Expected Return": float(np.sum(weights * recent_returns.values)),
                "Portfolio Volatility": float(np.std(returns.iloc[-20:] @ weights)),
                "Num Assets": len([w for w in weights if w > 0.01]),
            }
            
            self.call_from_thread(
                self.query_one("#content", MainContent).update_metrics,
                metrics
            )
            
            # Save results
            output_path = self.storage.save_portfolio_weights(
                self.current_weights,
                metadata={"timestamp": datetime.now().isoformat()}
            )
            
            # Save plots
            self.call_from_thread(self.log_action, "Generating plots...")
            plot_paths = self.visualizer.save_all_plots(
                weights=self.current_weights,
                metrics=metrics,
            )
            
            self.call_from_thread(self.log_action, f"Saved: {output_path.name}")
            self.call_from_thread(self.log_action, f"Saved {len(plot_paths)} plots")
            self.call_from_thread(self.update_status, "Optimization complete")
            
        except Exception as e:
            self.call_from_thread(self.log_action, f"Error: {e}")
            self.call_from_thread(self.update_status, "Optimization failed")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            self.is_running = False
    
    def action_show_status(self) -> None:
        """Show current status."""
        status_lines = [
            f"Tickers loaded: {len(self.tickers)}",
            f"Running: {self.is_running}",
            f"Allocation: {len(self.current_weights)} assets",
        ]
        for line in status_lines:
            self.log_action(line)
    
    def action_export_results(self) -> None:
        """Export current results."""
        if not self.current_weights:
            self.log_action("No results to export")
            return
        
        output_path = self.storage.save_portfolio_weights(
            self.current_weights,
            metadata={"exported": datetime.now().isoformat()}
        )
        self.log_action(f"Exported: {output_path}")
        self.update_status(f"Exported to {output_path.name}")
    
    def action_show_help(self) -> None:
        """Show help."""
        help_lines = [
            "--- COMMANDS ---",
            "LOAD <file>: Load tickers from CSV/XLSX",
            "LOADWEIGHTS <file>: Load previous weights CSV",
            "RUN: Run optimization (uses DGL if available)",
            "STATUS: Show current status",
            "EXPORT: Export portfolio weights",
            "PLOT: Save allocation plots to outputs/",
            "GRAPH: Save correlation graph to outputs/",
            "CLEAR: Clear all state",
            "--- KEYS ---",
            "q: Quit | r: Run | l: Load | e: Export",
        ]
        for line in help_lines:
            self.log_action(line)
    
    def action_clear(self) -> None:
        """Clear all state."""
        self.tickers = []
        self.current_weights = {}
        self.price_data = {}
        # Clear watchlist
        try:
            watchlist = self.query_one("#watchlist", Watchlist)
            watchlist.update_assets({})
        except Exception:
            pass
        self.log_action("State cleared")
        self.update_status("Ready")
    
    def action_focus_command(self) -> None:
        """Focus the command input."""
        self.query_one("#command-input", Input).focus()
    
    @work(exclusive=True, thread=True)
    def action_load_weights(self, file_path: str = "") -> None:
        """Load previous portfolio weights from CSV."""
        if not file_path:
            # Try to load latest weights
            latest = self.storage.get_latest_output("portfolio_weights")
            if latest:
                file_path = str(latest)
                self.call_from_thread(self.log_action, f"Loading latest: {latest.name}")
            else:
                self.call_from_thread(self.log_action, "Error: No weights file found")
                return
        
        try:
            import pandas as pd
            path = Path(file_path.strip())
            
            df = pd.read_csv(path)
            
            # Find ticker and weight columns
            ticker_col = None
            weight_col = None
            
            for col in df.columns:
                if col.lower() in ["ticker", "tickers", "symbol"]:
                    ticker_col = col
                elif col.lower() in ["weight", "weights", "allocation"]:
                    weight_col = col
            
            if ticker_col is None:
                ticker_col = df.columns[0]
            if weight_col is None:
                weight_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            
            weights = dict(zip(df[ticker_col], df[weight_col]))
            self.current_weights = weights
            self.tickers = list(weights.keys())
            
            # Update UI
            self.call_from_thread(
                self.query_one("#agent-panel", AgentPanel).update_allocation,
                self.current_weights
            )
            
            self.call_from_thread(self.log_action, f"Loaded {len(weights)} weights")
            self.call_from_thread(self.update_status, f"Loaded weights from {path.name}")
            
        except Exception as e:
            self.call_from_thread(self.log_action, f"Error: {e}")
    
    @work(exclusive=True, thread=True)
    def action_save_plots(self) -> None:
        """Save portfolio plots to outputs directory."""
        if not self.current_weights:
            self.call_from_thread(self.log_action, "Error: No weights to plot")
            return
        
        self.call_from_thread(self.log_action, "Generating plots...")
        
        try:
            saved = self.visualizer.save_all_plots(
                weights=self.current_weights,
                metrics=None,
            )
            
            self.call_from_thread(self.log_action, f"Saved {len(saved)} plots")
            for path in saved:
                self.call_from_thread(self.log_action, f"  - {path.name}")
            
            self.call_from_thread(self.update_status, f"Saved {len(saved)} plots")
            
        except Exception as e:
            self.call_from_thread(self.log_action, f"Error: {e}")
    
    def action_save_graph(self) -> None:
        """Save correlation graph visualization to outputs."""
        if self.graph_builder.graph is None:
            self.log_action("Error: No graph built yet. Run optimization first.")
            return
        
        self.log_action("Saving graph visualization...")
        
        try:
            graph_path = self.graph_builder.plot_graph()
            if graph_path:
                self.log_action(f"Saved: {Path(graph_path).name}")
                self.update_status("Graph saved")
            else:
                self.log_action("Failed to save graph")
        except Exception as e:
            self.log_action(f"Error: {e}")
    
    def update_watchlist_prices(self, data_dict: Dict) -> None:
        """Update watchlist with current prices."""
        try:
            assets = {}
            for ticker, df in data_dict.items():
                if len(df) >= 2:
                    current_price = float(df["close"].iloc[-1])
                    prev_price = float(df["close"].iloc[-2])
                    change = ((current_price - prev_price) / prev_price) * 100
                    assets[ticker] = {"price": current_price, "change": change}
            
            self.price_data = assets
            watchlist = self.query_one("#watchlist", Watchlist)
            watchlist.update_assets(assets)
        except Exception as e:
            logger.error(f"Failed to update watchlist: {e}")


# Import numpy for the optimization
import numpy as np


def main():
    """Run the SmartPortfolio TUI."""
    app = SmartPortfolioApp()
    app.run()


if __name__ == "__main__":
    main()
