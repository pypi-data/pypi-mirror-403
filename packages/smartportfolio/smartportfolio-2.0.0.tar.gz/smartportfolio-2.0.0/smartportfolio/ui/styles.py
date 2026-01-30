"""
Neural Terminal CSS Styles

Phosphor color palette and monospace typography for the TUI.
"""

# Neural Terminal CSS for Textual
NEURAL_TERMINAL_CSS = """
/* ============================================
   SmartPortfolio Neural Terminal Theme
   Phosphor Color Palette
   ============================================ */

/* Global App Styles */
Screen {
    background: #000000;
    color: #f8f8f2;
}

/* Backgrounds */
.deep-space {
    background: #000000;
}

.terminal-grey {
    background: #121212;
}

.active-grey {
    background: #2e3440;
}

/* Signal Colors */
.amber {
    color: #FF6A00;
}

.green {
    color: #00FF41;
}

.red {
    color: #FF433D;
}

.blue {
    color: #0068FF;
}

/* Text Colors */
.text-primary {
    color: #f8f8f2;
}

.text-muted {
    color: #888888;
}

.text-dim {
    color: #555555;
}

/* Borders */
.border-default {
    border: solid #333333;
}

.border-active {
    border: solid #FF6A00;
}

/* ============================================
   Component Styles
   ============================================ */

/* Header / Title Bar */
#header {
    dock: top;
    height: 3;
    background: #121212;
    border-bottom: solid #333333;
    padding: 0 1;
}

#title {
    text-style: bold;
    color: #FF6A00;
}

#subtitle {
    color: #888888;
}

/* Status Bar */
#status-bar {
    dock: bottom;
    height: 1;
    background: #121212;
    border-top: solid #333333;
    padding: 0 1;
}

/* Command Bar */
#command-bar {
    dock: bottom;
    height: 3;
    background: #121212;
    border: solid #FF6A00;
    padding: 0 1;
    margin: 0 1 1 1;
}

#command-input {
    background: #000000;
    color: #FF6A00;
    border: none;
    width: 100%;
}

#command-input:focus {
    background: #121212;
}

/* Sidebar Panels */
.sidebar {
    width: 30;
    background: #121212;
    border: solid #333333;
    padding: 1;
}

.sidebar-left {
    dock: left;
}

.sidebar-right {
    dock: right;
}

.sidebar-title {
    text-style: bold;
    color: #FF6A00;
    text-align: center;
    margin-bottom: 1;
}

/* Main Content Area */
#main-content {
    background: #000000;
    border: solid #333333;
    padding: 1;
}

/* Scrollable Panels */
.scrollable-panel {
    height: 1fr;
    max-height: 100%;
    overflow-y: auto;
    scrollbar-background: #121212;
    scrollbar-color: #333333;
    scrollbar-color-hover: #FF6A00;
    scrollbar-color-active: #FF6A00;
}

.scrollable-panel:focus {
    border: solid #FF6A00;
}

/* Watchlist */
#watchlist {
    height: 100%;
}

.watchlist-item {
    height: 1;
    padding: 0 1;
}

.watchlist-item:hover {
    background: #2e3440;
}

.watchlist-ticker {
    text-style: bold;
    color: #f8f8f2;
    width: 8;
}

.watchlist-price {
    width: 10;
    text-align: right;
}

.watchlist-change-up {
    color: #00FF41;
    width: 8;
    text-align: right;
}

.watchlist-change-down {
    color: #FF433D;
    width: 8;
    text-align: right;
}

/* Agent Panel */
#agent-panel {
    height: 100%;
}

.regime-indicator {
    height: 3;
    content-align: center middle;
    text-style: bold;
    margin-bottom: 1;
}

.regime-bull {
    background: #00FF41;
    color: #000000;
}

.regime-bear {
    background: #FF433D;
    color: #000000;
}

.regime-volatile {
    background: #FF6A00;
    color: #000000;
}

.regime-neutral {
    background: #333333;
    color: #f8f8f2;
}

/* Action Log */
#action-log {
    height: auto;
    max-height: 50%;
    background: #000000;
    border: solid #333333;
    padding: 1;
    overflow-y: auto;
}

.log-entry {
    height: 1;
    color: #888888;
}

.log-timestamp {
    color: #555555;
}

.log-action {
    color: #0068FF;
}

/* Allocation Display */
#allocation {
    margin-top: 1;
}

.allocation-row {
    height: 1;
}

.allocation-ticker {
    width: 8;
}

.allocation-bar {
    width: 12;
}

.allocation-weight {
    width: 8;
    text-align: right;
    color: #0068FF;
}

/* Chart Area */
#chart-area {
    height: 60%;
    background: #000000;
    border: solid #333333;
    padding: 1;
}

/* Graph Visualization */
#graph-area {
    height: 40%;
    background: #000000;
    border: solid #333333;
    padding: 1;
}

/* Progress Indicators */
.progress-bar {
    height: 1;
    background: #333333;
}

.progress-fill {
    background: #0068FF;
}

/* Buttons */
Button {
    background: #121212;
    color: #f8f8f2;
    border: solid #333333;
    height: 3;
    min-width: 10;
}

Button:hover {
    background: #2e3440;
    border: solid #FF6A00;
}

Button:focus {
    border: solid #FF6A00;
}

Button.-primary {
    background: #FF6A00;
    color: #000000;
}

Button.-primary:hover {
    background: #FB8B1E;
}

/* Input Fields */
Input {
    background: #121212;
    color: #f8f8f2;
    border: solid #333333;
    padding: 0 1;
}

Input:focus {
    border: solid #FF6A00;
}

/* Labels */
Label {
    color: #888888;
}

.label-value {
    color: #f8f8f2;
}

/* DataTable */
DataTable {
    background: #000000;
}

DataTable > .datatable--header {
    background: #121212;
    color: #FF6A00;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #2e3440;
}

/* Sparklines */
.sparkline {
    color: #0068FF;
}

.sparkline-up {
    color: #00FF41;
}

.sparkline-down {
    color: #FF433D;
}

/* Loading Indicator */
LoadingIndicator {
    color: #FF6A00;
}

/* Notifications */
.notification {
    background: #121212;
    border: solid #FF6A00;
    padding: 1;
    margin: 1;
}

.notification-success {
    border: solid #00FF41;
}

.notification-error {
    border: solid #FF433D;
}

/* Metrics Display */
.metric {
    height: 3;
    padding: 0 1;
}

.metric-label {
    color: #888888;
    text-align: left;
}

.metric-value {
    color: #f8f8f2;
    text-style: bold;
    text-align: right;
}

.metric-positive {
    color: #00FF41;
}

.metric-negative {
    color: #FF433D;
}
"""


# Color constants for programmatic use
class Colors:
    """Neural Terminal color constants."""
    
    # Backgrounds
    DEEP_SPACE_BLACK = "#000000"
    TERMINAL_GREY = "#121212"
    ACTIVE_GREY = "#2e3440"
    
    # Signal Colors
    BLOOMBERG_AMBER = "#FF6A00"
    TICK_GREEN = "#00FF41"
    STOP_RED = "#FF433D"
    NEURAL_BLUE = "#0068FF"
    
    # Text
    TEXT_PRIMARY = "#f8f8f2"
    TEXT_MUTED = "#888888"
    TEXT_DIM = "#555555"
    
    # Borders
    BORDER_DEFAULT = "#333333"
    BORDER_ACTIVE = "#FF6A00"
