"""
DrawingML-related enumerations matching python-pptx.

Provides MSO_THEME_COLOR, MSO_LINE_DASH_STYLE, MSO_FILL_TYPE,
MSO_PATTERN_TYPE, and MSO_COLOR_TYPE enumerations.
"""

from enum import IntEnum


class MSO_THEME_COLOR(IntEnum):
    """
    Theme color enumeration (MSO_THEME_COLOR_INDEX).

    Specifies a theme color from the presentation's color scheme.
    """
    NOT_THEME_COLOR = 0
    ACCENT_1 = 5
    ACCENT_2 = 6
    ACCENT_3 = 7
    ACCENT_4 = 8
    ACCENT_5 = 9
    ACCENT_6 = 10
    BACKGROUND_1 = 14
    BACKGROUND_2 = 15
    DARK_1 = 1
    DARK_2 = 3
    FOLLOWED_HYPERLINK = 12
    HYPERLINK = 11
    LIGHT_1 = 2
    LIGHT_2 = 4
    TEXT_1 = 13
    TEXT_2 = 16
    MIXED = -2


# Alias for compatibility
MSO_THEME_COLOR_INDEX = MSO_THEME_COLOR


class MSO_LINE_DASH_STYLE(IntEnum):
    """
    Line dash style enumeration.

    Specifies the dash style of a line.
    """
    SOLID = 1
    SQUARE_DOT = 2
    ROUND_DOT = 3
    DASH = 4
    DASH_DOT = 5
    LONG_DASH = 6
    LONG_DASH_DOT = 7
    LONG_DASH_DOT_DOT = 8
    MIXED = -2


class MSO_FILL_TYPE(IntEnum):
    """
    Fill type enumeration.

    Identifies the type of fill applied to a shape.
    """
    BACKGROUND = 5
    GRADIENT = 3
    GROUP = 7
    PATTERNED = 2
    PICTURE = 6
    SOLID = 1
    TEXTURED = 4
    MIXED = -2


class MSO_PATTERN_TYPE(IntEnum):
    """
    Pattern type enumeration.

    Specifies the pattern used in a patterned fill.
    """
    CROSS = 51
    DARK_DOWNWARD_DIAGONAL = 15
    DARK_HORIZONTAL = 13
    DARK_UPWARD_DIAGONAL = 16
    DARK_VERTICAL = 14
    DASHED_DOWNWARD_DIAGONAL = 28
    DASHED_HORIZONTAL = 32
    DASHED_UPWARD_DIAGONAL = 27
    DASHED_VERTICAL = 31
    DIAGONAL_BRICK = 40
    DIAGONAL_CROSS = 54
    DIVOT = 46
    DOTTED_DIAMOND = 24
    DOTTED_GRID = 45
    DOWNWARD_DIAGONAL = 52
    HORIZONTAL = 49
    HORIZONTAL_BRICK = 35
    LARGE_CHECKER_BOARD = 36
    LARGE_CONFETTI = 33
    LARGE_GRID = 34
    LIGHT_DOWNWARD_DIAGONAL = 21
    LIGHT_HORIZONTAL = 19
    LIGHT_UPWARD_DIAGONAL = 22
    LIGHT_VERTICAL = 20
    MIXED = -2
    NARROW_HORIZONTAL = 30
    NARROW_VERTICAL = 29
    OUTLINED_DIAMOND = 41
    PERCENT_10 = 2
    PERCENT_20 = 3
    PERCENT_25 = 4
    PERCENT_30 = 5
    PERCENT_40 = 6
    PERCENT_5 = 1
    PERCENT_50 = 7
    PERCENT_60 = 8
    PERCENT_70 = 9
    PERCENT_75 = 10
    PERCENT_80 = 11
    PERCENT_90 = 12
    PLAID = 42
    SHINGLE = 47
    SMALL_CHECKER_BOARD = 17
    SMALL_CONFETTI = 37
    SMALL_GRID = 23
    SOLID_DIAMOND = 39
    SPHERE = 43
    TRELLIS = 18
    UPWARD_DIAGONAL = 53
    VERTICAL = 50
    WAVE = 48
    WEAVE = 44
    WIDE_DOWNWARD_DIAGONAL = 25
    WIDE_UPWARD_DIAGONAL = 26
    ZIG_ZAG = 38


class MSO_COLOR_TYPE(IntEnum):
    """
    Color type enumeration.

    Identifies the type of color specification.
    """
    RGB = 1
    SCHEME = 2
    HSL = 101
    PRESET = 102
    SCRGB = 103
    SYSTEM = 104
    MIXED = -2


class MSO_ANCHOR(IntEnum):
    """
    Text anchor (vertical alignment) enumeration.

    Specifies the vertical alignment of text within a text frame.
    """
    TOP = 1
    MIDDLE = 3
    BOTTOM = 2
    MIXED = -2


# Alias for compatibility
MSO_VERTICAL_ANCHOR = MSO_ANCHOR


class MSO_AUTO_SIZE(IntEnum):
    """
    Text auto-size enumeration.

    Specifies how the text frame automatically resizes.
    """
    NONE = 0
    SHAPE_TO_FIT_TEXT = 1
    TEXT_TO_FIT_SHAPE = 2
    MIXED = -2


class MSO_TEXT_ORIENTATION(IntEnum):
    """
    Text orientation enumeration.

    Specifies the orientation of text in a text frame.
    """
    DOWNWARD = 3
    HORIZONTAL = 1
    HORIZONTAL_ROTATED_FAR_EAST = 6
    MIXED = -2
    STACKED = 5
    UPWARD = 2
    VERTICAL = 4
    VERTICAL_FAR_EAST = 4


class PP_MEDIA_TYPE(IntEnum):
    """
    Media type enumeration.

    Specifies the type of media.
    """
    MOVIE = 2
    SOUND = 1
    MIXED = -2


class PP_PARAGRAPH_ALIGNMENT(IntEnum):
    """
    Paragraph alignment enumeration (PP_ALIGN).

    Specifies the horizontal alignment of text in a paragraph.
    """
    LEFT = 1
    CENTER = 2
    RIGHT = 3
    JUSTIFY = 4
    DISTRIBUTE = 5
    JUSTIFY_LOW = 6
    THAI_DISTRIBUTE = 7
    MIXED = -2


# Alias for compatibility
PP_ALIGN = PP_PARAGRAPH_ALIGNMENT
