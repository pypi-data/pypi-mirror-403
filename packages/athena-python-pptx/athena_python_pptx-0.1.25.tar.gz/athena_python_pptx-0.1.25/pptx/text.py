"""
Text-related proxy classes.

Provides python-pptx-compatible TextFrame, Paragraph, and Run abstractions.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union

from .commands import SetText, SetRunStyle, SetParagraphStyle, SetTextFrameProperties, FitText
from .dml.color import RGBColor, ColorFormat
from .errors import UnsupportedFeatureError
from .typing import ShapeId, TextStyle

if TYPE_CHECKING:
    from .batching import CommandBuffer


# Paragraph alignment constants (matching python-pptx PP_PARAGRAPH_ALIGNMENT)
class PP_ALIGN:
    """Paragraph alignment enumeration."""
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'
    JUSTIFY = 'justify'
    DISTRIBUTE = 'justify'  # Map to justify for now
    JUSTIFY_LOW = 'justify'
    THAI_DISTRIBUTE = 'justify'


class _FontColorFormat(ColorFormat):
    """
    ColorFormat subclass that notifies the Font when color changes.

    This enables the python-pptx compatible pattern:
        font.color.rgb = RGBColor(255, 0, 0)

    When rgb is set, this notifies the parent Font to emit a style change command.
    """

    def __init__(self, font: Font, rgb: Optional[RGBColor] = None):
        super().__init__(rgb=rgb)
        self._font = font

    @ColorFormat.rgb.setter
    def rgb(self, value: RGBColor) -> None:
        """Set the RGB color and notify the font."""
        if not isinstance(value, RGBColor):
            raise TypeError(f"Expected RGBColor, got {type(value).__name__}")
        self._rgb = value
        self._theme_color = None
        # Notify font to emit style change
        self._font._on_color_change(str(value))


class Font:
    """
    Font styling for a text run.

    Mirrors python-pptx's Font class.
    """

    def __init__(
        self,
        run: Run,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        size: Optional[int] = None,
        name: Optional[str] = None,
        color_hex: Optional[str] = None,
        spacing_pt: Optional[float] = None,
    ):
        self._run = run
        self._bold = bold
        self._italic = italic
        self._underline = underline
        self._size = size  # In EMU
        self._name = name
        self._color_hex = color_hex
        self._spacing_pt = spacing_pt  # Character spacing in points
        # Initialize color format with callback
        rgb = RGBColor.from_string(color_hex) if color_hex else None
        self._color_format = _FontColorFormat(self, rgb=rgb)

    @property
    def bold(self) -> Optional[bool]:
        """Bold state."""
        return self._bold

    @bold.setter
    def bold(self, value: bool) -> None:
        self._bold = value
        self._emit_style_change()

    @property
    def italic(self) -> Optional[bool]:
        """Italic state."""
        return self._italic

    @italic.setter
    def italic(self, value: bool) -> None:
        self._italic = value
        self._emit_style_change()

    @property
    def underline(self) -> Optional[bool]:
        """Underline state."""
        return self._underline

    @underline.setter
    def underline(self, value: bool) -> None:
        self._underline = value
        self._emit_style_change()

    @property
    def size(self) -> Optional[int]:
        """Font size in EMU."""
        return self._size

    @size.setter
    def size(self, value: int) -> None:
        """Set font size in EMU."""
        self._size = value
        self._emit_style_change()

    @property
    def name(self) -> Optional[str]:
        """Font family name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._emit_style_change()

    @property
    def spacing(self) -> Optional[float]:
        """
        Character spacing in points.

        Positive values expand character spacing, negative values condense.
        For example, 1.5 expands spacing by 1.5 points between characters.
        """
        return self._spacing_pt

    @spacing.setter
    def spacing(self, value: float) -> None:
        """Set character spacing in points."""
        self._spacing_pt = value
        self._emit_style_change()

    # -------------------------------------------------------------------------
    # Convenience properties
    # -------------------------------------------------------------------------

    @property
    def size_pt(self) -> Optional[float]:
        """
        Font size in points (convenience property).

        This is a more user-friendly alternative to `size` which uses EMUs.

        Example:
            font.size_pt = 12.0  # Set 12pt font
        """
        if self._size is None:
            return None
        from .units import EMU_PER_PT
        return self._size / EMU_PER_PT

    @size_pt.setter
    def size_pt(self, value: Optional[float]) -> None:
        """Set font size in points."""
        if value is None:
            self._size = None
        else:
            from .units import EMU_PER_PT
            self._size = int(value * EMU_PER_PT)
        self._emit_style_change()

    @property
    def strikethrough(self) -> Optional[bool]:
        """
        Strikethrough (line-through) text.

        Note: This property is tracked locally but strikethrough support
        depends on backend capabilities.
        """
        return getattr(self, '_strikethrough', None)

    @strikethrough.setter
    def strikethrough(self, value: bool) -> None:
        self._strikethrough = value
        self._emit_style_change()

    @property
    def all_caps(self) -> Optional[bool]:
        """
        All capitals text transformation.

        Note: This property is tracked locally. Text will be displayed
        in uppercase but the underlying text content remains unchanged.
        """
        return getattr(self, '_all_caps', None)

    @all_caps.setter
    def all_caps(self, value: bool) -> None:
        self._all_caps = value
        self._emit_style_change()

    @property
    def small_caps(self) -> Optional[bool]:
        """
        Small capitals text transformation.

        Note: This property is tracked locally.
        """
        return getattr(self, '_small_caps', None)

    @small_caps.setter
    def small_caps(self, value: bool) -> None:
        self._small_caps = value
        self._emit_style_change()

    @property
    def superscript(self) -> Optional[bool]:
        """
        Superscript vertical positioning.

        Note: Mutually exclusive with subscript.
        """
        return getattr(self, '_superscript', None)

    @superscript.setter
    def superscript(self, value: bool) -> None:
        if value:
            self._subscript = False  # Clear subscript
        self._superscript = value
        self._emit_style_change()

    @property
    def subscript(self) -> Optional[bool]:
        """
        Subscript vertical positioning.

        Note: Mutually exclusive with superscript.
        """
        return getattr(self, '_subscript', None)

    @subscript.setter
    def subscript(self, value: bool) -> None:
        if value:
            self._superscript = False  # Clear superscript
        self._subscript = value
        self._emit_style_change()

    @property
    def color(self) -> _FontColorFormat:
        """
        Font color as a ColorFormat object (python-pptx compatible).

        Use font.color.rgb to get/set the color:
            font.color.rgb = RGBColor(255, 0, 0)  # Set red
            rgb = font.color.rgb  # Get RGBColor or None

        Example:
            from pptx.dml.color import RGBColor
            run.font.color.rgb = RGBColor(255, 0, 0)  # Red text
        """
        return self._color_format

    @property
    def color_hex(self) -> Optional[str]:
        """
        Font color as a hex string (e.g., "FF0000").

        Returns None if no color is explicitly set.
        This is an Athena extension for convenience.

        Can be set with a hex string:
            font.color_hex = "FF0000"
            font.color_hex = "#00FF00"  # Leading # is stripped
        """
        return self._color_hex

    @color_hex.setter
    def color_hex(self, value: Optional[str]) -> None:
        """Set font color with hex string."""
        if value is None:
            self._color_hex = None
            self._color_format._rgb = None
        else:
            # Strip leading # if present
            if value.startswith('#'):
                value = value[1:]
            self._color_hex = value
            self._color_format._rgb = RGBColor.from_string(value)
        self._emit_style_change()

    @property
    def is_styled(self) -> bool:
        """
        True if any explicit styling is applied to this font.

        Returns True if bold, italic, underline, size, name, or color
        has been explicitly set.
        """
        return any([
            self._bold is not None,
            self._italic is not None,
            self._underline is not None,
            self._size is not None,
            self._name is not None,
            self._color_hex is not None,
            getattr(self, '_strikethrough', None) is not None,
            getattr(self, '_all_caps', None) is not None,
            getattr(self, '_small_caps', None) is not None,
            getattr(self, '_superscript', None) is not None,
            getattr(self, '_subscript', None) is not None,
        ])

    def copy_style_from(self, other: "Font") -> None:
        """
        Copy all styling from another Font object.

        Args:
            other: Source Font to copy from
        """
        self._bold = other._bold
        self._italic = other._italic
        self._underline = other._underline
        self._size = other._size
        self._name = other._name
        self._color_hex = other._color_hex
        self._spacing_pt = other._spacing_pt
        self._strikethrough = getattr(other, '_strikethrough', None)
        self._all_caps = getattr(other, '_all_caps', None)
        self._small_caps = getattr(other, '_small_caps', None)
        self._superscript = getattr(other, '_superscript', None)
        self._subscript = getattr(other, '_subscript', None)
        # Update color format
        if self._color_hex:
            self._color_format._rgb = RGBColor.from_string(self._color_hex)
        else:
            self._color_format._rgb = None
        self._emit_style_change()

    def clear_style(self) -> None:
        """
        Clear all explicit styling, reverting to inherited/default values.
        """
        self._bold = None
        self._italic = None
        self._underline = None
        self._size = None
        self._name = None
        self._color_hex = None
        self._spacing_pt = None
        self._strikethrough = None
        self._all_caps = None
        self._small_caps = None
        self._superscript = None
        self._subscript = None
        self._color_format._rgb = None
        self._emit_style_change()

    def to_dict(self) -> dict:
        """
        Serialize font properties to a dictionary.

        Returns:
            Dictionary with all font properties
        """
        return {
            'bold': self._bold,
            'italic': self._italic,
            'underline': self._underline,
            'size_emu': self._size,
            'size_pt': self.size_pt,
            'name': self._name,
            'color_hex': self._color_hex,
            'spacing_pt': self._spacing_pt,
            'strikethrough': getattr(self, '_strikethrough', None),
            'all_caps': getattr(self, '_all_caps', None),
            'small_caps': getattr(self, '_small_caps', None),
            'superscript': getattr(self, '_superscript', None),
            'subscript': getattr(self, '_subscript', None),
        }

    def matches(self, other: "Font") -> bool:
        """
        Check if this font's styling matches another font.

        Args:
            other: Font to compare with

        Returns:
            True if all styling properties match
        """
        return (
            self._bold == other._bold and
            self._italic == other._italic and
            self._underline == other._underline and
            self._size == other._size and
            self._name == other._name and
            self._color_hex == other._color_hex and
            self._spacing_pt == other._spacing_pt
        )

    def apply_from_dict(self, style: dict) -> None:
        """
        Apply styling from a dictionary.

        Args:
            style: Dictionary with font properties
        """
        if 'bold' in style:
            self._bold = style['bold']
        if 'italic' in style:
            self._italic = style['italic']
        if 'underline' in style:
            self._underline = style['underline']
        if 'size_emu' in style:
            self._size = style['size_emu']
        elif 'size_pt' in style and style['size_pt'] is not None:
            from .units import EMU_PER_PT
            self._size = int(style['size_pt'] * EMU_PER_PT)
        if 'name' in style:
            self._name = style['name']
        if 'color_hex' in style:
            self._color_hex = style['color_hex']
            if self._color_hex:
                self._color_format._rgb = RGBColor.from_string(self._color_hex)
            else:
                self._color_format._rgb = None
        if 'spacing_pt' in style:
            self._spacing_pt = style['spacing_pt']
        self._emit_style_change()

    def _on_color_change(self, hex_value: str) -> None:
        """Called by ColorFormat when color changes."""
        self._color_hex = hex_value.upper()
        self._emit_style_change()

    def _emit_style_change(self) -> None:
        """Emit a SetRunStyle command for this run."""
        style: TextStyle = {}
        if self._bold is not None:
            style["bold"] = self._bold
        if self._italic is not None:
            style["italic"] = self._italic
        if self._underline is not None:
            style["underline"] = self._underline
        if self._size is not None:
            # Convert EMU to points for the command
            from .units import EMU_PER_PT
            style["fontSizePt"] = self._size / EMU_PER_PT
        if self._name is not None:
            style["fontFamily"] = self._name
        if self._color_hex is not None:
            style["colorHex"] = self._color_hex
        if self._spacing_pt is not None:
            style["spacingPt"] = self._spacing_pt

        if style and self._run._paragraph._text_frame._buffer:
            cmd = SetRunStyle(
                shape_id=self._run._paragraph._text_frame._shape_id,
                path={"p": self._run._paragraph._index, "r": self._run._index},
                style=style,
            )
            self._run._paragraph._text_frame._buffer.add(cmd)


class Hyperlink:
    """
    Hyperlink attached to a text run.

    Provides access to the hyperlink URL and tooltip. Mirrors python-pptx's
    _Hyperlink class.

    Note: Hyperlink support requires backend implementation. Currently this
    provides the API but changes may not persist to the exported PPTX.
    """

    def __init__(self, run: "Run", address: Optional[str] = None, tooltip: Optional[str] = None):
        self._run = run
        self._address = address
        self._tooltip = tooltip

    @property
    def address(self) -> Optional[str]:
        """
        Target URL of the hyperlink.

        Can be an external URL (https://...) or internal reference (#slide2).
        Returns None if no hyperlink is set.

        Example:
            run.hyperlink.address = "https://example.com"
            run.hyperlink.address = "#slide3"  # Link to slide 3
        """
        return self._address

    @address.setter
    def address(self, value: Optional[str]) -> None:
        """
        Set the hyperlink target URL.

        Args:
            value: URL string or None to remove the hyperlink
        """
        self._address = value
        # Note: When backend hyperlink support is added, emit a SetHyperlink command here
        # For now, store locally - backend doesn't yet support hyperlinks

    @property
    def tooltip(self) -> Optional[str]:
        """
        Tooltip text displayed when hovering over the hyperlink.

        Returns None if no tooltip is set.
        """
        return self._tooltip

    @tooltip.setter
    def tooltip(self, value: Optional[str]) -> None:
        """
        Set the hyperlink tooltip.

        Args:
            value: Tooltip text or None to remove
        """
        self._tooltip = value

    def __bool__(self) -> bool:
        """True if this run has a hyperlink address."""
        return self._address is not None and len(self._address) > 0

    def __repr__(self) -> str:
        if self._address:
            return f"<Hyperlink address='{self._address}'>"
        return "<Hyperlink (none)>"


class Run:
    """
    A run of text with consistent formatting.

    Mirrors python-pptx's _Run class.
    """

    def __init__(
        self,
        paragraph: "Paragraph",
        index: int,
        text: str = "",
        style: Optional[TextStyle] = None,
        hyperlink_address: Optional[str] = None,
        hyperlink_tooltip: Optional[str] = None,
    ):
        self._paragraph = paragraph
        self._index = index
        self._text = text
        self._font = Font(
            self,
            bold=style.get("bold") if style else None,
            italic=style.get("italic") if style else None,
            underline=style.get("underline") if style else None,
            size=int(style.get("fontSizePt", 0) * 12700) if style and style.get("fontSizePt") else None,
            name=style.get("fontFamily") if style else None,
            color_hex=style.get("colorHex") if style else None,
            spacing_pt=style.get("spacingPt") if style else None,
        )
        self._hyperlink = Hyperlink(self, address=hyperlink_address, tooltip=hyperlink_tooltip)

    @property
    def text(self) -> str:
        """The text content of this run."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Set text content. Note: This currently sets all text in the shape."""
        # For Phase 1, we only support setting full text content
        # Individual run edits would require more complex tracking
        self._text = value
        self._paragraph._text_frame._set_full_text(
            self._paragraph._text_frame._get_full_text()
        )

    @property
    def font(self) -> Font:
        """Font formatting for this run."""
        return self._font

    @property
    def hyperlink(self) -> Hyperlink:
        """
        Hyperlink attached to this run.

        Access the hyperlink properties:
            run.hyperlink.address = "https://example.com"
            run.hyperlink.tooltip = "Click to visit"

        Check if run has a hyperlink:
            if run.hyperlink:
                print(f"Links to: {run.hyperlink.address}")

        Note: Hyperlink support requires backend implementation. Currently
        this provides the python-pptx compatible API but links may not
        persist to the exported PPTX until backend support is added.
        """
        return self._hyperlink

    @property
    def has_hyperlink(self) -> bool:
        """
        True if this run has a hyperlink.

        Convenience property equivalent to `bool(run.hyperlink)`.
        """
        return bool(self._hyperlink)

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def length(self) -> int:
        """Character count of this run's text."""
        return len(self._text)

    @property
    def is_empty(self) -> bool:
        """True if run has no content or only whitespace."""
        return not self._text or self._text.strip() == ""

    @property
    def is_bold(self) -> bool:
        """True if run is bold."""
        return self._font._bold is True

    @property
    def is_italic(self) -> bool:
        """True if run is italic."""
        return self._font._italic is True

    @property
    def is_underlined(self) -> bool:
        """True if run is underlined."""
        return self._font._underline is True

    @property
    def has_styling(self) -> bool:
        """True if run has any explicit styling."""
        return self._font.is_styled

    @property
    def word_count(self) -> int:
        """Approximate word count in this run."""
        return len(self._text.split())

    def upper(self) -> None:
        """Convert run text to uppercase."""
        self._text = self._text.upper()
        self._paragraph._text_frame._set_full_text(
            self._paragraph._text_frame._get_full_text()
        )

    def lower(self) -> None:
        """Convert run text to lowercase."""
        self._text = self._text.lower()
        self._paragraph._text_frame._set_full_text(
            self._paragraph._text_frame._get_full_text()
        )

    def capitalize(self) -> None:
        """Capitalize first letter of run text."""
        self._text = self._text.capitalize()
        self._paragraph._text_frame._set_full_text(
            self._paragraph._text_frame._get_full_text()
        )

    def title(self) -> None:
        """Convert run text to title case."""
        self._text = self._text.title()
        self._paragraph._text_frame._set_full_text(
            self._paragraph._text_frame._get_full_text()
        )

    def strip(self) -> None:
        """Remove leading and trailing whitespace from run text."""
        self._text = self._text.strip()
        self._paragraph._text_frame._set_full_text(
            self._paragraph._text_frame._get_full_text()
        )

    def clear(self) -> None:
        """Clear the run's text content."""
        self._text = ""
        self._paragraph._text_frame._set_full_text(
            self._paragraph._text_frame._get_full_text()
        )

    def __len__(self) -> int:
        """Return length of text (allows len(run))."""
        return len(self._text)

    def __str__(self) -> str:
        """Return text content (allows str(run))."""
        return self._text

    def __bool__(self) -> bool:
        """Boolean evaluation - True if run has content."""
        return not self.is_empty

    def __contains__(self, item: str) -> bool:
        """Check if text contains substring (allows 'x' in run)."""
        return item in self._text

    def find(self, substring: str) -> int:
        """
        Find the position of a substring in the run text.

        Args:
            substring: Text to find

        Returns:
            Position of substring, or -1 if not found
        """
        return self._text.find(substring)

    def replace(self, old: str, new: str) -> int:
        """
        Replace occurrences of a substring in the run text.

        Args:
            old: Text to find
            new: Replacement text

        Returns:
            Number of replacements made
        """
        count = self._text.count(old)
        if count > 0:
            self._text = self._text.replace(old, new)
            self._paragraph._text_frame._set_full_text(
                self._paragraph._text_frame._get_full_text()
            )
        return count

    def startswith(self, prefix: str) -> bool:
        """Check if run text starts with prefix."""
        return self._text.startswith(prefix)

    def endswith(self, suffix: str) -> bool:
        """Check if run text ends with suffix."""
        return self._text.endswith(suffix)

    def to_dict(self) -> dict:
        """
        Serialize run to a dictionary.

        Returns:
            Dictionary with text and font properties
        """
        return {
            'text': self._text,
            'bold': self._font._bold,
            'italic': self._font._italic,
            'underline': self._font._underline,
            'size_emu': self._font._size,
            'font_name': self._font._name,
            'color_hex': self._font._color_hex,
        }

    def copy_format_from(self, other: "Run") -> None:
        """
        Copy formatting from another run (not text).

        Args:
            other: Source run to copy formatting from
        """
        self._font.copy_style_from(other._font)


class Paragraph:
    """
    A paragraph containing text runs.

    Mirrors python-pptx's _Paragraph class.
    """

    def __init__(
        self,
        text_frame: TextFrame,
        index: int,
        runs: Optional[list[dict[str, Any]]] = None,
        alignment: Optional[str] = None,
        level: int = 0,
        bullet: Optional[str] = None,
        bullet_color_hex: Optional[str] = None,
        line_spacing: Optional[float] = None,
        space_before: Optional[int] = None,
        space_after: Optional[int] = None,
        margin_left: Optional[int] = None,
        indent: Optional[int] = None,
    ):
        self._text_frame = text_frame
        self._index = index
        self._runs: list[Run] = []
        self._alignment = alignment
        self._level = level
        self._bullet = bullet
        self._bullet_color_hex = bullet_color_hex
        self._line_spacing = line_spacing
        self._space_before = space_before
        self._space_after = space_after
        self._margin_left = margin_left
        self._indent = indent

        if runs:
            for i, run_data in enumerate(runs):
                self._runs.append(
                    Run(
                        self,
                        i,
                        text=run_data.get("text", ""),
                        style=run_data.get("style"),
                    )
                )
        else:
            # Default single empty run
            self._runs.append(Run(self, 0, ""))

    @property
    def runs(self) -> list[Run]:
        """List of runs in this paragraph."""
        return self._runs

    @property
    def text(self) -> str:
        """Combined text of all runs."""
        return "".join(run.text for run in self._runs)

    @text.setter
    def text(self, value: str) -> None:
        """Set text, replacing all runs with a single run."""
        if self._runs:
            self._runs[0]._text = value
            self._runs = self._runs[:1]
        else:
            self._runs = [Run(self, 0, value)]

        self._text_frame._set_full_text(self._text_frame._get_full_text())

    def add_run(self) -> Run:
        """Add a new run to this paragraph."""
        run = Run(self, len(self._runs), "")
        self._runs.append(run)
        return run

    def clear(self) -> None:
        """
        Remove all runs from this paragraph.

        After clearing, the paragraph will have a single empty run.
        """
        self._runs = [Run(self, 0, "")]
        self._text_frame._set_full_text(self._text_frame._get_full_text())

    def add_line_break(self) -> None:
        """
        Add a line break at the end of the paragraph.

        Note: In our implementation this appends a newline to the last run's text.
        """
        if self._runs:
            self._runs[-1]._text += "\v"  # Vertical tab = soft line break in OOXML

    @property
    def space_before(self) -> Optional[int]:
        """
        Space before paragraph in EMU.

        Returns None if not explicitly set.
        """
        return self._space_before

    @space_before.setter
    def space_before(self, value: Optional[int]) -> None:
        """Set space before paragraph in EMU."""
        self._space_before = value
        self._emit_paragraph_style_change()

    @property
    def space_after(self) -> Optional[int]:
        """
        Space after paragraph in EMU.

        Returns None if not explicitly set.
        """
        return self._space_after

    @space_after.setter
    def space_after(self, value: Optional[int]) -> None:
        """Set space after paragraph in EMU."""
        self._space_after = value
        self._emit_paragraph_style_change()

    @property
    def font(self) -> Font:
        """
        Font for the paragraph (applies to first run).

        Note: python-pptx applies font changes at paragraph level,
        which we approximate by targeting the first run.
        """
        if self._runs:
            return self._runs[0].font
        run = self.add_run()
        return run.font

    @property
    def alignment(self) -> Optional[str]:
        """
        Paragraph alignment.

        Returns one of: 'left', 'center', 'right', 'justify', or None.
        Can be set using string values or PP_ALIGN constants.
        """
        return self._alignment

    @alignment.setter
    def alignment(self, value: Any) -> None:
        """
        Set paragraph alignment.

        Args:
            value: Alignment value - 'left', 'center', 'right', 'justify',
                   or a PP_ALIGN constant (integer enum)
        """
        # Handle PP_ALIGN enum values (integers)
        # PP_ALIGN: LEFT=1, CENTER=2, RIGHT=3, JUSTIFY=4, DISTRIBUTE=5, THAI_DISTRIBUTE=6, JUSTIFY_LOW=7
        if isinstance(value, int):
            int_to_str = {
                1: 'left',
                2: 'center',
                3: 'right',
                4: 'justify',
                5: 'justify',  # DISTRIBUTE -> justify
                6: 'justify',  # THAI_DISTRIBUTE -> justify
                7: 'justify',  # JUSTIFY_LOW -> justify
                -2: None,      # MIXED
            }
            value = int_to_str.get(value, 'left')
        # Handle string values
        elif isinstance(value, str):
            value = value.lower()
        elif value is None:
            value = None

        # Validate
        valid_alignments = ('left', 'center', 'right', 'justify', None)
        if value not in valid_alignments:
            raise ValueError(f"Invalid alignment: {value}. Must be one of {valid_alignments}")

        self._alignment = value
        self._emit_paragraph_style_change()

    @property
    def level(self) -> int:
        """
        Indentation level for bullet hierarchy (0-8).

        Level 0 is no indentation, level 1 is first indent level, etc.
        """
        return self._level

    @level.setter
    def level(self, value: int) -> None:
        """
        Set indentation level.

        Args:
            value: Integer 0-8
        """
        if not isinstance(value, int) or value < 0 or value > 8:
            raise ValueError(f"Level must be an integer between 0 and 8, got {value}")
        self._level = value
        self._emit_paragraph_style_change()

    @property
    def line_spacing(self) -> Optional[float]:
        """
        Line spacing multiplier.

        1.0 = single spacing, 1.5 = 1.5 lines, 2.0 = double spacing
        """
        return self._line_spacing

    @line_spacing.setter
    def line_spacing(self, value: float) -> None:
        """Set line spacing multiplier."""
        if value <= 0:
            raise ValueError(f"Line spacing must be positive, got {value}")
        self._line_spacing = value
        self._emit_paragraph_style_change()

    @property
    def margin_left(self) -> Optional[int]:
        """
        Left margin in EMU.

        This controls the distance from the text frame's left edge to
        where the paragraph starts.
        """
        return self._margin_left

    @margin_left.setter
    def margin_left(self, value: int) -> None:
        """Set left margin in EMU."""
        self._margin_left = value
        self._emit_paragraph_style_change()

    @property
    def indent(self) -> Optional[int]:
        """
        First-line indent in EMU.

        Positive values indent the first line further right.
        Negative values create a hanging indent (first line starts left of subsequent lines).
        """
        return self._indent

    @indent.setter
    def indent(self, value: int) -> None:
        """Set first-line indent in EMU."""
        self._indent = value
        self._emit_paragraph_style_change()

    @property
    def bullet_color(self) -> Optional[RGBColor]:
        """
        Bullet color as an RGBColor.

        Returns None if not explicitly set.
        """
        if self._bullet_color_hex:
            return RGBColor.from_string(self._bullet_color_hex)
        return None

    @bullet_color.setter
    def bullet_color(self, value: RGBColor) -> None:
        """
        Set bullet color.

        Args:
            value: RGBColor object
        """
        if value is None:
            self._bullet_color_hex = None
        elif isinstance(value, RGBColor):
            self._bullet_color_hex = str(value).upper()
        else:
            raise TypeError(f"Expected RGBColor, got {type(value).__name__}")
        self._emit_paragraph_style_change()

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def run_count(self) -> int:
        """Number of runs in this paragraph."""
        return len(self._runs)

    @property
    def first_run(self) -> Optional[Run]:
        """
        First run in the paragraph.

        Returns None if paragraph has no runs.
        """
        return self._runs[0] if self._runs else None

    @property
    def last_run(self) -> Optional[Run]:
        """
        Last run in the paragraph.

        Returns None if paragraph has no runs.
        """
        return self._runs[-1] if self._runs else None

    @property
    def is_empty(self) -> bool:
        """True if paragraph has no content or only whitespace."""
        return not self.text or self.text.strip() == ""

    @property
    def length(self) -> int:
        """Total character count of this paragraph's text."""
        return len(self.text)

    @property
    def word_count(self) -> int:
        """Approximate word count in this paragraph."""
        return len(self.text.split())

    @property
    def has_bullet(self) -> bool:
        """True if this paragraph has a bullet point."""
        return self._bullet is not None

    @property
    def bullet(self) -> Optional[bool]:
        """
        Bullet state - True if bullet is enabled.

        Set to True to enable bullets, False to disable.
        Use bullet_type property to control the bullet character.
        """
        return self._bullet is not None and self._bullet != 'none'

    @bullet.setter
    def bullet(self, value: bool) -> None:
        """
        Enable or disable bullet for this paragraph.

        Args:
            value: True to enable bullets, False to disable
        """
        if value:
            if self._bullet is None or self._bullet == 'none':
                self._bullet = 'disc'  # Default bullet style
        else:
            self._bullet = 'none'
        self._emit_paragraph_style_change()

    @property
    def bullet_type(self) -> Optional[str]:
        """
        Bullet type/style.

        Valid values: 'disc', 'circle', 'square', 'numbered', 'none'
        Returns None if not explicitly set.
        """
        return self._bullet

    @bullet_type.setter
    def bullet_type(self, value: str) -> None:
        """
        Set the bullet type/style.

        Args:
            value: Bullet style - 'disc', 'circle', 'square', 'numbered', or 'none'
        """
        valid_types = ('disc', 'circle', 'square', 'numbered', 'none', None)
        if value not in valid_types:
            raise ValueError(f"Invalid bullet_type: {value}. Must be one of {valid_types}")
        self._bullet = value
        self._emit_paragraph_style_change()

    @property
    def line_spacing_pt(self) -> Optional[float]:
        """
        Line spacing in points.

        Note: Line spacing is typically expressed as a multiplier (1.0 = single,
        1.5 = 1.5 lines, 2.0 = double). This property converts to/from points
        for convenience based on a 12pt base.

        Returns None if not explicitly set.
        """
        if self._line_spacing is None:
            return None
        return self._line_spacing * 12.0  # Assume 12pt base font

    @line_spacing_pt.setter
    def line_spacing_pt(self, value: float) -> None:
        """
        Set line spacing in points.

        Args:
            value: Line spacing in points
        """
        self._line_spacing = value / 12.0  # Convert to multiplier
        self._emit_paragraph_style_change()

    @property
    def space_before_pt(self) -> Optional[float]:
        """Space before paragraph in points."""
        if self._space_before is None:
            return None
        return self._space_before / 12700  # EMU to pt

    @space_before_pt.setter
    def space_before_pt(self, value: float) -> None:
        """Set space before paragraph in points."""
        self._space_before = int(value * 12700)  # pt to EMU
        self._emit_paragraph_style_change()

    @property
    def space_after_pt(self) -> Optional[float]:
        """Space after paragraph in points."""
        if self._space_after is None:
            return None
        return self._space_after / 12700  # EMU to pt

    @space_after_pt.setter
    def space_after_pt(self, value: float) -> None:
        """Set space after paragraph in points."""
        self._space_after = int(value * 12700)  # pt to EMU
        self._emit_paragraph_style_change()

    def __len__(self) -> int:
        """Return character count (allows len(paragraph))."""
        return self.length

    def __bool__(self) -> bool:
        """
        Boolean evaluation (allows `if paragraph:`).

        Returns True if paragraph has non-whitespace content.
        """
        return not self.is_empty

    def __iter__(self) -> Iterator[Run]:
        """Iterate over runs in this paragraph."""
        return iter(self._runs)

    def __getitem__(self, index: int) -> Run:
        """Get run by index (allows paragraph[0] syntax)."""
        return self._runs[index]

    def __contains__(self, text: str) -> bool:
        """Check if paragraph contains text (allows 'x' in paragraph)."""
        return text in self.text

    def upper(self) -> None:
        """Convert all text in paragraph to uppercase."""
        for run in self._runs:
            run._text = run._text.upper()
        self._text_frame._set_full_text(self._text_frame._get_full_text())

    def lower(self) -> None:
        """Convert all text in paragraph to lowercase."""
        for run in self._runs:
            run._text = run._text.lower()
        self._text_frame._set_full_text(self._text_frame._get_full_text())

    def capitalize(self) -> None:
        """Capitalize first letter of paragraph."""
        if self._runs and self._runs[0]._text:
            self._runs[0]._text = self._runs[0]._text.capitalize()
            self._text_frame._set_full_text(self._text_frame._get_full_text())

    def title(self) -> None:
        """Convert paragraph text to title case."""
        for run in self._runs:
            run._text = run._text.title()
        self._text_frame._set_full_text(self._text_frame._get_full_text())

    def strip(self) -> None:
        """Remove leading and trailing whitespace from paragraph."""
        if self._runs:
            # Strip leading from first run
            self._runs[0]._text = self._runs[0]._text.lstrip()
            # Strip trailing from last run
            self._runs[-1]._text = self._runs[-1]._text.rstrip()
            self._text_frame._set_full_text(self._text_frame._get_full_text())

    def get_run(self, index: int) -> Run:
        """
        Get run by index with bounds checking.

        Args:
            index: Zero-based run index (supports negative indices)

        Returns:
            The Run at the specified index

        Raises:
            IndexError: If index is out of range
        """
        if index < -len(self._runs) or index >= len(self._runs):
            raise IndexError(
                f"Run index {index} out of range (0-{len(self._runs) - 1})"
            )
        return self._runs[index]

    def merge_runs(self) -> None:
        """
        Merge all runs into a single run, combining their text.

        Note: This discards per-run styling differences. Use the first run's styling.
        """
        if len(self._runs) <= 1:
            return
        combined_text = self.text
        first_run = self._runs[0]
        first_run._text = combined_text
        self._runs = [first_run]
        self._text_frame._set_full_text(self._text_frame._get_full_text())

    def split_at(self, position: int) -> Optional["Paragraph"]:
        """
        Split this paragraph at a character position.

        Note: This is a client-side operation for convenience. The split
        is reflected in the text content but creates runs, not separate paragraphs.

        Args:
            position: Character position to split at

        Returns:
            None (modifies in place by creating additional runs)
        """
        text = self.text
        if position <= 0 or position >= len(text):
            return None

        # Create two runs from the split
        before = text[:position]
        after = text[position:]

        if self._runs:
            self._runs[0]._text = before
            if len(self._runs) > 1:
                self._runs[1]._text = after
                self._runs = self._runs[:2]
            else:
                new_run = Run(self, 1, after)
                self._runs.append(new_run)
        self._text_frame._set_full_text(self._text_frame._get_full_text())
        return None

    def find(self, substring: str) -> int:
        """
        Find the position of a substring in the paragraph text.

        Args:
            substring: Text to find

        Returns:
            Position of substring, or -1 if not found
        """
        return self.text.find(substring)

    def replace(self, old: str, new: str) -> int:
        """
        Replace occurrences of a substring in all runs.

        Args:
            old: Text to find
            new: Replacement text

        Returns:
            Number of replacements made
        """
        total_count = 0
        for run in self._runs:
            count = run._text.count(old)
            if count > 0:
                run._text = run._text.replace(old, new)
                total_count += count
        if total_count > 0:
            self._text_frame._set_full_text(self._text_frame._get_full_text())
        return total_count

    def startswith(self, prefix: str) -> bool:
        """Check if paragraph text starts with prefix."""
        return self.text.startswith(prefix)

    def endswith(self, suffix: str) -> bool:
        """Check if paragraph text ends with suffix."""
        return self.text.endswith(suffix)

    def to_dict(self) -> dict:
        """
        Serialize paragraph to a dictionary.

        Returns:
            Dictionary with paragraph properties and runs
        """
        return {
            'text': self.text,
            'alignment': self._alignment,
            'level': self._level,
            'bullet': self._bullet,
            'run_count': len(self._runs),
            'runs': [run.to_dict() for run in self._runs],
        }

    def clear(self) -> None:
        """Clear all text content from this paragraph."""
        for run in self._runs:
            run._text = ""
        self._text_frame._set_full_text(self._text_frame._get_full_text())

    @property
    def character_count(self) -> int:
        """Total character count (excluding whitespace)."""
        return len(self.text.replace(" ", ""))

    def copy_format_from(self, other: "Paragraph") -> None:
        """
        Copy formatting from another paragraph (not text).

        Args:
            other: Source paragraph to copy formatting from
        """
        self._alignment = other._alignment
        self._level = other._level
        self._bullet = other._bullet
        self._bullet_color_hex = other._bullet_color_hex
        self._line_spacing = other._line_spacing
        self._space_before = other._space_before
        self._space_after = other._space_after
        self._margin_left = other._margin_left
        self._indent = other._indent
        self._emit_paragraph_style_change()

    def _emit_paragraph_style_change(self) -> None:
        """Emit a SetParagraphStyle command."""
        if self._text_frame._buffer:
            cmd = SetParagraphStyle(
                shape_id=self._text_frame._shape_id,
                paragraph_index=self._index,
                alignment=self._alignment,
                level=self._level if self._level > 0 else None,
                bullet=self._bullet,
                bullet_color_hex=self._bullet_color_hex,
                line_spacing=self._line_spacing,
                space_before_emu=self._space_before,
                space_after_emu=self._space_after,
                margin_left_emu=self._margin_left,
                indent_emu=self._indent,
            )
            self._text_frame._buffer.add(cmd)


class TextFrame:
    """
    Container for text content in a shape.

    Mirrors python-pptx's TextFrame class.
    """

    def __init__(
        self,
        shape_id: ShapeId,
        buffer: Optional[CommandBuffer],
        preview_text: Optional[str] = None,
        rich_content: Optional[dict[str, Any]] = None,
    ):
        self._shape_id = shape_id
        self._buffer = buffer
        self._preview_text = preview_text or ""
        self._paragraphs: list[Paragraph] = []

        # Initialize paragraphs from rich content or plain text
        if rich_content and rich_content.get("paragraphs"):
            for i, para_data in enumerate(rich_content["paragraphs"]):
                self._paragraphs.append(
                    Paragraph(self, i, runs=para_data.get("runs"))
                )
        elif preview_text:
            # Split plain text into paragraphs
            for i, line in enumerate(preview_text.split("\n")):
                para = Paragraph(self, i)
                if para._runs:
                    para._runs[0]._text = line
                self._paragraphs.append(para)
        else:
            # Default empty paragraph
            self._paragraphs.append(Paragraph(self, 0))

    @property
    def paragraphs(self) -> list[Paragraph]:
        """List of paragraphs in this text frame."""
        return self._paragraphs

    @property
    def text(self) -> str:
        """
        Combined text of all paragraphs, joined by newlines.

        This is the primary way to get/set text in python-pptx.
        """
        return "\n".join(para.text for para in self._paragraphs)

    @text.setter
    def text(self, value: str) -> None:
        """
        Set text, replacing all paragraphs.

        This emits a SetText command to the server.
        """
        # Update local state
        lines = value.split("\n") if value else [""]
        self._paragraphs = []
        for i, line in enumerate(lines):
            para = Paragraph(self, i)
            if para._runs:
                para._runs[0]._text = line
            self._paragraphs.append(para)

        self._preview_text = value
        self._set_full_text(value)

    def _get_full_text(self) -> str:
        """Get the full text content."""
        return "\n".join(para.text for para in self._paragraphs)

    def _set_full_text(self, value: str) -> None:
        """Emit a SetText command."""
        if self._buffer:
            cmd = SetText(shape_id=self._shape_id, text=value)
            self._buffer.add(cmd)

    def add_paragraph(self) -> Paragraph:
        """Add a new paragraph to this text frame."""
        para = Paragraph(self, len(self._paragraphs))
        self._paragraphs.append(para)
        return para

    def clear(self) -> None:
        """Clear all text, leaving a single empty paragraph."""
        self._paragraphs = [Paragraph(self, 0)]
        self._preview_text = ""
        self._set_full_text("")

    # -------------------------------------------------------------------------
    # Convenience properties
    # -------------------------------------------------------------------------

    @property
    def text_length(self) -> int:
        """Total character count of all text (excluding newlines)."""
        return sum(len(para.text) for para in self._paragraphs)

    @property
    def word_count(self) -> int:
        """Approximate word count of all text."""
        return len(self.text.split())

    @property
    def line_count(self) -> int:
        """Number of paragraphs (lines)."""
        return len(self._paragraphs)

    @property
    def paragraph_count(self) -> int:
        """Number of paragraphs (alias for line_count)."""
        return len(self._paragraphs)

    @property
    def is_empty(self) -> bool:
        """True if text frame has no content or only whitespace."""
        return not self.text or self.text.strip() == ""

    @property
    def first_paragraph(self) -> Optional[Paragraph]:
        """
        First paragraph in the text frame.

        Returns None if there are no paragraphs.
        """
        return self._paragraphs[0] if self._paragraphs else None

    @property
    def last_paragraph(self) -> Optional[Paragraph]:
        """
        Last paragraph in the text frame.

        Returns None if there are no paragraphs.
        """
        return self._paragraphs[-1] if self._paragraphs else None

    def get_paragraph(self, index: int) -> Paragraph:
        """
        Get paragraph by index with bounds checking.

        Args:
            index: Zero-based paragraph index (supports negative indices)

        Returns:
            The Paragraph at the specified index

        Raises:
            IndexError: If index is out of range
        """
        if index < -len(self._paragraphs) or index >= len(self._paragraphs):
            raise IndexError(
                f"Paragraph index {index} out of range "
                f"(0-{len(self._paragraphs) - 1})"
            )
        return self._paragraphs[index]

    def __getitem__(self, index: int) -> Paragraph:
        """
        Get paragraph by index (allows text_frame[0] syntax).

        Args:
            index: Zero-based paragraph index

        Returns:
            The Paragraph at the specified index
        """
        return self._paragraphs[index]

    def __bool__(self) -> bool:
        """Boolean evaluation - True if text frame has content."""
        return not self.is_empty

    @property
    def character_count(self) -> int:
        """
        Total character count including spaces but excluding newlines.

        Alias for text_length.
        """
        return self.text_length

    @property
    def unique_words(self) -> set[str]:
        """
        Get set of unique words in the text frame.

        Words are converted to lowercase for comparison.
        """
        return set(word.lower() for word in self.text.split())

    @property
    def sentences(self) -> list[str]:
        """
        Split text into sentences.

        Simple sentence splitting on . ! ? followed by space or end.
        """
        import re
        text = self.text
        # Split on sentence-ending punctuation followed by space or end
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @property
    def sentence_count(self) -> int:
        """Number of sentences in the text."""
        return len(self.sentences)

    def count_occurrences(self, text: str, case_sensitive: bool = False) -> int:
        """
        Count occurrences of a substring.

        Args:
            text: Substring to count
            case_sensitive: Whether to do case-sensitive matching

        Returns:
            Number of occurrences
        """
        content = self.text
        if not case_sensitive:
            content = content.lower()
            text = text.lower()
        return content.count(text)

    def starts_with(self, prefix: str, case_sensitive: bool = False) -> bool:
        """
        Check if text starts with a prefix.

        Args:
            prefix: Prefix to check
            case_sensitive: Whether to do case-sensitive matching

        Returns:
            True if text starts with the prefix
        """
        content = self.text
        if not case_sensitive:
            content = content.lower()
            prefix = prefix.lower()
        return content.startswith(prefix)

    def ends_with(self, suffix: str, case_sensitive: bool = False) -> bool:
        """
        Check if text ends with a suffix.

        Args:
            suffix: Suffix to check
            case_sensitive: Whether to do case-sensitive matching

        Returns:
            True if text ends with the suffix
        """
        content = self.text
        if not case_sensitive:
            content = content.lower()
            suffix = suffix.lower()
        return content.endswith(suffix)

    def upper(self) -> None:
        """Convert all text to uppercase."""
        self.text = self.text.upper()

    def lower(self) -> None:
        """Convert all text to lowercase."""
        self.text = self.text.lower()

    def capitalize(self) -> None:
        """Capitalize first character of text."""
        self.text = self.text.capitalize()

    def title(self) -> None:
        """Convert text to title case."""
        self.text = self.text.title()

    def strip(self) -> None:
        """Remove leading and trailing whitespace."""
        self.text = self.text.strip()

    def find(self, text: str, case_sensitive: bool = False) -> int:
        """
        Find paragraph index containing text.

        Args:
            text: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            Paragraph index containing text, or -1 if not found
        """
        search_text = text if case_sensitive else text.lower()
        for i, para in enumerate(self._paragraphs):
            para_text = para.text if case_sensitive else para.text.lower()
            if search_text in para_text:
                return i
        return -1

    def replace(self, find: str, replace_with: str, case_sensitive: bool = False) -> int:
        """
        Replace all occurrences of text.

        Args:
            find: Text to find
            replace_with: Replacement text
            case_sensitive: Whether to do case-sensitive search

        Returns:
            Number of replacements made
        """
        import re
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(re.escape(find), flags)

        count = 0
        new_text_parts = []
        for para in self._paragraphs:
            new_para_text, n = pattern.subn(replace_with, para.text)
            new_text_parts.append(new_para_text)
            count += n

        if count > 0:
            self.text = "\n".join(new_text_parts)

        return count

    def prepend(self, text: str) -> None:
        """
        Add text at the beginning of the first paragraph.

        Args:
            text: Text to prepend
        """
        if self._paragraphs:
            self._paragraphs[0].text = text + self._paragraphs[0].text
            self._set_full_text(self.text)

    def append(self, text: str) -> None:
        """
        Add text at the end of the last paragraph.

        Args:
            text: Text to append
        """
        if self._paragraphs:
            self._paragraphs[-1].text = self._paragraphs[-1].text + text
            self._set_full_text(self.text)

    def fit_text(
        self,
        font_family: str = "Calibri",
        max_size: int = 18,
        bold: bool = False,
        italic: bool = False,
        font_file: Optional[str] = None,
    ) -> None:
        """
        Fit text to frame by adjusting font size.

        This method auto-sizes text to fit within the text frame bounds,
        reducing the font size as necessary to ensure all text is visible.

        Args:
            font_family: Font family name (default: "Calibri")
            max_size: Maximum font size in points (default: 18)
            bold: Whether text should be bold (default: False)
            italic: Not yet supported, included for API compatibility
            font_file: Not yet supported, included for API compatibility

        Example:
            # Auto-fit text to frame
            shape.text_frame.fit_text(font_family="Arial", max_size=24)

            # Fit with bold text
            shape.text_frame.fit_text(bold=True)
        """
        if self._buffer:
            cmd = FitText(
                shape_id=self._shape_id,
                max_font_size_pt=float(max_size),
                min_font_size_pt=6.0,
                font_family=font_family,
                bold=bold if bold else None,
            )
            self._buffer.add(cmd)

    @property
    def margin_bottom(self) -> Optional[int]:
        """Bottom margin in EMU."""
        return getattr(self, '_margin_bottom', None)

    @margin_bottom.setter
    def margin_bottom(self, value: int) -> None:
        """Set bottom margin in EMU."""
        self._margin_bottom = value
        self._emit_text_frame_properties_change()

    @property
    def margin_left(self) -> Optional[int]:
        """Left margin in EMU."""
        return getattr(self, '_margin_left', None)

    @margin_left.setter
    def margin_left(self, value: int) -> None:
        """Set left margin in EMU."""
        self._margin_left = value
        self._emit_text_frame_properties_change()

    @property
    def margin_right(self) -> Optional[int]:
        """Right margin in EMU."""
        return getattr(self, '_margin_right', None)

    @margin_right.setter
    def margin_right(self, value: int) -> None:
        """Set right margin in EMU."""
        self._margin_right = value
        self._emit_text_frame_properties_change()

    @property
    def margin_top(self) -> Optional[int]:
        """Top margin in EMU."""
        return getattr(self, '_margin_top', None)

    @margin_top.setter
    def margin_top(self, value: int) -> None:
        """Set top margin in EMU."""
        self._margin_top = value
        self._emit_text_frame_properties_change()

    @property
    def word_wrap(self) -> Optional[bool]:
        """
        Word wrap setting.

        When True, text wraps at the shape boundary. When False, text extends
        beyond the shape boundary (may be clipped).
        """
        return getattr(self, '_word_wrap', None)

    @word_wrap.setter
    def word_wrap(self, value: bool) -> None:
        """
        Set word wrap.

        Args:
            value: True to enable word wrapping, False to disable
        """
        self._word_wrap = value
        self._emit_text_frame_properties_change()

    @property
    def auto_size(self) -> Optional[str]:
        """
        Auto-size behavior for the text frame.

        Values:
            - None or 'none': No auto-sizing
            - 'shape_to_fit_text': Shape resizes to fit text content
            - 'text_to_fit_shape': Text shrinks to fit within shape
        """
        return getattr(self, '_auto_size', None)

    @auto_size.setter
    def auto_size(self, value: Optional[str]) -> None:
        """
        Set auto-size behavior.

        Args:
            value: 'none', 'shape_to_fit_text', 'text_to_fit_shape', or None
        """
        # Handle MSO_AUTO_SIZE enum values (integers)
        if isinstance(value, int):
            int_to_str = {
                0: 'none',
                1: 'shape_to_fit_text',
                2: 'text_to_fit_shape',
            }
            value = int_to_str.get(value, 'none')
        self._auto_size = value
        self._emit_text_frame_properties_change()

    @property
    def vertical_anchor(self) -> Optional[str]:
        """
        Vertical text anchor/alignment within the text frame.

        Values:
            - 'top': Text anchored at the top
            - 'middle': Text centered vertically
            - 'bottom': Text anchored at the bottom
        """
        return getattr(self, '_vertical_anchor', None)

    @vertical_anchor.setter
    def vertical_anchor(self, value: Optional[str]) -> None:
        """
        Set vertical text anchor.

        Args:
            value: 'top', 'middle', 'bottom', or None
        """
        # Handle MSO_ANCHOR enum values (integers)
        if isinstance(value, int):
            int_to_str = {
                1: 'top',
                3: 'middle',
                4: 'bottom',
            }
            value = int_to_str.get(value, 'top')
        self._vertical_anchor = value
        self._emit_text_frame_properties_change()

    def _emit_text_frame_properties_change(self) -> None:
        """Emit a SetTextFrameProperties command."""
        if self._buffer:
            cmd = SetTextFrameProperties(
                shape_id=self._shape_id,
                word_wrap=getattr(self, '_word_wrap', None),
                auto_size=getattr(self, '_auto_size', None),
                vertical_anchor=getattr(self, '_vertical_anchor', None),
                margin_left=getattr(self, '_margin_left', None),
                margin_right=getattr(self, '_margin_right', None),
                margin_top=getattr(self, '_margin_top', None),
                margin_bottom=getattr(self, '_margin_bottom', None),
            )
            self._buffer.add(cmd)

    def __iter__(self) -> Iterator[Paragraph]:
        """Iterate over paragraphs."""
        return iter(self._paragraphs)

    def __len__(self) -> int:
        """Number of paragraphs."""
        return len(self._paragraphs)

    # -------------------------------------------------------------------------
    # Additional convenience methods
    # -------------------------------------------------------------------------

    @property
    def run_count(self) -> int:
        """Total number of runs across all paragraphs."""
        return sum(len(para.runs) for para in self._paragraphs)

    def get_all_runs(self) -> list[Run]:
        """
        Get all runs from all paragraphs as a flat list.

        Returns:
            List of all Run objects in reading order
        """
        runs = []
        for para in self._paragraphs:
            runs.extend(para.runs)
        return runs

    def join_paragraphs(self, separator: str = " ") -> None:
        """
        Join all paragraphs into a single paragraph.

        Args:
            separator: String to use between paragraph texts (default: space)
        """
        if len(self._paragraphs) <= 1:
            return

        combined_text = separator.join(para.text for para in self._paragraphs)
        self.text = combined_text

    def split_into_paragraphs(self, delimiter: str = "\n") -> int:
        """
        Split the text into multiple paragraphs at delimiter.

        Args:
            delimiter: String to split on (default: newline)

        Returns:
            Number of resulting paragraphs
        """
        text = self.text
        parts = text.split(delimiter)
        self.text = "\n".join(parts)
        return len(self._paragraphs)

    @property
    def first_run(self) -> Optional[Run]:
        """
        Get the first run in the text frame.

        Returns None if there are no runs.
        """
        for para in self._paragraphs:
            if para.runs:
                return para.runs[0]
        return None

    @property
    def last_run(self) -> Optional[Run]:
        """
        Get the last run in the text frame.

        Returns None if there are no runs.
        """
        for para in reversed(self._paragraphs):
            if para.runs:
                return para.runs[-1]
        return None

    def get_run(self, paragraph_index: int, run_index: int) -> Run:
        """
        Get a specific run by paragraph and run indices.

        Args:
            paragraph_index: Zero-based paragraph index
            run_index: Zero-based run index within the paragraph

        Returns:
            The specified Run

        Raises:
            IndexError: If indices are out of range
        """
        return self._paragraphs[paragraph_index].runs[run_index]

    def remove_empty_paragraphs(self) -> int:
        """
        Remove paragraphs that are empty or contain only whitespace.

        Returns:
            Number of paragraphs removed
        """
        original_count = len(self._paragraphs)
        non_empty = [p for p in self._paragraphs if not p.is_empty]

        if len(non_empty) == 0:
            # Keep at least one paragraph
            non_empty = [Paragraph(self, 0)]

        if len(non_empty) < original_count:
            # Rebuild from non-empty paragraphs
            self.text = "\n".join(p.text for p in non_empty)

        return original_count - len(self._paragraphs)

    @property
    def has_formatting(self) -> bool:
        """
        True if any run has explicit styling.

        Checks all runs across all paragraphs for any styling.
        """
        for run in self.get_all_runs():
            if run.has_styling:
                return True
        return False

    def clear_formatting(self) -> None:
        """
        Clear all explicit styling from all runs.

        Text content is preserved but all formatting reverts to defaults.
        """
        for run in self.get_all_runs():
            run.font.clear_style()

    @property
    def lines(self) -> list[str]:
        """
        Get text as a list of lines (one per paragraph).

        Returns:
            List of paragraph text strings
        """
        return [para.text for para in self._paragraphs]

    def insert_paragraph(self, index: int, text: str = "") -> Paragraph:
        """
        Insert a new paragraph at the specified index.

        Args:
            index: Index at which to insert (0 = beginning)
            text: Initial text for the paragraph

        Returns:
            The newly created Paragraph
        """
        # Get current text as lines
        lines = self.lines
        # Insert new line
        lines.insert(index, text)
        # Rebuild
        self.text = "\n".join(lines)
        return self._paragraphs[index]

    def remove_paragraph(self, index: int) -> None:
        """
        Remove a paragraph at the specified index.

        Args:
            index: Index of paragraph to remove

        Raises:
            IndexError: If index is out of range
            ValueError: If trying to remove the last paragraph
        """
        if len(self._paragraphs) <= 1:
            raise ValueError("Cannot remove the last paragraph. Use clear() instead.")

        lines = self.lines
        del lines[index]
        self.text = "\n".join(lines)

    def swap_paragraphs(self, index1: int, index2: int) -> None:
        """
        Swap two paragraphs.

        Args:
            index1: Index of first paragraph
            index2: Index of second paragraph
        """
        lines = self.lines
        lines[index1], lines[index2] = lines[index2], lines[index1]
        self.text = "\n".join(lines)

    def reverse_paragraphs(self) -> None:
        """Reverse the order of paragraphs."""
        lines = self.lines
        lines.reverse()
        self.text = "\n".join(lines)

    def sort_paragraphs(self, reverse: bool = False, key=None) -> None:
        """
        Sort paragraphs alphabetically.

        Args:
            reverse: If True, sort in descending order
            key: Optional key function for sorting
        """
        lines = self.lines
        lines.sort(reverse=reverse, key=key)
        self.text = "\n".join(lines)

    # -------------------------------------------------------------------------
    # Export methods
    # -------------------------------------------------------------------------

    def to_html(self, inline_styles: bool = True) -> str:
        """
        Export text frame content as HTML.

        Creates HTML markup preserving basic formatting like bold, italic,
        and underline. Paragraphs become <p> elements.

        Args:
            inline_styles: If True, use inline styles for formatting.
                          If False, use semantic tags only.

        Returns:
            HTML string

        Example:
            html = text_frame.to_html()
            # <p><strong>Title</strong></p><p>Regular text</p>
        """
        html_parts = []
        for para in self._paragraphs:
            para_html = []
            for run in para.runs:
                text = run._text
                if not text:
                    continue

                # Escape HTML entities
                text = text.replace('&', '&amp;')
                text = text.replace('<', '&lt;')
                text = text.replace('>', '&gt;')

                # Apply formatting
                if run.font._bold:
                    text = f"<strong>{text}</strong>"
                if run.font._italic:
                    text = f"<em>{text}</em>"
                if run.font._underline:
                    text = f"<u>{text}</u>"

                # Add color styling if present
                if inline_styles and run.font._color_hex:
                    text = f'<span style="color:#{run.font._color_hex}">{text}</span>'

                para_html.append(text)

            if para_html:
                html_parts.append(f"<p>{''.join(para_html)}</p>")

        return '\n'.join(html_parts)

    def to_markdown(self) -> str:
        """
        Export text frame content as Markdown.

        Creates Markdown text preserving basic formatting like bold and italic.
        Paragraphs are separated by blank lines.

        Returns:
            Markdown string

        Example:
            md = text_frame.to_markdown()
            # **Title**
            #
            # Regular text with *emphasis*
        """
        md_parts = []
        for para in self._paragraphs:
            para_md = []
            for run in para.runs:
                text = run._text
                if not text:
                    continue

                # Apply formatting (note: bold+italic needs special handling)
                if run.font._bold and run.font._italic:
                    text = f"***{text}***"
                elif run.font._bold:
                    text = f"**{text}**"
                elif run.font._italic:
                    text = f"*{text}*"

                para_md.append(text)

            if para_md:
                md_parts.append(''.join(para_md))

        return '\n\n'.join(md_parts)

    def to_plain_text(self) -> str:
        """
        Export text frame content as plain text.

        Strips all formatting and returns just the text content.

        Returns:
            Plain text string
        """
        return self.text

    def get_styled_runs(self) -> list[dict]:
        """
        Get all runs with their styling information.

        Returns a list of dictionaries, each containing run text and
        all formatting properties.

        Returns:
            List of dictionaries with 'text', 'paragraph_index', 'run_index',
            and formatting properties.

        Example:
            styled = text_frame.get_styled_runs()
            for run_info in styled:
                if run_info['bold']:
                    print(f"Bold text: {run_info['text']}")
        """
        styled_runs = []
        for p_idx, para in enumerate(self._paragraphs):
            for r_idx, run in enumerate(para.runs):
                styled_runs.append({
                    'text': run._text,
                    'paragraph_index': p_idx,
                    'run_index': r_idx,
                    'bold': run.font._bold,
                    'italic': run.font._italic,
                    'underline': run.font._underline,
                    'size_emu': run.font._size,
                    'size_pt': run.font.size_pt,
                    'font_name': run.font._name,
                    'color_hex': run.font._color_hex,
                })
        return styled_runs

    def apply_style_to_all(self, style: dict) -> None:
        """
        Apply a style dictionary to all runs in the text frame.

        Useful for batch formatting operations.

        Args:
            style: Dictionary with style properties. Supported keys:
                   'bold', 'italic', 'underline', 'size_pt', 'font_name',
                   'color_hex'

        Example:
            text_frame.apply_style_to_all({
                'bold': True,
                'font_name': 'Arial',
                'size_pt': 14
            })
        """
        for para in self._paragraphs:
            for run in para.runs:
                run.font.apply_from_dict(style)

    def to_dict(self) -> dict:
        """
        Serialize text frame to a dictionary.

        Returns:
            Dictionary with text frame properties and paragraphs.
        """
        return {
            'text': self.text,
            'paragraph_count': len(self._paragraphs),
            'word_count': self.word_count,
            'character_count': self.character_count,
            'paragraphs': [para.to_dict() for para in self._paragraphs],
        }

    def get_formatting_summary(self) -> dict:
        """
        Get a summary of formatting used in the text frame.

        Returns:
            Dictionary with counts of formatting types:
            - bold_runs: Number of bold runs
            - italic_runs: Number of italic runs
            - underline_runs: Number of underlined runs
            - fonts_used: Set of font names
            - colors_used: Set of color hex values
            - sizes_used: Set of font sizes (in points)
        """
        summary = {
            'bold_runs': 0,
            'italic_runs': 0,
            'underline_runs': 0,
            'fonts_used': set(),
            'colors_used': set(),
            'sizes_used': set(),
        }

        for para in self._paragraphs:
            for run in para.runs:
                if run.font._bold:
                    summary['bold_runs'] += 1
                if run.font._italic:
                    summary['italic_runs'] += 1
                if run.font._underline:
                    summary['underline_runs'] += 1
                if run.font._name:
                    summary['fonts_used'].add(run.font._name)
                if run.font._color_hex:
                    summary['colors_used'].add(run.font._color_hex)
                if run.font.size_pt:
                    summary['sizes_used'].add(run.font.size_pt)

        return summary

    def highlight_text(
        self,
        text: str,
        style: dict,
        case_sensitive: bool = False,
    ) -> int:
        """
        Apply styling to all occurrences of text.

        Note: This modifies run styling but may not split runs perfectly.
        For best results, use with text that spans entire runs.

        Args:
            text: Text to highlight
            style: Style dictionary to apply (see apply_style_to_all)
            case_sensitive: Whether to match case

        Returns:
            Number of occurrences found
        """
        count = 0
        search = text if case_sensitive else text.lower()

        for para in self._paragraphs:
            for run in para.runs:
                run_text = run._text if case_sensitive else run._text.lower()
                if search in run_text:
                    run.font.apply_from_dict(style)
                    count += 1

        return count
