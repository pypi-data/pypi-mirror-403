"""
Chart-related enumerations matching python-pptx.

Provides XL_CHART_TYPE, XL_LEGEND_POSITION, and XL_DATA_LABEL_POSITION
enumerations.
"""

from enum import IntEnum


class XL_CHART_TYPE(IntEnum):
    """
    Chart type enumeration.

    Specifies the type of chart.
    """
    # Area charts
    AREA = 1
    AREA_STACKED = 76
    AREA_STACKED_100 = 77
    THREE_D_AREA = -4098
    THREE_D_AREA_STACKED = 78
    THREE_D_AREA_STACKED_100 = 79

    # Bar charts
    BAR_CLUSTERED = 57
    BAR_OF_PIE = 71
    BAR_STACKED = 58
    BAR_STACKED_100 = 59
    THREE_D_BAR_CLUSTERED = 60
    THREE_D_BAR_STACKED = 61
    THREE_D_BAR_STACKED_100 = 62

    # Column charts
    COLUMN_CLUSTERED = 51
    COLUMN_STACKED = 52
    COLUMN_STACKED_100 = 53
    THREE_D_COLUMN = -4100
    THREE_D_COLUMN_CLUSTERED = 54
    THREE_D_COLUMN_STACKED = 55
    THREE_D_COLUMN_STACKED_100 = 56

    # Line charts
    LINE = 4
    LINE_MARKERS = 65
    LINE_MARKERS_STACKED = 66
    LINE_MARKERS_STACKED_100 = 67
    LINE_STACKED = 63
    LINE_STACKED_100 = 64
    THREE_D_LINE = -4101

    # Pie charts
    PIE = 5
    PIE_EXPLODED = 69
    PIE_OF_PIE = 68
    THREE_D_PIE = -4102
    THREE_D_PIE_EXPLODED = 70

    # Doughnut charts
    DOUGHNUT = -4120
    DOUGHNUT_EXPLODED = 80

    # Radar charts
    RADAR = -4151
    RADAR_FILLED = 82
    RADAR_MARKERS = 81

    # XY (Scatter) charts
    XY_SCATTER = -4169
    XY_SCATTER_LINES = 74
    XY_SCATTER_LINES_NO_MARKERS = 75
    XY_SCATTER_SMOOTH = 72
    XY_SCATTER_SMOOTH_NO_MARKERS = 73

    # Bubble charts
    BUBBLE = 15
    BUBBLE_THREE_D_EFFECT = 87

    # Stock charts
    STOCK_HLC = 88
    STOCK_OHLC = 89
    STOCK_VHLC = 90
    STOCK_VOHLC = 91

    # Surface charts
    SURFACE = 83
    SURFACE_TOP_VIEW = 85
    SURFACE_TOP_VIEW_WIREFRAME = 86
    SURFACE_WIREFRAME = 84

    # Combo charts
    COMBO_AREA_STACKED_LINE_COLUMN_CLUSTERED = 113
    COMBO_CLUSTERED_COLUMN_LINE = 109
    COMBO_CLUSTERED_COLUMN_LINE_SECONDARY = 110
    COMBO_STACKED_AREA_CLUSTERED_COLUMN = 112


class XL_LEGEND_POSITION(IntEnum):
    """
    Legend position enumeration.

    Specifies the position of a chart legend.
    """
    BOTTOM = -4107
    CORNER = 2
    CUSTOM = -4161
    LEFT = -4131
    RIGHT = -4152
    TOP = -4160


class XL_DATA_LABEL_POSITION(IntEnum):
    """
    Data label position enumeration.

    Specifies the position of data labels relative to data points.
    """
    ABOVE = 0
    BELOW = 1
    BEST_FIT = 5
    CENTER = -4108
    INSIDE_BASE = 4
    INSIDE_END = 3
    LEFT = -4131
    MIXED = 6
    OUTSIDE_END = 2
    RIGHT = -4152


class XL_TICK_MARK(IntEnum):
    """
    Tick mark enumeration.

    Specifies the tick mark style on an axis.
    """
    CROSS = 4
    INSIDE = 2
    NONE = -4142
    OUTSIDE = 3


class XL_TICK_LABEL_POSITION(IntEnum):
    """
    Tick label position enumeration.

    Specifies the position of tick labels relative to an axis.
    """
    HIGH = -4127
    LOW = -4134
    NEXT_TO_AXIS = 4
    NONE = -4142
