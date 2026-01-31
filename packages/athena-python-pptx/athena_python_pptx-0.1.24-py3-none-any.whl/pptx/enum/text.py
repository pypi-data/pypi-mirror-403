"""
Text-related enumerations matching python-pptx.

Provides MSO_ANCHOR (vertical alignment), MSO_AUTO_SIZE, and
PP_PARAGRAPH_ALIGNMENT enumerations.
"""

from enum import IntEnum


class MSO_ANCHOR(IntEnum):
    """
    Vertical anchor/alignment enumeration (MSO_VERTICAL_ANCHOR).

    Specifies the vertical alignment of text in a text frame.
    """
    TOP = 1
    MIDDLE = 3
    BOTTOM = 4
    MIXED = -2


# Alias for compatibility
MSO_VERTICAL_ANCHOR = MSO_ANCHOR


class MSO_AUTO_SIZE(IntEnum):
    """
    Auto-size behavior enumeration.

    Specifies how a text frame responds to text that exceeds its bounds.
    """
    NONE = 0
    SHAPE_TO_FIT_TEXT = 1
    TEXT_TO_FIT_SHAPE = 2


class PP_PARAGRAPH_ALIGNMENT(IntEnum):
    """
    Paragraph horizontal alignment enumeration (PP_ALIGN).

    Specifies the horizontal alignment of a paragraph.
    """
    CENTER = 2
    DISTRIBUTE = 5
    JUSTIFY = 4
    JUSTIFY_LOW = 7
    LEFT = 1
    RIGHT = 3
    THAI_DISTRIBUTE = 6
    MIXED = -2


# Alias for compatibility
PP_ALIGN = PP_PARAGRAPH_ALIGNMENT


class MSO_TEXT_UNDERLINE_TYPE(IntEnum):
    """
    Underline type enumeration.

    Specifies the underline style for text.
    """
    NONE = 0
    SINGLE_LINE = 1
    DOUBLE_LINE = 3
    HEAVY_LINE = 4
    DOTTED_LINE = 5
    DASHED_LINE = 6
    DOT_DASH_LINE = 8
    DOT_DOT_DASH_LINE = 9
    WAVY_LINE = 10
    WAVY_HEAVY_LINE = 11
    WAVY_DOUBLE_LINE = 12
