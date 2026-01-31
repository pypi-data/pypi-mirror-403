"""
Crosstabs MCP Server - Statistical Analysis via Model Context Protocol

A comprehensive MCP server providing 40+ statistical tools for contingency
table analysis, including chi-square tests, Fisher's exact test, effect sizes,
ordinal measures, and more.
"""

__version__ = "1.0.0"

from .server import (
    StatisticalEngine,
    OrdinalTests,
    TrendTests,
    PowerAnalysis,
    MultipleComparison,
    VisualizationData,
    AdditionalStats,
)

__all__ = [
    "StatisticalEngine",
    "OrdinalTests",
    "TrendTests",
    "PowerAnalysis",
    "MultipleComparison",
    "VisualizationData",
    "AdditionalStats",
]
