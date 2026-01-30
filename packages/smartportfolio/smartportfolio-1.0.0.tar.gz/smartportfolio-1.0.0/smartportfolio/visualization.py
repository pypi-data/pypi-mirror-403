"""
Visualization Module

Creates and saves portfolio performance plots and allocation charts.
Uses matplotlib for static plots and plotext for terminal display.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Force matplotlib to use non-interactive Agg backend (thread-safe)
# Must be set BEFORE importing pyplot
import matplotlib
matplotlib.use('Agg')

import numpy as np
import pandas as pd

from smartportfolio.config import config


logger = logging.getLogger(__name__)


class PortfolioVisualizer:
    """
    Creates visualizations for portfolio performance and allocation.
    
    Saves plots to outputs directory and displays in terminal.
    """
    
    def __init__(self, outputs_dir: Path = None):
        """
        Initialize visualizer.
        
        Args:
            outputs_dir: Directory for saving plots
        """
        self.outputs_dir = outputs_dir or config.outputs_dir
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Color scheme from Neural Terminal
        self.colors = {
            'amber': '#FF6A00',
            'green': '#00FF41',
            'red': '#FF433D',
            'blue': '#0068FF',
            'grey': '#888888',
            'bg': '#121212',
        }
    
    def _generate_filename(self, prefix: str, extension: str = "png") -> Path:
        """Generate unique filename."""
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return self.outputs_dir / f"{timestamp}_{unique_id}_{prefix}.{extension}"
    
    def plot_allocation_pie(
        self,
        weights: Dict[str, float],
        title: str = "Portfolio Allocation",
        save: bool = True,
    ) -> Optional[Path]:
        """
        Create pie chart of portfolio allocation.
        
        Args:
            weights: Dictionary of ticker -> weight
            title: Chart title
            save: Whether to save the plot
            
        Returns:
            Path to saved plot or None
        """
        try:
            import matplotlib.pyplot as plt
            
            # Filter significant weights
            filtered = {k: v for k, v in weights.items() if v > 0.01}
            
            if not filtered:
                logger.warning("No significant weights to plot")
                return None
            
            # Create figure with dark background
            fig, ax = plt.subplots(figsize=(10, 8), facecolor=self.colors['bg'])
            ax.set_facecolor(self.colors['bg'])
            
            labels = list(filtered.keys())
            sizes = list(filtered.values())
            
            # Color gradient
            cmap = plt.cm.get_cmap('Blues')
            colors = [cmap(0.3 + 0.7 * i / len(sizes)) for i in range(len(sizes))]
            
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors,
                textprops={'color': 'white', 'fontsize': 10},
                wedgeprops={'edgecolor': self.colors['bg'], 'linewidth': 2},
            )
            
            # Style autotexts
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title(title, color=self.colors['amber'], fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            
            if save:
                filepath = self._generate_filename("allocation_pie")
                plt.savefig(filepath, facecolor=self.colors['bg'], dpi=150)
                logger.info(f"Saved allocation pie chart: {filepath}")
                plt.close()
                return filepath
            
            plt.show()
            return None
            
        except Exception as e:
            logger.error(f"Failed to create pie chart: {e}")
            return None
    
    def plot_allocation_bar(
        self,
        weights: Dict[str, float],
        title: str = "Portfolio Weights",
        save: bool = True,
    ) -> Optional[Path]:
        """
        Create horizontal bar chart of portfolio allocation.
        
        Args:
            weights: Dictionary of ticker -> weight
            title: Chart title
            save: Whether to save
            
        Returns:
            Path to saved plot or None
        """
        try:
            import matplotlib.pyplot as plt
            
            # Sort by weight
            sorted_weights = dict(sorted(weights.items(), key=lambda x: x[1], reverse=True))
            
            # Filter top weights
            top_n = 15
            filtered = dict(list(sorted_weights.items())[:top_n])
            
            if not filtered:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 8), facecolor=self.colors['bg'])
            ax.set_facecolor(self.colors['bg'])
            
            tickers = list(filtered.keys())
            values = list(filtered.values())
            
            # Create bars
            bars = ax.barh(tickers, values, color=self.colors['blue'], edgecolor=self.colors['amber'])
            
            # Style
            ax.set_xlabel('Weight', color='white')
            ax.set_title(title, color=self.colors['amber'], fontsize=14, fontweight='bold')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color(self.colors['grey'])
            ax.spines['left'].set_color(self.colors['grey'])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Add value labels
            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                    f'{val:.1%}', va='center', color='white'
                )
            
            plt.tight_layout()
            
            if save:
                filepath = self._generate_filename("allocation_bar")
                plt.savefig(filepath, facecolor=self.colors['bg'], dpi=150)
                logger.info(f"Saved allocation bar chart: {filepath}")
                plt.close()
                return filepath
            
            plt.show()
            return None
            
        except Exception as e:
            logger.error(f"Failed to create bar chart: {e}")
            return None
    
    def plot_performance(
        self,
        portfolio_values: np.ndarray,
        dates: List = None,
        title: str = "Portfolio Performance",
        save: bool = True,
    ) -> Optional[Path]:
        """
        Create line chart of portfolio performance over time.
        
        Args:
            portfolio_values: Array of portfolio values
            dates: Optional list of dates
            title: Chart title
            save: Whether to save
            
        Returns:
            Path to saved plot or None
        """
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.colors['bg'])
            ax.set_facecolor(self.colors['bg'])
            
            x = dates if dates else range(len(portfolio_values))
            
            # Determine color based on performance
            start_val = portfolio_values[0]
            end_val = portfolio_values[-1]
            line_color = self.colors['green'] if end_val >= start_val else self.colors['red']
            
            ax.plot(x, portfolio_values, color=line_color, linewidth=2)
            ax.fill_between(x, portfolio_values, alpha=0.3, color=line_color)
            
            # Style
            ax.set_xlabel('Time', color='white')
            ax.set_ylabel('Portfolio Value ($)', color='white')
            ax.set_title(title, color=self.colors['amber'], fontsize=14, fontweight='bold')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.3, color=self.colors['grey'])
            ax.spines['bottom'].set_color(self.colors['grey'])
            ax.spines['left'].set_color(self.colors['grey'])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Add return annotation
            total_return = (end_val - start_val) / start_val * 100
            ax.annotate(
                f'Return: {total_return:+.2f}%',
                xy=(0.02, 0.95), xycoords='axes fraction',
                color=line_color, fontsize=12, fontweight='bold'
            )
            
            plt.tight_layout()
            
            if save:
                filepath = self._generate_filename("performance")
                plt.savefig(filepath, facecolor=self.colors['bg'], dpi=150)
                logger.info(f"Saved performance chart: {filepath}")
                plt.close()
                return filepath
            
            plt.show()
            return None
            
        except Exception as e:
            logger.error(f"Failed to create performance chart: {e}")
            return None
    
    def plot_metrics_dashboard(
        self,
        metrics: Dict[str, float],
        weights: Dict[str, float] = None,
        save: bool = True,
    ) -> Optional[Path]:
        """
        Create metrics dashboard with multiple subplots.
        
        Args:
            metrics: Dictionary of metric name -> value
            weights: Optional allocation weights
            save: Whether to save
            
        Returns:
            Path to saved plot or None
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.gridspec import GridSpec
            
            fig = plt.figure(figsize=(14, 10), facecolor=self.colors['bg'])
            gs = GridSpec(2, 2, figure=fig)
            
            # Metrics table (top left)
            ax1 = fig.add_subplot(gs[0, 0])
            ax1.set_facecolor(self.colors['bg'])
            ax1.axis('off')
            
            table_data = [[k, f'{v:.4f}' if isinstance(v, float) else str(v)] 
                         for k, v in metrics.items()]
            table = ax1.table(
                cellText=table_data,
                colLabels=['Metric', 'Value'],
                loc='center',
                cellLoc='left',
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 1.8)
            
            # Color cells
            for (row, col), cell in table.get_celld().items():
                cell.set_facecolor(self.colors['bg'])
                cell.set_text_props(color='white')
                if row == 0:
                    cell.set_text_props(color=self.colors['amber'], weight='bold')
            
            ax1.set_title('Performance Metrics', color=self.colors['amber'], fontsize=12, pad=20)
            
            # Allocation bar (top right)
            if weights:
                ax2 = fig.add_subplot(gs[0, 1])
                ax2.set_facecolor(self.colors['bg'])
                
                sorted_w = dict(sorted(weights.items(), key=lambda x: -x[1])[:10])
                ax2.barh(list(sorted_w.keys()), list(sorted_w.values()), color=self.colors['blue'])
                ax2.set_title('Top Holdings', color=self.colors['amber'], fontsize=12)
                ax2.tick_params(colors='white')
                ax2.spines['bottom'].set_color(self.colors['grey'])
                ax2.spines['left'].set_color(self.colors['grey'])
                ax2.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            if save:
                filepath = self._generate_filename("dashboard")
                plt.savefig(filepath, facecolor=self.colors['bg'], dpi=150)
                logger.info(f"Saved dashboard: {filepath}")
                plt.close()
                return filepath
            
            plt.show()
            return None
            
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            return None
    
    def display_terminal_chart(
        self,
        data: List[float],
        title: str = "Chart",
        width: int = 60,
        height: int = 15,
    ) -> str:
        """
        Create ASCII chart for terminal display using plotext.
        
        Args:
            data: Data points to plot
            title: Chart title
            width: Chart width in characters
            height: Chart height in lines
            
        Returns:
            ASCII chart string
        """
        try:
            import plotext as plt
            
            plt.clear_figure()
            plt.plot(data, marker="braille")
            plt.title(title)
            plt.theme("dark")
            plt.plotsize(width, height)
            
            return plt.build()
            
        except ImportError:
            # Fallback simple sparkline
            return self._simple_sparkline(data, width)
        except Exception as e:
            logger.error(f"Failed to create terminal chart: {e}")
            return ""
    
    def _simple_sparkline(self, data: List[float], width: int = 60) -> str:
        """Create simple ASCII sparkline."""
        if not data:
            return ""
        
        # Normalize to chars
        chars = " _.-~*"
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val or 1
        
        # Sample if too many points
        if len(data) > width:
            step = len(data) // width
            data = data[::step][:width]
        
        line = ""
        for val in data:
            idx = int((val - min_val) / range_val * (len(chars) - 1))
            line += chars[idx]
        
        return line
    
    def save_all_plots(
        self,
        weights: Dict[str, float],
        metrics: Dict[str, float] = None,
        portfolio_values: np.ndarray = None,
    ) -> List[Path]:
        """
        Save all standard plots.
        
        Args:
            weights: Portfolio weights
            metrics: Performance metrics
            portfolio_values: Portfolio value history
            
        Returns:
            List of saved file paths
        """
        saved = []
        
        # Allocation charts
        path = self.plot_allocation_pie(weights)
        if path:
            saved.append(path)
        
        path = self.plot_allocation_bar(weights)
        if path:
            saved.append(path)
        
        # Performance chart
        if portfolio_values is not None:
            path = self.plot_performance(portfolio_values)
            if path:
                saved.append(path)
        
        # Dashboard
        if metrics:
            path = self.plot_metrics_dashboard(metrics, weights)
            if path:
                saved.append(path)
        
        logger.info(f"Saved {len(saved)} plots to {self.outputs_dir}")
        return saved
