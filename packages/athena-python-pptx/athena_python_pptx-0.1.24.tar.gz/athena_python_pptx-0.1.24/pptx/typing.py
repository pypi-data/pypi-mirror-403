"""
Type definitions and protocols for the PPTX SDK.
"""

from __future__ import annotations
from typing import Any, Literal, Optional, Protocol, TypedDict, Union
from dataclasses import dataclass
from enum import IntEnum


# Type aliases for IDs
DeckId = str
SlideId = str
ShapeId = str
ElementId = str
ExportJobId = str
RenderJobId = str


# Placeholder types (matching OOXML spec and python-pptx's PP_PLACEHOLDER_TYPE)
PlaceholderTypeLiteral = Literal[
    "title",
    "body",
    "ctrTitle",
    "subTitle",
    "dt",
    "sldNum",
    "ftr",
    "hdr",
    "pic",
    "chart",
    "tbl",
    "clipArt",
    "dgm",
    "media",
    "sldImg",
    "obj",
    "secHead",
]


class PP_PLACEHOLDER(IntEnum):
    """
    Placeholder type enumeration.

    Mirrors python-pptx's PP_PLACEHOLDER_TYPE.
    """

    BODY = 2
    CHART = 8
    BITMAP = 9
    CENTER_TITLE = 3
    DATE = 16
    FOOTER = 15
    HEADER = 14
    MEDIA_CLIP = 10
    OBJECT = 7
    SLIDE_IMAGE = 11
    SLIDE_NUMBER = 13
    SUBTITLE = 4
    TABLE = 12
    TITLE = 1
    PICTURE = 18
    VERTICAL_BODY = 5
    VERTICAL_OBJECT = 17
    VERTICAL_TEXT = 6
    VERTICAL_TITLE = 19

    # Map from OOXML string type to enum value
    @classmethod
    def from_ooxml_type(cls, ooxml_type: str) -> "PP_PLACEHOLDER":
        """Convert OOXML placeholder type string to enum value."""
        mapping = {
            "title": cls.TITLE,
            "body": cls.BODY,
            "ctrTitle": cls.CENTER_TITLE,
            "subTitle": cls.SUBTITLE,
            "dt": cls.DATE,
            "sldNum": cls.SLIDE_NUMBER,
            "ftr": cls.FOOTER,
            "hdr": cls.HEADER,
            "pic": cls.PICTURE,
            "chart": cls.CHART,
            "tbl": cls.TABLE,
            "clipArt": cls.BITMAP,
            "dgm": cls.OBJECT,  # SmartArt/Diagram -> object
            "media": cls.MEDIA_CLIP,
            "sldImg": cls.SLIDE_IMAGE,
            "obj": cls.OBJECT,
            "secHead": cls.TITLE,  # Section header -> title
        }
        return mapping.get(ooxml_type, cls.OBJECT)


# Command types
CommandType = Literal[
    "AddTextBox",
    "SetText",
    "SetTransform",
    "SetRunStyle",
    "AddSlide",
    "DeleteSlide",
    "DeleteShape",
]


class Transform(TypedDict, total=False):
    """Transform specification in EMUs."""

    x: int
    y: int
    w: int
    h: int
    rot: float
    flipH: bool
    flipV: bool


class TextRunPath(TypedDict):
    """Path to a specific text run within a shape."""

    p: int  # Paragraph index
    r: int  # Run index


class TextStyle(TypedDict, total=False):
    """Text styling options."""

    fontSizePt: float
    fontFamily: str
    bold: bool
    italic: bool
    underline: bool
    colorHex: str


@dataclass
class SlideSnapshot:
    """Snapshot of a slide's state."""

    id: SlideId
    index: int
    element_ids: list[ElementId]
    background_color_hex: Optional[str] = None
    notes: Optional[str] = None
    layout_path: Optional[str] = None


@dataclass
class PlaceholderSnapshot:
    """Snapshot of placeholder format info."""

    type: PlaceholderTypeLiteral
    idx: int
    sz: Optional[Literal["full", "half", "quarter"]] = None
    has_custom_prompt: Optional[bool] = None


@dataclass
class ElementSnapshot:
    """Snapshot of an element's state."""

    id: ElementId
    type: Literal["text", "shape", "image", "chart", "table", "group", "unknown"]
    slide_id: SlideId
    transform: Transform
    preview_text: Optional[str] = None
    placeholder: Optional[PlaceholderSnapshot] = None
    properties: Optional[dict[str, Any]] = None
    source: Optional[Literal["ingested", "sdk"]] = None


@dataclass
class DeckSnapshot:
    """Complete snapshot of a deck's state."""

    deck_id: DeckId
    name: str
    slide_width_emu: int
    slide_height_emu: int
    slide_count: int
    slides: list[SlideSnapshot]
    elements: dict[ElementId, ElementSnapshot]


class CommandDict(TypedDict, total=False):
    """Generic command dictionary."""

    type: CommandType
    slideIndex: int
    shapeId: ShapeId
    xEmu: int
    yEmu: int
    wEmu: int
    hEmu: int
    rotDeg: float
    text: str
    path: TextRunPath
    style: TextStyle


class CommandsRequest(TypedDict):
    """Request body for POST /commands."""

    client: dict[str, str]
    txn: dict[str, str]
    commands: list[CommandDict]
    return_: dict[str, bool]


class CommandsResponse(TypedDict, total=False):
    """Response from POST /commands."""

    applied: bool
    created: dict[str, list[str]]
    snapshot: DeckSnapshot
    error: dict[str, Any]


class ExportStatus(TypedDict, total=False):
    """Export job status."""

    job_id: ExportJobId
    status: Literal["queued", "processing", "completed", "failed"]
    download_url: Optional[str]
    error: Optional[str]


class RenderStatus(TypedDict, total=False):
    """Render job status."""

    job_id: RenderJobId
    status: Literal["queued", "processing", "completed", "failed"]
    image_url: Optional[str]
    error: Optional[str]


class ShapeProtocol(Protocol):
    """Protocol for shape objects."""

    @property
    def shape_id(self) -> ShapeId:
        ...

    @property
    def left(self) -> int:
        ...

    @property
    def top(self) -> int:
        ...

    @property
    def width(self) -> int:
        ...

    @property
    def height(self) -> int:
        ...


class TextFrameProtocol(Protocol):
    """Protocol for text frame objects."""

    @property
    def text(self) -> str:
        ...

    @text.setter
    def text(self, value: str) -> None:
        ...
