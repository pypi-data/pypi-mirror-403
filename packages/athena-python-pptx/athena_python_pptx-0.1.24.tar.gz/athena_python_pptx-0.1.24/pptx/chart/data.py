"""
Chart data classes matching python-pptx.

These are stub implementations that raise UnsupportedFeatureError.
"""

from __future__ import annotations
from typing import Any, Sequence

from ..errors import UnsupportedFeatureError


class CategoryChartData:
    """
    Chart data for category-based charts.

    This is a stub implementation - charts are not yet supported.
    """

    def __init__(self) -> None:
        self._categories: list[str] = []
        self._series: list[tuple[str, Sequence[float]]] = []

    @property
    def categories(self) -> list[str]:
        """Category labels."""
        return self._categories

    @categories.setter
    def categories(self, value: Sequence[str]) -> None:
        """Set category labels."""
        self._categories = list(value)

    def add_series(self, name: str, values: Sequence[float], number_format: str = "") -> None:
        """
        Add a data series.

        Note: This method stores data but actual chart creation is not yet supported.
        """
        self._series.append((name, values))

    def _raise_not_supported(self) -> None:
        raise UnsupportedFeatureError(
            "CategoryChartData",
            "Charts are not yet supported. Data can be stored but charts cannot be created."
        )


# Alias for compatibility
ChartData = CategoryChartData


class XyChartData:
    """
    Chart data for XY (scatter) charts.

    This is a stub implementation - charts are not yet supported.
    """

    def __init__(self) -> None:
        self._series: list[Any] = []

    def add_series(self, name: str, values: Any = None) -> Any:
        """
        Add a data series.

        Raises:
            UnsupportedFeatureError: Charts are not yet supported
        """
        raise UnsupportedFeatureError(
            "XyChartData.add_series",
            "XY charts are not yet supported"
        )


class BubbleChartData:
    """
    Chart data for bubble charts.

    This is a stub implementation - charts are not yet supported.
    """

    def __init__(self) -> None:
        self._series: list[Any] = []

    def add_series(self, name: str, values: Any = None) -> Any:
        """
        Add a data series.

        Raises:
            UnsupportedFeatureError: Charts are not yet supported
        """
        raise UnsupportedFeatureError(
            "BubbleChartData.add_series",
            "Bubble charts are not yet supported"
        )
