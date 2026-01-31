"""
Command dataclasses for the PPTX SDK.

Commands represent atomic operations that are sent to the server.
They are validated client-side before transmission.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, Union
from .errors import ValidationError
from .typing import ShapeId, TextRunPath, TextStyle


@dataclass
class Command:
    """Base class for all commands."""

    def to_dict(self) -> dict[str, Any]:
        """Convert command to dictionary for JSON serialization."""
        result = {"type": self.command_type}
        for key, value in asdict(self).items():
            if value is not None and key != "command_type":
                # Convert snake_case to camelCase
                camel_key = self._to_camel_case(key)
                result[camel_key] = value
        return result

    @staticmethod
    def _to_camel_case(snake_str: str) -> str:
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def validate(self) -> None:
        """Validate command parameters. Raises ValidationError if invalid."""
        pass

    @property
    def command_type(self) -> str:
        """Return the command type string."""
        raise NotImplementedError


@dataclass
class AddTextBox(Command):
    """
    Add a textbox to a slide.

    Args:
        slide_index: Zero-based index of the slide
        x_emu: X position in EMU
        y_emu: Y position in EMU
        w_emu: Width in EMU
        h_emu: Height in EMU
        client_id: Client-provided ID for the new shape (optional, for batch mode)
        text: Initial text content (optional)
        font_color_hex: Font color as 6-character hex (optional)
        font_size_pt: Font size in points (optional)
        bold: Bold text (optional)
        italic: Italic text (optional)
    """

    slide_index: int
    x_emu: int
    y_emu: int
    w_emu: int
    h_emu: int
    client_id: Optional[str] = None
    text: Optional[str] = None
    font_color_hex: Optional[str] = None
    font_size_pt: Optional[float] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None

    @property
    def command_type(self) -> str:
        return "AddTextBox"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")
        if self.w_emu < 0:
            raise ValidationError("width must be non-negative", "w_emu")
        if self.h_emu < 0:
            raise ValidationError("height must be non-negative", "h_emu")


@dataclass
class SetText(Command):
    """
    Set the text content of a shape.

    Args:
        shape_id: ID of the shape to modify
        text: New text content (replaces entire text body)
    """

    shape_id: ShapeId
    text: str

    @property
    def command_type(self) -> str:
        return "SetText"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")


@dataclass
class SetTransform(Command):
    """
    Set the position and size of a shape.

    Args:
        shape_id: ID of the shape to modify
        x_emu: X position in EMU (optional)
        y_emu: Y position in EMU (optional)
        w_emu: Width in EMU (optional)
        h_emu: Height in EMU (optional)
        rot_deg: Rotation in degrees (optional)
        flip_h: Flip horizontally (optional)
        flip_v: Flip vertically (optional)
    """

    shape_id: ShapeId
    x_emu: Optional[int] = None
    y_emu: Optional[int] = None
    w_emu: Optional[int] = None
    h_emu: Optional[int] = None
    rot_deg: Optional[float] = None
    flip_h: Optional[bool] = None
    flip_v: Optional[bool] = None

    @property
    def command_type(self) -> str:
        return "SetTransform"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.w_emu is not None and self.w_emu < 0:
            raise ValidationError("width must be non-negative", "w_emu")
        if self.h_emu is not None and self.h_emu < 0:
            raise ValidationError("height must be non-negative", "h_emu")


@dataclass
class SetRunStyle(Command):
    """
    Set styling for a specific text run.

    Args:
        shape_id: ID of the shape containing the text
        path: Path to the text run (paragraph index, run index)
        style: Style properties to set
    """

    shape_id: ShapeId
    path: TextRunPath
    style: TextStyle

    @property
    def command_type(self) -> str:
        return "SetRunStyle"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if "p" not in self.path or "r" not in self.path:
            raise ValidationError("path must contain 'p' and 'r'", "path")


@dataclass
class AddSlide(Command):
    """
    Add a new slide to the presentation.

    Args:
        index: Position to insert the slide (optional, defaults to end)
        layout_index: Layout template index (optional)
    """

    index: Optional[int] = None
    layout_index: Optional[int] = None

    @property
    def command_type(self) -> str:
        return "AddSlide"

    def validate(self) -> None:
        if self.index is not None and self.index < 0:
            raise ValidationError("index must be non-negative", "index")


@dataclass
class DeleteSlide(Command):
    """
    Delete a slide from the presentation.

    Args:
        slide_index: Zero-based index of the slide to delete
    """

    slide_index: int

    @property
    def command_type(self) -> str:
        return "DeleteSlide"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")


@dataclass
class DeleteShape(Command):
    """
    Delete a shape from a slide.

    Args:
        shape_id: ID of the shape to delete
    """

    shape_id: ShapeId

    @property
    def command_type(self) -> str:
        return "DeleteShape"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")


@dataclass
class SetParagraphStyle(Command):
    """
    Set paragraph styling (alignment, level, bullet type).

    Args:
        shape_id: ID of the shape containing the text
        paragraph_index: Zero-based paragraph index
        alignment: Alignment ('left', 'center', 'right', 'justify')
        level: Indentation level (0-8) for bullet hierarchy
        bullet: Bullet type ('none', 'disc', 'circle', 'square', 'numbered')
        bullet_color_hex: Bullet color as 6-character hex string (e.g., "FF0000")
        line_spacing: Line spacing multiplier
        space_before_emu: Space before paragraph in EMU
        space_after_emu: Space after paragraph in EMU
        margin_left_emu: Left margin in EMU
        indent_emu: First-line indent in EMU
    """

    shape_id: ShapeId
    paragraph_index: int
    alignment: Optional[str] = None
    level: Optional[int] = None
    bullet: Optional[str] = None
    bullet_color_hex: Optional[str] = None
    line_spacing: Optional[float] = None
    space_before_emu: Optional[int] = None
    space_after_emu: Optional[int] = None
    margin_left_emu: Optional[int] = None
    indent_emu: Optional[int] = None

    @property
    def command_type(self) -> str:
        return "SetParagraphStyle"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.paragraph_index < 0:
            raise ValidationError("paragraph_index must be non-negative", "paragraph_index")
        if self.alignment and self.alignment not in ("left", "center", "right", "justify"):
            raise ValidationError(
                "alignment must be 'left', 'center', 'right', or 'justify'", "alignment"
            )
        if self.level is not None and (self.level < 0 or self.level > 8):
            raise ValidationError("level must be between 0 and 8", "level")


@dataclass
class AddShape(Command):
    """
    Add an autoshape to a slide.

    Args:
        slide_index: Zero-based index of the slide
        shape_type: Shape type name (e.g., 'rectangle', 'oval', 'triangle')
        x_emu: X position in EMU
        y_emu: Y position in EMU
        w_emu: Width in EMU
        h_emu: Height in EMU
        client_id: Client-provided ID (optional)
        fill_color_hex: Fill color as 6-character hex string
        line_color_hex: Line/stroke color as 6-character hex string
        line_width_emu: Line width in EMU
        text: Initial text content
    """

    slide_index: int
    shape_type: str
    x_emu: int
    y_emu: int
    w_emu: int
    h_emu: int
    client_id: Optional[str] = None
    fill_color_hex: Optional[str] = None
    line_color_hex: Optional[str] = None
    line_width_emu: Optional[int] = None
    text: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "AddShape"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")
        if not self.shape_type:
            raise ValidationError("shape_type is required", "shape_type")
        if self.w_emu < 0:
            raise ValidationError("width must be non-negative", "w_emu")
        if self.h_emu < 0:
            raise ValidationError("height must be non-negative", "h_emu")


@dataclass
class SetShapeStyle(Command):
    """
    Set fill and line styling for a shape.

    Args:
        shape_id: ID of the shape to style
        fill_color_hex: Fill color (6-char hex) or None to remove
        fill_transparency: Fill transparency (0.0-1.0)
        line_color_hex: Line color (6-char hex) or None to remove
        line_width_emu: Line width in EMU
        line_dash: Line dash style
    """

    shape_id: ShapeId
    fill_color_hex: Optional[str] = None
    fill_transparency: Optional[float] = None
    line_color_hex: Optional[str] = None
    line_width_emu: Optional[int] = None
    line_dash: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "SetShapeStyle"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.fill_transparency is not None and not (0.0 <= self.fill_transparency <= 1.0):
            raise ValidationError("fill_transparency must be between 0.0 and 1.0", "fill_transparency")


@dataclass
class AddPicture(Command):
    """
    Add an image to a slide.

    Args:
        slide_index: Zero-based index of the slide
        x_emu: X position in EMU
        y_emu: Y position in EMU
        w_emu: Width in EMU (optional - uses image native size if not specified)
        h_emu: Height in EMU (optional)
        client_id: Client-provided ID (optional)
        image_base64: Image data as base64 string
        image_format: Image format ('png', 'jpeg', 'gif', 'bmp', 'tiff')
    """

    slide_index: int
    x_emu: int
    y_emu: int
    image_base64: str
    image_format: str
    w_emu: Optional[int] = None
    h_emu: Optional[int] = None
    client_id: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "AddPicture"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")
        if not self.image_base64:
            raise ValidationError("image_base64 is required", "image_base64")
        if self.image_format not in ("png", "jpeg", "gif", "bmp", "tiff"):
            raise ValidationError(
                "image_format must be 'png', 'jpeg', 'gif', 'bmp', or 'tiff'", "image_format"
            )


@dataclass
class AddTable(Command):
    """
    Add a table to a slide.

    Args:
        slide_index: Zero-based index of the slide
        rows: Number of rows
        cols: Number of columns
        x_emu: X position in EMU
        y_emu: Y position in EMU
        w_emu: Width in EMU
        h_emu: Height in EMU
        client_id: Client-provided ID (optional)
    """

    slide_index: int
    rows: int
    cols: int
    x_emu: int
    y_emu: int
    w_emu: int
    h_emu: int
    client_id: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "AddTable"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")
        if self.rows < 1 or self.rows > 100:
            raise ValidationError("rows must be between 1 and 100", "rows")
        if self.cols < 1 or self.cols > 26:
            raise ValidationError("cols must be between 1 and 26", "cols")
        if self.w_emu < 0:
            raise ValidationError("width must be non-negative", "w_emu")
        if self.h_emu < 0:
            raise ValidationError("height must be non-negative", "h_emu")


@dataclass
class SetTableCell(Command):
    """
    Set content and style of a table cell.

    Args:
        shape_id: ID of the table shape
        row: Row index (0-based)
        col: Column index (0-based)
        text: Cell text content
        fill_color_hex: Cell background color
    """

    shape_id: ShapeId
    row: int
    col: int
    text: Optional[str] = None
    fill_color_hex: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "SetTableCell"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.row < 0:
            raise ValidationError("row must be non-negative", "row")
        if self.col < 0:
            raise ValidationError("col must be non-negative", "col")


@dataclass
class SetSlideBackground(Command):
    """
    Set slide background color or fill.

    Args:
        slide_index: Zero-based index of the slide
        color_hex: Background color as 6-character hex string
        follow_master: Whether to follow master slide background
    """

    slide_index: int
    color_hex: Optional[str] = None
    follow_master: Optional[bool] = None

    @property
    def command_type(self) -> str:
        return "SetSlideBackground"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")


@dataclass
class SetSlideNotes(Command):
    """
    Set slide notes/speaker notes.

    Args:
        slide_index: Zero-based index of the slide
        notes: Notes text content
    """

    slide_index: int
    notes: str

    @property
    def command_type(self) -> str:
        return "SetSlideNotes"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")


@dataclass
class ReorderSlides(Command):
    """
    Reorder slides in the presentation.

    Args:
        new_order: List of slide indices in the new order
    """

    new_order: list[int]

    @property
    def command_type(self) -> str:
        return "ReorderSlides"

    def validate(self) -> None:
        if not self.new_order:
            raise ValidationError("new_order must not be empty", "new_order")
        for i, index in enumerate(self.new_order):
            if index < 0:
                raise ValidationError(f"Invalid index at position {i}: {index}", "new_order")


@dataclass
class CloneSlide(Command):
    """
    Clone a slide with all its content.

    Creates a duplicate of the slide at the specified source index,
    including all shapes, text, and formatting.

    Args:
        source_index: Zero-based index of the slide to clone
        target_index: Zero-based index where the clone should be inserted
                     (optional, defaults to after source slide)
    """

    source_index: int
    target_index: Optional[int] = None

    @property
    def command_type(self) -> str:
        return "CloneSlide"

    def validate(self) -> None:
        if self.source_index < 0:
            raise ValidationError("source_index must be non-negative", "source_index")
        if self.target_index is not None and self.target_index < 0:
            raise ValidationError("target_index must be non-negative", "target_index")


@dataclass
class SetTextFrameProperties(Command):
    """
    Set text frame properties for a shape.

    Controls word wrapping, auto-sizing behavior, vertical alignment,
    and text margins within the shape.

    Args:
        shape_id: ID of the shape to modify
        word_wrap: Enable word wrapping (text wraps at shape boundary)
        auto_size: Auto-size behavior ('none', 'shape_to_fit_text', 'text_to_fit_shape')
        vertical_anchor: Vertical text anchor ('top', 'middle', 'bottom')
        margin_left: Left margin/inset in EMUs
        margin_right: Right margin/inset in EMUs
        margin_top: Top margin/inset in EMUs
        margin_bottom: Bottom margin/inset in EMUs
    """

    shape_id: ShapeId
    word_wrap: Optional[bool] = None
    auto_size: Optional[str] = None
    vertical_anchor: Optional[str] = None
    margin_left: Optional[int] = None
    margin_right: Optional[int] = None
    margin_top: Optional[int] = None
    margin_bottom: Optional[int] = None

    @property
    def command_type(self) -> str:
        return "SetTextFrameProperties"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.auto_size is not None and self.auto_size not in ('none', 'shape_to_fit_text', 'text_to_fit_shape'):
            raise ValidationError(
                "auto_size must be 'none', 'shape_to_fit_text', or 'text_to_fit_shape'",
                "auto_size"
            )
        if self.vertical_anchor is not None and self.vertical_anchor not in ('top', 'middle', 'bottom'):
            raise ValidationError(
                "vertical_anchor must be 'top', 'middle', or 'bottom'",
                "vertical_anchor"
            )


# -------------------------------------------------------------------------
# Phase 3 Commands: Visual Styling & Layout
# -------------------------------------------------------------------------


@dataclass
class SetShapeShadow(Command):
    """
    Set shadow effect on a shape.

    Args:
        shape_id: ID of the shape
        visible: Whether shadow is visible
        shadow_type: Shadow type ('outer', 'inner', 'perspective')
        blur_radius_emu: Blur radius in EMU (default ~50000 = ~4pt)
        distance_emu: Distance from shape in EMU
        direction_deg: Shadow direction in degrees (0 = right, 90 = down)
        color_hex: Shadow color as 6-character hex
        transparency: Shadow transparency (0.0-1.0)
    """

    shape_id: ShapeId
    visible: Optional[bool] = None
    shadow_type: Optional[str] = None
    blur_radius_emu: Optional[int] = None
    distance_emu: Optional[int] = None
    direction_deg: Optional[float] = None
    color_hex: Optional[str] = None
    transparency: Optional[float] = None

    @property
    def command_type(self) -> str:
        return "SetShapeShadow"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.shadow_type is not None and self.shadow_type not in ('outer', 'inner', 'perspective'):
            raise ValidationError(
                "shadow_type must be 'outer', 'inner', or 'perspective'",
                "shadow_type"
            )
        if self.transparency is not None and not (0.0 <= self.transparency <= 1.0):
            raise ValidationError("transparency must be between 0.0 and 1.0", "transparency")


@dataclass
class SetGradientFill(Command):
    """
    Set gradient fill on a shape.

    Args:
        shape_id: ID of the shape
        gradient_type: Gradient type ('linear', 'radial', 'rectangular', 'path')
        angle_deg: Rotation angle in degrees (for linear gradient)
        stops: List of gradient stops, each with 'position' (0.0-1.0) and 'color_hex'
    """

    shape_id: ShapeId
    gradient_type: str
    angle_deg: Optional[float] = None
    stops: Optional[list[dict[str, Any]]] = None

    @property
    def command_type(self) -> str:
        return "SetGradientFill"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.gradient_type not in ('linear', 'radial', 'rectangular', 'path'):
            raise ValidationError(
                "gradient_type must be 'linear', 'radial', 'rectangular', or 'path'",
                "gradient_type"
            )
        if self.stops:
            for i, stop in enumerate(self.stops):
                if 'position' not in stop or 'color_hex' not in stop:
                    raise ValidationError(
                        f"Stop {i} must have 'position' and 'color_hex'",
                        "stops"
                    )
                if not (0.0 <= stop['position'] <= 1.0):
                    raise ValidationError(
                        f"Stop {i} position must be between 0.0 and 1.0",
                        "stops"
                    )


@dataclass
class SetShapeZOrder(Command):
    """
    Change z-order of a shape (bring forward/backward).

    Args:
        shape_id: ID of the shape
        action: Z-order action ('to_front', 'to_back', 'forward', 'backward')
    """

    shape_id: ShapeId
    action: str

    @property
    def command_type(self) -> str:
        return "SetShapeZOrder"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.action not in ('to_front', 'to_back', 'forward', 'backward'):
            raise ValidationError(
                "action must be 'to_front', 'to_back', 'forward', or 'backward'",
                "action"
            )


@dataclass
class AddConnector(Command):
    """
    Add a connector line between two shapes.

    Args:
        slide_index: Zero-based index of the slide
        connector_type: Connector type ('straight', 'elbow', 'curved')
        begin_shape_id: ID of the shape where connector starts (optional)
        begin_x_emu: Start X position in EMU (if no begin_shape_id)
        begin_y_emu: Start Y position in EMU (if no begin_shape_id)
        end_shape_id: ID of the shape where connector ends (optional)
        end_x_emu: End X position in EMU (if no end_shape_id)
        end_y_emu: End Y position in EMU (if no end_shape_id)
        line_color_hex: Line color as 6-character hex
        line_width_emu: Line width in EMU
        begin_arrow: Begin arrow style ('none', 'triangle', 'stealth', 'diamond', 'oval', 'open')
        end_arrow: End arrow style
        client_id: Client-provided ID (optional)
    """

    slide_index: int
    connector_type: str
    begin_shape_id: Optional[ShapeId] = None
    begin_x_emu: Optional[int] = None
    begin_y_emu: Optional[int] = None
    end_shape_id: Optional[ShapeId] = None
    end_x_emu: Optional[int] = None
    end_y_emu: Optional[int] = None
    line_color_hex: Optional[str] = None
    line_width_emu: Optional[int] = None
    begin_arrow: Optional[str] = None
    end_arrow: Optional[str] = None
    client_id: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "AddConnector"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")
        if self.connector_type not in ('straight', 'elbow', 'curved'):
            raise ValidationError(
                "connector_type must be 'straight', 'elbow', or 'curved'",
                "connector_type"
            )
        # Must have either shape_id or coordinates for both begin and end
        if self.begin_shape_id is None and (self.begin_x_emu is None or self.begin_y_emu is None):
            raise ValidationError(
                "Either begin_shape_id or both begin_x_emu and begin_y_emu required",
                "begin"
            )
        if self.end_shape_id is None and (self.end_x_emu is None or self.end_y_emu is None):
            raise ValidationError(
                "Either end_shape_id or both end_x_emu and end_y_emu required",
                "end"
            )
        arrow_styles = ('none', 'triangle', 'stealth', 'diamond', 'oval', 'open')
        if self.begin_arrow is not None and self.begin_arrow not in arrow_styles:
            raise ValidationError(f"begin_arrow must be one of {arrow_styles}", "begin_arrow")
        if self.end_arrow is not None and self.end_arrow not in arrow_styles:
            raise ValidationError(f"end_arrow must be one of {arrow_styles}", "end_arrow")


@dataclass
class SetSlideLayout(Command):
    """
    Set the layout for a slide.

    Args:
        slide_index: Zero-based index of the slide
        layout_index: Index of the layout in the slide master
        layout_name: Name of the layout (alternative to index)
    """

    slide_index: int
    layout_index: Optional[int] = None
    layout_name: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "SetSlideLayout"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")
        if self.layout_index is None and self.layout_name is None:
            raise ValidationError(
                "Either layout_index or layout_name is required",
                "layout"
            )


# -------------------------------------------------------------------------
# Phase 4 Commands: Presentation Properties & Names
# -------------------------------------------------------------------------


@dataclass
class SetCoreProperties(Command):
    """
    Set core document properties (metadata).

    Args:
        title: Document title
        author: Document author
        subject: Document subject
        keywords: Document keywords (comma-separated or list)
        comments: Document comments/description
        category: Document category
        last_modified_by: Last modified by user
    """

    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    comments: Optional[str] = None
    category: Optional[str] = None
    last_modified_by: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "SetCoreProperties"

    def validate(self) -> None:
        # At least one property should be set
        if all(v is None for v in [
            self.title, self.author, self.subject,
            self.keywords, self.comments, self.category,
            self.last_modified_by
        ]):
            raise ValidationError(
                "At least one property must be set",
                "properties"
            )


@dataclass
class SetShapeName(Command):
    """
    Set the name of a shape.

    Args:
        shape_id: ID of the shape
        name: New name for the shape
    """

    shape_id: ShapeId
    name: str

    @property
    def command_type(self) -> str:
        return "SetShapeName"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if not self.name:
            raise ValidationError("name is required", "name")


@dataclass
class SetSlideName(Command):
    """
    Set the name of a slide.

    Args:
        slide_index: Zero-based index of the slide
        name: New name for the slide
    """

    slide_index: int
    name: str

    @property
    def command_type(self) -> str:
        return "SetSlideName"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")
        if not self.name:
            raise ValidationError("name is required", "name")


@dataclass
class SetClickAction(Command):
    """
    Set click action (hyperlink) for a shape.

    Args:
        shape_id: ID of the shape
        action_type: Type of action ('hyperlink', 'slide', 'none')
        hyperlink_url: URL for hyperlink action
        target_slide_index: Target slide index for slide action
        tooltip: Tooltip text to show on hover
    """

    shape_id: ShapeId
    action_type: str
    hyperlink_url: Optional[str] = None
    target_slide_index: Optional[int] = None
    tooltip: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "SetClickAction"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        valid_types = ('hyperlink', 'slide', 'none', 'first_slide', 'last_slide',
                       'next_slide', 'previous_slide', 'end_show')
        if self.action_type not in valid_types:
            raise ValidationError(
                f"action_type must be one of {valid_types}",
                "action_type"
            )
        if self.action_type == 'hyperlink' and not self.hyperlink_url:
            raise ValidationError(
                "hyperlink_url is required for hyperlink action",
                "hyperlink_url"
            )
        if self.action_type == 'slide' and self.target_slide_index is None:
            raise ValidationError(
                "target_slide_index is required for slide action",
                "target_slide_index"
            )


@dataclass
class SetPresentationSize(Command):
    """
    Set presentation slide dimensions.

    Args:
        width_emu: Slide width in EMU
        height_emu: Slide height in EMU
    """

    width_emu: int
    height_emu: int

    @property
    def command_type(self) -> str:
        return "SetPresentationSize"

    def validate(self) -> None:
        if self.width_emu <= 0:
            raise ValidationError("width_emu must be positive", "width_emu")
        if self.height_emu <= 0:
            raise ValidationError("height_emu must be positive", "height_emu")


# -------------------------------------------------------------------------
# Phase 5 Commands: Notes, Layouts & Content Operations
# -------------------------------------------------------------------------


@dataclass
class CloneShape(Command):
    """
    Clone/duplicate a shape.

    Args:
        shape_id: ID of the shape to clone
        target_slide_index: Slide to place the clone (None = same slide)
        offset_x_emu: Horizontal offset from original position
        offset_y_emu: Vertical offset from original position
        client_id: Client-provided ID for the new shape
    """

    shape_id: ShapeId
    target_slide_index: Optional[int] = None
    offset_x_emu: int = 228600  # Default ~0.25 inch offset
    offset_y_emu: int = 228600
    client_id: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "CloneShape"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.target_slide_index is not None and self.target_slide_index < 0:
            raise ValidationError("target_slide_index must be non-negative", "target_slide_index")


@dataclass
class GroupShapes(Command):
    """
    Group multiple shapes together.

    Args:
        slide_index: Slide containing the shapes
        shape_ids: List of shape IDs to group
        client_id: Client-provided ID for the group shape
    """

    slide_index: int
    shape_ids: list[str]
    client_id: Optional[str] = None

    @property
    def command_type(self) -> str:
        return "GroupShapes"

    def validate(self) -> None:
        if self.slide_index < 0:
            raise ValidationError("slide_index must be non-negative", "slide_index")
        if not self.shape_ids or len(self.shape_ids) < 2:
            raise ValidationError("At least 2 shape_ids required for grouping", "shape_ids")


@dataclass
class UngroupShapes(Command):
    """
    Ungroup a group shape.

    Args:
        group_shape_id: ID of the group shape to ungroup
    """

    group_shape_id: ShapeId

    @property
    def command_type(self) -> str:
        return "UngroupShapes"

    def validate(self) -> None:
        if not self.group_shape_id:
            raise ValidationError("group_shape_id is required", "group_shape_id")


@dataclass
class SetShapeAdjustments(Command):
    """
    Set adjustment values for adjustable shapes.

    Adjustment values control shape-specific parameters like corner radius
    for rounded rectangles, arrow head size, etc.

    Args:
        shape_id: ID of the shape
        adjustments: Dictionary of adjustment name to value (0.0-1.0 typically)
    """

    shape_id: ShapeId
    adjustments: dict[str, float]

    @property
    def command_type(self) -> str:
        return "SetShapeAdjustments"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if not self.adjustments:
            raise ValidationError("adjustments must not be empty", "adjustments")


@dataclass
class FitText(Command):
    """
    Auto-fit text to shape by adjusting font size.

    Args:
        shape_id: ID of the shape containing text
        max_font_size_pt: Maximum font size in points
        min_font_size_pt: Minimum font size in points (default 6)
        font_family: Font family to use (optional)
        bold: Whether text should be bold (optional)
    """

    shape_id: ShapeId
    max_font_size_pt: float = 18.0
    min_font_size_pt: float = 6.0
    font_family: Optional[str] = None
    bold: Optional[bool] = None

    @property
    def command_type(self) -> str:
        return "FitText"

    def validate(self) -> None:
        if not self.shape_id:
            raise ValidationError("shape_id is required", "shape_id")
        if self.max_font_size_pt <= 0:
            raise ValidationError("max_font_size_pt must be positive", "max_font_size_pt")
        if self.min_font_size_pt <= 0:
            raise ValidationError("min_font_size_pt must be positive", "min_font_size_pt")
        if self.min_font_size_pt > self.max_font_size_pt:
            raise ValidationError(
                "min_font_size_pt must be <= max_font_size_pt",
                "min_font_size_pt"
            )


# Type alias for any command
AnyCommand = Union[
    AddTextBox,
    SetText,
    SetTransform,
    SetRunStyle,
    AddSlide,
    DeleteSlide,
    DeleteShape,
    SetParagraphStyle,
    AddShape,
    SetShapeStyle,
    AddPicture,
    AddTable,
    SetTableCell,
    SetSlideBackground,
    SetSlideNotes,
    ReorderSlides,
    CloneSlide,
    SetTextFrameProperties,
    # Phase 3
    SetShapeShadow,
    SetGradientFill,
    SetShapeZOrder,
    AddConnector,
    SetSlideLayout,
    # Phase 4
    SetCoreProperties,
    SetShapeName,
    SetSlideName,
    SetClickAction,
    SetPresentationSize,
    # Phase 5
    CloneShape,
    GroupShapes,
    UngroupShapes,
    SetShapeAdjustments,
    FitText,
]
