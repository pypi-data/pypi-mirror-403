"""
Unit conversion utilities mirroring python-pptx conventions.

EMU (English Metric Units) is the native unit used internally.
1 inch = 914400 EMU
1 cm = 360000 EMU
1 pt = 12700 EMU
"""

from __future__ import annotations
from typing import Union

# EMU constants
EMU_PER_INCH = 914400
EMU_PER_CM = 360000
EMU_PER_MM = 36000
EMU_PER_PT = 12700
EMU_PER_CENTIPOINT = 127
EMU_PER_PX = 9525  # At 96 DPI


class Emu(int):
    """
    EMU (English Metric Units) value.

    EMU is the native unit used in OOXML and this SDK.
    1 inch = 914400 EMU
    """

    def __new__(cls, value: Union[int, float, 'Emu']) -> 'Emu':
        return super().__new__(cls, int(round(value)))

    @property
    def inches(self) -> float:
        """Return value in inches."""
        return int(self) / EMU_PER_INCH

    @property
    def cm(self) -> float:
        """Return value in centimeters."""
        return int(self) / EMU_PER_CM

    @property
    def mm(self) -> float:
        """Return value in millimeters."""
        return int(self) / EMU_PER_MM

    @property
    def pt(self) -> float:
        """Return value in points."""
        return int(self) / EMU_PER_PT

    @property
    def centipoints(self) -> float:
        """Return value in centipoints (1/100 of a point)."""
        return int(self) / EMU_PER_CENTIPOINT

    @property
    def px(self) -> float:
        """Return value in pixels (at 96 DPI)."""
        return int(self) / EMU_PER_PX

    @property
    def emu(self) -> int:
        """Return raw EMU value."""
        return int(self)

    # -------------------------------------------------------------------------
    # Arithmetic operations (return Emu objects)
    # -------------------------------------------------------------------------

    def __add__(self, other: Union[int, float, 'Emu']) -> 'Emu':
        """Add two EMU values."""
        return Emu(int(self) + int(other))

    def __radd__(self, other: Union[int, float, 'Emu']) -> 'Emu':
        """Add two EMU values (reversed)."""
        return Emu(int(other) + int(self))

    def __sub__(self, other: Union[int, float, 'Emu']) -> 'Emu':
        """Subtract EMU values."""
        return Emu(int(self) - int(other))

    def __rsub__(self, other: Union[int, float, 'Emu']) -> 'Emu':
        """Subtract EMU values (reversed)."""
        return Emu(int(other) - int(self))

    def __mul__(self, other: Union[int, float]) -> 'Emu':
        """Multiply EMU by a scalar."""
        return Emu(int(self) * other)

    def __rmul__(self, other: Union[int, float]) -> 'Emu':
        """Multiply EMU by a scalar (reversed)."""
        return Emu(other * int(self))

    def __truediv__(self, other: Union[int, float]) -> 'Emu':
        """Divide EMU by a scalar."""
        return Emu(int(self) / other)

    def __floordiv__(self, other: Union[int, float]) -> 'Emu':
        """Integer divide EMU by a scalar."""
        return Emu(int(self) // other)

    def __neg__(self) -> 'Emu':
        """Negate EMU value."""
        return Emu(-int(self))

    def __abs__(self) -> 'Emu':
        """Absolute value of EMU."""
        return Emu(abs(int(self)))

    # -------------------------------------------------------------------------
    # Convenience conversion methods
    # -------------------------------------------------------------------------

    def to_inches(self) -> float:
        """Convert to inches (same as .inches property)."""
        return self.inches

    def to_cm(self) -> float:
        """Convert to centimeters (same as .cm property)."""
        return self.cm

    def to_pt(self) -> float:
        """Convert to points (same as .pt property)."""
        return self.pt

    def to_px(self, dpi: int = 96) -> float:
        """
        Convert to pixels at specified DPI.

        Args:
            dpi: Dots per inch (default 96)

        Returns:
            Pixel value at the specified DPI
        """
        inches = int(self) / EMU_PER_INCH
        return inches * dpi

    @classmethod
    def from_inches(cls, value: Union[int, float]) -> 'Emu':
        """Create Emu from inches."""
        return cls(value * EMU_PER_INCH)

    @classmethod
    def from_cm(cls, value: Union[int, float]) -> 'Emu':
        """Create Emu from centimeters."""
        return cls(value * EMU_PER_CM)

    @classmethod
    def from_pt(cls, value: Union[int, float]) -> 'Emu':
        """Create Emu from points."""
        return cls(value * EMU_PER_PT)

    @classmethod
    def from_px(cls, value: Union[int, float], dpi: int = 96) -> 'Emu':
        """
        Create Emu from pixels at specified DPI.

        Args:
            value: Pixel value
            dpi: Dots per inch (default 96)
        """
        inches = value / dpi
        return cls(inches * EMU_PER_INCH)

    def __repr__(self) -> str:
        return f"Emu({int(self)})"


def Inches(n: Union[int, float]) -> Emu:
    """
    Convert inches to EMU.

    Example:
        >>> Inches(1)
        Emu(914400)
        >>> Inches(0.5)
        Emu(457200)
    """
    return Emu(n * EMU_PER_INCH)


def Cm(n: Union[int, float]) -> Emu:
    """
    Convert centimeters to EMU.

    Example:
        >>> Cm(2.54)  # approximately 1 inch
        Emu(914400)
    """
    return Emu(n * EMU_PER_CM)


def Mm(n: Union[int, float]) -> Emu:
    """
    Convert millimeters to EMU.

    Example:
        >>> Mm(25.4)  # 1 inch
        Emu(914400)
    """
    return Emu(n * EMU_PER_MM)


def Pt(n: Union[int, float]) -> Emu:
    """
    Convert points to EMU.

    Example:
        >>> Pt(72)  # 1 inch
        Emu(914400)
    """
    return Emu(n * EMU_PER_PT)


def Centipoints(n: Union[int, float]) -> Emu:
    """
    Convert centipoints (1/100 of a point) to EMU.

    Example:
        >>> Centipoints(7200)  # 72 points = 1 inch
        Emu(914400)
    """
    return Emu(n * EMU_PER_CENTIPOINT)


def Px(n: Union[int, float]) -> Emu:
    """
    Convert pixels (at 96 DPI) to EMU.

    Example:
        >>> Px(96)  # 1 inch at 96 DPI
        Emu(914400)
    """
    return Emu(n * EMU_PER_PX)


# Type alias for EMU values accepted in APIs
Length = Union[int, Emu]


def ensure_emu(value: Length) -> Emu:
    """Ensure a value is an Emu instance."""
    if isinstance(value, Emu):
        return value
    return Emu(value)
