"""
Shape-related proxy classes.

Provides python-pptx-compatible Shape and Shapes collection abstractions.
"""

from __future__ import annotations
import base64
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union

from .commands import (
    AddTextBox, DeleteShape, SetTransform, AddShape as AddShapeCmd,
    SetShapeStyle, AddPicture as AddPictureCmd, AddTable as AddTableCmd,
    SetTableCell, SetShapeShadow, SetGradientFill, SetShapeZOrder,
    AddConnector as AddConnectorCmd, SetShapeName, SetClickAction,
    CloneShape, GroupShapes, UngroupShapes, SetShapeAdjustments,
)
from .dml.color import RGBColor, ColorFormat
from .errors import UnsupportedFeatureError
from .text import TextFrame
from .typing import ElementSnapshot, ShapeId, Transform, PlaceholderSnapshot, PP_PLACEHOLDER
from .units import Emu, Length, ensure_emu

if TYPE_CHECKING:
    from .batching import CommandBuffer
    from .slides import Slide


# MSO_SHAPE enumeration - maps python-pptx shape types to our string types
class MSO_SHAPE:
    """AutoShape type enumeration (matching python-pptx)."""
    # Basic shapes
    RECTANGLE = 'rectangle'
    ROUNDED_RECTANGLE = 'rounded_rectangle'
    OVAL = 'oval'
    DIAMOND = 'diamond'
    TRIANGLE = 'triangle'
    ISOSCELES_TRIANGLE = 'triangle'  # Alias
    RIGHT_TRIANGLE = 'right_triangle'
    PARALLELOGRAM = 'parallelogram'
    TRAPEZOID = 'trapezoid'
    PENTAGON = 'pentagon'
    REGULAR_PENTAGON = 'pentagon'  # Alias
    HEXAGON = 'hexagon'
    HEPTAGON = 'heptagon'
    OCTAGON = 'octagon'
    DECAGON = 'decagon'
    DODECAGON = 'dodecagon'

    # Stars
    STAR_4_POINT = 'star4'
    STAR_5_POINT = 'star5'
    STAR_6_POINT = 'star6'
    STAR_7_POINT = 'star7'
    STAR_8_POINT = 'star8'
    STAR_10_POINT = 'star10'
    STAR_12_POINT = 'star12'
    STAR_16_POINT = 'star16'
    STAR_24_POINT = 'star24'
    STAR_32_POINT = 'star32'

    # Arrows
    RIGHT_ARROW = 'right_arrow'
    LEFT_ARROW = 'left_arrow'
    UP_ARROW = 'up_arrow'
    DOWN_ARROW = 'down_arrow'
    LEFT_RIGHT_ARROW = 'left_right_arrow'
    UP_DOWN_ARROW = 'up_down_arrow'
    QUAD_ARROW = 'quad_arrow'
    LEFT_RIGHT_UP_ARROW = 'left_right_up_arrow'
    BENT_ARROW = 'bent_arrow'
    U_TURN_ARROW = 'u_turn_arrow'
    LEFT_UP_ARROW = 'left_up_arrow'
    BENT_UP_ARROW = 'bent_up_arrow'
    CURVED_RIGHT_ARROW = 'curved_right_arrow'
    CURVED_LEFT_ARROW = 'curved_left_arrow'
    CURVED_UP_ARROW = 'curved_up_arrow'
    CURVED_DOWN_ARROW = 'curved_down_arrow'
    STRIPED_RIGHT_ARROW = 'striped_right_arrow'
    NOTCHED_RIGHT_ARROW = 'notched_right_arrow'
    CHEVRON = 'chevron'
    RIGHT_ARROW_CALLOUT = 'right_arrow_callout'
    LEFT_ARROW_CALLOUT = 'left_arrow_callout'
    UP_ARROW_CALLOUT = 'up_arrow_callout'
    DOWN_ARROW_CALLOUT = 'down_arrow_callout'

    # Block shapes
    BLOCK_ARC = 'block_arc'

    # Flowchart shapes
    FLOWCHART_PROCESS = 'flowchart_process'
    FLOWCHART_ALTERNATE_PROCESS = 'flowchart_alternate_process'
    FLOWCHART_DECISION = 'flowchart_decision'
    FLOWCHART_DATA = 'flowchart_data'
    FLOWCHART_PREDEFINED_PROCESS = 'flowchart_predefined_process'
    FLOWCHART_INTERNAL_STORAGE = 'flowchart_internal_storage'
    FLOWCHART_DOCUMENT = 'flowchart_document'
    FLOWCHART_MULTIDOCUMENT = 'flowchart_multidocument'
    FLOWCHART_TERMINATOR = 'flowchart_terminator'
    FLOWCHART_PREPARATION = 'flowchart_preparation'
    FLOWCHART_MANUAL_INPUT = 'flowchart_manual_input'
    FLOWCHART_MANUAL_OPERATION = 'flowchart_manual_operation'
    FLOWCHART_CONNECTOR = 'flowchart_connector'
    FLOWCHART_OFFPAGE_CONNECTOR = 'flowchart_offpage_connector'
    FLOWCHART_CARD = 'flowchart_card'
    FLOWCHART_PUNCHED_TAPE = 'flowchart_punched_tape'
    FLOWCHART_SUMMING_JUNCTION = 'flowchart_summing_junction'
    FLOWCHART_OR = 'flowchart_or'
    FLOWCHART_COLLATE = 'flowchart_collate'
    FLOWCHART_SORT = 'flowchart_sort'
    FLOWCHART_EXTRACT = 'flowchart_extract'
    FLOWCHART_MERGE = 'flowchart_merge'
    FLOWCHART_STORED_DATA = 'flowchart_stored_data'
    FLOWCHART_DELAY = 'flowchart_delay'
    FLOWCHART_SEQUENTIAL_ACCESS_STORAGE = 'flowchart_sequential_access_storage'
    FLOWCHART_MAGNETIC_DISK = 'flowchart_magnetic_disk'
    FLOWCHART_DIRECT_ACCESS_STORAGE = 'flowchart_direct_access_storage'
    FLOWCHART_DISPLAY = 'flowchart_display'

    # Other shapes
    LINE = 'line'
    CLOUD = 'cloud'
    HEART = 'heart'
    LIGHTNING_BOLT = 'lightning_bolt'
    SUN = 'sun'
    MOON = 'moon'
    SMILEY_FACE = 'smiley_face'
    NO_SYMBOL = 'no_symbol'
    CROSS = 'cross'
    CUBE = 'cube'
    DONUT = 'donut'
    FRAME = 'frame'
    HALF_FRAME = 'half_frame'
    L_SHAPE = 'l_shape'
    CORNER = 'corner'
    DIAGONAL_STRIPE = 'diagonal_stripe'
    ARC = 'arc'
    CHORD = 'chord'
    PIE = 'pie'
    PIE_WEDGE = 'pie_wedge'
    TEAR = 'tear'
    PLAQUE = 'plaque'
    CAN = 'can'
    BEVEL = 'bevel'
    FOLDED_CORNER = 'folded_corner'

    # Callouts - both naming conventions for python-pptx compatibility
    RECTANGULAR_CALLOUT = 'callout_rectangle'
    ROUNDED_RECTANGULAR_CALLOUT = 'callout_rounded_rectangle'
    OVAL_CALLOUT = 'callout_oval'
    CLOUD_CALLOUT = 'callout_cloud'
    LINE_CALLOUT_1 = 'line_callout_1'
    LINE_CALLOUT_2 = 'line_callout_2'
    LINE_CALLOUT_3 = 'line_callout_3'
    LINE_CALLOUT_4 = 'line_callout_4'
    # Aliases with CALLOUT_ prefix
    CALLOUT_RECTANGLE = 'callout_rectangle'
    CALLOUT_ROUNDED_RECTANGLE = 'callout_rounded_rectangle'
    CALLOUT_OVAL = 'callout_oval'
    CALLOUT_CLOUD = 'callout_cloud'

    # Banners and scrolls
    HORIZONTAL_SCROLL = 'horizontal_scroll'
    VERTICAL_SCROLL = 'vertical_scroll'
    WAVE = 'wave'
    DOUBLE_WAVE = 'double_wave'

    # Action buttons
    ACTION_BUTTON_BACK_OR_PREVIOUS = 'action_button_back_or_previous'
    ACTION_BUTTON_BEGINNING = 'action_button_beginning'
    ACTION_BUTTON_BLANK = 'action_button_blank'
    ACTION_BUTTON_DOCUMENT = 'action_button_document'
    ACTION_BUTTON_END = 'action_button_end'
    ACTION_BUTTON_FORWARD_OR_NEXT = 'action_button_forward_or_next'
    ACTION_BUTTON_HELP = 'action_button_help'
    ACTION_BUTTON_HOME = 'action_button_home'
    ACTION_BUTTON_INFORMATION = 'action_button_information'
    ACTION_BUTTON_MOVIE = 'action_button_movie'
    ACTION_BUTTON_RETURN = 'action_button_return'
    ACTION_BUTTON_SOUND = 'action_button_sound'


class PlaceholderFormat:
    """
    Provides access to placeholder-specific properties.

    Mirrors python-pptx's _PlaceholderFormat class.
    """

    def __init__(self, placeholder_snapshot: PlaceholderSnapshot):
        self._type_str = placeholder_snapshot.type
        self._idx = placeholder_snapshot.idx
        self._sz = placeholder_snapshot.sz
        self._has_custom_prompt = placeholder_snapshot.has_custom_prompt

    @property
    def type(self) -> PP_PLACEHOLDER:
        """
        Placeholder type as PP_PLACEHOLDER enumeration member.

        Returns the placeholder type (e.g., PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.BODY).
        """
        return PP_PLACEHOLDER.from_ooxml_type(self._type_str)

    @property
    def idx(self) -> int:
        """
        Integer placeholder index.

        This value is unique for each placeholder on a slide and remains stable
        when the slide layout is changed.
        """
        return self._idx

    @property
    def sz(self) -> Optional[str]:
        """
        Placeholder size as OOXML string.

        Common values: 'full', 'half', 'quarter'.
        Returns None if not specified.
        """
        return self._sz

    @property
    def has_custom_prompt(self) -> bool:
        """
        True if this placeholder has a custom prompt text.

        Custom prompts override the default "Click to add..." text.
        """
        return self._has_custom_prompt or False

    # -------------------------------------------------------------------------
    # Convenience properties
    # -------------------------------------------------------------------------

    @property
    def is_title(self) -> bool:
        """True if this is a title placeholder."""
        return self._type_str in ('title', 'ctrTitle') or self._idx == 0

    @property
    def is_body(self) -> bool:
        """True if this is a body/content placeholder."""
        return self._type_str == 'body' or self._idx == 1

    @property
    def is_subtitle(self) -> bool:
        """True if this is a subtitle placeholder."""
        return self._type_str == 'subTitle'

    @property
    def is_picture(self) -> bool:
        """True if this is a picture placeholder."""
        return self._type_str == 'pic'

    @property
    def is_chart(self) -> bool:
        """True if this is a chart placeholder."""
        return self._type_str == 'chart'

    @property
    def is_table(self) -> bool:
        """True if this is a table placeholder."""
        return self._type_str == 'tbl'

    @property
    def is_footer(self) -> bool:
        """True if this is a footer placeholder."""
        return self._type_str == 'ftr'

    @property
    def is_date(self) -> bool:
        """True if this is a date placeholder."""
        return self._type_str == 'dt'

    @property
    def is_slide_number(self) -> bool:
        """True if this is a slide number placeholder."""
        return self._type_str == 'sldNum'

    @property
    def type_name(self) -> str:
        """Human-readable placeholder type name."""
        type_names = {
            'title': 'Title',
            'ctrTitle': 'Center Title',
            'subTitle': 'Subtitle',
            'body': 'Body',
            'pic': 'Picture',
            'chart': 'Chart',
            'tbl': 'Table',
            'dgm': 'Diagram',
            'media': 'Media',
            'clipArt': 'Clip Art',
            'ftr': 'Footer',
            'dt': 'Date',
            'sldNum': 'Slide Number',
            'hdr': 'Header',
        }
        return type_names.get(self._type_str, self._type_str or 'Unknown')

    def __repr__(self) -> str:
        return f"<PlaceholderFormat idx={self._idx} type={self._type_str}>"


class _FillColorFormat(ColorFormat):
    """
    ColorFormat subclass that notifies FillFormat when color changes.
    """

    def __init__(self, fill_format: "FillFormat", rgb: Optional[RGBColor] = None):
        super().__init__(rgb=rgb)
        self._fill_format = fill_format

    @ColorFormat.rgb.setter
    def rgb(self, value: RGBColor) -> None:
        """Set the RGB color and notify the fill format."""
        if not isinstance(value, RGBColor):
            raise TypeError(f"Expected RGBColor, got {type(value).__name__}")
        self._rgb = value
        self._theme_color = None
        self._fill_format._on_color_change(str(value))


class FillFormat:
    """
    Fill formatting for a shape.

    Provides access to shape fill properties like color and transparency.
    Mirrors python-pptx's FillFormat class.
    """

    def __init__(self, shape: Shape):
        self._shape = shape
        self._solid_color: Optional[str] = shape._properties.get("fillColorHex")
        self._transparency: float = 0.0
        self._type: Optional[str] = 'solid' if self._solid_color else None
        # Initialize fore_color ColorFormat
        rgb = RGBColor.from_string(self._solid_color) if self._solid_color else None
        self._fore_color_format = _FillColorFormat(self, rgb=rgb)

    def solid(self) -> None:
        """
        Set fill to solid color mode.

        After calling this method, set the color using `fore_color.rgb`.

        Example:
            shape.fill.solid()
            shape.fill.fore_color.rgb = RGBColor(0xFF, 0x00, 0x00)
        """
        self._type = 'solid'
        # Default to white if no color set
        if self._solid_color is None:
            self._solid_color = 'FFFFFF'
            self._fore_color_format._rgb = RGBColor(255, 255, 255)

    def solid_fill(self, color_hex: str) -> None:
        """
        Set fill to solid color mode with the specified color.

        Convenience method that combines solid() and setting fore_color.

        Args:
            color_hex: Color as hex string (e.g., "FF0000" or "#FF0000")

        Example:
            shape.fill.solid_fill("FF0000")
        """
        # Strip leading # if present
        if color_hex.startswith('#'):
            color_hex = color_hex[1:]
        self._solid_color = color_hex.upper()
        self._type = 'solid'
        self._fore_color_format._rgb = RGBColor.from_string(color_hex)
        self._emit_style_change()

    @property
    def type(self) -> Optional[str]:
        """
        Fill type ('solid', 'gradient', 'pattern', or None for no fill).
        """
        return self._type

    @property
    def fore_color(self) -> _FillColorFormat:
        """
        Foreground (fill) color as a ColorFormat object.

        Use `fore_color.rgb = RGBColor(...)` to set the color.
        """
        return self._fore_color_format

    def _on_color_change(self, hex_value: str) -> None:
        """Called by ColorFormat when color changes."""
        self._solid_color = hex_value.upper()
        self._type = 'solid'
        self._emit_style_change()

    @property
    def transparency(self) -> float:
        """Fill transparency (0.0 = opaque, 1.0 = fully transparent)."""
        return self._transparency

    @transparency.setter
    def transparency(self, value: float) -> None:
        """Set fill transparency."""
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"Transparency must be between 0.0 and 1.0, got {value}")
        self._transparency = value
        self._emit_style_change()

    def background(self) -> None:
        """Remove fill (make transparent/background)."""
        self._solid_color = None
        self._type = None
        self._fore_color_format._rgb = None
        self._emit_style_change()

    # -------------------------------------------------------------------------
    # Phase 3: Gradient fills
    # -------------------------------------------------------------------------

    def gradient(self) -> None:
        """
        Set fill to gradient mode.

        After calling this, configure the gradient using gradient_angle and
        gradient_stops properties.

        Example:
            shape.fill.gradient()
            shape.fill.gradient_angle = 45
            shape.fill.gradient_stops = [
                {'position': 0.0, 'color': RGBColor(255, 0, 0)},
                {'position': 1.0, 'color': RGBColor(0, 0, 255)},
            ]
        """
        self._type = 'gradient'
        if not hasattr(self, '_gradient_type'):
            self._gradient_type = 'linear'
        if not hasattr(self, '_gradient_angle'):
            self._gradient_angle = 0.0
        if not hasattr(self, '_gradient_stops'):
            self._gradient_stops = [
                {'position': 0.0, 'color_hex': 'FFFFFF'},
                {'position': 1.0, 'color_hex': '000000'},
            ]

    @property
    def gradient_angle(self) -> float:
        """
        Gradient rotation angle in degrees (for linear gradients).

        0 = left to right, 90 = top to bottom, 180 = right to left, etc.
        """
        return getattr(self, '_gradient_angle', 0.0)

    @gradient_angle.setter
    def gradient_angle(self, value: float) -> None:
        """Set gradient angle."""
        self._gradient_angle = value % 360
        if self._type == 'gradient':
            self._emit_gradient_change()

    @property
    def gradient_stops(self) -> list[dict]:
        """
        Gradient color stops.

        Each stop is a dict with 'position' (0.0-1.0) and 'color_hex' or 'color'.
        """
        return getattr(self, '_gradient_stops', [])

    @gradient_stops.setter
    def gradient_stops(self, stops: list[dict]) -> None:
        """
        Set gradient stops.

        Args:
            stops: List of dicts with 'position' (0.0-1.0) and either
                   'color_hex' (string) or 'color' (RGBColor)
        """
        normalized = []
        for stop in stops:
            pos = stop.get('position', 0.0)
            if 'color_hex' in stop:
                color_hex = stop['color_hex']
            elif 'color' in stop:
                color_hex = str(stop['color']).upper()
            else:
                color_hex = 'FFFFFF'
            normalized.append({'position': pos, 'color_hex': color_hex})
        self._gradient_stops = normalized
        if self._type == 'gradient':
            self._emit_gradient_change()

    def _emit_gradient_change(self) -> None:
        """Emit a SetGradientFill command."""
        if self._shape._buffer:
            cmd = SetGradientFill(
                shape_id=self._shape._shape_id,
                gradient_type=getattr(self, '_gradient_type', 'linear'),
                angle_deg=getattr(self, '_gradient_angle', 0.0),
                stops=getattr(self, '_gradient_stops', None),
            )
            self._shape._buffer.add(cmd)

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def has_fill(self) -> bool:
        """True if shape has a fill (not transparent)."""
        return self._type is not None and self._solid_color is not None

    @property
    def color_hex(self) -> Optional[str]:
        """Get fill color as hex string (without #)."""
        return self._solid_color

    @color_hex.setter
    def color_hex(self, value: str) -> None:
        """Set fill color from hex string."""
        if value.startswith('#'):
            value = value[1:]
        self._solid_color = value.upper()
        self._type = 'solid'
        self._fore_color_format._rgb = RGBColor.from_string(value)
        self._emit_style_change()

    @property
    def color_rgb(self) -> Optional[RGBColor]:
        """Get fill color as RGBColor object."""
        if self._solid_color:
            return RGBColor.from_string(self._solid_color)
        return None

    @color_rgb.setter
    def color_rgb(self, value: RGBColor) -> None:
        """Set fill color from RGBColor object."""
        self._solid_color = str(value).upper()
        self._type = 'solid'
        self._fore_color_format._rgb = value
        self._emit_style_change()

    def set_color(self, r: int, g: int, b: int) -> None:
        """
        Set fill color from RGB components.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        self.color_rgb = RGBColor(r, g, b)

    def _emit_style_change(self) -> None:
        """Emit a SetShapeStyle command."""
        if self._shape._buffer:
            cmd = SetShapeStyle(
                shape_id=self._shape._shape_id,
                fill_color_hex=self._solid_color,
                fill_transparency=self._transparency if self._transparency > 0 else None,
            )
            self._shape._buffer.add(cmd)


class _LineColorFormat(ColorFormat):
    """
    ColorFormat subclass that notifies LineFormat when color changes.
    """

    def __init__(self, line_format: "LineFormat", rgb: Optional[RGBColor] = None):
        super().__init__(rgb=rgb)
        self._line_format = line_format

    @ColorFormat.rgb.setter
    def rgb(self, value: RGBColor) -> None:
        """Set the RGB color and notify the line format."""
        if not isinstance(value, RGBColor):
            raise TypeError(f"Expected RGBColor, got {type(value).__name__}")
        self._rgb = value
        self._theme_color = None
        self._line_format._on_color_change(str(value))


class LineFormat:
    """
    Line formatting for a shape.

    Provides access to shape outline/border properties.
    Mirrors python-pptx's LineFormat class.
    """

    def __init__(self, shape: Shape):
        self._shape = shape
        self._color_hex: Optional[str] = shape._properties.get("strokeColorHex")
        self._width_emu: int = shape._properties.get("strokeWidthEmu", 12700)  # Default 1pt
        self._dash_style: str = 'solid'
        # Initialize color ColorFormat
        rgb = RGBColor.from_string(self._color_hex) if self._color_hex else None
        self._color_format = _LineColorFormat(self, rgb=rgb)

    @property
    def color(self) -> _LineColorFormat:
        """
        Line color as a ColorFormat object.

        Use `line.color.rgb = RGBColor(...)` to set the color,
        or `line.color = "FF0000"` for direct hex string assignment.
        """
        return self._color_format

    @color.setter
    def color(self, value: Optional[str]) -> None:
        """
        Set line color with a hex string.

        Args:
            value: Hex color string (e.g., "FF0000" or "#FF0000"), or None to clear.
        """
        if value is None:
            self._color_hex = None
            self._color_format._rgb = None
        else:
            if value.startswith('#'):
                value = value[1:]
            self._color_hex = value.upper()
            self._color_format._rgb = RGBColor.from_string(value)
        self._emit_style_change()

    def _on_color_change(self, hex_value: str) -> None:
        """Called by ColorFormat when color changes."""
        self._color_hex = hex_value.upper()
        self._emit_style_change()

    @property
    def width(self) -> Emu:
        """Line width in EMU."""
        return Emu(self._width_emu)

    @width.setter
    def width(self, value: Length) -> None:
        """Set line width."""
        self._width_emu = int(ensure_emu(value))
        self._emit_style_change()

    @property
    def dash_style(self) -> str:
        """Line dash style ('solid', 'dash', 'dot', 'dash_dot', 'long_dash', 'long_dash_dot')."""
        return self._dash_style

    @dash_style.setter
    def dash_style(self, value: Any) -> None:
        """
        Set line dash style.

        Args:
            value: Dash style - either a string ('solid', 'dash', 'dot', etc.)
                   or MSO_LINE_DASH_STYLE enum value
        """
        # Handle MSO_LINE_DASH_STYLE enum values (integers)
        if isinstance(value, int):
            # MSO_LINE_DASH_STYLE: SOLID=1, SQUARE_DOT=2, ROUND_DOT=3, DASH=4,
            # DASH_DOT=5, LONG_DASH=6, LONG_DASH_DOT=7, LONG_DASH_DOT_DOT=8
            int_to_str = {
                1: 'solid',
                2: 'dot',         # SQUARE_DOT
                3: 'dot',         # ROUND_DOT
                4: 'dash',
                5: 'dash_dot',
                6: 'long_dash',
                7: 'long_dash_dot',
                8: 'long_dash_dot',  # LONG_DASH_DOT_DOT -> long_dash_dot
            }
            value = int_to_str.get(value, 'solid')

        valid = ('solid', 'dash', 'dot', 'dash_dot', 'long_dash', 'long_dash_dot')
        if value not in valid:
            raise ValueError(f"Invalid dash_style: {value}. Must be one of {valid}")
        self._dash_style = value
        self._emit_style_change()

    @property
    def fill(self) -> "LineFillFormat":
        """
        Fill format for the line itself (for thick lines with patterns/gradients).

        For simple solid-color lines, use `line.color.rgb` instead.
        """
        if not hasattr(self, '_fill_format'):
            self._fill_format = LineFillFormat(self)
        return self._fill_format

    def no_fill(self) -> None:
        """
        Remove the line (no outline).

        After calling this method, the shape will have no visible outline.
        """
        self._color_hex = None
        self._color_format._rgb = None
        self._width_emu = 0
        self._emit_style_change()

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def has_line(self) -> bool:
        """True if shape has a visible line/outline."""
        return self._width_emu > 0 and self._color_hex is not None

    @property
    def color_hex(self) -> Optional[str]:
        """Get line color as hex string (without #)."""
        return self._color_hex

    @color_hex.setter
    def color_hex(self, value: str) -> None:
        """Set line color from hex string."""
        if value.startswith('#'):
            value = value[1:]
        self._color_hex = value.upper()
        self._color_format._rgb = RGBColor.from_string(value)
        self._emit_style_change()

    @property
    def color_rgb(self) -> Optional[RGBColor]:
        """Get line color as RGBColor object."""
        if self._color_hex:
            return RGBColor.from_string(self._color_hex)
        return None

    @color_rgb.setter
    def color_rgb(self, value: RGBColor) -> None:
        """Set line color from RGBColor object."""
        self._color_hex = str(value).upper()
        self._color_format._rgb = value
        self._emit_style_change()

    def set_color(self, r: int, g: int, b: int) -> None:
        """
        Set line color from RGB components.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        self.color_rgb = RGBColor(r, g, b)

    @property
    def width_pt(self) -> float:
        """Line width in points."""
        return self._width_emu / 12700

    @width_pt.setter
    def width_pt(self, value: float) -> None:
        """Set line width in points."""
        self._width_emu = int(value * 12700)
        self._emit_style_change()

    @property
    def is_solid(self) -> bool:
        """True if line style is solid."""
        return self._dash_style == 'solid'

    @property
    def is_dashed(self) -> bool:
        """True if line style is any dashed pattern."""
        return self._dash_style != 'solid'

    def _emit_style_change(self) -> None:
        """Emit a SetShapeStyle command."""
        if self._shape._buffer:
            cmd = SetShapeStyle(
                shape_id=self._shape._shape_id,
                line_color_hex=self._color_hex,
                line_width_emu=self._width_emu,
                line_dash=self._dash_style if self._dash_style != 'solid' else None,
            )
            self._shape._buffer.add(cmd)


class LineFillFormat:
    """
    Fill format for line fills (used for thick lines with patterns/gradients).

    For simple solid-color lines, use `line.color.rgb` instead.
    """

    def __init__(self, line_format: LineFormat):
        self._line_format = line_format
        self._type = 'solid'

    def solid(self) -> None:
        """Set solid fill for the line."""
        self._type = 'solid'

    def background(self) -> None:
        """Set background fill (transparent) for the line."""
        self._type = 'background'
        self._line_format.no_fill()

    @property
    def fore_color(self) -> _LineColorFormat:
        """Foreground color (alias for line.color for compatibility)."""
        return self._line_format.color


# -------------------------------------------------------------------------
# Phase 3: ShadowFormat class
# -------------------------------------------------------------------------

class ShadowFormat:
    """
    Shadow formatting for a shape.

    Provides access to shadow properties like visibility, blur, distance,
    direction, color, and transparency.

    Example:
        shape.shadow.visible = True
        shape.shadow.blur_radius = Pt(4)
        shape.shadow.distance = Pt(3)
        shape.shadow.direction = 45  # degrees
        shape.shadow.color = RGBColor(0, 0, 0)
        shape.shadow.transparency = 0.6
    """

    def __init__(self, shape: "Shape"):
        self._shape = shape
        self._visible: bool = False
        self._shadow_type: str = 'outer'
        self._blur_radius_emu: int = 50800  # ~4pt default
        self._distance_emu: int = 38100  # ~3pt default
        self._direction_deg: float = 45.0
        self._color_hex: str = '000000'  # Black default
        self._transparency: float = 0.6  # 60% transparent default

    @property
    def visible(self) -> bool:
        """Whether the shadow is visible."""
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """Set shadow visibility."""
        self._visible = value
        self._emit_shadow_change()

    @property
    def shadow_type(self) -> str:
        """Shadow type ('outer', 'inner', 'perspective')."""
        return self._shadow_type

    @shadow_type.setter
    def shadow_type(self, value: str) -> None:
        """Set shadow type."""
        valid = ('outer', 'inner', 'perspective')
        if value not in valid:
            raise ValueError(f"shadow_type must be one of {valid}")
        self._shadow_type = value
        self._emit_shadow_change()

    @property
    def blur_radius(self) -> Emu:
        """Shadow blur radius in EMU."""
        return Emu(self._blur_radius_emu)

    @blur_radius.setter
    def blur_radius(self, value: Length) -> None:
        """Set blur radius."""
        self._blur_radius_emu = int(ensure_emu(value))
        self._emit_shadow_change()

    @property
    def distance(self) -> Emu:
        """Shadow distance from shape in EMU."""
        return Emu(self._distance_emu)

    @distance.setter
    def distance(self, value: Length) -> None:
        """Set shadow distance."""
        self._distance_emu = int(ensure_emu(value))
        self._emit_shadow_change()

    @property
    def direction(self) -> float:
        """Shadow direction in degrees (0=right, 90=down, 180=left, 270=up)."""
        return self._direction_deg

    @direction.setter
    def direction(self, value: float) -> None:
        """Set shadow direction in degrees."""
        self._direction_deg = value % 360
        self._emit_shadow_change()

    @property
    def color(self) -> Optional[RGBColor]:
        """Shadow color as RGBColor."""
        if self._color_hex:
            return RGBColor.from_string(self._color_hex)
        return None

    @color.setter
    def color(self, value: RGBColor) -> None:
        """Set shadow color."""
        self._color_hex = str(value).upper()
        self._emit_shadow_change()

    @property
    def transparency(self) -> float:
        """Shadow transparency (0.0=opaque, 1.0=fully transparent)."""
        return self._transparency

    @transparency.setter
    def transparency(self, value: float) -> None:
        """Set shadow transparency."""
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"transparency must be between 0.0 and 1.0, got {value}")
        self._transparency = value
        self._emit_shadow_change()

    def inherit(self) -> None:
        """Inherit shadow settings from the slide master/layout."""
        self._visible = False
        self._emit_shadow_change()

    def _emit_shadow_change(self) -> None:
        """Emit a SetShapeShadow command."""
        if self._shape._buffer:
            cmd = SetShapeShadow(
                shape_id=self._shape._shape_id,
                visible=self._visible,
                shadow_type=self._shadow_type,
                blur_radius_emu=self._blur_radius_emu,
                distance_emu=self._distance_emu,
                direction_deg=self._direction_deg,
                color_hex=self._color_hex,
                transparency=self._transparency,
            )
            self._shape._buffer.add(cmd)

    def __repr__(self) -> str:
        return f"<ShadowFormat visible={self._visible} type={self._shadow_type}>"


# -------------------------------------------------------------------------
# Phase 4: ClickAction class
# -------------------------------------------------------------------------

class ClickAction:
    """
    Click action (hyperlink) for a shape.

    Configures what happens when a shape is clicked during
    a presentation. Can link to URLs, other slides, or perform
    navigation actions.

    Example:
        # Link to external URL
        shape.click_action.hyperlink = "https://example.com"
        shape.click_action.tooltip = "Visit our website"

        # Link to another slide
        shape.click_action.target_slide = 3

        # Navigation actions
        shape.click_action.action = 'next_slide'
        shape.click_action.action = 'previous_slide'
        shape.click_action.action = 'first_slide'
        shape.click_action.action = 'last_slide'
        shape.click_action.action = 'end_show'

        # Remove click action
        shape.click_action.action = 'none'
    """

    def __init__(self, shape: "Shape"):
        self._shape = shape
        self._action_type: str = 'none'
        self._hyperlink_url: Optional[str] = None
        self._target_slide_index: Optional[int] = None
        self._tooltip: Optional[str] = None

    @property
    def action(self) -> str:
        """
        Current action type.

        Returns one of: 'none', 'hyperlink', 'slide', 'next_slide',
        'previous_slide', 'first_slide', 'last_slide', 'end_show'
        """
        return self._action_type

    @action.setter
    def action(self, value: str) -> None:
        """Set the action type."""
        valid = ('none', 'hyperlink', 'slide', 'next_slide', 'previous_slide',
                 'first_slide', 'last_slide', 'end_show')
        if value not in valid:
            raise ValueError(f"action must be one of {valid}")
        self._action_type = value
        self._emit_action_change()

    @property
    def hyperlink(self) -> Optional[str]:
        """URL for hyperlink action."""
        return self._hyperlink_url

    @hyperlink.setter
    def hyperlink(self, url: str) -> None:
        """Set hyperlink URL (automatically sets action to 'hyperlink')."""
        self._hyperlink_url = url
        self._action_type = 'hyperlink'
        self._emit_action_change()

    @property
    def target_slide(self) -> Optional[int]:
        """Target slide index for slide action (0-based)."""
        return self._target_slide_index

    @target_slide.setter
    def target_slide(self, slide_index: int) -> None:
        """Set target slide (automatically sets action to 'slide')."""
        self._target_slide_index = slide_index
        self._action_type = 'slide'
        self._emit_action_change()

    @property
    def tooltip(self) -> Optional[str]:
        """Tooltip text shown on hover."""
        return self._tooltip

    @tooltip.setter
    def tooltip(self, text: str) -> None:
        """Set tooltip text."""
        self._tooltip = text
        self._emit_action_change()

    def clear(self) -> None:
        """Remove any click action from the shape."""
        self._action_type = 'none'
        self._hyperlink_url = None
        self._target_slide_index = None
        self._tooltip = None
        self._emit_action_change()

    def _emit_action_change(self) -> None:
        """Emit a SetClickAction command."""
        if self._shape._buffer:
            cmd = SetClickAction(
                shape_id=self._shape._shape_id,
                action_type=self._action_type,
                hyperlink_url=self._hyperlink_url,
                target_slide_index=self._target_slide_index,
                tooltip=self._tooltip,
            )
            self._shape._buffer.add(cmd)

    def __bool__(self) -> bool:
        """True if a click action is configured."""
        return self._action_type != 'none'

    def __repr__(self) -> str:
        if self._action_type == 'hyperlink':
            return f"<ClickAction hyperlink={self._hyperlink_url!r}>"
        elif self._action_type == 'slide':
            return f"<ClickAction slide={self._target_slide_index}>"
        elif self._action_type == 'none':
            return "<ClickAction (none)>"
        else:
            return f"<ClickAction action={self._action_type}>"


class _ElementParentProxy:
    """
    Proxy for shape.element.getparent() to support python-pptx deletion pattern.

    In python-pptx, shapes are deleted via:
        shape.element.getparent().remove(shape.element)

    This proxy intercepts that pattern and calls the SDK's delete() method.
    """

    def __init__(self, shape: Shape) -> None:
        self._shape = shape

    def remove(self, element: _ElementProxy) -> None:
        """Remove the element (delete the shape)."""
        self._shape.delete()


class _ElementProxy:
    """
    Proxy for shape.element to support python-pptx deletion pattern.

    In python-pptx, shapes are deleted via:
        shape.element.getparent().remove(shape.element)

    This proxy intercepts that pattern and calls the SDK's delete() method.
    """

    def __init__(self, shape: Shape) -> None:
        self._shape = shape
        self._parent = _ElementParentProxy(shape)

    def getparent(self) -> _ElementParentProxy:
        """Return the parent proxy for removal."""
        return self._parent


class Shape:
    """
    A shape on a slide.

    Mirrors python-pptx's Shape class with limited Phase 1 support.
    """

    def __init__(
        self,
        shape_id: ShapeId,
        slide: Slide,
        buffer: Optional[CommandBuffer],
        element_type: str = "text",
        transform: Optional[Transform] = None,
        preview_text: Optional[str] = None,
        properties: Optional[dict[str, Any]] = None,
        placeholder: Optional[PlaceholderSnapshot] = None,
        source: Optional[str] = None,
    ):
        self._shape_id = shape_id
        self._slide = slide
        self._buffer = buffer
        self._element_type = element_type
        self._transform = transform or Transform(x=0, y=0, w=0, h=0)
        self._preview_text = preview_text
        self._properties = properties or {}
        self._text_frame: Optional[TextFrame] = None
        self._placeholder = placeholder
        self._source = source

        # Initialize text frame for text elements
        if element_type == "text":
            rich_content = properties.get("richContent") if properties else None
            self._text_frame = TextFrame(
                shape_id=shape_id,
                buffer=buffer,
                preview_text=preview_text,
                rich_content=rich_content,
            )

    @property
    def shape_id(self) -> ShapeId:
        """Unique identifier for this shape."""
        return self._shape_id

    @property
    def shape_type(self) -> str:
        """Type of the shape (text, image, shape, table, etc.)."""
        return self._element_type

    @property
    def auto_shape_type(self) -> Optional[str]:
        """
        The autoshape type for shape elements (e.g., 'rectangle', 'oval', 'star5').

        Returns None if this is not an autoshape (e.g., for text boxes, images, tables).
        """
        return self._properties.get("shapeType")

    @property
    def source(self) -> Optional[str]:
        """
        Source of this shape: 'ingested' or 'sdk'.

        - 'ingested': Shape came from the original uploaded PPTX file
        - 'sdk': Shape was created via the SDK
        - None: Source unknown (e.g., for newly created shapes not yet synced)
        """
        return self._source

    @property
    def element(self) -> _ElementProxy:
        """
        Proxy for the underlying element.

        This provides compatibility with the python-pptx deletion pattern:
            shape.element.getparent().remove(shape.element)

        In this SDK, it's recommended to use shape.delete() directly instead.
        """
        return _ElementProxy(self)

    @property
    def has_text_frame(self) -> bool:
        """True if this shape has a text frame."""
        return self._text_frame is not None

    @property
    def text_frame(self) -> TextFrame:
        """
        Text frame for this shape.

        Raises AttributeError if the shape doesn't have text, matching python-pptx
        behavior. Use has_text_frame to check before accessing.
        """
        if self._text_frame is None:
            raise AttributeError(
                f"'{self._element_type}' object has no attribute 'text_frame'"
            )
        return self._text_frame

    @property
    def text(self) -> str:
        """
        Shortcut for shape.text_frame.text.

        Returns empty string for shapes without a text frame (images, connectors, etc.).
        Use has_text_frame to check if a shape supports text before setting.
        """
        if self._text_frame is None:
            return ""
        return self._text_frame.text

    @text.setter
    def text(self, value: str) -> None:
        """
        Shortcut for shape.text_frame.text = value.

        Raises UnsupportedFeatureError if the shape doesn't have a text frame.
        """
        self.text_frame.text = value

    # -------------------------------------------------------------------------
    # Position and size properties
    # -------------------------------------------------------------------------

    @property
    def left(self) -> Emu:
        """X position in EMU."""
        return Emu(self._transform.get("x", 0))

    @left.setter
    def left(self, value: Length) -> None:
        """Set X position."""
        emu_value = ensure_emu(value)
        self._transform["x"] = int(emu_value)
        self._emit_transform_change()

    @property
    def top(self) -> Emu:
        """Y position in EMU."""
        return Emu(self._transform.get("y", 0))

    @top.setter
    def top(self, value: Length) -> None:
        """Set Y position."""
        emu_value = ensure_emu(value)
        self._transform["y"] = int(emu_value)
        self._emit_transform_change()

    @property
    def width(self) -> Emu:
        """Width in EMU."""
        return Emu(self._transform.get("w", 0))

    @width.setter
    def width(self, value: Length) -> None:
        """Set width."""
        emu_value = ensure_emu(value)
        self._transform["w"] = int(emu_value)
        self._emit_transform_change()

    @property
    def height(self) -> Emu:
        """Height in EMU."""
        return Emu(self._transform.get("h", 0))

    @height.setter
    def height(self, value: Length) -> None:
        """Set height."""
        emu_value = ensure_emu(value)
        self._transform["h"] = int(emu_value)
        self._emit_transform_change()

    @property
    def rotation(self) -> float:
        """Rotation in degrees."""
        return self._transform.get("rot", 0.0) or 0.0

    @rotation.setter
    def rotation(self, value: float) -> None:
        """Set rotation in degrees."""
        self._transform["rot"] = value
        self._emit_transform_change()

    @property
    def flip_h(self) -> bool:
        """Whether the shape is flipped horizontally."""
        return self._transform.get("flipH", False) or False

    @flip_h.setter
    def flip_h(self, value: bool) -> None:
        """Set horizontal flip."""
        self._transform["flipH"] = value
        self._emit_transform_change()

    @property
    def flip_v(self) -> bool:
        """Whether the shape is flipped vertically."""
        return self._transform.get("flipV", False) or False

    @flip_v.setter
    def flip_v(self, value: bool) -> None:
        """Set vertical flip."""
        self._transform["flipV"] = value
        self._emit_transform_change()

    # -------------------------------------------------------------------------
    # Computed position properties (read-only)
    # -------------------------------------------------------------------------

    @property
    def right(self) -> Emu:
        """Right edge position in EMU (left + width). Read-only."""
        return Emu(int(self.left) + int(self.width))

    @property
    def bottom(self) -> Emu:
        """Bottom edge position in EMU (top + height). Read-only."""
        return Emu(int(self.top) + int(self.height))

    @property
    def center_x(self) -> Emu:
        """Horizontal center position in EMU. Read-only."""
        return Emu(int(self.left) + int(self.width) // 2)

    @property
    def center_y(self) -> Emu:
        """Vertical center position in EMU. Read-only."""
        return Emu(int(self.top) + int(self.height) // 2)

    @property
    def aspect_ratio(self) -> float:
        """Width-to-height aspect ratio. Returns 0.0 if height is 0."""
        h = int(self.height)
        if h == 0:
            return 0.0
        return float(self.width) / float(h)

    @property
    def bounds(self) -> tuple[Emu, Emu, Emu, Emu]:
        """
        Bounding box as (left, top, right, bottom) tuple in EMU.

        Returns:
            Tuple of (left, top, right, bottom) coordinates
        """
        return (self.left, self.top, self.right, self.bottom)

    @property
    def center(self) -> tuple[Emu, Emu]:
        """
        Center point as (x, y) tuple in EMU.

        Returns:
            Tuple of (center_x, center_y) coordinates
        """
        return (self.center_x, self.center_y)

    @property
    def size(self) -> tuple[Emu, Emu]:
        """
        Size as (width, height) tuple in EMU.

        Returns:
            Tuple of (width, height) dimensions
        """
        return (self.width, self.height)

    @property
    def position(self) -> tuple[Emu, Emu]:
        """
        Position as (left, top) tuple in EMU.

        Returns:
            Tuple of (left, top) coordinates
        """
        return (self.left, self.top)

    # -------------------------------------------------------------------------
    # Convenience positioning methods
    # -------------------------------------------------------------------------

    def move(self, dx: Length, dy: Length) -> None:
        """
        Move the shape by relative amounts.

        Args:
            dx: Horizontal distance to move (positive = right, negative = left)
            dy: Vertical distance to move (positive = down, negative = up)
        """
        dx_emu = int(ensure_emu(dx))
        dy_emu = int(ensure_emu(dy))
        self._transform["x"] = int(self.left) + dx_emu
        self._transform["y"] = int(self.top) + dy_emu
        self._emit_transform_change()

    def resize(self, dw: Length, dh: Length) -> None:
        """
        Resize the shape by relative amounts.

        Args:
            dw: Amount to add to width (positive = wider, negative = narrower)
            dh: Amount to add to height (positive = taller, negative = shorter)
        """
        dw_emu = int(ensure_emu(dw))
        dh_emu = int(ensure_emu(dh))
        new_w = max(0, int(self.width) + dw_emu)
        new_h = max(0, int(self.height) + dh_emu)
        self._transform["w"] = new_w
        self._transform["h"] = new_h
        self._emit_transform_change()

    def scale(self, factor: float) -> None:
        """
        Scale the shape uniformly by a factor.

        Args:
            factor: Scale factor (e.g., 2.0 = double size, 0.5 = half size)
        """
        self._transform["w"] = int(int(self.width) * factor)
        self._transform["h"] = int(int(self.height) * factor)
        self._emit_transform_change()

    def set_position(self, left: Length, top: Length) -> None:
        """
        Set the shape's position in a single call.

        Args:
            left: X position
            top: Y position
        """
        self._transform["x"] = int(ensure_emu(left))
        self._transform["y"] = int(ensure_emu(top))
        self._emit_transform_change()

    def set_size(self, width: Length, height: Length) -> None:
        """
        Set the shape's size in a single call.

        Args:
            width: Width
            height: Height
        """
        self._transform["w"] = int(ensure_emu(width))
        self._transform["h"] = int(ensure_emu(height))
        self._emit_transform_change()

    def contains_point(self, x: Length, y: Length) -> bool:
        """
        Check if a point is within this shape's bounding box.

        Args:
            x: X coordinate to test
            y: Y coordinate to test

        Returns:
            True if the point is within the shape's bounds
        """
        x_emu = int(ensure_emu(x))
        y_emu = int(ensure_emu(y))
        return (
            int(self.left) <= x_emu <= int(self.right) and
            int(self.top) <= y_emu <= int(self.bottom)
        )

    def intersects(self, other: "Shape") -> bool:
        """
        Check if this shape's bounding box intersects with another shape.

        Args:
            other: Another shape to test against

        Returns:
            True if the bounding boxes overlap
        """
        return not (
            int(self.right) < int(other.left) or
            int(other.right) < int(self.left) or
            int(self.bottom) < int(other.top) or
            int(other.bottom) < int(self.top)
        )

    def _emit_transform_change(self) -> None:
        """Emit a SetTransform command."""
        if self._buffer:
            cmd = SetTransform(
                shape_id=self._shape_id,
                x_emu=self._transform.get("x"),
                y_emu=self._transform.get("y"),
                w_emu=self._transform.get("w"),
                h_emu=self._transform.get("h"),
                rot_deg=self._transform.get("rot"),
                flip_h=self._transform.get("flipH"),
                flip_v=self._transform.get("flipV"),
            )
            self._buffer.add(cmd)

    def delete(self) -> None:
        """Delete this shape from the slide."""
        if self._buffer:
            cmd = DeleteShape(shape_id=self._shape_id)
            self._buffer.add(cmd)

    # -------------------------------------------------------------------------
    # Fill and line styling
    # -------------------------------------------------------------------------

    @property
    def fill(self) -> FillFormat:
        """
        Fill formatting for this shape.

        Returns a FillFormat object that can be used to set solid fill colors,
        transparency, or remove fill entirely.

        Example:
            shape.fill.solid_fill('FF0000')  # Red fill
            shape.fill.transparency = 0.5    # 50% transparent
            shape.fill.background()          # Remove fill
        """
        if not hasattr(self, '_fill_format') or self._fill_format is None:
            self._fill_format = FillFormat(self)
        return self._fill_format

    @property
    def line(self) -> LineFormat:
        """
        Line (outline/border) formatting for this shape.

        Returns a LineFormat object that can be used to set line color,
        width, and dash style.

        Example:
            shape.line.color = '000000'  # Black outline
            shape.line.width = Pt(2)     # 2-point line
            shape.line.dash_style = 'dash'
        """
        if not hasattr(self, '_line_format') or self._line_format is None:
            self._line_format = LineFormat(self)
        return self._line_format

    # -------------------------------------------------------------------------
    # Phase 4: Shape name and click action
    # -------------------------------------------------------------------------

    @property
    def name(self) -> Optional[str]:
        """
        Shape name.

        Shape names are useful for identifying shapes programmatically
        and are preserved in the PPTX file.

        Example:
            shape.name = "MyTitle"
            print(shape.name)  # "MyTitle"
        """
        return self._properties.get("name")

    @name.setter
    def name(self, value: str) -> None:
        """Set shape name."""
        self._properties["name"] = value
        if self._buffer:
            cmd = SetShapeName(shape_id=self._shape_id, name=value)
            self._buffer.add(cmd)

    @property
    def click_action(self) -> "ClickAction":
        """
        Click action (hyperlink) for this shape.

        Returns a ClickAction object for configuring what happens
        when the shape is clicked during a presentation.

        Example:
            # Link to URL
            shape.click_action.hyperlink = "https://example.com"

            # Link to another slide
            shape.click_action.target_slide = 3  # Go to slide 4

            # Navigation actions
            shape.click_action.action = 'next_slide'
        """
        if not hasattr(self, '_click_action') or self._click_action is None:
            self._click_action = ClickAction(self)
        return self._click_action

    @property
    def has_chart(self) -> bool:
        """True if this shape contains a chart."""
        return False  # Charts not supported yet

    @property
    def has_table(self) -> bool:
        """True if this shape is a table."""
        return self._element_type == "table"

    # -------------------------------------------------------------------------
    # Type checking helpers
    # -------------------------------------------------------------------------

    @property
    def is_text_shape(self) -> bool:
        """True if this is a text shape (textbox)."""
        return self._element_type == "text"

    @property
    def is_image(self) -> bool:
        """True if this is an image/picture shape."""
        return self._element_type == "image"

    @property
    def is_table(self) -> bool:
        """True if this is a table shape."""
        return self._element_type == "table"

    @property
    def is_autoshape(self) -> bool:
        """True if this is an autoshape (rectangle, oval, etc.)."""
        return self._element_type == "shape"

    @property
    def is_group(self) -> bool:
        """True if this is a group shape."""
        return self._element_type == "group"

    @property
    def is_connector(self) -> bool:
        """True if this is a connector line."""
        return self._element_type == "connector"

    # -------------------------------------------------------------------------
    # Position/size copying helpers
    # -------------------------------------------------------------------------

    def copy_position_from(self, other: "Shape") -> None:
        """
        Copy position (left, top) from another shape.

        Args:
            other: Source shape to copy position from
        """
        self._transform["x"] = int(other.left)
        self._transform["y"] = int(other.top)
        self._emit_transform_change()

    def copy_size_from(self, other: "Shape") -> None:
        """
        Copy size (width, height) from another shape.

        Args:
            other: Source shape to copy size from
        """
        self._transform["w"] = int(other.width)
        self._transform["h"] = int(other.height)
        self._emit_transform_change()

    def copy_transform_from(self, other: "Shape") -> None:
        """
        Copy full transform (position, size, rotation, flip) from another shape.

        Args:
            other: Source shape to copy transform from
        """
        self._transform["x"] = int(other.left)
        self._transform["y"] = int(other.top)
        self._transform["w"] = int(other.width)
        self._transform["h"] = int(other.height)
        self._transform["rot"] = other.rotation
        self._transform["flipH"] = other.flip_h
        self._transform["flipV"] = other.flip_v
        self._emit_transform_change()

    def align_left_to(self, other: "Shape") -> None:
        """Align left edge to another shape's left edge."""
        self._transform["x"] = int(other.left)
        self._emit_transform_change()

    def align_right_to(self, other: "Shape") -> None:
        """Align right edge to another shape's right edge."""
        self._transform["x"] = int(other.right) - int(self.width)
        self._emit_transform_change()

    def align_top_to(self, other: "Shape") -> None:
        """Align top edge to another shape's top edge."""
        self._transform["y"] = int(other.top)
        self._emit_transform_change()

    def align_bottom_to(self, other: "Shape") -> None:
        """Align bottom edge to another shape's bottom edge."""
        self._transform["y"] = int(other.bottom) - int(self.height)
        self._emit_transform_change()

    def align_center_x_to(self, other: "Shape") -> None:
        """Align horizontal center to another shape's center."""
        self._transform["x"] = int(other.center_x) - int(self.width) // 2
        self._emit_transform_change()

    def align_center_y_to(self, other: "Shape") -> None:
        """Align vertical center to another shape's center."""
        self._transform["y"] = int(other.center_y) - int(self.height) // 2
        self._emit_transform_change()

    def center_on(self, other: "Shape") -> None:
        """Center this shape on another shape (both horizontally and vertically)."""
        self._transform["x"] = int(other.center_x) - int(self.width) // 2
        self._transform["y"] = int(other.center_y) - int(self.height) // 2
        self._emit_transform_change()

    # -------------------------------------------------------------------------
    # Computed geometry properties
    # -------------------------------------------------------------------------

    @property
    def area(self) -> int:
        """Area of the shape in square EMU."""
        return int(self.width) * int(self.height)

    @property
    def perimeter(self) -> int:
        """Perimeter of the shape bounding box in EMU."""
        return 2 * (int(self.width) + int(self.height))

    @property
    def diagonal(self) -> float:
        """Diagonal length of the shape bounding box in EMU."""
        return (int(self.width) ** 2 + int(self.height) ** 2) ** 0.5

    @property
    def is_square(self) -> bool:
        """True if shape has equal width and height (within 1% tolerance)."""
        w, h = int(self.width), int(self.height)
        if h == 0:
            return w == 0
        ratio = w / h
        return 0.99 <= ratio <= 1.01

    @property
    def is_landscape(self) -> bool:
        """True if width > height."""
        return int(self.width) > int(self.height)

    @property
    def is_portrait(self) -> bool:
        """True if height > width."""
        return int(self.height) > int(self.width)

    @property
    def area_inches(self) -> float:
        """Area in square inches."""
        from .units import EMU_PER_INCH
        return (int(self.width) / EMU_PER_INCH) * (int(self.height) / EMU_PER_INCH)

    def distance_to(self, other: "Shape") -> float:
        """
        Calculate distance between shape centers.

        Args:
            other: Another shape

        Returns:
            Distance in EMU between the centers of the two shapes
        """
        dx = int(self.center_x) - int(other.center_x)
        dy = int(self.center_y) - int(other.center_y)
        return (dx ** 2 + dy ** 2) ** 0.5

    def is_above(self, other: "Shape") -> bool:
        """True if this shape's bottom edge is above other shape's top edge."""
        return int(self.bottom) < int(other.top)

    def is_below(self, other: "Shape") -> bool:
        """True if this shape's top edge is below other shape's bottom edge."""
        return int(self.top) > int(other.bottom)

    def is_left_of(self, other: "Shape") -> bool:
        """True if this shape's right edge is left of other shape's left edge."""
        return int(self.right) < int(other.left)

    def is_right_of(self, other: "Shape") -> bool:
        """True if this shape's left edge is right of other shape's right edge."""
        return int(self.left) > int(other.right)

    def get_text_stats(self) -> dict:
        """
        Get text statistics for this shape.

        Returns:
            Dictionary containing:
            - word_count: Total word count
            - character_count: Total character count (excluding whitespace)
            - paragraph_count: Number of paragraphs
            - run_count: Number of text runs
            - has_formatting: Whether any formatting is applied
            - is_empty: Whether the text is empty

        Returns empty stats if shape has no text frame.
        """
        if not self.has_text_frame:
            return {
                'word_count': 0,
                'character_count': 0,
                'paragraph_count': 0,
                'run_count': 0,
                'has_formatting': False,
                'is_empty': True,
            }

        text = self.text
        return {
            'word_count': len(text.split()) if text else 0,
            'character_count': len(text.replace(" ", "").replace("\n", "")) if text else 0,
            'paragraph_count': self.text_frame.paragraph_count,
            'run_count': self.text_frame.run_count,
            'has_formatting': self.text_frame.has_formatting,
            'is_empty': not bool(text.strip()) if text else True,
        }

    def get_transform_dict(self) -> dict:
        """
        Get the shape's transform as a dictionary.

        Returns:
            Dictionary with left, top, width, height in EMU
        """
        return {
            'left': int(self.left),
            'top': int(self.top),
            'width': int(self.width),
            'height': int(self.height),
        }

    def get_transform_dict_inches(self) -> dict:
        """
        Get the shape's transform as a dictionary in inches.

        Returns:
            Dictionary with left, top, width, height in inches
        """
        emu_per_inch = 914400
        return {
            'left': int(self.left) / emu_per_inch,
            'top': int(self.top) / emu_per_inch,
            'width': int(self.width) / emu_per_inch,
            'height': int(self.height) / emu_per_inch,
        }

    @property
    def center_point(self) -> tuple:
        """Get center point as (x, y) tuple in EMU."""
        return (int(self.center_x), int(self.center_y))

    def scale_by(self, factor: float, anchor: str = 'center') -> None:
        """
        Scale the shape by a factor.

        Args:
            factor: Scale factor (1.0 = no change, 2.0 = double size, 0.5 = half size)
            anchor: Anchor point for scaling - 'center', 'top-left', 'top-right',
                   'bottom-left', 'bottom-right'

        Note: This modifies the shape's transform locally. Changes are automatically
        emitted to the server if a buffer is configured.
        """
        new_width = int(int(self.width) * factor)
        new_height = int(int(self.height) * factor)

        # Calculate offset based on anchor
        delta_w = new_width - int(self.width)
        delta_h = new_height - int(self.height)

        if anchor == 'center':
            self._transform['x'] = int(self._transform['x']) - delta_w // 2
            self._transform['y'] = int(self._transform['y']) - delta_h // 2
        elif anchor == 'top-right':
            self._transform['x'] = int(self._transform['x']) - delta_w
        elif anchor == 'bottom-left':
            self._transform['y'] = int(self._transform['y']) - delta_h
        elif anchor == 'bottom-right':
            self._transform['x'] = int(self._transform['x']) - delta_w
            self._transform['y'] = int(self._transform['y']) - delta_h
        # 'top-left' needs no adjustment

        self._transform['w'] = new_width
        self._transform['h'] = new_height
        self._emit_transform_change()

    def move_by(self, delta_x: int = 0, delta_y: int = 0) -> None:
        """
        Move the shape by relative amounts.

        Args:
            delta_x: Amount to move horizontally in EMU (positive = right)
            delta_y: Amount to move vertically in EMU (positive = down)
        """
        self._transform['x'] = int(self._transform['x']) + delta_x
        self._transform['y'] = int(self._transform['y']) + delta_y
        self._emit_transform_change()

    def resize_to(self, width: int, height: int) -> None:
        """
        Resize shape to exact dimensions.

        Args:
            width: New width in EMU
            height: New height in EMU
        """
        self._transform['w'] = width
        self._transform['h'] = height
        self._emit_transform_change()

    def move_to(self, x: int, y: int) -> None:
        """
        Move shape to exact position.

        Args:
            x: New left position in EMU
            y: New top position in EMU
        """
        self._transform['x'] = x
        self._transform['y'] = y
        self._emit_transform_change()

    def to_dict(self) -> dict:
        """
        Serialize shape to a dictionary.

        Returns a comprehensive dictionary representation of the shape
        suitable for JSON serialization or debugging.

        Returns:
            Dictionary with shape properties
        """
        result = {
            'id': self._shape_id,
            'type': self._element_type,
            'position': {
                'left': int(self.left),
                'top': int(self.top),
                'width': int(self.width),
                'height': int(self.height),
            },
            'rotation': self.rotation,
            'flip_h': self.flip_h,
            'flip_v': self.flip_v,
            'is_placeholder': self.is_placeholder,
        }

        # Add text content if available
        if self.has_text_frame:
            result['text'] = self.text
            result['text_stats'] = self.get_text_stats()

        # Add auto shape type if applicable
        if self._element_type == 'shape':
            result['auto_shape_type'] = self.auto_shape_type

        return result

    def get_bounds(self) -> dict:
        """
        Get bounding box as a dictionary.

        Returns:
            Dictionary with left, top, right, bottom, width, height, center_x, center_y
        """
        return {
            'left': int(self.left),
            'top': int(self.top),
            'right': int(self.right),
            'bottom': int(self.bottom),
            'width': int(self.width),
            'height': int(self.height),
            'center_x': int(self.center_x),
            'center_y': int(self.center_y),
        }

    def overlaps(self, other: "Shape") -> bool:
        """
        Check if this shape overlaps with another shape.

        Alias for intersects() method.

        Args:
            other: Another shape to test against

        Returns:
            True if the bounding boxes overlap
        """
        return self.intersects(other)

    def get_overlap_area(self, other: "Shape") -> int:
        """
        Calculate the area of overlap between two shapes.

        Args:
            other: Another shape

        Returns:
            Overlap area in square EMU (0 if no overlap)
        """
        if not self.intersects(other):
            return 0

        left = max(int(self.left), int(other.left))
        top = max(int(self.top), int(other.top))
        right = min(int(self.right), int(other.right))
        bottom = min(int(self.bottom), int(other.bottom))

        return (right - left) * (bottom - top)

    def contains(self, other: "Shape") -> bool:
        """
        Check if this shape fully contains another shape.

        Args:
            other: Another shape

        Returns:
            True if this shape's bounds fully contain the other shape
        """
        return (
            int(self.left) <= int(other.left) and
            int(self.top) <= int(other.top) and
            int(self.right) >= int(other.right) and
            int(self.bottom) >= int(other.bottom)
        )

    @property
    def shadow(self) -> ShadowFormat:
        """
        Shadow formatting for this shape.

        Returns a ShadowFormat object that can be used to add drop shadows,
        inner shadows, or perspective shadows to the shape.

        Example:
            shape.shadow.visible = True
            shape.shadow.blur_radius = Pt(4)
            shape.shadow.distance = Pt(3)
            shape.shadow.direction = 45
            shape.shadow.color = RGBColor(0, 0, 0)
            shape.shadow.transparency = 0.6
        """
        if not hasattr(self, '_shadow_format') or self._shadow_format is None:
            self._shadow_format = ShadowFormat(self)
        return self._shadow_format

    # -------------------------------------------------------------------------
    # Phase 3: Z-Order methods
    # -------------------------------------------------------------------------

    def bring_to_front(self) -> None:
        """
        Move shape to the front (top of z-order).

        The shape will be drawn on top of all other shapes.
        """
        if self._buffer:
            cmd = SetShapeZOrder(shape_id=self._shape_id, action='to_front')
            self._buffer.add(cmd)

    def send_to_back(self) -> None:
        """
        Move shape to the back (bottom of z-order).

        The shape will be drawn behind all other shapes.
        """
        if self._buffer:
            cmd = SetShapeZOrder(shape_id=self._shape_id, action='to_back')
            self._buffer.add(cmd)

    def bring_forward(self) -> None:
        """
        Move shape one level forward in z-order.

        The shape will be drawn on top of the next shape.
        """
        if self._buffer:
            cmd = SetShapeZOrder(shape_id=self._shape_id, action='forward')
            self._buffer.add(cmd)

    def send_backward(self) -> None:
        """
        Move shape one level backward in z-order.

        The shape will be drawn behind the previous shape.
        """
        if self._buffer:
            cmd = SetShapeZOrder(shape_id=self._shape_id, action='backward')
            self._buffer.add(cmd)

    # -------------------------------------------------------------------------
    # Phase 5: Clone and Adjustments
    # -------------------------------------------------------------------------

    def clone(
        self,
        target_slide: Optional["Slide"] = None,
        offset_x: Optional[Length] = None,
        offset_y: Optional[Length] = None,
    ) -> "Shape":
        """
        Clone/duplicate this shape.

        Creates a copy of this shape with all its properties, optionally
        placing it on a different slide and/or with a position offset.

        Args:
            target_slide: Slide to place the clone (default: same slide)
            offset_x: Horizontal offset from original position (default: 0.25 inch)
            offset_y: Vertical offset from original position (default: 0.25 inch)

        Returns:
            Shape: The newly created cloned shape.

        Example:
            # Clone on same slide with default offset
            new_shape = shape.clone()

            # Clone to another slide
            new_shape = shape.clone(target_slide=prs.slides[2])

            # Clone with custom offset
            new_shape = shape.clone(offset_x=Inches(1), offset_y=Inches(1))

            # Clone in place (no offset)
            new_shape = shape.clone(offset_x=0, offset_y=0)
        """
        import uuid

        # Default offsets (~0.25 inch)
        offset_x_emu = int(ensure_emu(offset_x)) if offset_x is not None else 228600
        offset_y_emu = int(ensure_emu(offset_y)) if offset_y is not None else 228600

        target_slide_index = target_slide.slide_index if target_slide else None
        client_id = f"shp_{uuid.uuid4().hex[:8]}"

        cmd = CloneShape(
            shape_id=self._shape_id,
            target_slide_index=target_slide_index,
            offset_x_emu=offset_x_emu,
            offset_y_emu=offset_y_emu,
            client_id=client_id,
        )

        if self._buffer:
            response = self._buffer.add(cmd)
            shape_id = client_id
            if response and response.get("created"):
                shape_ids = response["created"].get("shapeIds", [])
                if shape_ids:
                    shape_id = shape_ids[0]
        else:
            shape_id = client_id

        # Create local shape proxy for the clone
        target = target_slide if target_slide else self._slide
        new_shape = Shape(
            shape_id=shape_id,
            slide=target,
            buffer=self._buffer,
            element_type=self._element_type,
            transform=Transform(
                x=int(self.left) + offset_x_emu,
                y=int(self.top) + offset_y_emu,
                w=int(self.width),
                h=int(self.height),
                rot=self.rotation,
                flipH=self.flip_h,
                flipV=self.flip_v,
            ),
            preview_text=self._preview_text,
            properties=dict(self._properties),
            source="sdk",
        )
        target._shapes._shapes.append(new_shape)
        target._shapes._shapes_by_id[shape_id] = new_shape
        return new_shape

    @property
    def adjustments(self) -> dict[str, float]:
        """
        Adjustment values for adjustable shapes.

        Adjustment values control shape-specific parameters like corner radius
        for rounded rectangles, arrow head size, etc. Values are typically
        in the range 0.0 to 1.0.

        Returns:
            Dictionary of adjustment name to value

        Example:
            # Get current adjustments
            print(shape.adjustments)  # {'adj': 0.25}

            # Set adjustments
            shape.adjustments = {'adj': 0.5}  # More rounded corners
        """
        return self._properties.get("adjustments", {})

    @adjustments.setter
    def adjustments(self, value: dict[str, float]) -> None:
        """Set adjustment values for the shape."""
        self._properties["adjustments"] = value
        if self._buffer:
            cmd = SetShapeAdjustments(
                shape_id=self._shape_id,
                adjustments=value,
            )
            self._buffer.add(cmd)

    def ungroup(self) -> list["Shape"]:
        """
        Ungroup this group shape into its component shapes.

        Only applicable to group shapes (is_group == True).

        Returns:
            List of ungrouped shapes

        Raises:
            ValueError: If this shape is not a group

        Example:
            if shape.is_group:
                children = shape.ungroup()
                for child in children:
                    print(child.shape_id)
        """
        if not self.is_group:
            raise ValueError("Cannot ungroup a non-group shape")

        cmd = UngroupShapes(group_shape_id=self._shape_id)

        if self._buffer:
            self._buffer.add(cmd)

        # The server will return the ungrouped shapes; for now return empty list
        # as we don't have the response handling for this yet
        return []

    @property
    def is_placeholder(self) -> bool:
        """
        True if this shape is a placeholder.

        A placeholder is a pre-positioned shape on a slide layout that can be
        populated with content. Common placeholder types include title, body,
        picture, chart, and table.
        """
        return self._placeholder is not None

    @property
    def placeholder_format(self) -> Optional[PlaceholderFormat]:
        """
        Access placeholder properties for this shape.

        Returns a PlaceholderFormat object if the shape is a placeholder, or None
        if the shape is not a placeholder.

        Example:
            if shape.is_placeholder:
                ph = shape.placeholder_format
                print(f"Placeholder type: {ph.type}")
                print(f"Placeholder index: {ph.idx}")
        """
        if self._placeholder is None:
            return None
        return PlaceholderFormat(self._placeholder)

    def __repr__(self) -> str:
        return f"<Shape shape_id='{self._shape_id}' type='{self._element_type}'>"


class Shapes:
    """
    Collection of shapes on a slide.

    Mirrors python-pptx's Shapes class.
    """

    def __init__(
        self,
        slide: Slide,
        buffer: Optional[CommandBuffer],
        elements: Optional[dict[str, ElementSnapshot]] = None,
        element_ids: Optional[list[str]] = None,
    ):
        self._slide = slide
        self._buffer = buffer
        self._shapes: list[Shape] = []
        self._shapes_by_id: dict[ShapeId, Shape] = {}
        self._placeholders_by_idx: dict[int, Shape] = {}
        self._title_shape: Optional[Shape] = None

        # Build shapes from element snapshots
        if elements and element_ids:
            for elem_id in element_ids:
                elem = elements.get(elem_id)
                if elem:
                    shape = Shape(
                        shape_id=elem.id,
                        slide=slide,
                        buffer=buffer,
                        element_type=elem.type,
                        transform=elem.transform,
                        preview_text=elem.preview_text,
                        properties=elem.properties,
                        placeholder=elem.placeholder,
                        source=elem.source,
                    )
                    self._shapes.append(shape)
                    self._shapes_by_id[elem.id] = shape

                    # Track placeholders by idx
                    if elem.placeholder:
                        self._placeholders_by_idx[elem.placeholder.idx] = shape
                        # Title placeholder has idx 0
                        if elem.placeholder.type in ("title", "ctrTitle") or elem.placeholder.idx == 0:
                            self._title_shape = shape

    def __len__(self) -> int:
        """Number of shapes."""
        return len(self._shapes)

    def __iter__(self) -> Iterator[Shape]:
        """Iterate over shapes."""
        return iter(self._shapes)

    def __getitem__(self, key: int) -> Shape:
        """Get shape by index."""
        return self._shapes[key]

    def get_by_id(self, shape_id: ShapeId) -> Optional[Shape]:
        """Get shape by ID."""
        return self._shapes_by_id.get(shape_id)

    def index(self, shape: Shape) -> int:
        """
        Return the index of shape in the sequence.

        Args:
            shape: The shape to find

        Returns:
            Zero-based index of the shape

        Raises:
            ValueError: If shape is not in collection
        """
        for i, s in enumerate(self._shapes):
            if s.shape_id == shape.shape_id:
                return i
        raise ValueError("shape not in collection")

    def add_textbox(
        self,
        left: Length,
        top: Length,
        width: Length,
        height: Length,
    ) -> Shape:
        """
        Add a new textbox shape.

        Args:
            left: X position in EMU
            top: Y position in EMU
            width: Width in EMU
            height: Height in EMU

        Returns:
            The newly created Shape
        """
        import uuid

        x_emu = int(ensure_emu(left))
        y_emu = int(ensure_emu(top))
        w_emu = int(ensure_emu(width))
        h_emu = int(ensure_emu(height))

        # Generate a client ID for referencing in batch mode
        client_id = f"shp_{uuid.uuid4().hex[:8]}"

        # Create command with client ID
        cmd = AddTextBox(
            slide_index=self._slide.slide_index,
            x_emu=x_emu,
            y_emu=y_emu,
            w_emu=w_emu,
            h_emu=h_emu,
            client_id=client_id,
        )

        # Send command and get response
        if self._buffer:
            response = self._buffer.add(cmd)

            # Extract created shape ID from response (immediate mode)
            shape_id = client_id  # Use client_id by default
            if response and response.get("created"):
                shape_ids = response["created"].get("shapeIds", [])
                if shape_ids:
                    shape_id = shape_ids[0]

            # Create local shape proxy
            shape = Shape(
                shape_id=shape_id,
                slide=self._slide,
                buffer=self._buffer,
                element_type="text",
                transform=Transform(x=x_emu, y=y_emu, w=w_emu, h=h_emu),
                preview_text="",
                source="sdk",
            )
            self._shapes.append(shape)
            self._shapes_by_id[shape_id] = shape
            return shape

        # If no buffer (unlikely), still create a local placeholder
        shape = Shape(
            shape_id=client_id,
            slide=self._slide,
            buffer=self._buffer,
            element_type="text",
            transform=Transform(x=x_emu, y=y_emu, w=w_emu, h=h_emu),
            preview_text="",
            source="sdk",
        )
        self._shapes.append(shape)
        self._shapes_by_id[client_id] = shape
        return shape

    def add_picture(
        self,
        image_file: Union[str, Path, BytesIO, bytes],
        left: Length,
        top: Length,
        width: Optional[Length] = None,
        height: Optional[Length] = None,
    ) -> Shape:
        """
        Add a picture to the slide.

        Args:
            image_file: Path to image file, file-like object, or bytes
            left: X position
            top: Y position
            width: Width (optional - uses image native size if not specified)
            height: Height (optional)

        Returns:
            The newly created picture Shape
        """
        import uuid

        x_emu = int(ensure_emu(left))
        y_emu = int(ensure_emu(top))
        w_emu = int(ensure_emu(width)) if width else None
        h_emu = int(ensure_emu(height)) if height else None

        # Read image data and determine format
        if isinstance(image_file, bytes):
            image_data = image_file
        elif isinstance(image_file, BytesIO):
            image_data = image_file.read()
        else:
            # Treat as path
            path = Path(image_file)
            with open(path, 'rb') as f:
                image_data = f.read()

        # Determine format from magic bytes
        image_format = self._detect_image_format(image_data)

        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('ascii')

        client_id = f"pic_{uuid.uuid4().hex[:8]}"

        cmd = AddPictureCmd(
            slide_index=self._slide.slide_index,
            x_emu=x_emu,
            y_emu=y_emu,
            w_emu=w_emu,
            h_emu=h_emu,
            client_id=client_id,
            image_base64=image_base64,
            image_format=image_format,
        )

        if self._buffer:
            response = self._buffer.add(cmd)
            shape_id = client_id
            if response and response.get("created"):
                shape_ids = response["created"].get("shapeIds", [])
                if shape_ids:
                    shape_id = shape_ids[0]

            shape = Shape(
                shape_id=shape_id,
                slide=self._slide,
                buffer=self._buffer,
                element_type="image",
                transform=Transform(x=x_emu, y=y_emu, w=w_emu or 914400, h=h_emu or 914400),
                source="sdk",
            )
            self._shapes.append(shape)
            self._shapes_by_id[shape_id] = shape
            return shape

        shape = Shape(
            shape_id=client_id,
            slide=self._slide,
            buffer=self._buffer,
            element_type="image",
            transform=Transform(x=x_emu, y=y_emu, w=w_emu or 914400, h=h_emu or 914400),
            source="sdk",
        )
        self._shapes.append(shape)
        self._shapes_by_id[client_id] = shape
        return shape

    def _detect_image_format(self, data: bytes) -> str:
        """Detect image format from magic bytes."""
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'png'
        elif data[:2] == b'\xff\xd8':
            return 'jpeg'
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            return 'gif'
        elif data[:2] == b'BM':
            return 'bmp'
        elif data[:4] in (b'II*\x00', b'MM\x00*'):
            return 'tiff'
        else:
            # Default to PNG
            return 'png'

    def add_shape(
        self,
        autoshape_type: str,
        left: Length,
        top: Length,
        width: Length,
        height: Length,
    ) -> Shape:
        """
        Add an autoshape to the slide.

        Args:
            autoshape_type: Shape type from MSO_SHAPE (e.g., MSO_SHAPE.RECTANGLE)
            left: X position
            top: Y position
            width: Width
            height: Height

        Returns:
            The newly created Shape
        """
        import uuid

        x_emu = int(ensure_emu(left))
        y_emu = int(ensure_emu(top))
        w_emu = int(ensure_emu(width))
        h_emu = int(ensure_emu(height))

        # Handle MSO_SHAPE enum values - convert to backend string type
        # Supports both our string-based MSO_SHAPE and python-pptx's IntEnum
        from .enum.shapes import mso_shape_to_string
        shape_type = mso_shape_to_string(autoshape_type)

        client_id = f"shp_{uuid.uuid4().hex[:8]}"

        cmd = AddShapeCmd(
            slide_index=self._slide.slide_index,
            shape_type=shape_type,
            x_emu=x_emu,
            y_emu=y_emu,
            w_emu=w_emu,
            h_emu=h_emu,
            client_id=client_id,
        )

        if self._buffer:
            response = self._buffer.add(cmd)
            shape_id = client_id
            if response and response.get("created"):
                shape_ids = response["created"].get("shapeIds", [])
                if shape_ids:
                    shape_id = shape_ids[0]

            shape = Shape(
                shape_id=shape_id,
                slide=self._slide,
                buffer=self._buffer,
                element_type="shape",
                transform=Transform(x=x_emu, y=y_emu, w=w_emu, h=h_emu),
                properties={"shapeType": shape_type},
                source="sdk",
            )
            self._shapes.append(shape)
            self._shapes_by_id[shape_id] = shape
            return shape

        shape = Shape(
            shape_id=client_id,
            slide=self._slide,
            buffer=self._buffer,
            element_type="shape",
            transform=Transform(x=x_emu, y=y_emu, w=w_emu, h=h_emu),
            properties={"shapeType": shape_type},
            source="sdk",
        )
        self._shapes.append(shape)
        self._shapes_by_id[client_id] = shape
        return shape

    def add_table(
        self,
        rows: int,
        cols: int,
        left: Length,
        top: Length,
        width: Length,
        height: Length,
    ) -> "Table":
        """
        Add a table to the slide.

        Args:
            rows: Number of rows
            cols: Number of columns
            left: X position
            top: Y position
            width: Total table width
            height: Total table height

        Returns:
            A Table object
        """
        import uuid

        x_emu = int(ensure_emu(left))
        y_emu = int(ensure_emu(top))
        w_emu = int(ensure_emu(width))
        h_emu = int(ensure_emu(height))

        client_id = f"tbl_{uuid.uuid4().hex[:8]}"

        cmd = AddTableCmd(
            slide_index=self._slide.slide_index,
            rows=rows,
            cols=cols,
            x_emu=x_emu,
            y_emu=y_emu,
            w_emu=w_emu,
            h_emu=h_emu,
            client_id=client_id,
        )

        if self._buffer:
            response = self._buffer.add(cmd)
            shape_id = client_id
            if response and response.get("created"):
                shape_ids = response["created"].get("shapeIds", [])
                if shape_ids:
                    shape_id = shape_ids[0]

            table = Table(
                shape_id=shape_id,
                slide=self._slide,
                buffer=self._buffer,
                rows=rows,
                cols=cols,
                transform=Transform(x=x_emu, y=y_emu, w=w_emu, h=h_emu),
            )
            self._shapes.append(table)
            self._shapes_by_id[shape_id] = table
            return table

        table = Table(
            shape_id=client_id,
            slide=self._slide,
            buffer=self._buffer,
            rows=rows,
            cols=cols,
            transform=Transform(x=x_emu, y=y_emu, w=w_emu, h=h_emu),
        )
        self._shapes.append(table)
        self._shapes_by_id[client_id] = table
        return table

    # -------------------------------------------------------------------------
    # Phase 3: Connectors
    # -------------------------------------------------------------------------

    def add_connector(
        self,
        connector_type: str,
        begin_x: Length,
        begin_y: Length,
        end_x: Length,
        end_y: Length,
        begin_shape: Optional[Shape] = None,
        end_shape: Optional[Shape] = None,
    ) -> Shape:
        """
        Add a connector line to the slide.

        Connectors can be free-floating (with explicit coordinates) or
        attached to shapes (using begin_shape/end_shape).

        Args:
            connector_type: Type of connector ('straight', 'elbow', 'curved')
            begin_x: Start X position (used if begin_shape is None)
            begin_y: Start Y position (used if begin_shape is None)
            end_x: End X position (used if end_shape is None)
            end_y: End Y position (used if end_shape is None)
            begin_shape: Shape to connect from (optional)
            end_shape: Shape to connect to (optional)

        Returns:
            The created connector Shape

        Example:
            # Free connector
            conn = shapes.add_connector(
                'straight',
                Inches(1), Inches(1),
                Inches(5), Inches(3)
            )

            # Connector between shapes
            conn = shapes.add_connector(
                'elbow',
                Inches(0), Inches(0),  # ignored when shape is specified
                Inches(0), Inches(0),
                begin_shape=shape1,
                end_shape=shape2
            )
        """
        import uuid

        begin_x_emu = int(ensure_emu(begin_x))
        begin_y_emu = int(ensure_emu(begin_y))
        end_x_emu = int(ensure_emu(end_x))
        end_y_emu = int(ensure_emu(end_y))

        client_id = f"conn_{uuid.uuid4().hex[:8]}"

        cmd = AddConnectorCmd(
            slide_index=self._slide.slide_index,
            connector_type=connector_type,
            begin_shape_id=begin_shape._shape_id if begin_shape else None,
            begin_x_emu=begin_x_emu if not begin_shape else None,
            begin_y_emu=begin_y_emu if not begin_shape else None,
            end_shape_id=end_shape._shape_id if end_shape else None,
            end_x_emu=end_x_emu if not end_shape else None,
            end_y_emu=end_y_emu if not end_shape else None,
            client_id=client_id,
        )

        if self._buffer:
            response = self._buffer.add(cmd)
            shape_id = client_id
            if response and response.get("created"):
                shape_ids = response["created"].get("shapeIds", [])
                if shape_ids:
                    shape_id = shape_ids[0]
        else:
            shape_id = client_id

        # Calculate approximate transform for connector
        x = min(begin_x_emu, end_x_emu)
        y = min(begin_y_emu, end_y_emu)
        w = abs(end_x_emu - begin_x_emu)
        h = abs(end_y_emu - begin_y_emu)

        shape = Shape(
            shape_id=shape_id,
            slide=self._slide,
            buffer=self._buffer,
            element_type="connector",
            transform=Transform(x=x, y=y, w=w, h=h),
            properties={"connectorType": connector_type},
            source="sdk",
        )
        self._shapes.append(shape)
        self._shapes_by_id[shape_id] = shape
        return shape

    def add_chart(
        self,
        chart_type: Any,
        left: Length,
        top: Length,
        width: Length,
        height: Length,
        chart_data: Any,
    ) -> Any:
        """Add a chart (not yet supported)."""
        raise UnsupportedFeatureError(
            "shapes.add_chart", "Adding charts is not yet supported"
        )

    # -------------------------------------------------------------------------
    # Phase 5: Grouping
    # -------------------------------------------------------------------------

    def group_shapes(self, shapes: list[Shape]) -> Shape:
        """
        Group multiple shapes together into a single group shape.

        The grouped shapes will be treated as a single unit for moving,
        resizing, and other operations.

        Args:
            shapes: List of Shape objects to group (at least 2 shapes required)

        Returns:
            Shape: The newly created group shape

        Raises:
            ValueError: If fewer than 2 shapes are provided

        Example:
            # Group three shapes
            rect1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, ...)
            rect2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, ...)
            rect3 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, ...)
            group = slide.shapes.group_shapes([rect1, rect2, rect3])

            # The group can be moved as a unit
            group.left = Inches(1)

            # Ungroup later if needed
            children = group.ungroup()
        """
        import uuid

        if len(shapes) < 2:
            raise ValueError("At least 2 shapes are required for grouping")

        shape_ids = [s.shape_id for s in shapes]
        client_id = f"grp_{uuid.uuid4().hex[:8]}"

        cmd = GroupShapes(
            slide_index=self._slide.slide_index,
            shape_ids=shape_ids,
            client_id=client_id,
        )

        if self._buffer:
            response = self._buffer.add(cmd)
            shape_id = client_id
            if response and response.get("created"):
                group_ids = response["created"].get("shapeIds", [])
                if group_ids:
                    shape_id = group_ids[0]
        else:
            shape_id = client_id

        # Calculate bounding box for the group
        left = min(int(s.left) for s in shapes)
        top = min(int(s.top) for s in shapes)
        right = max(int(s.right) for s in shapes)
        bottom = max(int(s.bottom) for s in shapes)

        group_shape = Shape(
            shape_id=shape_id,
            slide=self._slide,
            buffer=self._buffer,
            element_type="group",
            transform=Transform(x=left, y=top, w=right - left, h=bottom - top),
            properties={"childIds": shape_ids},
            source="sdk",
        )
        self._shapes.append(group_shape)
        self._shapes_by_id[shape_id] = group_shape
        return group_shape

    @property
    def title(self) -> Optional[Shape]:
        """
        Title placeholder shape on this slide, or None if not present.

        Returns the title placeholder shape if the slide has one. The title
        placeholder typically has idx 0 and type 'title' or 'ctrTitle'.

        Example:
            title = slide.shapes.title
            if title:
                title.text = "New Slide Title"
        """
        return self._title_shape

    @property
    def placeholders(self) -> "SlidePlaceholders":
        """
        Collection of placeholder shapes on this slide.

        Returns a SlidePlaceholders object that supports dictionary-style access
        by placeholder idx.

        Example:
            title = slide.placeholders[0]  # Title placeholder
            body = slide.placeholders[1]   # Body placeholder
        """
        return SlidePlaceholders(self._placeholders_by_idx)

    def _add_shape_from_snapshot(self, elem: ElementSnapshot) -> Shape:
        """Internal: Add a shape from a snapshot element."""
        shape = Shape(
            shape_id=elem.id,
            slide=self._slide,
            buffer=self._buffer,
            element_type=elem.type,
            transform=elem.transform,
            preview_text=elem.preview_text,
            properties=elem.properties,
            placeholder=elem.placeholder,
            source=elem.source,
        )
        self._shapes.append(shape)
        self._shapes_by_id[elem.id] = shape

        # Track placeholders by idx
        if elem.placeholder:
            self._placeholders_by_idx[elem.placeholder.idx] = shape
            if elem.placeholder.type in ("title", "ctrTitle") or elem.placeholder.idx == 0:
                self._title_shape = shape

        return shape

    # -------------------------------------------------------------------------
    # Convenience properties
    # -------------------------------------------------------------------------

    @property
    def first(self) -> Optional[Shape]:
        """
        First shape in the collection.

        Returns None if there are no shapes.
        """
        return self._shapes[0] if self._shapes else None

    @property
    def last(self) -> Optional[Shape]:
        """
        Last shape in the collection.

        Returns None if there are no shapes.
        """
        return self._shapes[-1] if self._shapes else None

    @property
    def is_empty(self) -> bool:
        """True if there are no shapes on this slide."""
        return len(self._shapes) == 0

    @property
    def count(self) -> int:
        """Number of shapes (alias for len())."""
        return len(self._shapes)

    # -------------------------------------------------------------------------
    # Convenience search and filter methods
    # -------------------------------------------------------------------------

    def filter_by_type(self, element_type: str) -> list[Shape]:
        """
        Get all shapes of a specific type.

        Args:
            element_type: The type to filter by ('text', 'image', 'shape', 'table')

        Returns:
            List of shapes matching the type
        """
        return [s for s in self._shapes if s.shape_type == element_type]

    def filter_by_text(self, text_contains: str, case_sensitive: bool = False) -> list[Shape]:
        """
        Get all shapes containing specific text.

        Args:
            text_contains: Text substring to search for
            case_sensitive: Whether to do case-sensitive search (default: False)

        Returns:
            List of shapes containing the text
        """
        results = []
        search_text = text_contains if case_sensitive else text_contains.lower()
        for shape in self._shapes:
            if shape.has_text_frame:
                shape_text = shape.text if case_sensitive else shape.text.lower()
                if search_text in shape_text:
                    results.append(shape)
        return results

    def find_by_text(self, text: str, case_sensitive: bool = False) -> Optional[Shape]:
        """
        Find the first shape with exactly matching text.

        Args:
            text: Exact text to match
            case_sensitive: Whether to do case-sensitive match (default: False)

        Returns:
            The first matching shape, or None
        """
        search_text = text if case_sensitive else text.lower()
        for shape in self._shapes:
            if shape.has_text_frame:
                shape_text = shape.text if case_sensitive else shape.text.lower()
                if shape_text == search_text:
                    return shape
        return None

    def get_textboxes(self) -> list[Shape]:
        """Get all text shapes (convenience method)."""
        return self.filter_by_type('text')

    def get_images(self) -> list[Shape]:
        """Get all image shapes (convenience method)."""
        return self.filter_by_type('image')

    def get_tables(self) -> list["Table"]:
        """Get all table shapes (convenience method)."""
        return [s for s in self._shapes if s.shape_type == 'table']

    def get_autoshapes(self) -> list[Shape]:
        """Get all autoshape shapes (convenience method)."""
        return self.filter_by_type('shape')

    def get_placeholders_list(self) -> list[Shape]:
        """Get all placeholder shapes as a list."""
        return [s for s in self._shapes if s.is_placeholder]

    # -------------------------------------------------------------------------
    # Bounding box and geometry methods
    # -------------------------------------------------------------------------

    def get_bounding_box(self) -> Optional[tuple[Emu, Emu, Emu, Emu]]:
        """
        Get the bounding box that contains all shapes.

        Returns:
            Tuple of (left, top, right, bottom) in EMU, or None if no shapes
        """
        if not self._shapes:
            return None

        left = min(int(s.left) for s in self._shapes)
        top = min(int(s.top) for s in self._shapes)
        right = max(int(s.right) for s in self._shapes)
        bottom = max(int(s.bottom) for s in self._shapes)

        return (Emu(left), Emu(top), Emu(right), Emu(bottom))

    def get_total_area(self) -> Emu:
        """
        Get the total area of all shapes combined.

        Returns:
            Total area in square EMU
        """
        return Emu(sum(int(s.width) * int(s.height) for s in self._shapes))

    # -------------------------------------------------------------------------
    # Sorting methods
    # -------------------------------------------------------------------------

    def sorted_by_left(self, reverse: bool = False) -> list[Shape]:
        """
        Get shapes sorted by left position.

        Args:
            reverse: If True, sort right-to-left

        Returns:
            List of shapes sorted by left position
        """
        return sorted(self._shapes, key=lambda s: int(s.left), reverse=reverse)

    def sorted_by_top(self, reverse: bool = False) -> list[Shape]:
        """
        Get shapes sorted by top position.

        Args:
            reverse: If True, sort bottom-to-top

        Returns:
            List of shapes sorted by top position
        """
        return sorted(self._shapes, key=lambda s: int(s.top), reverse=reverse)

    def sorted_by_area(self, reverse: bool = False) -> list[Shape]:
        """
        Get shapes sorted by area (width * height).

        Args:
            reverse: If True, sort largest first

        Returns:
            List of shapes sorted by area
        """
        return sorted(
            self._shapes,
            key=lambda s: int(s.width) * int(s.height),
            reverse=reverse
        )

    def sorted_by_width(self, reverse: bool = False) -> list[Shape]:
        """
        Get shapes sorted by width.

        Args:
            reverse: If True, sort widest first

        Returns:
            List of shapes sorted by width
        """
        return sorted(self._shapes, key=lambda s: int(s.width), reverse=reverse)

    def sorted_by_height(self, reverse: bool = False) -> list[Shape]:
        """
        Get shapes sorted by height.

        Args:
            reverse: If True, sort tallest first

        Returns:
            List of shapes sorted by height
        """
        return sorted(self._shapes, key=lambda s: int(s.height), reverse=reverse)

    # -------------------------------------------------------------------------
    # Selection methods
    # -------------------------------------------------------------------------

    def get_largest(self) -> Optional[Shape]:
        """Get the shape with the largest area."""
        if not self._shapes:
            return None
        return max(self._shapes, key=lambda s: int(s.width) * int(s.height))

    def get_smallest(self) -> Optional[Shape]:
        """Get the shape with the smallest area."""
        if not self._shapes:
            return None
        return min(self._shapes, key=lambda s: int(s.width) * int(s.height))

    def get_leftmost(self) -> Optional[Shape]:
        """Get the leftmost shape."""
        if not self._shapes:
            return None
        return min(self._shapes, key=lambda s: int(s.left))

    def get_rightmost(self) -> Optional[Shape]:
        """Get the rightmost shape (by right edge)."""
        if not self._shapes:
            return None
        return max(self._shapes, key=lambda s: int(s.right))

    def get_topmost(self) -> Optional[Shape]:
        """Get the topmost shape."""
        if not self._shapes:
            return None
        return min(self._shapes, key=lambda s: int(s.top))

    def get_bottommost(self) -> Optional[Shape]:
        """Get the bottommost shape (by bottom edge)."""
        if not self._shapes:
            return None
        return max(self._shapes, key=lambda s: int(s.bottom))

    def get_shapes_at_point(self, x: Length, y: Length) -> list[Shape]:
        """
        Get all shapes that contain a specific point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            List of shapes containing the point
        """
        return [s for s in self._shapes if s.contains_point(x, y)]

    def get_overlapping(self, shape: Shape) -> list[Shape]:
        """
        Get all shapes that overlap with a given shape.

        Args:
            shape: Shape to check overlaps with

        Returns:
            List of shapes that intersect with the given shape
        """
        return [s for s in self._shapes if s != shape and s.intersects(shape)]

    def __repr__(self) -> str:
        return f"<Shapes count={len(self._shapes)}>"


class SlidePlaceholders:
    """
    Collection of placeholder shapes on a slide.

    Provides dictionary-style access to placeholder shapes by their idx value.
    Mirrors python-pptx's SlidePlaceholders class.
    """

    def __init__(self, placeholders_by_idx: dict[int, Shape]):
        self._placeholders = placeholders_by_idx

    def __len__(self) -> int:
        """Number of placeholders."""
        return len(self._placeholders)

    def __iter__(self) -> Iterator[Shape]:
        """Iterate over placeholder shapes in idx order."""
        for idx in sorted(self._placeholders.keys()):
            yield self._placeholders[idx]

    def __getitem__(self, key: int) -> Shape:
        """
        Get placeholder by idx.

        Args:
            key: Placeholder idx value (0 for title, etc.)

        Returns:
            The placeholder Shape

        Raises:
            KeyError: If no placeholder with that idx exists
        """
        if key not in self._placeholders:
            raise KeyError(f"No placeholder with idx={key} on this slide")
        return self._placeholders[key]

    def __contains__(self, key: int) -> bool:
        """Check if a placeholder with the given idx exists."""
        return key in self._placeholders

    def get(self, idx: int, default: Optional[Shape] = None) -> Optional[Shape]:
        """
        Get placeholder by idx, or default if not found.

        Args:
            idx: Placeholder idx value
            default: Value to return if placeholder not found

        Returns:
            The placeholder Shape or default
        """
        return self._placeholders.get(idx, default)

    def keys(self) -> Iterator[int]:
        """Iterate over placeholder idx values."""
        return iter(sorted(self._placeholders.keys()))

    def values(self) -> Iterator[Shape]:
        """Iterate over placeholder shapes."""
        return iter(self)

    def items(self) -> Iterator[tuple[int, Shape]]:
        """Iterate over (idx, shape) pairs."""
        for idx in sorted(self._placeholders.keys()):
            yield idx, self._placeholders[idx]

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def title(self) -> Optional[Shape]:
        """
        Get title placeholder (idx 0).

        Returns None if no title placeholder exists.
        """
        return self._placeholders.get(0)

    @property
    def body(self) -> Optional[Shape]:
        """
        Get body/content placeholder (idx 1).

        Returns None if no body placeholder exists.
        """
        return self._placeholders.get(1)

    @property
    def subtitle(self) -> Optional[Shape]:
        """
        Get subtitle placeholder.

        Searches for a placeholder with subtitle type.
        Returns None if not found.
        """
        for shape in self._placeholders.values():
            if shape.placeholder_format and shape.placeholder_format.is_subtitle:
                return shape
        return None

    @property
    def has_title(self) -> bool:
        """True if a title placeholder exists."""
        return 0 in self._placeholders

    @property
    def has_body(self) -> bool:
        """True if a body placeholder exists."""
        return 1 in self._placeholders

    @property
    def count(self) -> int:
        """Number of placeholders."""
        return len(self._placeholders)

    @property
    def is_empty(self) -> bool:
        """True if there are no placeholders."""
        return len(self._placeholders) == 0

    @property
    def indices(self) -> list[int]:
        """List of all placeholder indices."""
        return sorted(self._placeholders.keys())

    def get_by_type(self, type_name: str) -> Optional[Shape]:
        """
        Get placeholder by type name.

        Args:
            type_name: Placeholder type (e.g., 'title', 'body', 'pic', 'chart')

        Returns:
            First placeholder matching the type, or None
        """
        for shape in self._placeholders.values():
            if shape.placeholder_format:
                if shape.placeholder_format._type_str == type_name:
                    return shape
        return None

    def filter_by_type(self, type_name: str) -> list[Shape]:
        """
        Get all placeholders of a specific type.

        Args:
            type_name: Placeholder type to filter by

        Returns:
            List of placeholders matching the type
        """
        results = []
        for shape in self._placeholders.values():
            if shape.placeholder_format:
                if shape.placeholder_format._type_str == type_name:
                    results.append(shape)
        return results

    def __repr__(self) -> str:
        return f"<SlidePlaceholders count={len(self._placeholders)}>"


class TableCell:
    """
    A single cell in a table.

    Provides access to cell text and formatting.
    """

    def __init__(
        self,
        table: "Table",
        row: int,
        col: int,
        text: str = "",
        fill_color_hex: Optional[str] = None,
    ):
        self._table = table
        self._row = row
        self._col = col
        self._text = text
        self._fill_color_hex = fill_color_hex

    @property
    def text(self) -> str:
        """Cell text content."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Set cell text."""
        self._text = value
        self._emit_cell_change()

    @property
    def fill(self) -> Optional[str]:
        """Cell background color as hex string."""
        return self._fill_color_hex

    @fill.setter
    def fill(self, value: str) -> None:
        """Set cell background color."""
        if value.startswith('#'):
            value = value[1:]
        self._fill_color_hex = value.upper()
        self._emit_cell_change()

    def _emit_cell_change(self) -> None:
        """Emit a SetTableCell command."""
        if self._table._buffer:
            cmd = SetTableCell(
                shape_id=self._table._shape_id,
                row=self._row,
                col=self._col,
                text=self._text,
                fill_color_hex=self._fill_color_hex,
            )
            self._table._buffer.add(cmd)

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def row_index(self) -> int:
        """Zero-based row index of this cell."""
        return self._row

    @property
    def column_index(self) -> int:
        """Zero-based column index of this cell."""
        return self._col

    @property
    def is_empty(self) -> bool:
        """True if cell has no content or only whitespace."""
        return not self._text or self._text.strip() == ""

    @property
    def has_fill(self) -> bool:
        """True if cell has a background fill color."""
        return self._fill_color_hex is not None

    def clear(self) -> None:
        """Clear cell text content."""
        self.text = ""

    def __len__(self) -> int:
        """Return text length (allows len(cell))."""
        return len(self._text)

    def __str__(self) -> str:
        """Return cell text (allows str(cell))."""
        return self._text

    def __bool__(self) -> bool:
        """Boolean evaluation - True if cell has content."""
        return not self.is_empty

    @property
    def word_count(self) -> int:
        """Approximate word count in this cell."""
        return len(self._text.split())

    def upper(self) -> None:
        """Convert cell text to uppercase."""
        self.text = self._text.upper()

    def lower(self) -> None:
        """Convert cell text to lowercase."""
        self.text = self._text.lower()

    def capitalize(self) -> None:
        """Capitalize first letter of cell text."""
        self.text = self._text.capitalize()

    def title(self) -> None:
        """Convert cell text to title case."""
        self.text = self._text.title()

    def strip(self) -> None:
        """Remove leading and trailing whitespace from cell text."""
        self.text = self._text.strip()

    @property
    def address(self) -> str:
        """
        Get cell address in A1 notation (e.g., 'A1', 'B2', 'C3').

        Returns:
            Cell address string
        """
        # Convert column index to letter(s)
        col = self._col
        col_str = ""
        while col >= 0:
            col_str = chr(65 + (col % 26)) + col_str
            col = col // 26 - 1
            if col < 0:
                break
        return f"{col_str}{self._row + 1}"

    def copy_from(self, other: "TableCell") -> None:
        """
        Copy text and fill from another cell.

        Args:
            other: Source cell to copy from
        """
        self._text = other._text
        self._fill_color_hex = other._fill_color_hex
        self._emit_cell_change()


class Table(Shape):
    """
    A table shape on a slide.

    Provides row/column access for table editing.
    """

    def __init__(
        self,
        shape_id: ShapeId,
        slide: "Slide",
        buffer: Optional["CommandBuffer"],
        rows: int,
        cols: int,
        transform: Optional[Transform] = None,
    ):
        super().__init__(
            shape_id=shape_id,
            slide=slide,
            buffer=buffer,
            element_type="table",
            transform=transform,
        )
        self._rows = rows
        self._cols = cols
        self._cells: list[list[TableCell]] = []

        # Initialize empty cell grid
        for r in range(rows):
            row_cells = []
            for c in range(cols):
                row_cells.append(TableCell(self, r, c))
            self._cells.append(row_cells)

    def cell(self, row: int, col: int) -> TableCell:
        """
        Get a specific cell.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            TableCell object
        """
        if row < 0 or row >= self._rows:
            raise IndexError(f"Row {row} out of range (0-{self._rows - 1})")
        if col < 0 or col >= self._cols:
            raise IndexError(f"Column {col} out of range (0-{self._cols - 1})")
        return self._cells[row][col]

    @property
    def rows(self) -> int:
        """Number of rows."""
        return self._rows

    @property
    def cols(self) -> int:
        """Number of columns."""
        return self._cols

    def iter_cells(self) -> Iterator[TableCell]:
        """Iterate over all cells row by row."""
        for row in self._cells:
            for cell in row:
                yield cell

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def row_count(self) -> int:
        """Number of rows (alias for rows property)."""
        return self._rows

    @property
    def column_count(self) -> int:
        """Number of columns (alias for cols property)."""
        return self._cols

    @property
    def cell_count(self) -> int:
        """Total number of cells in the table."""
        return self._rows * self._cols

    def get_row(self, row_index: int) -> list[TableCell]:
        """
        Get all cells in a specific row.

        Args:
            row_index: Zero-based row index

        Returns:
            List of TableCell objects in the row
        """
        if row_index < 0 or row_index >= self._rows:
            raise IndexError(f"Row {row_index} out of range (0-{self._rows - 1})")
        return self._cells[row_index][:]

    def get_column(self, col_index: int) -> list[TableCell]:
        """
        Get all cells in a specific column.

        Args:
            col_index: Zero-based column index

        Returns:
            List of TableCell objects in the column
        """
        if col_index < 0 or col_index >= self._cols:
            raise IndexError(f"Column {col_index} out of range (0-{self._cols - 1})")
        return [self._cells[r][col_index] for r in range(self._rows)]

    def set_row_text(self, row_index: int, texts: list[str]) -> None:
        """
        Set text for all cells in a row.

        Args:
            row_index: Zero-based row index
            texts: List of text values (one per column)
        """
        if row_index < 0 or row_index >= self._rows:
            raise IndexError(f"Row {row_index} out of range (0-{self._rows - 1})")
        for col, text in enumerate(texts[:self._cols]):
            self._cells[row_index][col].text = text

    def set_column_text(self, col_index: int, texts: list[str]) -> None:
        """
        Set text for all cells in a column.

        Args:
            col_index: Zero-based column index
            texts: List of text values (one per row)
        """
        if col_index < 0 or col_index >= self._cols:
            raise IndexError(f"Column {col_index} out of range (0-{self._cols - 1})")
        for row, text in enumerate(texts[:self._rows]):
            self._cells[row][col_index].text = text

    def set_row_fill(self, row_index: int, color_hex: str) -> None:
        """
        Set background color for all cells in a row.

        Args:
            row_index: Zero-based row index
            color_hex: Color as hex string (e.g., 'FF0000' or '#FF0000')
        """
        if row_index < 0 or row_index >= self._rows:
            raise IndexError(f"Row {row_index} out of range (0-{self._rows - 1})")
        for col in range(self._cols):
            self._cells[row_index][col].fill = color_hex

    def set_column_fill(self, col_index: int, color_hex: str) -> None:
        """
        Set background color for all cells in a column.

        Args:
            col_index: Zero-based column index
            color_hex: Color as hex string (e.g., 'FF0000' or '#FF0000')
        """
        if col_index < 0 or col_index >= self._cols:
            raise IndexError(f"Column {col_index} out of range (0-{self._cols - 1})")
        for row in range(self._rows):
            self._cells[row][col_index].fill = color_hex

    def get_all_text(self) -> list[list[str]]:
        """
        Get text from all cells as a 2D list.

        Returns:
            List of lists containing cell text, organized as rows[cols]
        """
        return [[cell.text for cell in row] for row in self._cells]

    def set_all_text(self, data: list[list[str]]) -> None:
        """
        Set text for all cells from a 2D list.

        Args:
            data: List of lists containing cell text, organized as rows[cols]
        """
        for row_idx, row_data in enumerate(data[:self._rows]):
            for col_idx, text in enumerate(row_data[:self._cols]):
                self._cells[row_idx][col_idx].text = text

    def clear_all(self) -> None:
        """Clear text from all cells in the table."""
        for row in self._cells:
            for cell in row:
                cell.clear()

    def iter_rows(self) -> Iterator[list[TableCell]]:
        """
        Iterate over rows as lists of cells.

        Yields:
            List of TableCell objects for each row
        """
        for row in self._cells:
            yield row

    def iter_columns(self) -> Iterator[list[TableCell]]:
        """
        Iterate over columns as lists of cells.

        Yields:
            List of TableCell objects for each column
        """
        for col_idx in range(self._cols):
            yield [self._cells[row_idx][col_idx] for row_idx in range(self._rows)]

    @property
    def first_row(self) -> list[TableCell]:
        """Get the first row of cells."""
        return self._cells[0] if self._rows > 0 else []

    @property
    def last_row(self) -> list[TableCell]:
        """Get the last row of cells."""
        return self._cells[-1] if self._rows > 0 else []

    @property
    def first_column(self) -> list[TableCell]:
        """Get the first column of cells."""
        return [self._cells[r][0] for r in range(self._rows)] if self._cols > 0 else []

    @property
    def last_column(self) -> list[TableCell]:
        """Get the last column of cells."""
        return [self._cells[r][-1] for r in range(self._rows)] if self._cols > 0 else []

    @property
    def top_left(self) -> Optional[TableCell]:
        """Get the top-left cell (0, 0)."""
        if self._rows > 0 and self._cols > 0:
            return self._cells[0][0]
        return None

    @property
    def top_right(self) -> Optional[TableCell]:
        """Get the top-right cell (0, last_col)."""
        if self._rows > 0 and self._cols > 0:
            return self._cells[0][-1]
        return None

    @property
    def bottom_left(self) -> Optional[TableCell]:
        """Get the bottom-left cell (last_row, 0)."""
        if self._rows > 0 and self._cols > 0:
            return self._cells[-1][0]
        return None

    @property
    def bottom_right(self) -> Optional[TableCell]:
        """Get the bottom-right cell (last_row, last_col)."""
        if self._rows > 0 and self._cols > 0:
            return self._cells[-1][-1]
        return None

    @property
    def all_text(self) -> str:
        """
        Get all cell text as a single string.

        Cells are separated by tabs, rows by newlines (TSV format).
        """
        return "\n".join(
            "\t".join(cell.text for cell in row)
            for row in self._cells
        )

    @property
    def word_count(self) -> int:
        """Total word count across all cells."""
        return sum(cell.word_count for cell in self.iter_cells())

    @property
    def is_empty(self) -> bool:
        """True if all cells are empty."""
        return all(cell.is_empty for cell in self.iter_cells())

    def contains_text(self, text: str, case_sensitive: bool = False) -> bool:
        """
        Check if any cell contains the specified text.

        Args:
            text: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            True if any cell contains the text
        """
        search = text if case_sensitive else text.lower()
        for cell in self.iter_cells():
            cell_text = cell.text if case_sensitive else cell.text.lower()
            if search in cell_text:
                return True
        return False

    def find_cells(self, text: str, case_sensitive: bool = False) -> list[TableCell]:
        """
        Find all cells containing the specified text.

        Args:
            text: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            List of cells containing the text
        """
        results = []
        search = text if case_sensitive else text.lower()
        for cell in self.iter_cells():
            cell_text = cell.text if case_sensitive else cell.text.lower()
            if search in cell_text:
                results.append(cell)
        return results

    def get_diagonal(self, start_top_left: bool = True) -> list[TableCell]:
        """
        Get cells along a diagonal.

        Args:
            start_top_left: If True, get diagonal from top-left to bottom-right.
                           If False, get diagonal from top-right to bottom-left.

        Returns:
            List of cells along the diagonal
        """
        diagonal = []
        size = min(self._rows, self._cols)
        for i in range(size):
            if start_top_left:
                diagonal.append(self._cells[i][i])
            else:
                diagonal.append(self._cells[i][self._cols - 1 - i])
        return diagonal

    def transpose_text(self) -> list[list[str]]:
        """
        Get transposed text data (rows become columns).

        Returns:
            2D list with rows and columns swapped
        """
        return [
            [self._cells[r][c].text for r in range(self._rows)]
            for c in range(self._cols)
        ]

    def to_csv(self, delimiter: str = ",", quote_char: str = '"') -> str:
        """
        Export table data as CSV string.

        Args:
            delimiter: Field separator (default comma)
            quote_char: Character to quote fields containing delimiter

        Returns:
            CSV formatted string
        """
        lines = []
        for row in self._cells:
            cells = []
            for cell in row:
                text = cell.text
                # Quote if contains delimiter or newline
                if delimiter in text or '\n' in text or quote_char in text:
                    text = text.replace(quote_char, quote_char + quote_char)
                    text = f'{quote_char}{text}{quote_char}'
                cells.append(text)
            lines.append(delimiter.join(cells))
        return '\n'.join(lines)

    def to_list(self) -> list[list[str]]:
        """
        Export table data as 2D list.

        Returns:
            2D list of cell text values
        """
        return [
            [cell.text for cell in row]
            for row in self._cells
        ]

    def to_dict_list(self, header_row: bool = True) -> list[dict]:
        """
        Export table as list of dictionaries.

        Args:
            header_row: If True, use first row as keys

        Returns:
            List of dictionaries, one per row (excluding header if used)
        """
        if not header_row or self._rows < 2:
            # Use column indices as keys
            return [
                {str(i): cell.text for i, cell in enumerate(row)}
                for row in self._cells
            ]

        # Use first row as headers
        headers = [cell.text for cell in self._cells[0]]
        return [
            {headers[i]: cell.text for i, cell in enumerate(row)}
            for row in self._cells[1:]
        ]

    def set_row(self, row_index: int, values: list[str]) -> None:
        """
        Set all cells in a row.

        Args:
            row_index: Zero-based row index
            values: List of text values (truncated or padded to fit columns)
        """
        for col_idx in range(min(len(values), self._cols)):
            self._cells[row_index][col_idx].text = values[col_idx]

    def set_column(self, col_index: int, values: list[str]) -> None:
        """
        Set all cells in a column.

        Args:
            col_index: Zero-based column index
            values: List of text values (truncated or padded to fit rows)
        """
        for row_idx in range(min(len(values), self._rows)):
            self._cells[row_idx][col_index].text = values[row_idx]

    def get_row_text(self, row_index: int) -> list[str]:
        """
        Get text from all cells in a row.

        Args:
            row_index: Zero-based row index

        Returns:
            List of cell text values
        """
        return [cell.text for cell in self._cells[row_index]]

    def get_column_text(self, col_index: int) -> list[str]:
        """
        Get text from all cells in a column.

        Args:
            col_index: Zero-based column index

        Returns:
            List of cell text values
        """
        return [self._cells[row_idx][col_index].text for row_idx in range(self._rows)]

    def fill_row(self, row_index: int, value: str) -> None:
        """
        Fill all cells in a row with the same value.

        Args:
            row_index: Zero-based row index
            value: Text to set in all cells
        """
        for cell in self._cells[row_index]:
            cell.text = value

    def fill_column(self, col_index: int, value: str) -> None:
        """
        Fill all cells in a column with the same value.

        Args:
            col_index: Zero-based column index
            value: Text to set in all cells
        """
        for row_idx in range(self._rows):
            self._cells[row_idx][col_index].text = value

    def swap_rows(self, row1: int, row2: int) -> None:
        """
        Swap text content between two rows.

        Args:
            row1: First row index
            row2: Second row index
        """
        for col_idx in range(self._cols):
            temp = self._cells[row1][col_idx].text
            self._cells[row1][col_idx].text = self._cells[row2][col_idx].text
            self._cells[row2][col_idx].text = temp

    def swap_columns(self, col1: int, col2: int) -> None:
        """
        Swap text content between two columns.

        Args:
            col1: First column index
            col2: Second column index
        """
        for row_idx in range(self._rows):
            temp = self._cells[row_idx][col1].text
            self._cells[row_idx][col1].text = self._cells[row_idx][col2].text
            self._cells[row_idx][col2].text = temp

    def replace_all(self, old: str, new: str) -> int:
        """
        Replace text in all cells.

        Args:
            old: Text to find
            new: Replacement text

        Returns:
            Total number of replacements made
        """
        count = 0
        for cell in self.iter_cells():
            cell_count = cell.text.count(old)
            if cell_count > 0:
                cell.text = cell.text.replace(old, new)
                count += cell_count
        return count

    def upper_all(self) -> None:
        """Convert all cell text to uppercase."""
        for cell in self.iter_cells():
            cell.upper()

    def lower_all(self) -> None:
        """Convert all cell text to lowercase."""
        for cell in self.iter_cells():
            cell.lower()

    def strip_all(self) -> None:
        """Remove leading/trailing whitespace from all cells."""
        for cell in self.iter_cells():
            cell.strip()

    def to_markdown(self, alignment: str = "left") -> str:
        """
        Export table as Markdown-formatted table.

        Args:
            alignment: Column alignment - 'left', 'center', 'right', or
                      a string with one character per column (e.g., 'lcr')

        Returns:
            Markdown table string

        Example:
            md = table.to_markdown()
            # | Header 1 | Header 2 |
            # |----------|----------|
            # | Cell 1   | Cell 2   |
        """
        if self._rows == 0 or self._cols == 0:
            return ""

        # Get all text
        data = self.to_list()

        # Calculate column widths
        col_widths = []
        for col_idx in range(self._cols):
            max_width = max(len(data[row_idx][col_idx]) for row_idx in range(self._rows))
            col_widths.append(max(3, max_width))  # Minimum 3 for separator

        # Determine alignment per column
        if len(alignment) == 1:
            alignments = [alignment] * self._cols
        elif len(alignment) == self._cols:
            alignments = list(alignment)
        else:
            alignments = ['left'] * self._cols

        # Build header separator
        separators = []
        for i, width in enumerate(col_widths):
            align = alignments[i] if i < len(alignments) else 'left'
            if align == 'center' or align == 'c':
                separators.append(':' + '-' * (width - 2) + ':')
            elif align == 'right' or align == 'r':
                separators.append('-' * (width - 1) + ':')
            else:  # left
                separators.append(':' + '-' * (width - 1))

        # Build rows
        lines = []
        for row_idx, row_data in enumerate(data):
            cells = [cell.ljust(col_widths[i]) for i, cell in enumerate(row_data)]
            lines.append('| ' + ' | '.join(cells) + ' |')

            # Add separator after first row (header)
            if row_idx == 0:
                lines.append('| ' + ' | '.join(separators) + ' |')

        return '\n'.join(lines)

    def sort_rows(
        self,
        key_column: int = 0,
        reverse: bool = False,
        numeric: bool = False,
    ) -> None:
        """
        Sort rows by values in a specific column.

        Note: This reorders the cell text content but not the cells themselves.

        Args:
            key_column: Column index to sort by
            reverse: If True, sort descending
            numeric: If True, parse values as numbers
        """
        if self._rows <= 1:
            return

        # Extract data
        data = self.to_list()

        # Sort data (skip header row)
        if self._rows > 1:
            header = data[0]
            body = data[1:]

            def get_key(row: list[str]):
                val = row[key_column]
                if numeric:
                    try:
                        return float(val.replace(',', ''))
                    except ValueError:
                        return 0.0
                return val.lower()

            body.sort(key=get_key, reverse=reverse)
            data = [header] + body

        # Write back
        self.set_all_text(data)

    def filter_rows(self, column: int, contains: str, case_sensitive: bool = False) -> list[int]:
        """
        Find rows where a column contains specific text.

        Args:
            column: Column index to search
            contains: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            List of row indices matching the filter
        """
        results = []
        search = contains if case_sensitive else contains.lower()

        for row_idx in range(self._rows):
            cell_text = self._cells[row_idx][column].text
            if not case_sensitive:
                cell_text = cell_text.lower()
            if search in cell_text:
                results.append(row_idx)

        return results

    def copy_row(self, from_row: int, to_row: int) -> None:
        """
        Copy text content from one row to another.

        Args:
            from_row: Source row index
            to_row: Destination row index
        """
        for col_idx in range(self._cols):
            self._cells[to_row][col_idx].text = self._cells[from_row][col_idx].text

    def copy_column(self, from_col: int, to_col: int) -> None:
        """
        Copy text content from one column to another.

        Args:
            from_col: Source column index
            to_col: Destination column index
        """
        for row_idx in range(self._rows):
            self._cells[row_idx][to_col].text = self._cells[row_idx][from_col].text

    def sum_column(self, column: int, skip_header: bool = True) -> float:
        """
        Sum numeric values in a column.

        Args:
            column: Column index
            skip_header: If True, skip the first row

        Returns:
            Sum of numeric values (non-numeric cells are treated as 0)
        """
        total = 0.0
        start_row = 1 if skip_header and self._rows > 1 else 0

        for row_idx in range(start_row, self._rows):
            text = self._cells[row_idx][column].text.strip()
            try:
                total += float(text.replace(',', ''))
            except ValueError:
                pass

        return total

    def average_column(self, column: int, skip_header: bool = True) -> float:
        """
        Calculate average of numeric values in a column.

        Args:
            column: Column index
            skip_header: If True, skip the first row

        Returns:
            Average of numeric values (non-numeric cells are excluded)
        """
        total = 0.0
        count = 0
        start_row = 1 if skip_header and self._rows > 1 else 0

        for row_idx in range(start_row, self._rows):
            text = self._cells[row_idx][column].text.strip()
            try:
                total += float(text.replace(',', ''))
                count += 1
            except ValueError:
                pass

        return total / count if count > 0 else 0.0

    def get_headers(self) -> list[str]:
        """
        Get the first row as column headers.

        Returns:
            List of header strings
        """
        if self._rows == 0:
            return []
        return [cell.text for cell in self._cells[0]]

    def set_headers(self, headers: list[str]) -> None:
        """
        Set the first row as column headers.

        Args:
            headers: List of header strings
        """
        if self._rows == 0:
            return
        for col_idx, header in enumerate(headers[:self._cols]):
            self._cells[0][col_idx].text = header

    def to_dict(self) -> dict:
        """
        Serialize table to a comprehensive dictionary.

        Returns:
            Dictionary with table metadata and content
        """
        return {
            'rows': self._rows,
            'columns': self._cols,
            'cell_count': self.cell_count,
            'word_count': self.word_count,
            'is_empty': self.is_empty,
            'headers': self.get_headers(),
            'data': self.to_list(),
        }

    def find_and_replace(
        self,
        find: str,
        replace: str,
        column: Optional[int] = None,
        case_sensitive: bool = False,
    ) -> int:
        """
        Find and replace text in the table.

        Args:
            find: Text to find
            replace: Replacement text
            column: If specified, only search in this column
            case_sensitive: Whether to do case-sensitive search

        Returns:
            Number of replacements made
        """
        import re
        count = 0
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(find), flags)

        for row_idx in range(self._rows):
            cols = [column] if column is not None else range(self._cols)
            for col_idx in cols:
                text = self._cells[row_idx][col_idx].text
                new_text, n = pattern.subn(replace, text)
                if n > 0:
                    self._cells[row_idx][col_idx].text = new_text
                    count += n

        return count

    def get_unique_values(self, column: int, skip_header: bool = True) -> set[str]:
        """
        Get unique values in a column.

        Args:
            column: Column index
            skip_header: If True, skip the first row

        Returns:
            Set of unique values
        """
        start_row = 1 if skip_header and self._rows > 1 else 0
        return {
            self._cells[row_idx][column].text
            for row_idx in range(start_row, self._rows)
        }

    def count_values(self, column: int, skip_header: bool = True) -> dict[str, int]:
        """
        Count occurrences of each value in a column.

        Args:
            column: Column index
            skip_header: If True, skip the first row

        Returns:
            Dictionary mapping values to counts
        """
        counts: dict[str, int] = {}
        start_row = 1 if skip_header and self._rows > 1 else 0

        for row_idx in range(start_row, self._rows):
            text = self._cells[row_idx][column].text
            counts[text] = counts.get(text, 0) + 1

        return counts

    def __repr__(self) -> str:
        return f"<Table shape_id='{self._shape_id}' rows={self._rows} cols={self._cols}>"
