"""
InstaViz - Intelligent Data Visualization
See truth, not just charts.

Author: Md. Ujayer Hasnat
Email: dev.ujayerhasnat@gmail.com
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any, Callable, Dict, List, Literal, Optional,
    Tuple, Union, Sequence
)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.ticker import MaxNLocator, FuncFormatter
from scipy import stats
from scipy.ndimage import gaussian_filter1d
import colorsys


# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & CONSTANTS
# ════════════════════════════════════════════════════════════════════════════════

__version__ = "1.0.0"
__author__ = "Md. Ujayer Hasnat"
__email__ = "dev.ujayerhasnat@gmail.com"


class Intent(Enum):
    """Analytical intent types."""
    DISTRIBUTION = auto()
    COMPARISON = auto()
    TREND = auto()
    RELATIONSHIP = auto()
    COMPOSITION = auto()
    RANKING = auto()
    CORRELATION = auto()
    DEVIATION = auto()
    FLOW = auto()
    GEOSPATIAL = auto()


class DataType(Enum):
    """Detected data types."""
    NUMERIC_CONTINUOUS = auto()
    NUMERIC_DISCRETE = auto()
    CATEGORICAL_LOW = auto()      # <= 10 categories
    CATEGORICAL_MEDIUM = auto()   # 11-30 categories
    CATEGORICAL_HIGH = auto()     # > 30 categories
    DATETIME = auto()
    BOOLEAN = auto()
    TEXT = auto()
    IDENTIFIER = auto()


class ChartType(Enum):
    """Supported chart types."""
    HISTOGRAM = "histogram"
    KDE = "kde"
    BOXPLOT = "boxplot"
    VIOLIN = "violin"
    BAR = "bar"
    HBAR = "hbar"
    LINE = "line"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    STRIP = "strip"
    SWARM = "swarm"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    STACKED_BAR = "stacked_bar"
    GROUPED_BAR = "grouped_bar"
    RIDGE = "ridge"
    LOLLIPOP = "lollipop"
    RAINCLOUD = "raincloud"
    HEXBIN = "hexbin"
    CONTOUR = "contour"


@dataclass
class Theme:
    """Visualization theme configuration."""
    name: str = "instaviz"
    background: str = "#FFFFFF"
    text_color: str = "#2D3748"
    grid_color: str = "#E2E8F0"
    spine_color: str = "#CBD5E0"
    font_family: str = "sans-serif"
    title_size: int = 14
    label_size: int = 11
    tick_size: int = 10
    annotation_size: int = 9
    line_width: float = 2.0
    marker_size: float = 50
    alpha: float = 0.85
    grid_alpha: float = 0.5
    palette: List[str] = field(default_factory=lambda: [
        "#4361EE", "#F72585", "#4CC9F0", "#7209B7", "#3A0CA3",
        "#4895EF", "#560BAD", "#B5179E", "#480CA8", "#3F37C9"
    ])
    sequential_palette: List[str] = field(default_factory=lambda: [
        "#F7FBFF", "#DEEBF7", "#C6DBEF", "#9ECAE1", "#6BAED6",
        "#4292C6", "#2171B5", "#08519C", "#08306B"
    ])
    diverging_palette: List[str] = field(default_factory=lambda: [
        "#D73027", "#F46D43", "#FDAE61", "#FEE090", "#FFFFBF",
        "#E0F3F8", "#ABD9E9", "#74ADD1", "#4575B4"
    ])
    success_color: str = "#10B981"
    warning_color: str = "#F59E0B"
    error_color: str = "#EF4444"
    highlight_color: str = "#F72585"


# Predefined themes
THEMES = {
    "instaviz": Theme(),
    "dark": Theme(
        name="dark",
        background="#1A202C",
        text_color="#E2E8F0",
        grid_color="#2D3748",
        spine_color="#4A5568",
        palette=["#63B3ED", "#FC8181", "#68D391", "#F6AD55", "#B794F4",
                 "#4FD1C5", "#F687B3", "#9F7AEA", "#FBD38D", "#76E4F7"]
    ),
    "minimal": Theme(
        name="minimal",
        grid_color="#F7FAFC",
        spine_color="#FFFFFF",
        palette=["#2D3748", "#4A5568", "#718096", "#A0AEC0", "#CBD5E0"]
    ),
    "vibrant": Theme(
        name="vibrant",
        palette=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                 "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"]
    ),
    "corporate": Theme(
        name="corporate",
        palette=["#1B4F72", "#2874A6", "#3498DB", "#85C1E9", "#D4E6F1",
                 "#145A32", "#1E8449", "#27AE60", "#82E0AA", "#D5F5E3"]
    ),
}


@dataclass
class VizConfig:
    """Global visualization configuration."""
    theme: Theme = field(default_factory=Theme)
    figsize: Tuple[float, float] = (10, 6)
    dpi: int = 100
    tight_layout: bool = True
    show_insights: bool = True
    auto_annotate: bool = True
    warn_on_issues: bool = True
    max_categories: int = 20
    max_points_scatter: int = 5000
    min_samples_kde: int = 30
    outlier_method: Literal["iqr", "zscore", "isolation"] = "iqr"
    outlier_threshold: float = 1.5
    trend_smoothing: float = 0.0  # 0 = no smoothing
    date_format: str = "%Y-%m-%d"
    number_format: str = "{:,.2f}"
    percentage_format: str = "{:.1%}"


# Global config instance
_config = VizConfig()


# ════════════════════════════════════════════════════════════════════════════════
# DATA ANALYSIS ENGINE
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class ColumnProfile:
    """Statistical profile of a single column."""
    name: str
    dtype: DataType
    n_total: int
    n_valid: int
    n_missing: int
    missing_pct: float
    n_unique: int
    cardinality_ratio: float

    # Numeric stats
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None
    iqr: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    n_zeros: Optional[int] = None
    n_negative: Optional[int] = None
    is_integer: bool = False
    has_outliers: bool = False
    n_outliers: int = 0
    suggested_log: bool = False

    # Categorical stats
    mode: Optional[Any] = None
    mode_freq: Optional[int] = None
    top_values: Optional[List[Tuple[Any, int]]] = None

    # Datetime stats
    min_date: Optional[pd.Timestamp] = None
    max_date: Optional[pd.Timestamp] = None
    date_range_days: Optional[int] = None

    # Flags
    is_target_candidate: bool = False
    is_id_column: bool = False


@dataclass
class DataProfile:
    """Full profile of a DataFrame."""
    n_rows: int
    n_cols: int
    columns: Dict[str, ColumnProfile]
    memory_usage: int
    duplicates: int
    complete_rows: int
    correlations: Optional[pd.DataFrame] = None


class DataAnalyzer:
    """Analyzes data to determine optimal visualization strategies."""

    def __init__(self, config: VizConfig = None):
        self.config = config or _config

    def analyze_column(self, series: pd.Series) -> ColumnProfile:
        """Generate a complete profile for a single column."""
        name = series.name or "unnamed"
        n_total = len(series)
        n_missing = series.isna().sum()
        n_valid = n_total - n_missing
        valid_data = series.dropna()
        n_unique = valid_data.nunique()
        cardinality_ratio = n_unique / n_valid if n_valid > 0 else 0

        # Detect data type
        dtype = self._detect_dtype(series, n_unique, cardinality_ratio)

        profile = ColumnProfile(
            name=name,
            dtype=dtype,
            n_total=n_total,
            n_valid=n_valid,
            n_missing=n_missing,
            missing_pct=n_missing / n_total if n_total > 0 else 0,
            n_unique=n_unique,
            cardinality_ratio=cardinality_ratio,
        )

        # Numeric analysis
        if dtype in (DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE):
            self._analyze_numeric(valid_data, profile)

        # Categorical analysis
        elif dtype in (DataType.CATEGORICAL_LOW, DataType.CATEGORICAL_MEDIUM,
                       DataType.CATEGORICAL_HIGH, DataType.BOOLEAN):
            self._analyze_categorical(valid_data, profile)

        # Datetime analysis
        elif dtype == DataType.DATETIME:
            self._analyze_datetime(valid_data, profile)

        # Check if likely ID column
        profile.is_id_column = self._is_identifier(series, cardinality_ratio)

        return profile

    def _detect_dtype(self, series: pd.Series, n_unique: int,
                      cardinality_ratio: float) -> DataType:
        """Intelligently detect the semantic data type."""
        pandas_dtype = series.dtype

        # Boolean
        if pandas_dtype == bool or (n_unique == 2 and
                                     set(series.dropna().unique()).issubset({0, 1, True, False, 'yes', 'no', 'Yes', 'No'})):
            return DataType.BOOLEAN

        # Datetime
        if pd.api.types.is_datetime64_any_dtype(pandas_dtype):
            return DataType.DATETIME

        # Numeric
        if pd.api.types.is_numeric_dtype(pandas_dtype):
            # Check if discrete (integer-like with low unique values)
            valid = series.dropna()
            if len(valid) > 0:
                is_int_like = np.allclose(valid, valid.astype(int), equal_nan=True)
                if is_int_like and n_unique <= 20:
                    return DataType.NUMERIC_DISCRETE
            return DataType.NUMERIC_CONTINUOUS

        # Categorical by cardinality
        if n_unique <= 10:
            return DataType.CATEGORICAL_LOW
        elif n_unique <= 30:
            return DataType.CATEGORICAL_MEDIUM
        elif cardinality_ratio > 0.9:
            return DataType.IDENTIFIER
        elif n_unique <= 100:
            return DataType.CATEGORICAL_HIGH
        else:
            return DataType.TEXT

    def _analyze_numeric(self, data: pd.Series, profile: ColumnProfile):
        """Compute numeric statistics."""
        if len(data) == 0:
            return

        profile.mean = data.mean()
        profile.median = data.median()
        profile.std = data.std()
        profile.min_val = data.min()
        profile.max_val = data.max()
        profile.q1 = data.quantile(0.25)
        profile.q3 = data.quantile(0.75)
        profile.iqr = profile.q3 - profile.q1
        profile.n_zeros = (data == 0).sum()
        profile.n_negative = (data < 0).sum()
        profile.is_integer = np.allclose(data, data.astype(int), equal_nan=True)

        # Skewness and kurtosis
        if len(data) >= 3:
            profile.skewness = stats.skew(data)
            profile.kurtosis = stats.kurtosis(data)

        # Outlier detection (IQR method)
        if profile.iqr > 0:
            lower = profile.q1 - self.config.outlier_threshold * profile.iqr
            upper = profile.q3 + self.config.outlier_threshold * profile.iqr
            outliers = (data < lower) | (data > upper)
            profile.n_outliers = outliers.sum()
            profile.has_outliers = profile.n_outliers > 0

        # Suggest log scale for highly skewed positive data
        if profile.min_val is not None and profile.min_val > 0:
            if profile.skewness is not None and abs(profile.skewness) > 2:
                range_ratio = profile.max_val / profile.min_val if profile.min_val > 0 else 0
                if range_ratio > 100:
                    profile.suggested_log = True

    def _analyze_categorical(self, data: pd.Series, profile: ColumnProfile):
        """Compute categorical statistics."""
        if len(data) == 0:
            return

        value_counts = data.value_counts()
        profile.mode = value_counts.index[0] if len(value_counts) > 0 else None
        profile.mode_freq = value_counts.iloc[0] if len(value_counts) > 0 else None
        profile.top_values = list(value_counts.head(10).items())

    def _analyze_datetime(self, data: pd.Series, profile: ColumnProfile):
        """Compute datetime statistics."""
        if len(data) == 0:
            return

        profile.min_date = data.min()
        profile.max_date = data.max()
        if profile.min_date and profile.max_date:
            profile.date_range_days = (profile.max_date - profile.min_date).days

    def _is_identifier(self, series: pd.Series, cardinality_ratio: float) -> bool:
        """Detect if column is likely an ID/index column."""
        name_lower = str(series.name).lower()
        id_patterns = ['id', 'key', 'index', 'uuid', 'guid', 'code']

        if any(p in name_lower for p in id_patterns):
            return True
        if cardinality_ratio > 0.95:
            return True
        return False

    def analyze_dataframe(self, df: pd.DataFrame) -> DataProfile:
        """Generate a complete profile for a DataFrame."""
        columns = {col: self.analyze_column(df[col]) for col in df.columns}

        # Compute correlations for numeric columns
        numeric_cols = [c for c, p in columns.items()
                       if p.dtype in (DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE)]

        correlations = None
        if len(numeric_cols) >= 2:
            correlations = df[numeric_cols].corr()

        return DataProfile(
            n_rows=len(df),
            n_cols=len(df.columns),
            columns=columns,
            memory_usage=df.memory_usage(deep=True).sum(),
            duplicates=df.duplicated().sum(),
            complete_rows=(~df.isna().any(axis=1)).sum(),
            correlations=correlations,
        )


# ════════════════════════════════════════════════════════════════════════════════
# CHART RECOMMENDATION ENGINE
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class ChartRecommendation:
    """A chart recommendation with reasoning."""
    chart_type: ChartType
    score: float
    reason: str
    warnings: List[str] = field(default_factory=list)
    enhancements: List[str] = field(default_factory=list)
    alternatives: List[ChartType] = field(default_factory=list)


class ChartRecommender:
    """Recommends optimal chart types based on data and intent."""

    def __init__(self, analyzer: DataAnalyzer = None, config: VizConfig = None):
        self.analyzer = analyzer or DataAnalyzer()
        self.config = config or _config

    def recommend(
        self,
        df: pd.DataFrame,
        x: Optional[str] = None,
        y: Optional[str] = None,
        hue: Optional[str] = None,
        intent: Optional[Intent] = None,
    ) -> ChartRecommendation:
        """Get the optimal chart recommendation."""

        # Analyze columns
        x_profile = self.analyzer.analyze_column(df[x]) if x else None
        y_profile = self.analyzer.analyze_column(df[y]) if y else None
        hue_profile = self.analyzer.analyze_column(df[hue]) if hue else None

        # Infer intent if not provided
        if intent is None:
            intent = self._infer_intent(x_profile, y_profile)

        # Get recommendation based on profiles and intent
        return self._get_recommendation(
            df, x_profile, y_profile, hue_profile, intent
        )

    def _infer_intent(
        self,
        x_profile: Optional[ColumnProfile],
        y_profile: Optional[ColumnProfile]
    ) -> Intent:
        """Infer analytical intent from column profiles."""

        # Single variable
        if y_profile is None:
            if x_profile is None:
                return Intent.DISTRIBUTION
            if x_profile.dtype == DataType.DATETIME:
                return Intent.TREND
            if x_profile.dtype in (DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE):
                return Intent.DISTRIBUTION
            return Intent.COMPARISON

        # Two variables
        x_is_numeric = x_profile and x_profile.dtype in (
            DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE
        )
        y_is_numeric = y_profile.dtype in (
            DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE
        )
        x_is_datetime = x_profile and x_profile.dtype == DataType.DATETIME
        x_is_cat = x_profile and x_profile.dtype in (
            DataType.CATEGORICAL_LOW, DataType.CATEGORICAL_MEDIUM, DataType.BOOLEAN
        )

        if x_is_datetime:
            return Intent.TREND
        if x_is_numeric and y_is_numeric:
            return Intent.RELATIONSHIP
        if x_is_cat and y_is_numeric:
            return Intent.COMPARISON

        return Intent.DISTRIBUTION

    def _get_recommendation(
        self,
        df: pd.DataFrame,
        x_profile: Optional[ColumnProfile],
        y_profile: Optional[ColumnProfile],
        hue_profile: Optional[ColumnProfile],
        intent: Intent,
    ) -> ChartRecommendation:
        """Generate chart recommendation based on analysis."""

        warnings = []
        enhancements = []

        # Distribution intent
        if intent == Intent.DISTRIBUTION:
            if x_profile and x_profile.dtype in (DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE):
                n = x_profile.n_valid

                if n < 30:
                    warnings.append(f"Small sample size (n={n}). Distribution may not be reliable.")
                    return ChartRecommendation(
                        chart_type=ChartType.STRIP,
                        score=0.8,
                        reason="Strip plot shows individual points for small samples",
                        warnings=warnings,
                        alternatives=[ChartType.HISTOGRAM]
                    )

                if x_profile.has_outliers:
                    enhancements.append("Outliers will be highlighted")

                if x_profile.suggested_log:
                    enhancements.append("Log scale recommended due to skewness")

                # Prefer KDE for larger samples, histogram for smaller
                if n > 100:
                    return ChartRecommendation(
                        chart_type=ChartType.HISTOGRAM,
                        score=0.95,
                        reason="Histogram with KDE overlay shows distribution shape clearly",
                        enhancements=enhancements,
                        warnings=warnings,
                        alternatives=[ChartType.VIOLIN, ChartType.BOXPLOT]
                    )
                else:
                    return ChartRecommendation(
                        chart_type=ChartType.HISTOGRAM,
                        score=0.9,
                        reason="Histogram for moderate sample size",
                        enhancements=enhancements,
                        warnings=warnings,
                        alternatives=[ChartType.STRIP]
                    )

            # Categorical distribution
            if x_profile and x_profile.dtype in (DataType.CATEGORICAL_LOW, DataType.BOOLEAN):
                return ChartRecommendation(
                    chart_type=ChartType.BAR,
                    score=0.95,
                    reason="Bar chart clearly shows category frequencies",
                    alternatives=[ChartType.PIE, ChartType.LOLLIPOP]
                )

            if x_profile and x_profile.dtype == DataType.CATEGORICAL_MEDIUM:
                warnings.append(f"Many categories ({x_profile.n_unique}). Consider aggregation.")
                return ChartRecommendation(
                    chart_type=ChartType.HBAR,
                    score=0.85,
                    reason="Horizontal bar chart for many categories",
                    warnings=warnings,
                    alternatives=[ChartType.LOLLIPOP]
                )

        # Comparison intent
        if intent == Intent.COMPARISON:
            if x_profile and y_profile:
                x_is_cat = x_profile.dtype in (
                    DataType.CATEGORICAL_LOW, DataType.CATEGORICAL_MEDIUM, DataType.BOOLEAN
                )
                y_is_numeric = y_profile.dtype in (
                    DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE
                )

                if x_is_cat and y_is_numeric:
                    n_cats = x_profile.n_unique
                    n_per_group = y_profile.n_valid / n_cats if n_cats > 0 else 0

                    if n_cats > self.config.max_categories:
                        warnings.append(f"Too many categories ({n_cats}). Showing top {self.config.max_categories}.")

                    if n_per_group < 10:
                        return ChartRecommendation(
                            chart_type=ChartType.STRIP,
                            score=0.85,
                            reason="Strip plot shows individual points for small groups",
                            warnings=warnings,
                            alternatives=[ChartType.BOXPLOT]
                        )
                    elif n_per_group < 50:
                        return ChartRecommendation(
                            chart_type=ChartType.BOXPLOT,
                            score=0.9,
                            reason="Box plot shows distribution summary per category",
                            warnings=warnings,
                            enhancements=["Median and quartiles shown"],
                            alternatives=[ChartType.VIOLIN]
                        )
                    else:
                        return ChartRecommendation(
                            chart_type=ChartType.VIOLIN,
                            score=0.92,
                            reason="Violin plot shows full distribution shape per category",
                            warnings=warnings,
                            alternatives=[ChartType.BOXPLOT, ChartType.RAINCLOUD]
                        )

        # Trend intent
        if intent == Intent.TREND:
            if x_profile and x_profile.dtype == DataType.DATETIME:
                n_points = x_profile.n_valid

                if n_points > 500:
                    enhancements.append("Trend smoothing applied for clarity")

                return ChartRecommendation(
                    chart_type=ChartType.LINE,
                    score=0.95,
                    reason="Line chart shows trends over time",
                    enhancements=enhancements,
                    alternatives=[ChartType.AREA]
                )

        # Relationship intent
        if intent == Intent.RELATIONSHIP:
            if x_profile and y_profile:
                n_points = min(x_profile.n_valid, y_profile.n_valid)

                if n_points > self.config.max_points_scatter:
                    warnings.append(f"Large dataset ({n_points} points). Using hexbin to prevent overplotting.")
                    return ChartRecommendation(
                        chart_type=ChartType.HEXBIN,
                        score=0.9,
                        reason="Hexbin plot handles large datasets without overplotting",
                        warnings=warnings,
                        alternatives=[ChartType.CONTOUR]
                    )

                if n_points > 1000:
                    enhancements.append("Alpha reduced to show density")

                return ChartRecommendation(
                    chart_type=ChartType.SCATTER,
                    score=0.95,
                    reason="Scatter plot reveals relationships between numeric variables",
                    enhancements=enhancements,
                    alternatives=[ChartType.HEXBIN]
                )

        # Correlation intent
        if intent == Intent.CORRELATION:
            return ChartRecommendation(
                chart_type=ChartType.HEATMAP,
                score=0.95,
                reason="Heatmap shows correlations between all numeric pairs",
                alternatives=[]
            )

        # Default fallback
        return ChartRecommendation(
            chart_type=ChartType.BAR,
            score=0.5,
            reason="Default chart type",
            warnings=["Could not determine optimal chart. Using bar chart as fallback."]
        )


# ════════════════════════════════════════════════════════════════════════════════
# INSIGHT GENERATOR
# ════════════════════════════════════════════════════════════════════════════════

class InsightGenerator:
    """Generates natural language insights from data."""

    def __init__(self, config: VizConfig = None):
        self.config = config or _config

    def distribution_insights(self, profile: ColumnProfile) -> List[str]:
        """Generate insights for a distribution."""
        insights = []

        if profile.dtype in (DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE):
            # Central tendency
            if profile.mean and profile.median:
                diff = abs(profile.mean - profile.median) / profile.std if profile.std else 0
                if diff > 0.5:
                    if profile.mean > profile.median:
                        insights.append("⚡ Right-skewed distribution (mean > median)")
                    else:
                        insights.append("⚡ Left-skewed distribution (mean < median)")
                else:
                    insights.append("✓ Distribution is approximately symmetric")

            # Spread
            if profile.std and profile.mean:
                cv = profile.std / abs(profile.mean) if profile.mean != 0 else 0
                if cv > 1:
                    insights.append(f"📊 High variability (CV = {cv:.1%})")

            # Outliers
            if profile.has_outliers:
                pct = profile.n_outliers / profile.n_valid * 100
                insights.append(f"⚠️ {profile.n_outliers} outliers detected ({pct:.1f}% of data)")

            # Range and values
            if profile.n_zeros and profile.n_zeros > 0:
                pct = profile.n_zeros / profile.n_valid * 100
                if pct > 10:
                    insights.append(f"📍 {pct:.1f}% of values are zero")

            if profile.n_negative and profile.n_negative > 0:
                pct = profile.n_negative / profile.n_valid * 100
                insights.append(f"📉 {pct:.1f}% of values are negative")

        elif profile.dtype in (DataType.CATEGORICAL_LOW, DataType.CATEGORICAL_MEDIUM):
            if profile.top_values:
                top_val, top_count = profile.top_values[0]
                pct = top_count / profile.n_valid * 100
                insights.append(f"🏆 Most common: '{top_val}' ({pct:.1f}%)")

                if len(profile.top_values) >= 2:
                    second_val, second_count = profile.top_values[1]
                    ratio = top_count / second_count if second_count > 0 else 0
                    if ratio > 3:
                        insights.append("⚡ Highly imbalanced - one category dominates")

        # Missing data
        if profile.missing_pct > 0.05:
            insights.append(f"⚠️ {profile.missing_pct:.1%} missing values")

        return insights

    def comparison_insights(
        self,
        df: pd.DataFrame,
        x: str,
        y: str
    ) -> List[str]:
        """Generate insights for category comparisons."""
        insights = []

        grouped = df.groupby(x)[y].agg(['mean', 'median', 'std', 'count'])

        if len(grouped) >= 2:
            # Range of means
            max_mean = grouped['mean'].max()
            min_mean = grouped['mean'].min()
            max_cat = grouped['mean'].idxmax()
            min_cat = grouped['mean'].idxmin()

            if min_mean > 0:
                ratio = max_mean / min_mean
                if ratio > 2:
                    insights.append(
                        f"📊 '{max_cat}' has {ratio:.1f}x higher average than '{min_cat}'"
                    )

            # Variance comparison
            max_std = grouped['std'].max()
            min_std = grouped['std'].min()
            if min_std > 0:
                std_ratio = max_std / min_std
                if std_ratio > 3:
                    insights.append("⚡ Large variance differences between groups")

            # Sample size warning
            min_count = grouped['count'].min()
            if min_count < 30:
                insights.append(f"⚠️ Smallest group has only {int(min_count)} samples")

        return insights

    def correlation_insights(self, corr_matrix: pd.DataFrame) -> List[str]:
        """Generate insights for correlation matrix."""
        insights = []

        # Find strongest correlations (excluding diagonal)
        corr_unstacked = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        ).unstack().dropna()

        if len(corr_unstacked) > 0:
            strongest = corr_unstacked.abs().nlargest(3)

            for (col1, col2), corr_val in strongest.items():
                actual_val = corr_matrix.loc[col1, col2]
                if abs(actual_val) > 0.7:
                    direction = "positive" if actual_val > 0 else "negative"
                    insights.append(
                        f"🔗 Strong {direction} correlation between '{col1}' and '{col2}' (r={actual_val:.2f})"
                    )
                elif abs(actual_val) > 0.5:
                    direction = "positive" if actual_val > 0 else "negative"
                    insights.append(
                        f"📈 Moderate {direction} correlation between '{col1}' and '{col2}' (r={actual_val:.2f})"
                    )

        return insights

    def trend_insights(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str
    ) -> List[str]:
        """Generate insights for time series data."""
        insights = []

        sorted_df = df.sort_values(date_col)
        values = sorted_df[value_col].dropna()

        if len(values) < 2:
            return insights

        # Overall trend
        first_quarter = values.head(len(values) // 4).mean()
        last_quarter = values.tail(len(values) // 4).mean()

        if first_quarter > 0:
            change = (last_quarter - first_quarter) / first_quarter
            if abs(change) > 0.1:
                direction = "increased" if change > 0 else "decreased"
                insights.append(f"📈 Overall trend: {direction} by {abs(change):.1%}")

        # Volatility
        if len(values) > 10:
            rolling_std = values.rolling(window=max(3, len(values)//10)).std()
            if rolling_std.iloc[-1] > rolling_std.iloc[len(values)//2] * 1.5:
                insights.append("⚡ Volatility has increased in recent period")

        return insights


# ════════════════════════════════════════════════════════════════════════════════
# CHART RENDERER
# ════════════════════════════════════════════════════════════════════════════════

class ChartRenderer:
    """Renders beautiful charts with automatic enhancements."""

    def __init__(self, config: VizConfig = None):
        self.config = config or _config
        self.analyzer = DataAnalyzer(config)
        self.insight_gen = InsightGenerator(config)

    def _apply_theme(self, ax: Axes, title: str = None):
        """Apply theme styling to axes."""
        theme = self.config.theme

        ax.set_facecolor(theme.background)
        ax.figure.set_facecolor(theme.background)

        # Spines
        for spine in ax.spines.values():
            spine.set_color(theme.spine_color)
            spine.set_linewidth(0.5)

        # Grid
        ax.grid(True, alpha=theme.grid_alpha, color=theme.grid_color, linestyle='-', linewidth=0.5)
        ax.set_axisbelow(True)

        # Ticks
        ax.tick_params(colors=theme.text_color, labelsize=theme.tick_size)

        # Labels
        if ax.get_xlabel():
            ax.xaxis.label.set_color(theme.text_color)
            ax.xaxis.label.set_fontsize(theme.label_size)
        if ax.get_ylabel():
            ax.yaxis.label.set_color(theme.text_color)
            ax.yaxis.label.set_fontsize(theme.label_size)

        # Title
        if title:
            ax.set_title(title, fontsize=theme.title_size, color=theme.text_color,
                        fontweight='bold', pad=15)

    def _create_figure(self, figsize: Tuple[float, float] = None) -> Tuple[Figure, Axes]:
        """Create a styled figure and axes."""
        figsize = figsize or self.config.figsize
        fig, ax = plt.subplots(figsize=figsize, dpi=self.config.dpi)
        return fig, ax

    def _get_color(self, index: int = 0) -> str:
        """Get color from palette by index."""
        palette = self.config.theme.palette
        return palette[index % len(palette)]

    def _smart_bins(self, data: pd.Series, profile: ColumnProfile) -> int:
        """Calculate optimal number of bins."""
        n = len(data)

        # Freedman-Diaconis rule
        if profile.iqr and profile.iqr > 0:
            h = 2 * profile.iqr / (n ** (1/3))
            range_val = profile.max_val - profile.min_val
            n_bins = max(1, int(np.ceil(range_val / h))) if h > 0 else 30
        else:
            # Sturges' rule fallback
            n_bins = int(np.ceil(np.log2(n) + 1))

        return min(max(n_bins, 10), 100)  # Clamp between 10-100

    # ────────────────────────────────────────────────────────────────────────────
    # DISTRIBUTION CHARTS
    # ────────────────────────────────────────────────────────────────────────────

    def histogram(
        self,
        df: pd.DataFrame,
        x: str,
        bins: int = None,
        kde: bool = True,
        show_stats: bool = True,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a histogram with optional KDE and statistics."""

        data = df[x].dropna()
        profile = self.analyzer.analyze_column(data)

        if ax is None:
            fig, ax = self._create_figure()
        else:
            fig = ax.figure

        # Calculate bins
        if bins is None:
            bins = self._smart_bins(data, profile)

        # Determine if log scale is needed
        use_log = profile.suggested_log and profile.min_val > 0
        plot_data = np.log10(data) if use_log else data

        # Plot histogram
        color = self._get_color(0)
        n, bin_edges, patches = ax.hist(
            plot_data, bins=bins, color=color,
            alpha=self.config.theme.alpha, edgecolor='white', linewidth=0.5
        )

        # KDE overlay
        if kde and len(data) >= self.config.min_samples_kde:
            try:
                kde_x = np.linspace(plot_data.min(), plot_data.max(), 200)
                kde_obj = stats.gaussian_kde(plot_data)
                kde_y = kde_obj(kde_x)
                # Scale KDE to histogram height
                kde_y = kde_y * len(data) * (bin_edges[1] - bin_edges[0])
                ax.plot(kde_x, kde_y, color=self._get_color(1),
                       linewidth=self.config.theme.line_width)
            except Exception:
                pass  # KDE can fail for some distributions

        # Add statistics lines
        if show_stats:
            mean_val = np.log10(profile.mean) if use_log else profile.mean
            median_val = np.log10(profile.median) if use_log else profile.median

            ax.axvline(mean_val, color=self.config.theme.error_color,
                      linestyle='--', linewidth=1.5, label=f'Mean: {profile.mean:.2f}')
            ax.axvline(median_val, color=self.config.theme.success_color,
                      linestyle='-', linewidth=1.5, label=f'Median: {profile.median:.2f}')
            ax.legend(loc='upper right', framealpha=0.9)

        # Labels
        xlabel = f'{x} (log₁₀ scale)' if use_log else x
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Count')

        title = title or f'Distribution of {x}'
        if use_log:
            title += ' (log scale)'

        self._apply_theme(ax, title)

        # Generate insights
        insights = self.insight_gen.distribution_insights(profile)

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    def boxplot(
        self,
        df: pd.DataFrame,
        x: str = None,
        y: str = None,
        show_points: bool = True,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a box plot with optional strip overlay."""

        if ax is None:
            fig, ax = self._create_figure()
        else:
            fig = ax.figure

        theme = self.config.theme

        if x is None:
            # Single distribution
            data = df[y].dropna()
            bp = ax.boxplot(
                data, patch_artist=True, widths=0.5,
                boxprops=dict(facecolor=to_rgba(self._get_color(0), 0.7), edgecolor=theme.text_color),
                whiskerprops=dict(color=theme.text_color),
                capprops=dict(color=theme.text_color),
                medianprops=dict(color=theme.highlight_color, linewidth=2),
                flierprops=dict(markerfacecolor=theme.warning_color, markeredgecolor='none',
                              markersize=6, alpha=0.7)
            )

            if show_points and len(data) < 200:
                jitter = np.random.normal(1, 0.04, len(data))
                ax.scatter(jitter, data, alpha=0.4, s=20, color=self._get_color(0), zorder=3)

            ax.set_ylabel(y)
            ax.set_xticklabels([y])
            insights = self.insight_gen.distribution_insights(self.analyzer.analyze_column(data))
        else:
            # Grouped box plot
            categories = df[x].dropna().unique()
            n_cats = len(categories)

            if n_cats > self.config.max_categories:
                # Get top categories by count
                top_cats = df[x].value_counts().head(self.config.max_categories).index
                df = df[df[x].isin(top_cats)]
                categories = top_cats
                n_cats = len(categories)

            data_by_cat = [df[df[x] == cat][y].dropna().values for cat in categories]
            positions = np.arange(1, n_cats + 1)

            bp = ax.boxplot(
                data_by_cat, positions=positions, patch_artist=True, widths=0.6,
                boxprops=dict(facecolor=to_rgba(self._get_color(0), 0.7), edgecolor=theme.text_color),
                whiskerprops=dict(color=theme.text_color),
                capprops=dict(color=theme.text_color),
                medianprops=dict(color=theme.highlight_color, linewidth=2),
                flierprops=dict(markerfacecolor=theme.warning_color, markeredgecolor='none',
                              markersize=6, alpha=0.7)
            )

            if show_points:
                for i, (cat, pos) in enumerate(zip(categories, positions)):
                    cat_data = df[df[x] == cat][y].dropna()
                    if len(cat_data) < 100:
                        jitter = np.random.normal(pos, 0.08, len(cat_data))
                        ax.scatter(jitter, cat_data, alpha=0.3, s=15,
                                 color=self._get_color(0), zorder=3)

            ax.set_xticks(positions)
            ax.set_xticklabels(categories, rotation=45 if n_cats > 5 else 0, ha='right')
            ax.set_xlabel(x)
            ax.set_ylabel(y)
            insights = self.insight_gen.comparison_insights(df, x, y)

        title = title or (f'{y} by {x}' if x else f'Distribution of {y}')
        self._apply_theme(ax, title)

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    def violin(
        self,
        df: pd.DataFrame,
        x: str = None,
        y: str = None,
        show_box: bool = True,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a violin plot."""

        if ax is None:
            fig, ax = self._create_figure()
        else:
            fig = ax.figure

        theme = self.config.theme

        if x is None:
            data = [df[y].dropna().values]
            positions = [1]
            labels = [y]
        else:
            categories = df[x].dropna().unique()
            if len(categories) > self.config.max_categories:
                top_cats = df[x].value_counts().head(self.config.max_categories).index
                df = df[df[x].isin(top_cats)]
                categories = top_cats

            data = [df[df[x] == cat][y].dropna().values for cat in categories]
            # Filter out empty arrays
            valid = [(d, cat) for d, cat in zip(data, categories) if len(d) > 0]
            if valid:
                data, categories = zip(*valid)
                data = list(data)
            positions = range(1, len(data) + 1)
            labels = categories

        parts = ax.violinplot(data, positions=positions, showmeans=False,
                             showmedians=False, showextrema=False)

        # Style violin bodies
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(to_rgba(self._get_color(i % len(theme.palette)), 0.7))
            pc.set_edgecolor(theme.text_color)
            pc.set_linewidth(1)

        # Add box plot inside
        if show_box:
            bp = ax.boxplot(data, positions=positions, widths=0.15, patch_artist=True,
                           showfliers=False,
                           boxprops=dict(facecolor='white', edgecolor=theme.text_color),
                           whiskerprops=dict(color=theme.text_color),
                           capprops=dict(color=theme.text_color),
                           medianprops=dict(color=theme.highlight_color, linewidth=2))

        ax.set_xticks(list(positions))
        ax.set_xticklabels(labels, rotation=45 if len(labels) > 5 else 0, ha='right')

        if x:
            ax.set_xlabel(x)
        ax.set_ylabel(y)

        title = title or (f'{y} Distribution by {x}' if x else f'Distribution of {y}')
        self._apply_theme(ax, title)

        insights = self.insight_gen.comparison_insights(df, x, y) if x else []

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    # ────────────────────────────────────────────────────────────────────────────
    # CATEGORICAL CHARTS
    # ────────────────────────────────────────────────────────────────────────────

    def bar(
        self,
        df: pd.DataFrame,
        x: str,
        y: str = None,
        horizontal: bool = False,
        sort: bool = True,
        top_n: int = None,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a bar chart."""

        if ax is None:
            figsize = (self.config.figsize[1], self.config.figsize[0]) if horizontal else self.config.figsize
            fig, ax = self._create_figure(figsize)
        else:
            fig = ax.figure

        theme = self.config.theme

        # Prepare data
        if y is None:
            # Count plot
            data = df[x].value_counts()
            ylabel = 'Count'
        else:
            # Mean by category
            data = df.groupby(x)[y].mean()
            ylabel = f'Mean {y}'

        if sort:
            data = data.sort_values(ascending=horizontal)

        if top_n:
            data = data.head(top_n)
        elif len(data) > self.config.max_categories:
            data = data.head(self.config.max_categories)

        # Colors
        colors = [self._get_color(i) for i in range(len(data))]

        if horizontal:
            bars = ax.barh(data.index, data.values, color=colors,
                          alpha=theme.alpha, edgecolor='white', linewidth=0.5)
            ax.set_xlabel(ylabel)
            ax.set_ylabel(x)

            # Add value labels
            if self.config.auto_annotate:
                for bar, val in zip(bars, data.values):
                    ax.annotate(f'{val:,.1f}', xy=(val, bar.get_y() + bar.get_height()/2),
                               xytext=(5, 0), textcoords='offset points',
                               va='center', fontsize=theme.annotation_size, color=theme.text_color)
        else:
            bars = ax.bar(data.index, data.values, color=colors,
                         alpha=theme.alpha, edgecolor='white', linewidth=0.5)
            ax.set_xlabel(x)
            ax.set_ylabel(ylabel)

            # Rotate labels if needed
            if len(data) > 5:
                plt.xticks(rotation=45, ha='right')

            # Add value labels
            if self.config.auto_annotate and len(data) <= 10:
                for bar, val in zip(bars, data.values):
                    ax.annotate(f'{val:,.1f}', xy=(bar.get_x() + bar.get_width()/2, val),
                               xytext=(0, 5), textcoords='offset points',
                               ha='center', fontsize=theme.annotation_size, color=theme.text_color)

        title = title or (f'{ylabel}' if y else f'{x} Counts')
        self._apply_theme(ax, title)

        insights = []
        if len(data) >= 2:
            max_val = data.max()
            min_val = data.min()
            max_cat = data.idxmax()
            if min_val > 0:
                ratio = max_val / min_val
                if ratio > 2:
                    insights.append(f"📊 Highest category '{max_cat}' is {ratio:.1f}x larger than the smallest")

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    # ────────────────────────────────────────────────────────────────────────────
    # RELATIONSHIP CHARTS
    # ────────────────────────────────────────────────────────────────────────────

    def scatter(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        hue: str = None,
        size: str = None,
        trendline: bool = True,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a scatter plot with optional trendline."""

        if ax is None:
            fig, ax = self._create_figure()
        else:
            fig = ax.figure

        theme = self.config.theme

        # Handle large datasets
        n_points = len(df)
        alpha = max(0.1, min(0.8, 1000 / n_points)) if n_points > 500 else theme.alpha

        # Size mapping
        sizes = theme.marker_size
        if size:
            size_data = df[size]
            sizes = (size_data - size_data.min()) / (size_data.max() - size_data.min())
            sizes = 20 + sizes * 200  # Scale between 20-220

        if hue is None:
            ax.scatter(df[x], df[y], s=sizes, alpha=alpha,
                      color=self._get_color(0), edgecolor='white', linewidth=0.5)
        else:
            categories = df[hue].unique()
            for i, cat in enumerate(categories):
                mask = df[hue] == cat
                cat_sizes = sizes[mask] if isinstance(sizes, pd.Series) else sizes
                ax.scatter(df.loc[mask, x], df.loc[mask, y], s=cat_sizes, alpha=alpha,
                          color=self._get_color(i), label=str(cat),
                          edgecolor='white', linewidth=0.5)
            ax.legend(title=hue, loc='best', framealpha=0.9)

        # Trendline
        if trendline:
            valid = df[[x, y]].dropna()
            if len(valid) >= 3:
                try:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[x], valid[y])
                    x_line = np.linspace(valid[x].min(), valid[x].max(), 100)
                    y_line = slope * x_line + intercept
                    ax.plot(x_line, y_line, color=theme.highlight_color,
                           linestyle='--', linewidth=2, alpha=0.8,
                           label=f'R² = {r_value**2:.3f}')
                    if hue is None:
                        ax.legend(loc='best', framealpha=0.9)
                except Exception:
                    pass

        ax.set_xlabel(x)
        ax.set_ylabel(y)

        title = title or f'{y} vs {x}'
        self._apply_theme(ax, title)

        # Insights
        insights = []
        try:
            corr = df[[x, y]].corr().iloc[0, 1]
            if abs(corr) > 0.7:
                insights.append(f"🔗 Strong {'positive' if corr > 0 else 'negative'} correlation (r={corr:.2f})")
            elif abs(corr) > 0.4:
                insights.append(f"📈 Moderate {'positive' if corr > 0 else 'negative'} correlation (r={corr:.2f})")
        except Exception:
            pass

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    def hexbin(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        gridsize: int = 30,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a hexbin plot for large datasets."""

        if ax is None:
            fig, ax = self._create_figure()
        else:
            fig = ax.figure

        theme = self.config.theme

        # Create custom colormap from theme
        cmap = LinearSegmentedColormap.from_list('custom', theme.sequential_palette)

        hb = ax.hexbin(df[x], df[y], gridsize=gridsize, cmap=cmap,
                      edgecolors='white', linewidths=0.2, mincnt=1)

        cb = plt.colorbar(hb, ax=ax)
        cb.set_label('Count', color=theme.text_color)
        cb.ax.yaxis.set_tick_params(color=theme.text_color)
        plt.setp(plt.getp(cb.ax.axes, 'yticklabels'), color=theme.text_color)

        ax.set_xlabel(x)
        ax.set_ylabel(y)

        title = title or f'{y} vs {x} (Density)'
        self._apply_theme(ax, title)

        insights = [f"📊 {len(df):,} points displayed using hexagonal binning"]

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    # ────────────────────────────────────────────────────────────────────────────
    # TIME SERIES CHARTS
    # ────────────────────────────────────────────────────────────────────────────

    def line(
        self,
        df: pd.DataFrame,
        x: str,
        y: Union[str, List[str]],
        smooth: float = None,
        show_points: bool = None,
        fill: bool = False,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a line chart."""

        if ax is None:
            fig, ax = self._create_figure()
        else:
            fig = ax.figure

        theme = self.config.theme

        # Handle single or multiple y columns
        y_cols = [y] if isinstance(y, str) else y

        # Sort by x
        plot_df = df.sort_values(x)

        # Determine if points should be shown
        if show_points is None:
            show_points = len(plot_df) < 50

        # Smoothing
        smooth = smooth if smooth is not None else self.config.trend_smoothing

        for i, col in enumerate(y_cols):
            y_data = plot_df[col].values

            if smooth > 0:
                y_data = gaussian_filter1d(y_data, sigma=smooth)

            line, = ax.plot(plot_df[x], y_data, color=self._get_color(i),
                           linewidth=theme.line_width, label=col, alpha=theme.alpha)

            if fill:
                ax.fill_between(plot_df[x], y_data, alpha=0.2, color=self._get_color(i))

            if show_points:
                ax.scatter(plot_df[x], y_data, s=30, color=self._get_color(i),
                          edgecolor='white', linewidth=0.5, zorder=3)

        if len(y_cols) > 1:
            ax.legend(loc='best', framealpha=0.9)

        ax.set_xlabel(x)
        ax.set_ylabel(y_cols[0] if len(y_cols) == 1 else 'Value')

        # Format x-axis for dates
        if pd.api.types.is_datetime64_any_dtype(plot_df[x]):
            fig.autofmt_xdate()

        title = title or (f'{y_cols[0]} over {x}' if len(y_cols) == 1 else f'Trends over {x}')
        self._apply_theme(ax, title)

        insights = []
        if len(y_cols) == 1:
            insights = self.insight_gen.trend_insights(plot_df, x, y_cols[0])

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    # ────────────────────────────────────────────────────────────────────────────
    # CORRELATION CHARTS
    # ────────────────────────────────────────────────────────────────────────────

    def heatmap(
        self,
        df: pd.DataFrame = None,
        data: pd.DataFrame = None,
        annot: bool = True,
        mask_upper: bool = True,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a correlation heatmap."""

        if ax is None:
            figsize = (max(8, len(df.columns) * 0.8), max(6, len(df.columns) * 0.6)) if df is not None else self.config.figsize
            fig, ax = self._create_figure(figsize)
        else:
            fig = ax.figure

        theme = self.config.theme

        # Use provided data or compute correlation
        if data is not None:
            corr = data
        else:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            corr = df[numeric_cols].corr()

        # Create mask for upper triangle
        mask = None
        if mask_upper:
            mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

        # Create diverging colormap
        cmap = LinearSegmentedColormap.from_list('diverging', theme.diverging_palette)

        # Plot heatmap
        im = ax.imshow(corr.where(~mask if mask is not None else True),
                      cmap=cmap, vmin=-1, vmax=1, aspect='auto')

        # Set ticks
        ax.set_xticks(np.arange(len(corr.columns)))
        ax.set_yticks(np.arange(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha='right')
        ax.set_yticklabels(corr.columns)

        # Annotations
        if annot:
            for i in range(len(corr)):
                for j in range(len(corr)):
                    if mask is not None and mask[i, j]:
                        continue
                    val = corr.iloc[i, j]
                    color = 'white' if abs(val) > 0.5 else theme.text_color
                    ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                           color=color, fontsize=theme.annotation_size)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Correlation', color=theme.text_color)

        title = title or 'Correlation Matrix'
        self._apply_theme(ax, title)

        insights = self.insight_gen.correlation_insights(corr)

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    # ────────────────────────────────────────────────────────────────────────────
    # ADVANCED CHARTS
    # ────────────────────────────────────────────────────────────────────────────

    def raincloud(
        self,
        df: pd.DataFrame,
        x: str = None,
        y: str = None,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a raincloud plot (violin + strip + box)."""

        if ax is None:
            fig, ax = self._create_figure()
        else:
            fig = ax.figure

        theme = self.config.theme

        if x is None:
            categories = [y]
            data_list = [df[y].dropna().values]
        else:
            categories = df[x].dropna().unique()
            if len(categories) > self.config.max_categories:
                categories = df[x].value_counts().head(self.config.max_categories).index
            data_list = [df[df[x] == cat][y].dropna().values for cat in categories]

        positions = np.arange(1, len(categories) + 1)

        for i, (pos, data) in enumerate(zip(positions, data_list)):
            if len(data) < 2:
                continue

            color = self._get_color(i)

            # Half violin (cloud)
            try:
                kde = stats.gaussian_kde(data)
                x_grid = np.linspace(data.min(), data.max(), 100)
                kde_vals = kde(x_grid)
                kde_vals = kde_vals / kde_vals.max() * 0.3  # Scale width

                ax.fill_betweenx(x_grid, pos, pos + kde_vals,
                                alpha=0.6, color=color)
            except Exception:
                pass

            # Strip (rain)
            jitter = np.random.uniform(pos - 0.1, pos - 0.05, len(data))
            ax.scatter(jitter, data, s=15, alpha=0.3, color=color)

            # Box
            bp = ax.boxplot([data], positions=[pos + 0.15], widths=0.1,
                           patch_artist=True, vert=True, showfliers=False,
                           boxprops=dict(facecolor='white', edgecolor=color),
                           whiskerprops=dict(color=color),
                           capprops=dict(color=color),
                           medianprops=dict(color=theme.highlight_color, linewidth=2))

        ax.set_xticks(positions)
        ax.set_xticklabels(categories, rotation=45 if len(categories) > 5 else 0, ha='right')
        if x:
            ax.set_xlabel(x)
        ax.set_ylabel(y)

        title = title or f'{y} Distribution' + (f' by {x}' if x else '')
        self._apply_theme(ax, title)

        insights = self.insight_gen.comparison_insights(df, x, y) if x else []

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, insights

    def lollipop(
        self,
        df: pd.DataFrame,
        x: str,
        y: str = None,
        sort: bool = True,
        top_n: int = None,
        title: str = None,
        ax: Axes = None,
    ) -> Tuple[Figure, Axes, List[str]]:
        """Render a lollipop chart."""

        if ax is None:
            fig, ax = self._create_figure()
        else:
            fig = ax.figure

        theme = self.config.theme

        # Prepare data
        if y is None:
            data = df[x].value_counts()
            ylabel = 'Count'
        else:
            data = df.groupby(x)[y].mean()
            ylabel = f'Mean {y}'

        if sort:
            data = data.sort_values(ascending=True)

        if top_n:
            data = data.tail(top_n)
        elif len(data) > self.config.max_categories:
            data = data.tail(self.config.max_categories)

        positions = np.arange(len(data))

        # Plot stems
        ax.hlines(y=positions, xmin=0, xmax=data.values,
                 color=theme.grid_color, linewidth=2)

        # Plot lollipop heads
        ax.scatter(data.values, positions, color=self._get_color(0),
                  s=100, zorder=3, edgecolor='white', linewidth=2)

        ax.set_yticks(positions)
        ax.set_yticklabels(data.index)
        ax.set_xlabel(ylabel)
        ax.set_ylabel(x)

        # Add value labels
        if self.config.auto_annotate:
            for pos, val in zip(positions, data.values):
                ax.annotate(f'{val:,.1f}', xy=(val, pos), xytext=(5, 0),
                           textcoords='offset points', va='center',
                           fontsize=theme.annotation_size, color=theme.text_color)

        title = title or ylabel
        self._apply_theme(ax, title)

        if self.config.tight_layout:
            fig.tight_layout()

        return fig, ax, []


# ════════════════════════════════════════════════════════════════════════════════
# MAIN API
# ════════════════════════════════════════════════════════════════════════════════

class InstaViz:
    """
    InstaViz - Intelligent Data Visualization

    A next-generation visualization module that makes data visualization
    faster, easier, and more insightful by default.

    Examples
    --------
    >>> import instaviz as viz
    >>> viz.show(df)  # Auto-EDA with smart charts
    >>> viz.plot(df, 'category', 'value')  # Smart auto-chart
    >>> viz.distribution(df, 'price')  # Distribution analysis
    >>> viz.compare(df, 'region', 'sales')  # Category comparison
    >>> viz.trend(df, 'date', 'revenue')  # Time series
    >>> viz.correlate(df)  # Correlation heatmap
    """

    def __init__(self, config: VizConfig = None):
        self.config = config or _config
        self.analyzer = DataAnalyzer(self.config)
        self.recommender = ChartRecommender(self.analyzer, self.config)
        self.renderer = ChartRenderer(self.config)
        self.insight_gen = InsightGenerator(self.config)

    def set_theme(self, theme: Union[str, Theme]):
        """Set the visualization theme."""
        if isinstance(theme, str):
            if theme not in THEMES:
                raise ValueError(f"Unknown theme: {theme}. Available: {list(THEMES.keys())}")
            self.config.theme = THEMES[theme]
        else:
            self.config.theme = theme

    def set_config(self, **kwargs):
        """Update configuration options."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"Unknown config option: {key}")

    def plot(
        self,
        df: pd.DataFrame,
        x: str = None,
        y: str = None,
        hue: str = None,
        intent: Intent = None,
        chart: ChartType = None,
        title: str = None,
        **kwargs
    ) -> Tuple[Figure, Axes]:
        """
        Smart plotting - automatically chooses the best chart.

        Parameters
        ----------
        df : pd.DataFrame
            The data to visualize
        x : str, optional
            Column for x-axis
        y : str, optional
            Column for y-axis
        hue : str, optional
            Column for color grouping
        intent : Intent, optional
            Analytical intent (auto-detected if not provided)
        chart : ChartType, optional
            Force a specific chart type
        title : str, optional
            Chart title
        **kwargs
            Additional chart-specific parameters

        Returns
        -------
        fig, ax : matplotlib Figure and Axes
        """

        # Get recommendation
        if chart is None:
            rec = self.recommender.recommend(df, x, y, hue, intent)
            chart = rec.chart_type

            # Show recommendation info
            if self.config.warn_on_issues:
                for warning in rec.warnings:
                    print(f"⚠️  {warning}")

            if rec.enhancements and self.config.show_insights:
                for enh in rec.enhancements:
                    print(f"✨ {enh}")

        # Render the chart
        fig, ax, insights = self._render_chart(df, x, y, hue, chart, title, **kwargs)

        # Show insights
        if self.config.show_insights and insights:
            print("\n📊 Insights:")
            for insight in insights:
                print(f"   {insight}")

        return fig, ax

    def _render_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        hue: str,
        chart: ChartType,
        title: str,
        **kwargs
    ) -> Tuple[Figure, Axes, List[str]]:
        """Route to appropriate renderer."""

        if chart == ChartType.HISTOGRAM:
            return self.renderer.histogram(df, x or y, title=title, **kwargs)
        elif chart == ChartType.BOXPLOT:
            return self.renderer.boxplot(df, x, y or x, title=title, **kwargs)
        elif chart == ChartType.VIOLIN:
            return self.renderer.violin(df, x, y or x, title=title, **kwargs)
        elif chart == ChartType.BAR:
            return self.renderer.bar(df, x, y, horizontal=False, title=title, **kwargs)
        elif chart == ChartType.HBAR:
            return self.renderer.bar(df, x, y, horizontal=True, title=title, **kwargs)
        elif chart == ChartType.SCATTER:
            return self.renderer.scatter(df, x, y, hue=hue, title=title, **kwargs)
        elif chart == ChartType.HEXBIN:
            return self.renderer.hexbin(df, x, y, title=title, **kwargs)
        elif chart == ChartType.LINE:
            return self.renderer.line(df, x, y, title=title, **kwargs)
        elif chart == ChartType.HEATMAP:
            return self.renderer.heatmap(df, title=title, **kwargs)
        elif chart == ChartType.RAINCLOUD:
            return self.renderer.raincloud(df, x, y, title=title, **kwargs)
        elif chart == ChartType.LOLLIPOP:
            return self.renderer.lollipop(df, x, y, title=title, **kwargs)
        elif chart == ChartType.STRIP:
            # Strip plot as scatter with jitter
            return self.renderer.boxplot(df, x, y or x, show_points=True, title=title, **kwargs)
        else:
            raise ValueError(f"Chart type {chart} not implemented yet")

    def distribution(
        self,
        df: pd.DataFrame,
        column: str,
        kind: Literal["histogram", "kde", "box", "violin", "raincloud"] = "histogram",
        **kwargs
    ) -> Tuple[Figure, Axes]:
        """
        Analyze and visualize the distribution of a column.

        Parameters
        ----------
        df : pd.DataFrame
            The data
        column : str
            Column to analyze
        kind : str
            Type of distribution plot
        """
        chart_map = {
            "histogram": ChartType.HISTOGRAM,
            "kde": ChartType.KDE,
            "box": ChartType.BOXPLOT,
            "violin": ChartType.VIOLIN,
            "raincloud": ChartType.RAINCLOUD,
        }
        return self.plot(df, x=column, chart=chart_map.get(kind, ChartType.HISTOGRAM), **kwargs)

    def compare(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        kind: Literal["box", "violin", "bar", "strip", "raincloud"] = None,
        **kwargs
    ) -> Tuple[Figure, Axes]:
        """
        Compare a numeric variable across categories.

        Parameters
        ----------
        df : pd.DataFrame
            The data
        x : str
            Categorical column
        y : str
            Numeric column to compare
        kind : str, optional
            Chart type (auto-selected if not provided)
        """
        if kind:
            chart_map = {
                "box": ChartType.BOXPLOT,
                "violin": ChartType.VIOLIN,
                "bar": ChartType.BAR,
                "strip": ChartType.STRIP,
                "raincloud": ChartType.RAINCLOUD,
            }
            return self.plot(df, x=x, y=y, chart=chart_map[kind], **kwargs)
        return self.plot(df, x=x, y=y, intent=Intent.COMPARISON, **kwargs)

    def trend(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: Union[str, List[str]],
        smooth: float = None,
        **kwargs
    ) -> Tuple[Figure, Axes]:
        """
        Visualize trends over time.

        Parameters
        ----------
        df : pd.DataFrame
            The data
        date_col : str
            DateTime column
        value_col : str or list of str
            Value column(s) to plot
        smooth : float, optional
            Smoothing factor (0 = none)
        """
        return self.renderer.line(df, date_col, value_col, smooth=smooth, **kwargs)[:2]

    def correlate(
        self,
        df: pd.DataFrame,
        columns: List[str] = None,
        method: Literal["pearson", "spearman", "kendall"] = "pearson",
        **kwargs
    ) -> Tuple[Figure, Axes]:
        """
        Visualize correlations between numeric columns.

        Parameters
        ----------
        df : pd.DataFrame
            The data
        columns : list of str, optional
            Columns to include (all numeric if not specified)
        method : str
            Correlation method
        """
        if columns:
            df = df[columns]
        else:
            df = df.select_dtypes(include=[np.number])

        corr = df.corr(method=method)
        fig, ax, insights = self.renderer.heatmap(data=corr, **kwargs)

        if self.config.show_insights and insights:
            print("\n📊 Insights:")
            for insight in insights:
                print(f"   {insight}")

        return fig, ax

    def relationship(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        hue: str = None,
        kind: Literal["scatter", "hexbin", "contour"] = None,
        **kwargs
    ) -> Tuple[Figure, Axes]:
        """
        Visualize relationship between two numeric variables.

        Parameters
        ----------
        df : pd.DataFrame
            The data
        x : str
            X-axis column
        y : str
            Y-axis column
        hue : str, optional
            Grouping column
        kind : str, optional
            Chart type (auto-selected if not provided)
        """
        if kind:
            chart_map = {
                "scatter": ChartType.SCATTER,
                "hexbin": ChartType.HEXBIN,
                "contour": ChartType.CONTOUR,
            }
            return self.plot(df, x=x, y=y, hue=hue, chart=chart_map[kind], **kwargs)
        return self.plot(df, x=x, y=y, hue=hue, intent=Intent.RELATIONSHIP, **kwargs)

    def target(
        self,
        df: pd.DataFrame,
        target: str,
        features: List[str] = None,
        n_cols: int = 3,
        figsize: Tuple[float, float] = None,
    ) -> Figure:
        """
        Analyze features against a target variable.

        Creates a grid of plots showing each feature's relationship
        with the target.

        Parameters
        ----------
        df : pd.DataFrame
            The data
        target : str
            Target column name
        features : list of str, optional
            Features to analyze (all non-target if not specified)
        n_cols : int
            Number of columns in the grid
        figsize : tuple, optional
            Figure size
        """
        if features is None:
            features = [c for c in df.columns if c != target]

        # Limit number of features
        if len(features) > 12:
            print(f"⚠️  Showing first 12 of {len(features)} features")
            features = features[:12]

        n_features = len(features)
        n_rows = int(np.ceil(n_features / n_cols))

        figsize = figsize or (5 * n_cols, 4 * n_rows)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten() if n_features > 1 else [axes]

        target_profile = self.analyzer.analyze_column(df[target])
        target_is_numeric = target_profile.dtype in (
            DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE
        )

        for i, feat in enumerate(features):
            ax = axes[i]
            feat_profile = self.analyzer.analyze_column(df[feat])

            feat_is_numeric = feat_profile.dtype in (
                DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE
            )
            feat_is_cat = feat_profile.dtype in (
                DataType.CATEGORICAL_LOW, DataType.CATEGORICAL_MEDIUM, DataType.BOOLEAN
            )

            # Choose appropriate plot
            if feat_is_numeric and target_is_numeric:
                self.renderer.scatter(df, feat, target, trendline=True, ax=ax)
            elif feat_is_cat and target_is_numeric:
                self.renderer.boxplot(df, feat, target, ax=ax)
            elif feat_is_numeric and not target_is_numeric:
                self.renderer.boxplot(df, target, feat, ax=ax)
            else:
                # Both categorical - use stacked bar or grouped bar
                self.renderer.bar(df[feat], feat, ax=ax)

        # Hide unused axes
        for j in range(i + 1, len(axes)):
            axes[j].set_visible(False)

        fig.suptitle(f'Feature Analysis vs {target}', fontsize=14, fontweight='bold')
        fig.tight_layout()

        return fig

    def show(
        self,
        df: pd.DataFrame,
        max_features: int = 8,
        figsize: Tuple[float, float] = None,
    ) -> Figure:
        """
        Automatic EDA - generates a dashboard of key visualizations.

        Parameters
        ----------
        df : pd.DataFrame
            The data to explore
        max_features : int
            Maximum number of features to show
        figsize : tuple, optional
            Figure size

        Returns
        -------
        fig : matplotlib Figure
        """
        profile = self.analyzer.analyze_dataframe(df)

        # Select most interesting columns
        numeric_cols = [c for c, p in profile.columns.items()
                       if p.dtype in (DataType.NUMERIC_CONTINUOUS, DataType.NUMERIC_DISCRETE)
                       and not p.is_id_column][:max_features//2]

        cat_cols = [c for c, p in profile.columns.items()
                   if p.dtype in (DataType.CATEGORICAL_LOW, DataType.CATEGORICAL_MEDIUM, DataType.BOOLEAN)][:max_features//2]

        n_plots = len(numeric_cols) + len(cat_cols)
        if profile.correlations is not None and len(numeric_cols) >= 2:
            n_plots += 1  # Add correlation heatmap

        if n_plots == 0:
            print("⚠️  No suitable columns found for visualization")
            return None

        n_cols = min(3, n_plots)
        n_rows = int(np.ceil(n_plots / n_cols))

        figsize = figsize or (5 * n_cols, 4 * n_rows)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = np.array(axes).flatten() if n_plots > 1 else [axes]

        plot_idx = 0

        # Numeric distributions
        for col in numeric_cols:
            self.renderer.histogram(df, col, ax=axes[plot_idx])
            plot_idx += 1

        # Categorical distributions
        for col in cat_cols:
            self.renderer.bar(df, col, ax=axes[plot_idx])
            plot_idx += 1

        # Correlation heatmap
        if profile.correlations is not None and len(numeric_cols) >= 2 and plot_idx < len(axes):
            self.renderer.heatmap(df[numeric_cols], ax=axes[plot_idx])
            plot_idx += 1

        # Hide unused axes
        for j in range(plot_idx, len(axes)):
            axes[j].set_visible(False)

        fig.suptitle('Data Overview', fontsize=16, fontweight='bold', y=1.02)
        fig.tight_layout()

        # Print summary
        print(f"\n📊 Dataset Summary:")
        print(f"   • {profile.n_rows:,} rows × {profile.n_cols} columns")
        print(f"   • {profile.complete_rows:,} complete rows ({profile.complete_rows/profile.n_rows:.1%})")
        print(f"   • {profile.duplicates:,} duplicate rows")
        print(f"   • Memory: {profile.memory_usage / 1024**2:.1f} MB")

        return fig

    def save(
        self,
        fig: Figure,
        path: str,
        dpi: int = None,
        transparent: bool = False,
        **kwargs
    ):
        """Save a figure to file."""
        dpi = dpi or self.config.dpi * 2  # Higher DPI for saving
        fig.savefig(path, dpi=dpi, transparent=transparent,
                   bbox_inches='tight', **kwargs)
        print(f"✅ Saved to {path}")


# ════════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL API (CONVENIENCE FUNCTIONS)
# ════════════════════════════════════════════════════════════════════════════════

# Global instance
_viz = InstaViz()


def set_theme(theme: Union[str, Theme]):
    """Set the global visualization theme."""
    _viz.set_theme(theme)


def set_config(**kwargs):
    """Update global configuration."""
    _viz.set_config(**kwargs)


def plot(df: pd.DataFrame, x: str = None, y: str = None, **kwargs) -> Tuple[Figure, Axes]:
    """Smart plotting - automatically chooses the best chart."""
    return _viz.plot(df, x, y, **kwargs)


def distribution(df: pd.DataFrame, column: str, **kwargs) -> Tuple[Figure, Axes]:
    """Analyze and visualize distribution."""
    return _viz.distribution(df, column, **kwargs)


def compare(df: pd.DataFrame, x: str, y: str, **kwargs) -> Tuple[Figure, Axes]:
    """Compare a numeric variable across categories."""
    return _viz.compare(df, x, y, **kwargs)


def trend(df: pd.DataFrame, date_col: str, value_col: str, **kwargs) -> Tuple[Figure, Axes]:
    """Visualize trends over time."""
    return _viz.trend(df, date_col, value_col, **kwargs)


def correlate(df: pd.DataFrame, **kwargs) -> Tuple[Figure, Axes]:
    """Visualize correlations."""
    return _viz.correlate(df, **kwargs)


def relationship(df: pd.DataFrame, x: str, y: str, **kwargs) -> Tuple[Figure, Axes]:
    """Visualize relationship between two variables."""
    return _viz.relationship(df, x, y, **kwargs)


def target(df: pd.DataFrame, target: str, **kwargs) -> Figure:
    """Analyze features against a target variable."""
    return _viz.target(df, target, **kwargs)


def show(df: pd.DataFrame, **kwargs) -> Figure:
    """Automatic EDA dashboard."""
    return _viz.show(df, **kwargs)


def save(fig: Figure, path: str, **kwargs):
    """Save a figure to file."""
    _viz.save(fig, path, **kwargs)