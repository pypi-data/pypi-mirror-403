"""
Shape-related enumerations matching python-pptx.

Provides MSO_SHAPE (auto shape types), MSO_SHAPE_TYPE, MSO_CONNECTOR_TYPE,
and PP_PLACEHOLDER enumerations.
"""

from enum import IntEnum
from typing import Optional


# Mapping from MSO_SHAPE enum values to backend shape type strings
_MSO_SHAPE_TO_STRING = {
    1: 'rectangle',  # RECTANGLE
    2: 'parallelogram',  # PARALLELOGRAM
    3: 'trapezoid',  # TRAPEZOID
    4: 'diamond',  # DIAMOND
    5: 'rounded_rectangle',  # ROUNDED_RECTANGLE
    6: 'octagon',  # OCTAGON
    7: 'triangle',  # ISOSCELES_TRIANGLE
    8: 'right_triangle',  # RIGHT_TRIANGLE
    9: 'oval',  # OVAL
    10: 'hexagon',  # HEXAGON
    11: 'cross',  # CROSS
    56: 'pentagon',  # REGULAR_PENTAGON / PENTAGON
    145: 'heptagon',  # HEPTAGON
    144: 'decagon',  # DECAGON
    146: 'dodecagon',  # DODECAGON
    # Arrows
    13: 'right_arrow',  # RIGHT_ARROW
    66: 'left_arrow',  # LEFT_ARROW
    68: 'up_arrow',  # UP_ARROW
    67: 'down_arrow',  # DOWN_ARROW
    69: 'left_right_arrow',  # LEFT_RIGHT_ARROW
    70: 'up_down_arrow',  # UP_DOWN_ARROW
    76: 'quad_arrow',  # QUAD_ARROW
    182: 'left_right_up_arrow',  # LEFT_RIGHT_UP_ARROW
    91: 'bent_arrow',  # BENT_ARROW
    101: 'u_turn_arrow',  # U_TURN_ARROW
    89: 'left_up_arrow',  # LEFT_UP_ARROW
    90: 'bent_up_arrow',  # BENT_UP_ARROW
    102: 'curved_right_arrow',  # CURVED_RIGHT_ARROW
    103: 'curved_left_arrow',  # CURVED_LEFT_ARROW
    104: 'curved_up_arrow',  # CURVED_UP_ARROW
    105: 'curved_down_arrow',  # CURVED_DOWN_ARROW
    93: 'striped_right_arrow',  # STRIPED_RIGHT_ARROW
    94: 'notched_right_arrow',  # NOTCHED_RIGHT_ARROW
    55: 'chevron',  # CHEVRON
    78: 'right_arrow_callout',  # RIGHT_ARROW_CALLOUT
    # Block shapes
    20: 'block_arc',  # BLOCK_ARC
    # Stars
    187: 'star4',  # STAR_4_POINT
    12: 'star5',  # STAR_5_POINT
    147: 'star6',  # STAR_6_POINT
    148: 'star7',  # STAR_7_POINT
    58: 'star8',  # STAR_8_POINT
    149: 'star10',  # STAR_10_POINT
    150: 'star12',  # STAR_12_POINT
    59: 'star16',  # STAR_16_POINT
    95: 'star24',  # STAR_24_POINT
    96: 'star32',  # STAR_32_POINT
    # Callouts
    41: 'callout_rectangle',  # RECTANGULAR_CALLOUT
    42: 'callout_rounded_rectangle',  # ROUNDED_RECTANGULAR_CALLOUT
    43: 'callout_oval',  # OVAL_CALLOUT
    44: 'callout_cloud',  # CLOUD_CALLOUT
    109: 'line_callout_1',  # LINE_CALLOUT_1
    110: 'line_callout_2',  # LINE_CALLOUT_2
    111: 'line_callout_3',  # LINE_CALLOUT_3
    112: 'line_callout_4',  # LINE_CALLOUT_4
    # Flowchart
    61: 'flowchart_process',  # FLOWCHART_PROCESS
    62: 'flowchart_decision',  # FLOWCHART_DECISION
    64: 'flowchart_data',  # FLOWCHART_DATA
    65: 'flowchart_predefined_process',  # FLOWCHART_PREDEFINED_PROCESS
    # 66 already mapped to left_arrow
    # 67 already mapped to down_arrow
    # 68 already mapped to up_arrow
    69: 'flowchart_terminator',  # FLOWCHART_TERMINATOR (conflicts, using arrow)
    # Basic shapes
    22: 'can',  # CAN
    23: 'cube',  # CUBE
    197: 'bevel',  # BEVEL
    18: 'donut',  # DONUT
    19: 'no_symbol',  # NO_SYMBOL
    158: 'frame',  # FRAME
    159: 'half_frame',  # HALF_FRAME
    160: 'corner',  # L_SHAPE / CORNER
    141: 'diagonal_stripe',  # DIAGONAL_STRIPE
    162: 'corner',  # CORNER
    25: 'arc',  # ARC
    28: 'plaque',  # PLAQUE
    161: 'chord',  # CHORD
    179: 'cloud',  # CLOUD
    142: 'pie',  # PIE
    17: 'smiley_face',  # SMILEY_FACE
    21: 'heart',  # HEART
    26: 'lightning_bolt',  # LIGHTNING_BOLT
    24: 'sun',  # SUN
    27: 'moon',  # MOON
    # Lines
    1000: 'line',  # LINE
}


def mso_shape_to_string(shape: "MSO_SHAPE") -> str:
    """
    Convert an MSO_SHAPE enum value to the backend shape type string.

    Args:
        shape: MSO_SHAPE enum value

    Returns:
        String shape type name for the backend API
    """
    if isinstance(shape, str):
        # Already a string (e.g., user passed 'rectangle' directly)
        return shape.lower()

    value = int(shape)
    result = _MSO_SHAPE_TO_STRING.get(value)
    if result:
        return result

    # Fallback: convert enum name to lowercase snake_case
    if hasattr(shape, 'name'):
        return shape.name.lower()

    # Last resort: return rectangle as default
    return 'rectangle'


class MSO_SHAPE(IntEnum):
    """
    AutoShape type enumeration (MSO_AUTO_SHAPE_TYPE).

    Specifies the type of AutoShape for shapes.add_shape().
    Values match those in python-pptx.
    """
    # Basic shapes
    RECTANGLE = 1
    PARALLELOGRAM = 2
    TRAPEZOID = 3
    DIAMOND = 4
    ROUNDED_RECTANGLE = 5
    OCTAGON = 6
    ISOSCELES_TRIANGLE = 7
    RIGHT_TRIANGLE = 8
    OVAL = 9
    HEXAGON = 10
    CROSS = 11
    REGULAR_PENTAGON = 56
    PENTAGON = 56  # Alias
    HEPTAGON = 145
    DECAGON = 144
    DODECAGON = 146

    # Arrows
    RIGHT_ARROW = 13
    LEFT_ARROW = 66
    UP_ARROW = 68
    DOWN_ARROW = 67
    LEFT_RIGHT_ARROW = 69
    UP_DOWN_ARROW = 70
    QUAD_ARROW = 76
    LEFT_RIGHT_UP_ARROW = 182
    BENT_ARROW = 91
    U_TURN_ARROW = 101
    LEFT_UP_ARROW = 89
    BENT_UP_ARROW = 90
    CURVED_RIGHT_ARROW = 102
    CURVED_LEFT_ARROW = 103
    CURVED_UP_ARROW = 104
    CURVED_DOWN_ARROW = 105
    STRIPED_RIGHT_ARROW = 93
    NOTCHED_RIGHT_ARROW = 94
    CHEVRON = 55
    RIGHT_ARROW_CALLOUT = 78
    LEFT_ARROW_CALLOUT = 77
    UP_ARROW_CALLOUT = 79
    DOWN_ARROW_CALLOUT = 80

    # Block arrows
    BLOCK_ARC = 20

    # Stars and banners
    STAR_4_POINT = 187
    STAR_5_POINT = 12
    STAR_6_POINT = 147
    STAR_7_POINT = 148
    STAR_8_POINT = 58
    STAR_10_POINT = 149
    STAR_12_POINT = 150
    STAR_16_POINT = 59
    STAR_24_POINT = 95
    STAR_32_POINT = 96
    EXPLOSION_1 = 89
    EXPLOSION_2 = 90
    HORIZONTAL_SCROLL = 98
    VERTICAL_SCROLL = 97
    WAVE = 64
    DOUBLE_WAVE = 188

    # Callouts
    RECTANGULAR_CALLOUT = 41
    ROUNDED_RECTANGULAR_CALLOUT = 42
    OVAL_CALLOUT = 43
    CLOUD_CALLOUT = 44
    LINE_CALLOUT_1 = 109
    LINE_CALLOUT_2 = 110
    LINE_CALLOUT_3 = 111
    LINE_CALLOUT_4 = 112
    LINE_CALLOUT_1_ACCENT_BAR = 113
    LINE_CALLOUT_2_ACCENT_BAR = 114
    LINE_CALLOUT_3_ACCENT_BAR = 115
    LINE_CALLOUT_4_ACCENT_BAR = 116
    LINE_CALLOUT_1_NO_BORDER = 117
    LINE_CALLOUT_2_NO_BORDER = 118
    LINE_CALLOUT_3_NO_BORDER = 119
    LINE_CALLOUT_4_NO_BORDER = 120
    LINE_CALLOUT_1_BORDER_AND_ACCENT_BAR = 121
    LINE_CALLOUT_2_BORDER_AND_ACCENT_BAR = 122
    LINE_CALLOUT_3_BORDER_AND_ACCENT_BAR = 123
    LINE_CALLOUT_4_BORDER_AND_ACCENT_BAR = 124

    # Flowchart
    FLOWCHART_PROCESS = 61
    FLOWCHART_ALTERNATE_PROCESS = 176
    FLOWCHART_DECISION = 62
    FLOWCHART_DATA = 64
    FLOWCHART_PREDEFINED_PROCESS = 65
    FLOWCHART_INTERNAL_STORAGE = 66
    FLOWCHART_DOCUMENT = 67
    FLOWCHART_MULTIDOCUMENT = 115
    FLOWCHART_TERMINATOR = 69
    FLOWCHART_PREPARATION = 70
    FLOWCHART_MANUAL_INPUT = 71
    FLOWCHART_MANUAL_OPERATION = 72
    FLOWCHART_CONNECTOR = 73
    FLOWCHART_OFFPAGE_CONNECTOR = 177
    FLOWCHART_CARD = 75
    FLOWCHART_PUNCHED_TAPE = 76
    FLOWCHART_SUMMING_JUNCTION = 78
    FLOWCHART_OR = 79
    FLOWCHART_COLLATE = 80
    FLOWCHART_SORT = 81
    FLOWCHART_EXTRACT = 82
    FLOWCHART_MERGE = 83
    FLOWCHART_STORED_DATA = 178
    FLOWCHART_DELAY = 84
    FLOWCHART_SEQUENTIAL_ACCESS_STORAGE = 85
    FLOWCHART_MAGNETIC_DISK = 86
    FLOWCHART_DIRECT_ACCESS_STORAGE = 87
    FLOWCHART_DISPLAY = 88

    # Basic shapes continued
    CAN = 22
    CUBE = 23
    BEVEL = 197
    DONUT = 18
    NO_SYMBOL = 19
    FRAME = 158
    HALF_FRAME = 159
    L_SHAPE = 160
    DIAGONAL_STRIPE = 141
    CORNER = 162
    ARC = 25
    PLAQUE = 28
    CHORD = 161
    CLOUD = 179
    PIE = 142
    PIE_WEDGE = 175
    # BLOCK_ARC already defined above
    FOLDED_CORNER = 65
    SMILEY_FACE = 17
    HEART = 21
    LIGHTNING_BOLT = 26
    SUN = 24
    MOON = 27
    TEAR = 160

    # Action buttons
    ACTION_BUTTON_BACK_OR_PREVIOUS = 194
    ACTION_BUTTON_BEGINNING = 196
    ACTION_BUTTON_BLANK = 189
    ACTION_BUTTON_DOCUMENT = 198
    ACTION_BUTTON_END = 195
    ACTION_BUTTON_FORWARD_OR_NEXT = 193
    ACTION_BUTTON_HELP = 191
    ACTION_BUTTON_HOME = 190
    ACTION_BUTTON_INFORMATION = 192
    ACTION_BUTTON_MOVIE = 200
    ACTION_BUTTON_RETURN = 197
    ACTION_BUTTON_SOUND = 199

    # Lines (not really autoshapes but included for compatibility)
    LINE = 1000  # Custom value for our implementation
    LINE_INVERSE = 1001


# Alias for compatibility
MSO_AUTO_SHAPE_TYPE = MSO_SHAPE


class MSO_SHAPE_TYPE(IntEnum):
    """
    Shape type enumeration.

    Identifies the type of a shape (autoshape, picture, chart, etc.).
    """
    AUTO_SHAPE = 1
    CALLOUT = 2
    CANVAS = 20
    CHART = 3
    COMMENT = 4
    CONTENT_APP = 25
    DIAGRAM = 21
    EMBEDDED_OLE_OBJECT = 7
    FORM_CONTROL = 8
    FREEFORM = 5
    GROUP = 6
    IGX_GRAPHIC = 24
    INK = 22
    INK_COMMENT = 23
    LINE = 9
    LINKED_OLE_OBJECT = 10
    LINKED_PICTURE = 11
    MEDIA = 16
    OLE_CONTROL_OBJECT = 12
    PICTURE = 13
    PLACEHOLDER = 14
    SCRIPT_ANCHOR = 18
    TABLE = 19
    TEXT_BOX = 17
    TEXT_EFFECT = 15
    WEB_VIDEO = 26


class MSO_CONNECTOR_TYPE(IntEnum):
    """
    Connector type enumeration.

    Specifies the type of connector.
    """
    CURVE = 3
    ELBOW = 2
    STRAIGHT = 1
    MIXED = -2


class PP_PLACEHOLDER(IntEnum):
    """
    Placeholder type enumeration (PP_PLACEHOLDER_TYPE).

    Specifies the type of placeholder shape.
    """
    TITLE = 1
    BODY = 2
    CENTER_TITLE = 3
    SUBTITLE = 4
    DATE = 10
    FOOTER = 11
    SLIDE_NUMBER = 12
    HEADER = 13
    OBJECT = 7
    CHART = 8
    TABLE = 9
    PICTURE = 18
    MEDIA_CLIP = 16
    ORG_CHART = 17
    BITMAP = 15
    VERTICAL_BODY = 5
    VERTICAL_OBJECT = 19
    VERTICAL_TITLE = 6
    MIXED = -2

    @classmethod
    def from_ooxml_type(cls, type_str: str) -> "PP_PLACEHOLDER":
        """
        Convert OOXML placeholder type string to PP_PLACEHOLDER enum.

        Args:
            type_str: OOXML placeholder type (e.g., 'title', 'body', 'ctrTitle')

        Returns:
            Corresponding PP_PLACEHOLDER enum member
        """
        mapping = {
            'title': cls.TITLE,
            'body': cls.BODY,
            'ctrTitle': cls.CENTER_TITLE,
            'subTitle': cls.SUBTITLE,
            'dt': cls.DATE,
            'ftr': cls.FOOTER,
            'sldNum': cls.SLIDE_NUMBER,
            'hdr': cls.HEADER,
            'obj': cls.OBJECT,
            'chart': cls.CHART,
            'tbl': cls.TABLE,
            'pic': cls.PICTURE,
            'media': cls.MEDIA_CLIP,
            'dgm': cls.ORG_CHART,
        }
        return mapping.get(type_str, cls.OBJECT)


# Alias for compatibility
PP_PLACEHOLDER_TYPE = PP_PLACEHOLDER
