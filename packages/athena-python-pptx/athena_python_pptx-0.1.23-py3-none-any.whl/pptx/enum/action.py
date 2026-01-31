"""
Action-related enumerations matching python-pptx.

Provides PP_ACTION_TYPE enumeration.
"""

from enum import IntEnum


class PP_ACTION_TYPE(IntEnum):
    """
    Action type enumeration.

    Specifies the action to take when a shape is clicked.
    """
    END_SHOW = 6
    FIRST_SLIDE = 3
    HYPERLINK = 7
    LAST_SLIDE = 4
    LAST_SLIDE_VIEWED = 5
    NAMED_SLIDE = 101
    NAMED_SLIDE_SHOW = 10
    NEXT_SLIDE = 1
    NONE = 0
    OLE_VERB = 11
    OPEN_FILE = 102
    PLAY = 12
    PREVIOUS_SLIDE = 2
    RUN_MACRO = 8
    RUN_PROGRAM = 9
