"""
Slide-related proxy classes.

Provides python-pptx-compatible Slide and Slides collection abstractions.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union

if TYPE_CHECKING:
    from .dml.color import RGBColor

from .commands import AddSlide, DeleteSlide, SetSlideBackground, SetSlideNotes, CloneSlide, SetSlideName, SetSlideLayout
from .decorators import athena_only
from .errors import UnsupportedFeatureError
from .shapes import Shapes, SlidePlaceholders
from .typing import DeckSnapshot, ElementSnapshot, SlideId, SlideSnapshot

if TYPE_CHECKING:
    from .batching import CommandBuffer
    from .presentation import Presentation


class SlideBackground:
    """
    Slide background formatting.

    Provides access to slide background properties like color.
    """

    def __init__(self, slide: "Slide"):
        self._slide = slide
        self._color_hex: Optional[str] = slide._background_color_hex
        self._follow_master: bool = True

    @property
    def fill(self) -> "BackgroundFill":
        """Access background fill properties."""
        return BackgroundFill(self)

    @property
    def color(self) -> Optional[str]:
        """Background color as hex string."""
        return self._color_hex

    @color.setter
    def color(self, value: Union[str, "RGBColor"]) -> None:
        """Set background color."""
        # Handle RGBColor objects
        from .dml.color import RGBColor
        if isinstance(value, RGBColor):
            value = str(value)
        elif hasattr(value, 'startswith') and value.startswith('#'):
            value = value[1:]
        self._color_hex = value.upper()
        self._follow_master = False
        self._emit_background_change()

    def follow_master_background(self) -> None:
        """Reset to follow master slide background."""
        self._color_hex = None
        self._follow_master = True
        self._emit_background_change()

    def _emit_background_change(self) -> None:
        """Emit a SetSlideBackground command."""
        if self._slide._buffer:
            cmd = SetSlideBackground(
                slide_index=self._slide._slide_index,
                color_hex=self._color_hex,
                follow_master=self._follow_master,
            )
            self._slide._buffer.add(cmd)


class BackgroundFill:
    """
    Background fill formatting (for python-pptx compatibility).
    """

    def __init__(self, background: SlideBackground):
        self._background = background

    def solid(self) -> None:
        """Enable solid fill mode (already enabled when color is set)."""
        pass

    @property
    def fore_color(self) -> "BackgroundColor":
        """Foreground color for the fill."""
        return BackgroundColor(self._background)


class BackgroundColor:
    """
    Background color wrapper (for python-pptx compatibility).
    """

    def __init__(self, background: SlideBackground):
        self._background = background

    @property
    def rgb(self) -> Optional[str]:
        """RGB color value."""
        return self._background._color_hex

    @rgb.setter
    def rgb(self, value: Union[str, "RGBColor"]) -> None:
        """Set RGB color."""
        self._background.color = value

    @property
    def srgb_color(self) -> Optional[str]:
        """
        sRGB color value (alias for rgb, for python-pptx compatibility).

        Returns the color as a hex string.
        """
        return self._background._color_hex

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def hex(self) -> Optional[str]:
        """Color as hex string (without #)."""
        return self._background._color_hex

    @hex.setter
    def hex(self, value: str) -> None:
        """Set color from hex string."""
        self._background.color = value

    @property
    def as_rgb_color(self) -> Optional["RGBColor"]:
        """
        Get color as RGBColor object.

        Returns None if no color is set.
        """
        if self._background._color_hex:
            from .dml.color import RGBColor
            return RGBColor.from_string(self._background._color_hex)
        return None

    def set_rgb(self, r: int, g: int, b: int) -> None:
        """
        Set color from RGB components.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        from .dml.color import RGBColor
        self._background.color = RGBColor(r, g, b)

    @property
    def is_set(self) -> bool:
        """True if a background color is explicitly set."""
        return self._background._color_hex is not None

    def clear(self) -> None:
        """Clear the background color (revert to default/master)."""
        self._background.follow_master_background()


class Slide:
    """
    A single slide in a presentation.

    Mirrors python-pptx's Slide class.
    """

    def __init__(
        self,
        presentation: Presentation,
        slide_id: SlideId,
        slide_index: int,
        buffer: Optional[CommandBuffer],
        element_ids: Optional[list[str]] = None,
        elements: Optional[dict[str, ElementSnapshot]] = None,
        background_color_hex: Optional[str] = None,
        notes: Optional[str] = None,
        layout_index: Optional[int] = None,
        layout_name: Optional[str] = None,
    ):
        self._presentation = presentation
        self._slide_id = slide_id
        self._slide_index = slide_index
        self._buffer = buffer
        self._background_color_hex = background_color_hex
        self._notes = notes

        # Layout tracking
        self._layout_index = layout_index
        self._layout_name = layout_name
        self._layout: Optional[SlideLayout] = None

        # Initialize shapes collection
        self._shapes = Shapes(
            slide=self,
            buffer=buffer,
            elements=elements,
            element_ids=element_ids,
        )

    @property
    def slide_id(self) -> SlideId:
        """Unique identifier for this slide."""
        return self._slide_id

    @property
    def slide_index(self) -> int:
        """Zero-based index of this slide in the presentation."""
        return self._slide_index

    @property
    def shapes(self) -> Shapes:
        """Collection of shapes on this slide."""
        return self._shapes

    @property
    def placeholders(self) -> SlidePlaceholders:
        """
        Collection of placeholder shapes on this slide.

        Returns a SlidePlaceholders object that supports dictionary-style access
        by placeholder idx.

        Example:
            title = slide.placeholders[0]  # Title placeholder (idx 0)
            body = slide.placeholders[1]   # Body placeholder (idx 1)
            slide.placeholders[0].text = "New Title"
        """
        return self._shapes.placeholders

    @property
    def background(self) -> SlideBackground:
        """
        Slide background formatting.

        Returns a SlideBackground object that can be used to set background
        color or reset to follow master.

        Example:
            slide.background.color = 'FFFFFF'  # White background
            slide.background.fill.fore_color.rgb = '0000FF'  # Blue background
            slide.background.follow_master_background()  # Follow master
        """
        if not hasattr(self, '_background') or self._background is None:
            self._background = SlideBackground(self)
        return self._background

    @property
    def slide_layout(self) -> "SlideLayout":
        """
        The slide layout applied to this slide.

        Returns the SlideLayout object for this slide's current layout.

        Example:
            # Get layout info
            layout = slide.slide_layout
            print(layout.name)  # "Blank"

            # Change layout
            slide.slide_layout = prs.slide_layouts[0]  # Title Slide
        """
        if not hasattr(self, '_layout') or self._layout is None:
            # Create a proxy layout object
            self._layout = SlideLayout(
                name=self._layout_name or "Unknown",
                index=self._layout_index or 0,
                slide=self,
            )
        return self._layout

    @slide_layout.setter
    def slide_layout(self, value: Union["SlideLayout", int, str]) -> None:
        """
        Set the slide layout.

        Args:
            value: SlideLayout object, layout index (int), or layout name (str)

        Example:
            slide.slide_layout = prs.slide_layouts[0]  # By layout object
            slide.slide_layout = 6  # By index (0-based)
            slide.slide_layout = "Blank"  # By name
        """
        if isinstance(value, SlideLayout):
            layout_index = value._index
            layout_name = value.name
        elif isinstance(value, int):
            layout_index = value
            layout_name = None
        elif isinstance(value, str):
            layout_index = None
            layout_name = value
        else:
            raise TypeError(f"Expected SlideLayout, int, or str, got {type(value)}")

        self._layout_index = layout_index
        self._layout_name = layout_name
        self._layout = None  # Reset cached layout

        if self._buffer:
            cmd = SetSlideLayout(
                slide_index=self._slide_index,
                layout_index=layout_index,
                layout_name=layout_name,
            )
            self._buffer.add(cmd)

    @property
    def notes_slide(self) -> Any:
        """Notes slide (not yet supported)."""
        raise UnsupportedFeatureError(
            "slide.notes_slide", "Notes slides are not yet supported"
        )

    @property
    def has_notes_slide(self) -> bool:
        """Whether this slide has notes."""
        return bool(self._notes)

    @property
    def notes(self) -> Optional[str]:
        """
        Slide notes/speaker notes content.

        Returns the notes text or None if no notes are set.
        """
        return self._notes

    @notes.setter
    def notes(self, value: str) -> None:
        """
        Set slide notes.

        Args:
            value: Notes text content
        """
        self._notes = value
        if self._buffer:
            cmd = SetSlideNotes(
                slide_index=self._slide_index,
                notes=value,
            )
            self._buffer.add(cmd)

    @athena_only(
        description="Render slide to PNG image",
        since="0.1.5",
    )
    def render(
        self,
        format: str = "png",
        scale: int = 2,
        as_pil: bool = False,
    ) -> Union[bytes, Any]:
        """
        Render the slide to an image.

        Returns PNG image data that can be saved to a file or converted
        to a PIL Image for further processing.

        Args:
            format: Image format (currently only "png" is supported)
            scale: Render scale factor (default 2x for high resolution)
            as_pil: If True, return a PIL.Image.Image object instead of bytes.
                    Requires the Pillow library to be installed.

        Returns:
            bytes: PNG image data (if as_pil=False)
            PIL.Image.Image: PIL Image object (if as_pil=True)

        Raises:
            ValueError: If an unsupported format is specified
            ImportError: If as_pil=True but Pillow is not installed

        Example:
            # Get raw PNG bytes
            png_bytes = slide.render()
            with open("slide.png", "wb") as f:
                f.write(png_bytes)

            # Get PIL Image (requires Pillow)
            img = slide.render(as_pil=True)
            img.save("slide.png")
            img.show()  # Display the image

            # High resolution render
            img = slide.render(scale=4, as_pil=True)

        Note:
            This method is Athena-specific and not available in python-pptx.
        """
        if format.lower() != "png":
            raise ValueError(f"Unsupported format: {format}. Only 'png' is currently supported.")

        # Render via the presentation's render method
        png_bytes = self._presentation.render_slide(
            slide_index=self._slide_index,
            scale=scale,
        )

        if as_pil:
            try:
                from PIL import Image
                import io
                return Image.open(io.BytesIO(png_bytes))
            except ImportError:
                raise ImportError(
                    "Pillow is required for as_pil=True. "
                    "Install it with: pip install Pillow"
                )

        return png_bytes

    @athena_only(
        description="Clone slide with all its content",
        since="0.1.6",
    )
    def clone(self, target_index: Optional[int] = None) -> "Slide":
        """
        Clone this slide with all its content.

        Creates a duplicate of this slide including all shapes, text,
        formatting, and background settings. The cloned slide is inserted
        at the specified target index.

        Args:
            target_index: Zero-based index where the clone should be inserted.
                         If None, the clone is inserted immediately after this slide.

        Returns:
            Slide: The newly created slide object.

        Example:
            # Clone slide and insert after it
            new_slide = slide.clone()

            # Clone slide and insert at beginning
            new_slide = slide.clone(target_index=0)

            # Clone slide and insert at end
            new_slide = slide.clone(target_index=len(prs.slides))

        Note:
            This method is Athena-specific and not available in python-pptx.
        """
        # Flush any pending commands first
        if self._buffer:
            self._buffer.flush()

        # Send clone command
        cmd = CloneSlide(
            source_index=self._slide_index,
            target_index=target_index,
        )

        if self._buffer:
            self._buffer.add(cmd)
            self._buffer.flush()

        # Refresh the presentation to get the updated slides list
        self._presentation.refresh()

        # Get the updated slides collection and return the new slide
        # The new slide will be at target_index or at source_index + 1
        actual_target = target_index if target_index is not None else self._slide_index + 1
        return self._presentation.slides[actual_target]

    @property
    def name(self) -> Optional[str]:
        """
        Slide name.

        Slide names can be used to identify slides programmatically.
        They are stored in the PPTX file and can be referenced in
        hyperlinks and navigation.

        Example:
            slide.name = "Introduction"
            print(slide.name)  # "Introduction"
        """
        return self._name if hasattr(self, '_name') else None

    @name.setter
    def name(self, value: str) -> None:
        """Set slide name."""
        self._name = value
        if self._buffer:
            cmd = SetSlideName(slide_index=self._slide_index, name=value)
            self._buffer.add(cmd)

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def shape_count(self) -> int:
        """Number of shapes on this slide."""
        return len(self._shapes)

    @property
    def has_title(self) -> bool:
        """True if this slide has a title placeholder with text."""
        title = self._shapes.title
        return title is not None and title.has_text_frame and bool(title.text.strip())

    @property
    def title_text(self) -> Optional[str]:
        """
        Get the title placeholder text.

        Returns None if there is no title placeholder.
        """
        title = self._shapes.title
        if title and title.has_text_frame:
            return title.text
        return None

    @title_text.setter
    def title_text(self, value: str) -> None:
        """
        Set the title placeholder text.

        Raises UnsupportedFeatureError if there is no title placeholder.
        """
        title = self._shapes.title
        if not title:
            raise UnsupportedFeatureError(
                "slide.title_text",
                "This slide does not have a title placeholder"
            )
        title.text = value

    @property
    def is_blank(self) -> bool:
        """True if this slide has no shapes (completely empty)."""
        return len(self._shapes) == 0

    def get_shape_by_text(self, text: str, case_sensitive: bool = False) -> Optional[Any]:
        """
        Find a shape by its text content.

        Args:
            text: Exact text to match
            case_sensitive: Whether to do case-sensitive match

        Returns:
            The first shape with matching text, or None
        """
        return self._shapes.find_by_text(text, case_sensitive)

    def get_shapes_containing(self, text: str, case_sensitive: bool = False) -> list:
        """
        Find all shapes containing specific text.

        Args:
            text: Text substring to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            List of shapes containing the text
        """
        return self._shapes.filter_by_text(text, case_sensitive)

    @property
    def all_text(self) -> str:
        """
        Get all text content from all shapes on this slide.

        Returns text from all text-containing shapes, joined by newlines.
        Useful for search indexing or text analysis.
        """
        texts = []
        for shape in self._shapes:
            if shape.has_text_frame:
                text = shape.text.strip()
                if text:
                    texts.append(text)
        return "\n".join(texts)

    @property
    def word_count(self) -> int:
        """
        Total word count across all shapes on this slide.
        """
        return len(self.all_text.split())

    @property
    def shape_types(self) -> set:
        """
        Get the set of shape types present on this slide.

        Returns:
            Set of shape type strings (e.g., {'text', 'image', 'shape'})
        """
        return {shape.shape_type for shape in self._shapes}

    @property
    def has_images(self) -> bool:
        """True if this slide contains any image shapes."""
        return any(s.shape_type == 'image' for s in self._shapes)

    @property
    def has_tables(self) -> bool:
        """True if this slide contains any table shapes."""
        return any(s.shape_type == 'table' for s in self._shapes)

    @property
    def image_count(self) -> int:
        """Number of images on this slide."""
        return sum(1 for s in self._shapes if s.shape_type == 'image')

    @property
    def table_count(self) -> int:
        """Number of tables on this slide."""
        return sum(1 for s in self._shapes if s.shape_type == 'table')

    @property
    def textbox_count(self) -> int:
        """Number of text shapes on this slide."""
        return sum(1 for s in self._shapes if s.shape_type == 'text')

    @property
    def autoshape_count(self) -> int:
        """Number of autoshapes on this slide."""
        return sum(1 for s in self._shapes if s.shape_type == 'shape')

    @property
    def placeholder_count(self) -> int:
        """Number of placeholder shapes on this slide."""
        return len(self.placeholders)

    def get_shapes_by_type(self, shape_type: str) -> list:
        """
        Get all shapes of a specific type.

        Args:
            shape_type: Shape type ('text', 'image', 'shape', 'table')

        Returns:
            List of shapes of the specified type
        """
        return self._shapes.filter_by_type(shape_type)

    def get_largest_shape(self) -> Optional[Any]:
        """Get the shape with the largest area on this slide."""
        return self._shapes.get_largest()

    def get_smallest_shape(self) -> Optional[Any]:
        """Get the shape with the smallest area on this slide."""
        return self._shapes.get_smallest()

    @property
    def bounding_box(self) -> Optional[tuple]:
        """
        Get the bounding box containing all shapes on this slide.

        Returns:
            Tuple of (left, top, right, bottom) in EMU, or None if no shapes
        """
        return self._shapes.get_bounding_box()

    def contains_text(self, text: str, case_sensitive: bool = False) -> bool:
        """
        Check if slide contains specific text.

        Args:
            text: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            True if any shape contains the text
        """
        search_text = text if case_sensitive else text.lower()
        slide_text = self.all_text if case_sensitive else self.all_text.lower()
        return search_text in slide_text

    def replace_text(
        self, find: str, replace_with: str, case_sensitive: bool = False
    ) -> int:
        """
        Replace text in all shapes on this slide.

        Args:
            find: Text to find
            replace_with: Replacement text
            case_sensitive: Whether to do case-sensitive search

        Returns:
            Number of replacements made
        """
        total_count = 0
        for shape in self._shapes:
            if shape.has_text_frame:
                count = shape.text_frame.replace(find, replace_with, case_sensitive)
                total_count += count
        return total_count

    @property
    def body_text(self) -> Optional[str]:
        """
        Get the body placeholder text.

        Returns None if there is no body placeholder.
        """
        body = self.placeholders.body
        if body and body.has_text_frame:
            return body.text
        return None

    @body_text.setter
    def body_text(self, value: str) -> None:
        """
        Set the body placeholder text.

        Raises UnsupportedFeatureError if there is no body placeholder.
        """
        body = self.placeholders.body
        if not body:
            from .errors import UnsupportedFeatureError
            raise UnsupportedFeatureError(
                "slide.body_text",
                "This slide does not have a body placeholder"
            )
        body.text = value

    def clear_all_text(self) -> None:
        """Clear text from all shapes on this slide."""
        for shape in self._shapes:
            if shape.has_text_frame:
                shape.text_frame.clear()

    @property
    def has_autoshapes(self) -> bool:
        """True if this slide contains any autoshapes."""
        return self.autoshape_count > 0

    @property
    def has_placeholders(self) -> bool:
        """True if this slide contains any placeholder shapes."""
        return self.placeholder_count > 0

    @property
    def has_textboxes(self) -> bool:
        """True if this slide contains any text shapes."""
        return self.textbox_count > 0

    def get_text_stats(self) -> dict:
        """
        Get text statistics for this slide.

        Returns:
            Dictionary containing:
            - word_count: Total word count
            - character_count: Total character count (excluding whitespace)
            - paragraph_count: Total number of paragraphs
            - shape_count: Number of text-containing shapes
            - average_words_per_shape: Average words per text shape
            - unique_words: Number of unique words (lowercase)
        """
        word_count = 0
        char_count = 0
        paragraph_count = 0
        text_shape_count = 0
        all_words: set = set()

        for shape in self._shapes:
            if shape.has_text_frame:
                text = shape.text
                if text:
                    text_shape_count += 1
                    words = text.split()
                    word_count += len(words)
                    char_count += len(text.replace(" ", "").replace("\n", ""))
                    all_words.update(w.lower() for w in words)
                    paragraph_count += shape.text_frame.paragraph_count

        return {
            'word_count': word_count,
            'character_count': char_count,
            'paragraph_count': paragraph_count,
            'shape_count': text_shape_count,
            'average_words_per_shape': word_count / text_shape_count if text_shape_count > 0 else 0,
            'unique_words': len(all_words),
        }

    @property
    def character_count(self) -> int:
        """Total character count across all text (excluding whitespace)."""
        count = 0
        for shape in self._shapes:
            if shape.has_text_frame:
                text = shape.text
                count += len(text.replace(" ", "").replace("\n", ""))
        return count

    def get_shapes_by_position(self, position: str) -> list:
        """
        Get shapes by their relative position on the slide.

        Args:
            position: Position filter - 'top', 'bottom', 'left', 'right', 'center'

        Returns:
            List of shapes in that region
        """
        if not self._shapes:
            return []

        shapes = list(self._shapes)
        result = []

        # Use presentation slide dimensions if available
        width = getattr(self._presentation, '_slide_width', 9144000)  # Default 10 inches
        height = getattr(self._presentation, '_slide_height', 6858000)  # Default 7.5 inches

        half_w = width / 2
        half_h = height / 2

        for shape in shapes:
            cx = shape.center_x if hasattr(shape, 'center_x') else int(shape.left) + int(shape.width) / 2
            cy = shape.center_y if hasattr(shape, 'center_y') else int(shape.top) + int(shape.height) / 2

            if position == 'top' and cy < half_h:
                result.append(shape)
            elif position == 'bottom' and cy >= half_h:
                result.append(shape)
            elif position == 'left' and cx < half_w:
                result.append(shape)
            elif position == 'right' and cx >= half_w:
                result.append(shape)
            elif position == 'center':
                # Within center 50% of slide
                if half_w * 0.5 <= cx <= half_w * 1.5 and half_h * 0.5 <= cy <= half_h * 1.5:
                    result.append(shape)

        return result

    def clear_notes(self) -> None:
        """Clear speaker notes from this slide."""
        self.notes = ""

    def to_dict(self) -> dict:
        """
        Serialize slide to a dictionary.

        Returns a comprehensive dictionary representation suitable for
        JSON serialization or analysis.

        Returns:
            Dictionary with slide properties and content
        """
        return {
            'slide_id': self._slide_id,
            'slide_index': self._slide_index,
            'title': self.title_text,
            'shape_count': self.shape_count,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'has_notes': self.has_notes_slide,
            'notes': self._notes,
            'has_images': self.has_images,
            'has_tables': self.has_tables,
            'background_color': self._background_color_hex,
            'shapes': [shape.to_dict() for shape in self._shapes],
        }

    def get_all_runs(self) -> list:
        """
        Get all text runs from all shapes on this slide.

        Returns:
            List of Run objects
        """
        runs = []
        for shape in self._shapes:
            if shape.has_text_frame:
                runs.extend(shape.text_frame.get_all_runs())
        return runs

    def get_all_paragraphs(self) -> list:
        """
        Get all paragraphs from all shapes on this slide.

        Returns:
            List of Paragraph objects
        """
        paragraphs = []
        for shape in self._shapes:
            if shape.has_text_frame:
                paragraphs.extend(shape.text_frame.paragraphs)
        return paragraphs

    def _update_from_snapshot(
        self,
        slide_snapshot: SlideSnapshot,
        elements: dict[str, ElementSnapshot],
    ) -> None:
        """Update slide state from a snapshot."""
        self._slide_index = slide_snapshot.index
        self._background_color_hex = slide_snapshot.background_color_hex
        self._notes = slide_snapshot.notes

        # Rebuild shapes collection
        self._shapes = Shapes(
            slide=self,
            buffer=self._buffer,
            elements=elements,
            element_ids=slide_snapshot.element_ids,
        )

    def __repr__(self) -> str:
        return f"<Slide slide_id='{self._slide_id}' index={self._slide_index}>"


class Slides:
    """
    Collection of slides in a presentation.

    Mirrors python-pptx's Slides class.
    """

    def __init__(
        self,
        presentation: Presentation,
        buffer: Optional[CommandBuffer],
        snapshot: Optional[DeckSnapshot] = None,
    ):
        self._presentation = presentation
        self._buffer = buffer
        self._slides: list[Slide] = []
        self._slides_by_id: dict[SlideId, Slide] = {}

        # Build slides from snapshot
        if snapshot:
            for slide_snapshot in snapshot.slides:
                # Parse layout index from layout path (e.g., ppt/slideLayouts/slideLayout1.xml -> 0)
                layout_index = None
                if slide_snapshot.layout_path:
                    import re
                    match = re.search(r'slideLayout(\d+)\.xml$', slide_snapshot.layout_path)
                    if match:
                        layout_index = int(match.group(1)) - 1  # Convert 1-based to 0-based

                slide = Slide(
                    presentation=presentation,
                    slide_id=slide_snapshot.id,
                    slide_index=slide_snapshot.index,
                    buffer=buffer,
                    element_ids=slide_snapshot.element_ids,
                    elements=snapshot.elements,
                    background_color_hex=slide_snapshot.background_color_hex,
                    notes=slide_snapshot.notes,
                    layout_index=layout_index,
                )
                self._slides.append(slide)
                self._slides_by_id[slide_snapshot.id] = slide

    def __len__(self) -> int:
        """Number of slides."""
        return len(self._slides)

    def __iter__(self) -> Iterator[Slide]:
        """Iterate over slides."""
        return iter(self._slides)

    def __getitem__(self, key: Union[int, slice]) -> Union[Slide, list[Slide]]:
        """
        Get slide by index or slice.

        Args:
            key: Integer index or slice object

        Returns:
            Single Slide if index, list of Slides if slice

        Examples:
            slide = prs.slides[0]  # First slide
            last_slide = prs.slides[-1]  # Last slide
            first_three = prs.slides[:3]  # First three slides
            every_other = prs.slides[::2]  # Every other slide
        """
        return self._slides[key]

    def get_by_id(self, slide_id: SlideId) -> Optional[Slide]:
        """Get slide by ID."""
        return self._slides_by_id.get(slide_id)

    # -------------------------------------------------------------------------
    # Convenience properties and methods
    # -------------------------------------------------------------------------

    @property
    def first(self) -> Optional[Slide]:
        """
        Get the first slide in the presentation.

        Returns None if there are no slides.
        """
        return self._slides[0] if self._slides else None

    @property
    def last(self) -> Optional[Slide]:
        """
        Get the last slide in the presentation.

        Returns None if there are no slides.
        """
        return self._slides[-1] if self._slides else None

    @property
    def is_empty(self) -> bool:
        """True if the presentation has no slides."""
        return len(self._slides) == 0

    @property
    def count(self) -> int:
        """
        Number of slides (alias for len()).

        Provided for API convenience.
        """
        return len(self._slides)

    @property
    def titles(self) -> list[Optional[str]]:
        """
        Get list of all slide titles.

        Returns a list where each element is the title text of the
        corresponding slide, or None if the slide has no title.

        Example:
            titles = prs.slides.titles
            # ['Introduction', 'Overview', None, 'Conclusion']
        """
        return [slide.title_text for slide in self._slides]

    def find_by_title(
        self, title: str, case_sensitive: bool = False
    ) -> Optional[Slide]:
        """
        Find a slide by its title text.

        Args:
            title: Title text to search for
            case_sensitive: Whether to do case-sensitive match

        Returns:
            The first slide with matching title, or None
        """
        for slide in self._slides:
            slide_title = slide.title_text
            if slide_title is None:
                continue
            if case_sensitive:
                if slide_title == title:
                    return slide
            else:
                if slide_title.lower() == title.lower():
                    return slide
        return None

    def filter_by_title(
        self, text: str, case_sensitive: bool = False
    ) -> list[Slide]:
        """
        Find all slides with titles containing specific text.

        Args:
            text: Text to search for in titles
            case_sensitive: Whether to do case-sensitive search

        Returns:
            List of slides with titles containing the text
        """
        results = []
        for slide in self._slides:
            slide_title = slide.title_text
            if slide_title is None:
                continue
            if case_sensitive:
                if text in slide_title:
                    results.append(slide)
            else:
                if text.lower() in slide_title.lower():
                    results.append(slide)
        return results

    def get_blank_slides(self) -> list[Slide]:
        """
        Get all blank slides (slides with no shapes).

        Returns:
            List of slides that have no shapes
        """
        return [slide for slide in self._slides if slide.is_blank]

    def get_slides_with_shapes(self) -> list[Slide]:
        """
        Get all slides that have at least one shape.

        Returns:
            List of slides with shapes
        """
        return [slide for slide in self._slides if not slide.is_blank]

    def get_slides_with_images(self) -> list[Slide]:
        """
        Get all slides that contain at least one image.

        Returns:
            List of slides containing images
        """
        return [slide for slide in self._slides if slide.has_images]

    def get_slides_with_tables(self) -> list[Slide]:
        """
        Get all slides that contain at least one table.

        Returns:
            List of slides containing tables
        """
        return [slide for slide in self._slides if slide.has_tables]

    def get_slides_with_text(self, text: str, case_sensitive: bool = False) -> list[Slide]:
        """
        Get all slides containing specific text.

        Args:
            text: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            List of slides containing the text
        """
        results = []
        search_text = text if case_sensitive else text.lower()
        for slide in self._slides:
            slide_text = slide.all_text if case_sensitive else slide.all_text.lower()
            if search_text in slide_text:
                results.append(slide)
        return results

    @property
    def total_shape_count(self) -> int:
        """Total number of shapes across all slides."""
        return sum(slide.shape_count for slide in self._slides)

    @property
    def total_word_count(self) -> int:
        """Total word count across all slides."""
        return sum(slide.word_count for slide in self._slides)

    def enumerate(self) -> Iterator[tuple[int, Slide]]:
        """
        Enumerate slides with their indices.

        Yields:
            Tuples of (index, slide)
        """
        for i, slide in enumerate(self._slides):
            yield i, slide

    def reversed(self) -> Iterator[Slide]:
        """
        Iterate over slides in reverse order.

        Yields:
            Slides from last to first
        """
        return reversed(self._slides)

    def get_slides_with_notes(self) -> list[Slide]:
        """
        Get all slides that have speaker notes.

        Returns:
            List of slides with notes
        """
        return [slide for slide in self._slides if slide.has_notes_slide]

    def get_slides_without_notes(self) -> list[Slide]:
        """
        Get all slides that don't have speaker notes.

        Returns:
            List of slides without notes
        """
        return [slide for slide in self._slides if not slide.has_notes_slide]

    @property
    def all_notes(self) -> list[Optional[str]]:
        """
        Get list of all slide notes.

        Returns a list where each element is the notes text of the
        corresponding slide, or None if the slide has no notes.
        """
        return [slide.notes for slide in self._slides]

    @property
    def notes_word_count(self) -> int:
        """Total word count across all slide notes."""
        count = 0
        for slide in self._slides:
            if slide.notes:
                count += len(slide.notes.split())
        return count

    def filter_by_shape_count(
        self, min_shapes: int = 0, max_shapes: Optional[int] = None
    ) -> list[Slide]:
        """
        Filter slides by number of shapes.

        Args:
            min_shapes: Minimum number of shapes (inclusive)
            max_shapes: Maximum number of shapes (inclusive), or None for no limit

        Returns:
            List of slides matching the criteria
        """
        results = []
        for slide in self._slides:
            shape_count = slide.shape_count
            if shape_count >= min_shapes:
                if max_shapes is None or shape_count <= max_shapes:
                    results.append(slide)
        return results

    def filter_by_word_count(
        self, min_words: int = 0, max_words: Optional[int] = None
    ) -> list[Slide]:
        """
        Filter slides by word count.

        Args:
            min_words: Minimum word count (inclusive)
            max_words: Maximum word count (inclusive), or None for no limit

        Returns:
            List of slides matching the criteria
        """
        results = []
        for slide in self._slides:
            word_count = slide.word_count
            if word_count >= min_words:
                if max_words is None or word_count <= max_words:
                    results.append(slide)
        return results

    def get_slides_with_placeholders(self) -> list[Slide]:
        """
        Get all slides that have placeholder shapes.

        Returns:
            List of slides with placeholders
        """
        return [slide for slide in self._slides if slide.placeholder_count > 0]

    def get_slides_with_autoshapes(self) -> list[Slide]:
        """
        Get all slides that have autoshapes.

        Returns:
            List of slides with autoshapes
        """
        return [slide for slide in self._slides if slide.autoshape_count > 0]

    @property
    def average_shapes_per_slide(self) -> float:
        """Average number of shapes per slide."""
        if not self._slides:
            return 0.0
        return self.total_shape_count / len(self._slides)

    @property
    def average_words_per_slide(self) -> float:
        """Average word count per slide."""
        if not self._slides:
            return 0.0
        return self.total_word_count / len(self._slides)

    def add_slide(self, layout: Any = None) -> Slide:
        """
        Add a new slide to the presentation.

        Args:
            layout: Slide layout (optional, not yet fully supported)

        Returns:
            The newly created Slide
        """
        # Create command
        cmd = AddSlide(index=len(self._slides))

        # Send command and get response
        slide_id = None
        if self._buffer:
            response = self._buffer.add(cmd)

            # Extract created slide ID from response
            if response and response.get("created"):
                slide_ids = response["created"].get("slideIds", [])
                if slide_ids:
                    slide_id = slide_ids[0]

        if not slide_id:
            # Generate a temporary ID if server didn't return one
            import uuid
            slide_id = f"sld_{uuid.uuid4().hex[:8]}"

        # Create local slide proxy
        slide = Slide(
            presentation=self._presentation,
            slide_id=slide_id,
            slide_index=len(self._slides),
            buffer=self._buffer,
            element_ids=[],
            elements={},
        )
        self._slides.append(slide)
        self._slides_by_id[slide_id] = slide
        return slide

    def add_blank_slide(self) -> Slide:
        """
        Add a new blank slide to the presentation.

        This is a convenience method equivalent to add_slide(layout=6)
        where layout 6 is typically the blank layout in PowerPoint.

        Returns:
            The newly created Slide
        """
        return self.add_slide(layout=None)

    def index(self, slide: Slide) -> int:
        """Get the index of a slide."""
        return self._slides.index(slide)

    def delete(self, slide: Slide) -> None:
        """
        Delete a slide from the presentation.

        Args:
            slide: The slide to delete

        Raises:
            ValueError: If slide is not in this collection
        """
        if slide not in self._slides:
            raise ValueError("Slide not found in presentation")

        slide_index = self._slides.index(slide)

        # Create and send delete command
        cmd = DeleteSlide(slide_index=slide_index)
        if self._buffer:
            self._buffer.add(cmd)

        # Remove from local collections
        self._slides.remove(slide)
        if slide._slide_id in self._slides_by_id:
            del self._slides_by_id[slide._slide_id]

        # Update indices of remaining slides
        for i, s in enumerate(self._slides):
            s._slide_index = i

    @athena_only(
        description="Delete multiple slides at once by index",
        since="0.1.2",
    )
    def delete_slides(self, indices: list[int]) -> None:
        """
        Delete multiple slides from the presentation by their indices.

        This is more efficient than calling delete() multiple times as it
        batches the operations. Indices are processed from highest to lowest
        to avoid index shifting issues.

        Args:
            indices: List of zero-based slide indices to delete

        Raises:
            ValueError: If any index is out of range
            ValueError: If duplicate indices are provided

        Example:
            # Delete slides at indices 1, 3, and 5
            prs.slides.delete_slides([1, 3, 5])

            # Delete the last two slides
            prs.slides.delete_slides([len(prs.slides) - 1, len(prs.slides) - 2])

        Note:
            This method is Athena-specific and not available in python-pptx.
        """
        # Validate indices
        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate indices are not allowed")

        for idx in indices:
            if idx < 0 or idx >= len(self._slides):
                raise ValueError(f"Slide index {idx} is out of range (0-{len(self._slides) - 1})")

        # Sort indices in descending order to avoid index shifting
        sorted_indices = sorted(indices, reverse=True)

        # Delete from highest to lowest
        for idx in sorted_indices:
            slide = self._slides[idx]

            # Create and send delete command
            cmd = DeleteSlide(slide_index=idx)
            if self._buffer:
                self._buffer.add(cmd)

            # Remove from local collections
            self._slides.remove(slide)
            if slide._slide_id in self._slides_by_id:
                del self._slides_by_id[slide._slide_id]

        # Update indices of remaining slides
        for i, s in enumerate(self._slides):
            s._slide_index = i

    @athena_only(
        description="Keep only specified slides, removing all others",
        since="0.1.2",
    )
    def keep_only(self, indices: list[int]) -> None:
        """
        Keep only the slides at the specified indices, deleting all others.

        This is the inverse of delete_slides() - instead of specifying which
        slides to remove, you specify which slides to keep.

        Args:
            indices: List of zero-based slide indices to keep

        Raises:
            ValueError: If any index is out of range
            ValueError: If duplicate indices are provided
            ValueError: If indices list is empty

        Example:
            # Keep only the first and last slides
            prs.slides.keep_only([0, len(prs.slides) - 1])

            # Keep only slide at index 2
            prs.slides.keep_only([2])

        Note:
            This method is Athena-specific and not available in python-pptx.
            The order of indices does not affect the final slide order -
            slides maintain their relative positions.
        """
        if not indices:
            raise ValueError("indices list cannot be empty")

        # Validate indices
        if len(indices) != len(set(indices)):
            raise ValueError("Duplicate indices are not allowed")

        for idx in indices:
            if idx < 0 or idx >= len(self._slides):
                raise ValueError(f"Slide index {idx} is out of range (0-{len(self._slides) - 1})")

        # Calculate which slides to delete (inverse of keep list)
        all_indices = set(range(len(self._slides)))
        keep_indices = set(indices)
        delete_indices = list(all_indices - keep_indices)

        # Use delete_slides for the actual deletion
        if delete_indices:
            self.delete_slides(delete_indices)

    def _update_from_snapshot(self, snapshot: DeckSnapshot) -> None:
        """Update slides from a snapshot."""
        # Clear existing slides
        self._slides = []
        self._slides_by_id = {}

        # Rebuild from snapshot
        for slide_snapshot in snapshot.slides:
            # Parse layout index from layout path (e.g., ppt/slideLayouts/slideLayout1.xml -> 0)
            layout_index = None
            if slide_snapshot.layout_path:
                import re
                match = re.search(r'slideLayout(\d+)\.xml$', slide_snapshot.layout_path)
                if match:
                    layout_index = int(match.group(1)) - 1  # Convert 1-based to 0-based

            slide = Slide(
                presentation=self._presentation,
                slide_id=slide_snapshot.id,
                slide_index=slide_snapshot.index,
                buffer=self._buffer,
                element_ids=slide_snapshot.element_ids,
                elements=snapshot.elements,
                background_color_hex=slide_snapshot.background_color_hex,
                notes=slide_snapshot.notes,
                layout_index=layout_index,
            )
            self._slides.append(slide)
            self._slides_by_id[slide_snapshot.id] = slide

    def __repr__(self) -> str:
        return f"<Slides count={len(self._slides)}>"


class SlideLayout:
    """
    Slide layout template.

    Represents a slide layout that can be applied to slides.
    Layouts define placeholder positions and default styling.

    Standard PowerPoint layout indices (0-based):
        0: Title Slide
        1: Title and Content
        2: Section Header
        3: Two Content
        4: Comparison
        5: Title Only
        6: Blank
        7: Content with Caption
        8: Picture with Caption
        9: Title and Vertical Text
        10: Vertical Title and Text

    Example:
        # Get a layout from the presentation
        blank_layout = prs.slide_layouts[6]
        print(blank_layout.name)  # "Blank"

        # Apply layout to a slide
        slide.slide_layout = blank_layout

        # Or set by index/name
        slide.slide_layout = 6
        slide.slide_layout = "Blank"
    """

    def __init__(
        self,
        index: int,
        name: Optional[str] = None,
        slide: Optional["Slide"] = None,
    ):
        self._index = index
        self._name = name
        self._slide = slide

    @property
    def index(self) -> int:
        """Layout index (0-based)."""
        return self._index

    @property
    def name(self) -> str:
        """
        Layout name.

        Returns the layout name if known, otherwise generates
        a name based on the standard layout order.
        """
        if self._name:
            return self._name
        # Common layout names by index
        names = {
            0: "Title Slide",
            1: "Title and Content",
            2: "Section Header",
            3: "Two Content",
            4: "Comparison",
            5: "Title Only",
            6: "Blank",
            7: "Content with Caption",
            8: "Picture with Caption",
            9: "Title and Vertical Text",
            10: "Vertical Title and Text",
        }
        return names.get(self._index, f"Custom Layout {self._index}")

    def __repr__(self) -> str:
        return f"<SlideLayout index={self._index} name='{self.name}'>"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SlideLayout):
            return self._index == other._index
        return False

    def __hash__(self) -> int:
        return hash(self._index)


class SlideLayouts:
    """
    Collection of slide layouts (stub for API compatibility).

    Note: Full slide layout support is not yet implemented.
    This collection allows code that accesses layouts to work,
    but layouts are not actually applied to new slides.
    """

    def __init__(self):
        # Standard PowerPoint has 11 built-in layouts
        self._layouts = [SlideLayout(i) for i in range(11)]

    def __len__(self) -> int:
        return len(self._layouts)

    def __iter__(self) -> Iterator[SlideLayout]:
        return iter(self._layouts)

    def __getitem__(self, key: int) -> SlideLayout:
        if key < 0 or key >= len(self._layouts):
            # Auto-extend for custom layout indices
            while len(self._layouts) <= key:
                self._layouts.append(SlideLayout(len(self._layouts)))
        return self._layouts[key]

    def get_by_name(self, name: str) -> Optional[SlideLayout]:
        """Get layout by name (returns first match or None)."""
        for layout in self._layouts:
            if layout.name.lower() == name.lower():
                return layout
        return None


class SlideMasters:
    """
    Collection of slide masters (stub for API compatibility).

    Not yet supported - raises UnsupportedFeatureError on use.
    """

    def __init__(self):
        pass

    def __len__(self) -> int:
        raise UnsupportedFeatureError(
            "slide_masters", "Slide masters are not yet supported"
        )

    def __iter__(self) -> Iterator[Any]:
        raise UnsupportedFeatureError(
            "slide_masters", "Slide masters are not yet supported"
        )

    def __getitem__(self, key: int) -> Any:
        raise UnsupportedFeatureError(
            "slide_masters", "Slide masters are not yet supported"
        )
