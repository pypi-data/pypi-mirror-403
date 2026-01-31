"""
InstaViz - Intelligent Data Visualization
See truth, not just charts.

Author: Md. Ujayer Hasnat
Email: dev.ujayerhasnat@gmail.com
"""

from .core import (
    # Main class
    InstaViz,
    
    # Convenience functions
    plot,
    distribution,
    compare,
    trend,
    correlate,
    relationship,
    target,
    show,
    save,
    set_theme,
    set_config,
    
    # Enums and classes
    Intent,
    ChartType,
    Theme,
    DataType,
    
    # Data structures
    THEMES,
    VizConfig,
    ColumnProfile,
    DataProfile,
    ChartRecommendation,
    
    # Analyzers
    DataAnalyzer,
    ChartRecommender,
    InsightGenerator,
    ChartRenderer,
)

__version__ = "1.0.0"
__author__ = "Md. Ujayer Hasnat"
__email__ = "dev.ujayerhasnat@gmail.com"

__all__ = [
    # Main class
    "InstaViz",
    
    # Convenience functions
    "plot",
    "distribution", 
    "compare",
    "trend",
    "correlate",
    "relationship",
    "target",
    "show",
    "save",
    "set_theme",
    "set_config",
    
    # Enums
    "Intent",
    "ChartType",
    "Theme",
    "DataType",
    
    # Configuration
    "THEMES",
    "VizConfig",
    
    # Version info
    "__version__",
    "__author__",
    "__email__",
]