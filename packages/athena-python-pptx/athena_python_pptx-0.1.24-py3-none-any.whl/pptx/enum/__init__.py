"""
Enumerations for python-pptx compatibility.

This module provides enumerations that match the python-pptx API.
"""

from .shapes import MSO_SHAPE, MSO_SHAPE_TYPE, MSO_CONNECTOR_TYPE, PP_PLACEHOLDER
from .text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_PARAGRAPH_ALIGNMENT
from .dml import MSO_THEME_COLOR, MSO_LINE_DASH_STYLE, MSO_FILL_TYPE
from .chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from .action import PP_ACTION_TYPE

__all__ = [
    # Shapes
    "MSO_SHAPE",
    "MSO_SHAPE_TYPE",
    "MSO_CONNECTOR_TYPE",
    "PP_PLACEHOLDER",
    # Text
    "MSO_ANCHOR",
    "MSO_AUTO_SIZE",
    "PP_PARAGRAPH_ALIGNMENT",
    # DML
    "MSO_THEME_COLOR",
    "MSO_LINE_DASH_STYLE",
    "MSO_FILL_TYPE",
    # Chart
    "XL_CHART_TYPE",
    "XL_LEGEND_POSITION",
    # Action
    "PP_ACTION_TYPE",
]
