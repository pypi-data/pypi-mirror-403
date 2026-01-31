"""
Presentation proxy class - the main entry point for the SDK.

Provides python-pptx-compatible Presentation API that operates
on remote decks via the PPTX Studio API.
"""

from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional, Union

from .batching import CommandBuffer, batch_context
from .client import Client
from .commands import SetCoreProperties, SetPresentationSize
from .errors import UnsupportedFeatureError
from .slides import SlideLayouts, SlideMasters, Slides
from .typing import DeckId, DeckSnapshot
from .units import Emu, Length, ensure_emu


# -------------------------------------------------------------------------
# Phase 4: CoreProperties class
# -------------------------------------------------------------------------

class CoreProperties:
    """
    Core document properties (metadata) for a presentation.

    Provides access to standard document metadata like title, author,
    subject, keywords, etc. Mirrors python-pptx's CoreProperties class.

    Example:
        prs.core_properties.title = "My Presentation"
        prs.core_properties.author = "John Doe"
        prs.core_properties.subject = "Q4 Report"
        prs.core_properties.keywords = "quarterly, report, 2024"
    """

    def __init__(self, presentation: "Presentation"):
        self._presentation = presentation
        self._title: Optional[str] = None
        self._author: Optional[str] = None
        self._subject: Optional[str] = None
        self._keywords: Optional[str] = None
        self._comments: Optional[str] = None
        self._category: Optional[str] = None
        self._last_modified_by: Optional[str] = None
        self._created: Optional[str] = None
        self._modified: Optional[str] = None

    @property
    def title(self) -> Optional[str]:
        """Document title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Set document title."""
        self._title = value
        self._emit_properties_change()

    @property
    def author(self) -> Optional[str]:
        """Document author."""
        return self._author

    @author.setter
    def author(self, value: str) -> None:
        """Set document author."""
        self._author = value
        self._emit_properties_change()

    @property
    def subject(self) -> Optional[str]:
        """Document subject."""
        return self._subject

    @subject.setter
    def subject(self, value: str) -> None:
        """Set document subject."""
        self._subject = value
        self._emit_properties_change()

    @property
    def keywords(self) -> Optional[str]:
        """Document keywords (comma-separated string)."""
        return self._keywords

    @keywords.setter
    def keywords(self, value: str) -> None:
        """Set document keywords."""
        self._keywords = value
        self._emit_properties_change()

    @property
    def comments(self) -> Optional[str]:
        """Document comments/description."""
        return self._comments

    @comments.setter
    def comments(self, value: str) -> None:
        """Set document comments."""
        self._comments = value
        self._emit_properties_change()

    @property
    def category(self) -> Optional[str]:
        """Document category."""
        return self._category

    @category.setter
    def category(self, value: str) -> None:
        """Set document category."""
        self._category = value
        self._emit_properties_change()

    @property
    def last_modified_by(self) -> Optional[str]:
        """Last modified by user."""
        return self._last_modified_by

    @last_modified_by.setter
    def last_modified_by(self, value: str) -> None:
        """Set last modified by user."""
        self._last_modified_by = value
        self._emit_properties_change()

    @property
    def created(self) -> Optional[str]:
        """Document creation timestamp (read-only)."""
        return self._created

    @property
    def modified(self) -> Optional[str]:
        """Document last modified timestamp (read-only)."""
        return self._modified

    def _emit_properties_change(self) -> None:
        """Emit a SetCoreProperties command."""
        if self._presentation._buffer:
            cmd = SetCoreProperties(
                title=self._title,
                author=self._author,
                subject=self._subject,
                keywords=self._keywords,
                comments=self._comments,
                category=self._category,
                last_modified_by=self._last_modified_by,
            )
            self._presentation._buffer.add(cmd)

    def __repr__(self) -> str:
        return f"<CoreProperties title={self._title!r} author={self._author!r}>"


class Presentation:
    """
    Presentation proxy - the main entry point for working with a deck.

    Mirrors python-pptx's Presentation class but operates on remote
    decks stored in PPTX Studio.

    Example:
        from pptx import Presentation
        from pptx.units import Inches

        prs = Presentation(
            deck_id="deck_123",
            base_url="https://api.pptx-studio.com",
            api_key="sk_live_..."
        )

        slide = prs.slides[0]
        tb = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
        tb.text_frame.text = "Hello"
        prs.save("out.pptx")
    """

    def __init__(
        self,
        deck_id: DeckId,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        auto_refresh: bool = True,
    ):
        """
        Initialize a Presentation proxy.

        Args:
            deck_id: ID of the deck to work with
            base_url: Base URL of the API. If not provided, uses ATHENA_PPTX_BASE_URL
                     environment variable.
            api_key: Optional API key for authentication. If not provided, uses
                    ATHENA_PPTX_API_KEY environment variable.
            auto_refresh: Whether to automatically fetch snapshot on init
        """
        self._deck_id = deck_id
        self._client = Client(base_url=base_url, api_key=api_key)
        self._buffer = CommandBuffer(self._client, deck_id)
        self._snapshot: Optional[DeckSnapshot] = None
        self._slides: Optional[Slides] = None

        if auto_refresh:
            self.refresh()

    @classmethod
    def from_url(
        cls,
        url: str,
        api_key: Optional[str] = None,
    ) -> Presentation:
        """
        Create a Presentation from a full URL.

        Args:
            url: Full URL including deck ID (e.g., https://api.example.com/decks/deck_123)
            api_key: Optional API key

        Returns:
            Presentation instance
        """
        # Parse URL to extract base_url and deck_id
        from urllib.parse import urlparse

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Extract deck_id from path (assumes /decks/{deck_id} or /v1/decks/{deck_id})
        path_parts = parsed.path.strip("/").split("/")
        deck_id = None
        for i, part in enumerate(path_parts):
            if part == "decks" and i + 1 < len(path_parts):
                deck_id = path_parts[i + 1]
                break

        if not deck_id:
            raise ValueError(f"Could not extract deck_id from URL: {url}")

        return cls(deck_id=deck_id, base_url=base_url, api_key=api_key)

    @classmethod
    def create(
        cls,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Presentation:
        """
        Create a new empty presentation.

        This creates an empty presentation that's immediately ready to use.
        You can then add slides and content.

        Args:
            base_url: Base URL of the API. If not provided, uses ATHENA_PPTX_BASE_URL
                     environment variable.
            api_key: Optional API key. If not provided, uses ATHENA_PPTX_API_KEY
                    environment variable.
            name: Optional name for the presentation

        Returns:
            Presentation instance for the new deck

        Example:
            # Using environment variables
            prs = Presentation.create(name="My New Presentation")

            # Or with explicit parameters
            prs = Presentation.create(
                base_url="http://localhost:4000",
                api_key="your-api-key",
                name="My New Presentation"
            )
            slide = prs.slides.add_slide()
        """
        client = Client(base_url=base_url, api_key=api_key)
        result = client.create_empty_deck(name=name)
        deck_id = result["id"]
        prs = cls(deck_id=deck_id, base_url=base_url, api_key=api_key)

        # Delete any default slides from the blank template
        # The blank template includes one slide that we need to remove
        # to provide a truly empty presentation
        while len(prs.slides) > 0:
            prs.slides.delete(prs.slides[0])

        return prs

    @classmethod
    def upload(
        cls,
        path: Union[str, Path],
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        name: Optional[str] = None,
        wait: bool = True,
    ) -> Presentation:
        """
        Upload a local PPTX file and create a Presentation.

        This is the recommended way to open an existing PPTX file for editing.

        Args:
            path: Path to the local PPTX file
            base_url: Base URL of the API. If not provided, uses ATHENA_PPTX_BASE_URL
                     environment variable.
            api_key: Optional API key. If not provided, uses ATHENA_PPTX_API_KEY
                    environment variable.
            name: Optional name for the presentation (defaults to filename)
            wait: Whether to wait for processing to complete (default True)

        Returns:
            Presentation instance for the uploaded deck

        Example:
            from pptx import Presentation

            # Upload using environment variables
            prs = Presentation.upload("my_presentation.pptx")

            # Or with explicit parameters
            prs = Presentation.upload(
                "my_presentation.pptx",
                base_url="http://localhost:4000"
            )

            # Edit the presentation
            slide = prs.slides[0]
            slide.shapes[0].text_frame.text = "New title"

            # Save changes
            prs.save("modified.pptx")
        """
        client = Client(base_url=base_url, api_key=api_key)

        if wait:
            # Upload and wait for processing
            deck_id = client.upload_file(str(path), name=name)
        else:
            # Upload without waiting
            deck_id = client.upload_file_async(str(path), name=name)

        return cls(deck_id=deck_id, base_url=base_url, api_key=api_key, auto_refresh=wait)

    @classmethod
    def open(
        cls,
        path: Union[str, Path],
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Presentation:
        """
        Open a local PPTX file by uploading it to the server.

        This is an alias for upload() to match python-pptx's Presentation(path) pattern.

        Args:
            path: Path to the local PPTX file
            base_url: Base URL of the API. If not provided, uses ATHENA_PPTX_BASE_URL
                     environment variable.
            api_key: Optional API key. If not provided, uses ATHENA_PPTX_API_KEY
                    environment variable.
            name: Optional name for the presentation

        Returns:
            Presentation instance for the uploaded deck

        Example:
            from pptx import Presentation

            # Using environment variables
            prs = Presentation.open("my_presentation.pptx")

            # Or with explicit parameters
            prs = Presentation.open("my_presentation.pptx", base_url="http://localhost:4000")
        """
        return cls.upload(path, base_url=base_url, api_key=api_key, name=name)

    @property
    def deck_id(self) -> DeckId:
        """ID of the deck."""
        return self._deck_id

    @property
    def slides(self) -> Slides:
        """Collection of slides in the presentation."""
        if self._slides is None:
            self._slides = Slides(
                presentation=self,
                buffer=self._buffer,
                snapshot=self._snapshot,
            )
        return self._slides

    @property
    def slide_width(self) -> Emu:
        """Width of slides in EMU."""
        if self._snapshot:
            return Emu(self._snapshot.slide_width_emu)
        return Emu(9144000)  # Default 10 inches

    @property
    def slide_height(self) -> Emu:
        """Height of slides in EMU."""
        if self._snapshot:
            return Emu(self._snapshot.slide_height_emu)
        return Emu(6858000)  # Default 7.5 inches

    @property
    def slide_layouts(self) -> SlideLayouts:
        """Slide layouts (not yet supported)."""
        return SlideLayouts()

    @property
    def slide_masters(self) -> SlideMasters:
        """Slide masters (not yet supported)."""
        return SlideMasters()

    def reorder_slides(self, new_order: list[int]) -> None:
        """
        Reorder slides in the presentation.

        Args:
            new_order: List of slide indices representing the new order.
                      Must contain all indices from 0 to len(slides)-1 exactly once.

        Example:
            # Move last slide to first position
            prs.reorder_slides([2, 0, 1])  # For a 3-slide deck
        """
        from .commands import ReorderSlides

        # Validate
        if len(new_order) != len(self.slides):
            raise ValueError(
                f"new_order must contain {len(self.slides)} indices, got {len(new_order)}"
            )

        seen = set()
        for index in new_order:
            if index < 0 or index >= len(self.slides):
                raise ValueError(f"Invalid slide index: {index}")
            if index in seen:
                raise ValueError(f"Duplicate slide index: {index}")
            seen.add(index)

        # Send command
        cmd = ReorderSlides(new_order=list(new_order))
        self._buffer.add(cmd)

        # Update local state to reflect new order
        if self._slides is not None:
            old_slides = list(self._slides._slides)
            self._slides._slides = [old_slides[i] for i in new_order]
            # Update indices
            for i, slide in enumerate(self._slides._slides):
                slide._slide_index = i

    @property
    def core_properties(self) -> CoreProperties:
        """
        Core document properties (metadata).

        Returns a CoreProperties object for accessing and setting
        document metadata like title, author, subject, keywords.

        Example:
            prs.core_properties.title = "My Presentation"
            prs.core_properties.author = "John Doe"
        """
        if not hasattr(self, '_core_properties') or self._core_properties is None:
            self._core_properties = CoreProperties(self)
        return self._core_properties

    def set_slide_size(self, width: Length, height: Length) -> None:
        """
        Set the slide dimensions.

        Args:
            width: Slide width (Length, e.g., Inches(10))
            height: Slide height (Length, e.g., Inches(7.5))

        Example:
            from pptx.util import Inches
            prs.set_slide_size(Inches(13.333), Inches(7.5))  # 16:9
        """
        width_emu = int(ensure_emu(width))
        height_emu = int(ensure_emu(height))

        cmd = SetPresentationSize(width_emu=width_emu, height_emu=height_emu)
        self._buffer.add(cmd)

        # Update local snapshot if available
        if self._snapshot:
            self._snapshot.slide_width_emu = width_emu
            self._snapshot.slide_height_emu = height_emu

    @property
    def notes_master(self) -> Any:
        """Notes master (not yet supported)."""
        raise UnsupportedFeatureError(
            "notes_master", "Notes master is not yet supported"
        )

    # -------------------------------------------------------------------------
    # Convenience properties
    # -------------------------------------------------------------------------

    @property
    def name(self) -> Optional[str]:
        """
        Name of the presentation.

        Returns the deck name if available, or None.
        """
        if self._snapshot:
            return self._snapshot.name
        return None

    @property
    def slide_count(self) -> int:
        """
        Number of slides in the presentation.

        This is a convenience alias for len(prs.slides).
        """
        return len(self.slides)

    @property
    def is_empty(self) -> bool:
        """True if the presentation has no slides."""
        return len(self.slides) == 0

    @property
    def slide_size(self) -> tuple[Emu, Emu]:
        """
        Slide dimensions as (width, height) tuple in EMU.

        Returns:
            Tuple of (slide_width, slide_height) in EMU
        """
        return (self.slide_width, self.slide_height)

    @property
    def slide_size_inches(self) -> tuple[float, float]:
        """
        Slide dimensions as (width, height) tuple in inches.

        Returns:
            Tuple of (width, height) in inches
        """
        from .units import EMU_PER_INCH
        return (
            float(self.slide_width) / EMU_PER_INCH,
            float(self.slide_height) / EMU_PER_INCH,
        )

    @property
    def aspect_ratio(self) -> float:
        """
        Slide aspect ratio (width / height).

        Common values:
            - 1.333 (4:3 standard)
            - 1.778 (16:9 widescreen)
        """
        h = int(self.slide_height)
        if h == 0:
            return 0.0
        return float(self.slide_width) / float(h)

    @property
    def first_slide(self) -> Optional[Any]:
        """
        First slide in the presentation.

        Returns None if there are no slides.
        """
        return self.slides.first

    @property
    def last_slide(self) -> Optional[Any]:
        """
        Last slide in the presentation.

        Returns None if there are no slides.
        """
        return self.slides.last

    @property
    def all_text(self) -> str:
        """
        Get all text content from the entire presentation.

        Returns text from all slides and shapes, useful for
        search indexing or text analysis.
        """
        texts = []
        for slide in self.slides:
            slide_text = slide.all_text
            if slide_text:
                texts.append(slide_text)
        return "\n\n".join(texts)

    @property
    def total_word_count(self) -> int:
        """
        Total word count across all slides.
        """
        return sum(slide.word_count for slide in self.slides)

    @property
    def total_shape_count(self) -> int:
        """
        Total number of shapes across all slides.
        """
        return sum(slide.shape_count for slide in self.slides)

    def find_text(self, text: str, case_sensitive: bool = False) -> list[tuple[int, Any]]:
        """
        Find all shapes containing specific text across all slides.

        Args:
            text: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            List of (slide_index, shape) tuples for matching shapes
        """
        results = []
        for slide in self.slides:
            shapes = slide.get_shapes_containing(text, case_sensitive)
            for shape in shapes:
                results.append((slide.slide_index, shape))
        return results

    def replace_text(
        self, find: str, replace_with: str, case_sensitive: bool = False
    ) -> int:
        """
        Replace text across all slides in the presentation.

        Args:
            find: Text to find
            replace_with: Replacement text
            case_sensitive: Whether to do case-sensitive search

        Returns:
            Total number of replacements made
        """
        total_count = 0
        for slide in self.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    count = shape.text_frame.replace(find, replace_with, case_sensitive)
                    total_count += count
        return total_count

    def get_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive statistics about the presentation.

        Returns:
            Dictionary with statistics including:
            - slide_count: Number of slides
            - total_shapes: Total shapes across all slides
            - total_words: Total word count
            - shape_types: Breakdown by shape type
            - slides_with_images: Number of slides containing images
            - slides_with_tables: Number of slides containing tables
            - average_shapes_per_slide: Average shapes per slide
        """
        shape_type_counts: dict[str, int] = {}
        slides_with_images = 0
        slides_with_tables = 0

        for slide in self.slides:
            if slide.has_images:
                slides_with_images += 1
            if slide.has_tables:
                slides_with_tables += 1

            for shape_type in slide.shape_types:
                shape_type_counts[shape_type] = shape_type_counts.get(shape_type, 0) + 1

        slide_count = len(self.slides)
        total_shapes = self.total_shape_count

        return {
            'slide_count': slide_count,
            'total_shapes': total_shapes,
            'total_words': self.total_word_count,
            'shape_types': shape_type_counts,
            'slides_with_images': slides_with_images,
            'slides_with_tables': slides_with_tables,
            'average_shapes_per_slide': total_shapes / slide_count if slide_count > 0 else 0,
        }

    @property
    def image_count(self) -> int:
        """Total number of images across all slides."""
        return sum(slide.image_count for slide in self.slides)

    @property
    def table_count(self) -> int:
        """Total number of tables across all slides."""
        return sum(slide.table_count for slide in self.slides)

    @property
    def has_images(self) -> bool:
        """True if presentation contains any images."""
        return any(slide.has_images for slide in self.slides)

    @property
    def has_tables(self) -> bool:
        """True if presentation contains any tables."""
        return any(slide.has_tables for slide in self.slides)

    @property
    def textbox_count(self) -> int:
        """Total number of textboxes across all slides."""
        return sum(slide.textbox_count for slide in self.slides)

    @property
    def autoshape_count(self) -> int:
        """Total number of autoshapes across all slides."""
        return sum(slide.autoshape_count for slide in self.slides)

    @property
    def placeholder_count(self) -> int:
        """Total number of placeholders across all slides."""
        return sum(slide.placeholder_count for slide in self.slides)

    # -------------------------------------------------------------------------
    # Notes-related properties
    # -------------------------------------------------------------------------

    @property
    def all_notes(self) -> str:
        """
        Get all speaker notes from all slides.

        Returns notes from all slides concatenated, with slide markers.
        """
        notes_parts = []
        for i, slide in enumerate(self.slides):
            if slide.notes:
                notes_parts.append(f"[Slide {i + 1}]\n{slide.notes}")
        return "\n\n".join(notes_parts)

    @property
    def slides_with_notes_count(self) -> int:
        """Number of slides that have speaker notes."""
        return sum(1 for slide in self.slides if slide.has_notes_slide)

    @property
    def has_notes(self) -> bool:
        """True if any slide has speaker notes."""
        return any(slide.has_notes_slide for slide in self.slides)

    @property
    def notes_word_count(self) -> int:
        """Total word count across all speaker notes."""
        return self.slides.notes_word_count

    def get_slides_with_notes(self) -> list[Any]:
        """Get all slides that have speaker notes."""
        return self.slides.get_slides_with_notes()

    def get_slides_without_notes(self) -> list[Any]:
        """Get all slides that don't have speaker notes."""
        return self.slides.get_slides_without_notes()

    # -------------------------------------------------------------------------
    # Additional convenience methods
    # -------------------------------------------------------------------------

    def get_slides_with_text(self, text: str, case_sensitive: bool = False) -> list[Any]:
        """
        Get all slides containing specific text.

        Args:
            text: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            List of slides containing the text
        """
        return self.slides.get_slides_with_text(text, case_sensitive)

    def get_text_summary(self) -> dict[str, Any]:
        """
        Get a summary of text content across the presentation.

        Returns:
            Dictionary with text statistics:
            - total_words: Total word count
            - total_characters: Total character count
            - average_words_per_slide: Average words per slide
            - slides_with_text: Number of slides containing text
            - unique_words: Number of unique words (lowercase)
        """
        total_words = 0
        total_chars = 0
        slides_with_text = 0
        all_words: set[str] = set()

        for slide in self.slides:
            text = slide.all_text
            if text:
                slides_with_text += 1
                words = text.split()
                total_words += len(words)
                total_chars += len(text)
                all_words.update(w.lower() for w in words)

        slide_count = len(self.slides)
        return {
            'total_words': total_words,
            'total_characters': total_chars,
            'average_words_per_slide': total_words / slide_count if slide_count > 0 else 0,
            'slides_with_text': slides_with_text,
            'unique_words': len(all_words),
        }

    @property
    def is_widescreen(self) -> bool:
        """
        True if presentation uses widescreen (16:9) aspect ratio.

        Returns True if aspect ratio is approximately 1.77 (16:9).
        """
        ratio = self.aspect_ratio
        return 1.7 <= ratio <= 1.85

    @property
    def is_standard(self) -> bool:
        """
        True if presentation uses standard (4:3) aspect ratio.

        Returns True if aspect ratio is approximately 1.33 (4:3).
        """
        ratio = self.aspect_ratio
        return 1.25 <= ratio <= 1.4

    def to_outline(self, include_body: bool = True) -> str:
        """
        Generate a text outline of the presentation.

        Creates a hierarchical text representation with slide titles
        and optionally body text.

        Args:
            include_body: If True, include body text under titles

        Returns:
            Formatted outline string
        """
        lines = []
        for i, slide in enumerate(self.slides):
            # Slide header
            title = slide.title_text or f"(Slide {i + 1})"
            lines.append(f"{i + 1}. {title}")

            if include_body:
                # Add body text indented
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        text = shape.text.strip()
                        if text and text != title:
                            for line in text.split('\n'):
                                if line.strip():
                                    lines.append(f"   - {line.strip()}")

            lines.append("")  # Blank line between slides

        return '\n'.join(lines)

    def get_all_fonts(self) -> set:
        """
        Get all unique font names used in the presentation.

        Returns:
            Set of font family names
        """
        fonts: set = set()
        for slide in self.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for run in shape.text_frame.get_all_runs():
                        if run.font._name:
                            fonts.add(run.font._name)
        return fonts

    def get_all_colors(self) -> set:
        """
        Get all unique colors used in the presentation.

        Returns:
            Set of color hex strings (without #)
        """
        colors: set = set()
        for slide in self.slides:
            # Background color
            if slide._background_color_hex:
                colors.add(slide._background_color_hex)

            for shape in slide.shapes:
                # Fill color
                if hasattr(shape, 'fill') and shape.fill.has_fill:
                    color = shape.fill.color_hex
                    if color:
                        colors.add(color)

                # Line color
                if hasattr(shape, 'line') and shape.line.has_line:
                    color = shape.line.color_hex
                    if color:
                        colors.add(color)

                # Text colors
                if shape.has_text_frame:
                    for run in shape.text_frame.get_all_runs():
                        if run.font._color_hex:
                            colors.add(run.font._color_hex)

        return colors

    def get_shape_types_summary(self) -> dict:
        """
        Get a count of each shape type in the presentation.

        Returns:
            Dictionary mapping shape type to count
        """
        counts: dict = {}
        for slide in self.slides:
            for shape in slide.shapes:
                shape_type = shape.shape_type or 'unknown'
                counts[shape_type] = counts.get(shape_type, 0) + 1
        return counts

    def contains_text(self, text: str, case_sensitive: bool = False) -> bool:
        """
        Check if presentation contains specific text anywhere.

        Args:
            text: Text to search for
            case_sensitive: Whether to do case-sensitive search

        Returns:
            True if text is found in any slide
        """
        search = text if case_sensitive else text.lower()
        all_text = self.all_text if case_sensitive else self.all_text.lower()
        return search in all_text

    def get_slide_by_title(self, title: str, case_sensitive: bool = False) -> Any:
        """
        Find a slide by its title.

        Args:
            title: Title text to search for
            case_sensitive: Whether to do case-sensitive match

        Returns:
            Slide with matching title, or None
        """
        return self.slides.find_by_title(title, case_sensitive)

    def get_empty_slides(self) -> list:
        """
        Get all slides that have no content (no shapes or only empty shapes).

        Returns:
            List of empty slides
        """
        empty = []
        for slide in self.slides:
            if slide.is_blank:
                empty.append(slide)
            elif slide.word_count == 0 and not slide.has_images:
                empty.append(slide)
        return empty

    # -------------------------------------------------------------------------
    # Serialization methods
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Serialize presentation to a dictionary.

        Returns a comprehensive dictionary representation suitable for
        JSON serialization, debugging, or analysis.

        Returns:
            Dictionary with presentation metadata and content
        """
        return {
            'deck_id': self._deck_id,
            'name': self.name,
            'slide_count': len(self.slides),
            'slide_width_emu': int(self.slide_width),
            'slide_height_emu': int(self.slide_height),
            'slide_size_inches': self.slide_size_inches,
            'aspect_ratio': self.aspect_ratio,
            'is_widescreen': self.is_widescreen,
            'is_standard': self.is_standard,
            'statistics': self.get_statistics(),
            'slides': [slide.to_dict() for slide in self.slides],
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Serialize presentation to JSON string.

        Args:
            indent: Indentation level for pretty printing (default 2)

        Returns:
            JSON string representation

        Example:
            json_str = prs.to_json()
            with open('presentation.json', 'w') as f:
                f.write(json_str)
        """
        import json
        return json.dumps(self.to_dict(), indent=indent)

    def get_all_shapes(self) -> list:
        """
        Get all shapes from all slides as a flat list.

        Returns:
            List of all Shape objects across all slides
        """
        shapes = []
        for slide in self.slides:
            shapes.extend(list(slide.shapes))
        return shapes

    def get_all_text_shapes(self) -> list:
        """
        Get all text-containing shapes from all slides.

        Returns:
            List of shapes that have text frames
        """
        return [s for s in self.get_all_shapes() if s.has_text_frame]

    def get_all_text_frames(self) -> list:
        """
        Get all text frames from all slides.

        Returns:
            List of TextFrame objects
        """
        return [s.text_frame for s in self.get_all_shapes() if s.has_text_frame]

    def get_word_frequency(self, top_n: int = 20, min_length: int = 3) -> list:
        """
        Get most frequently used words in the presentation.

        Args:
            top_n: Number of top words to return
            min_length: Minimum word length to consider

        Returns:
            List of (word, count) tuples sorted by frequency
        """
        word_counts: dict[str, int] = {}
        text = self.all_text.lower()

        # Simple word tokenization
        import re
        words = re.findall(r'\b[a-z]+\b', text)

        for word in words:
            if len(word) >= min_length:
                word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:top_n]

    def get_bullet_points(self) -> list:
        """
        Extract all bullet points from the presentation.

        Returns a list of bullet point strings found across all slides.
        Identifies bullets by paragraph level > 0 or bullet characters.

        Returns:
            List of bullet point text strings
        """
        bullets = []
        for slide in self.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        if para._level > 0 or para._bullet:
                            text = para.text.strip()
                            if text:
                                bullets.append(text)
        return bullets

    # -------------------------------------------------------------------------
    # Data operations
    # -------------------------------------------------------------------------

    def refresh(self) -> None:
        """
        Fetch the latest snapshot from the server.

        This updates the local state to match the server's current state.
        Call this to sync after external changes or periodically for
        long-running sessions.
        """
        self._snapshot = self._client.get_snapshot(self._deck_id)

        # Update slides from new snapshot
        if self._slides is not None:
            self._slides._update_from_snapshot(self._snapshot)
        else:
            self._slides = Slides(
                presentation=self,
                buffer=self._buffer,
                snapshot=self._snapshot,
            )

    def save(self, path: Union[str, Path]) -> None:
        """
        Export the presentation and download to a local file.

        Args:
            path: Path where the PPTX file should be saved
        """
        # Flush any pending commands first
        self._buffer.flush()

        # Export and download
        pptx_bytes = self._client.export_and_download(self._deck_id)

        # Write to file
        path = Path(path)
        path.write_bytes(pptx_bytes)

    def save_to_bytes(self) -> bytes:
        """
        Export the presentation and return as bytes.

        Returns:
            PPTX file bytes
        """
        # Flush any pending commands first
        self._buffer.flush()

        return self._client.export_and_download(self._deck_id)

    # -------------------------------------------------------------------------
    # Batching
    # -------------------------------------------------------------------------

    @contextmanager
    def batch(self) -> Generator[Presentation, None, None]:
        """
        Context manager for batching multiple operations.

        All commands within this context are collected and sent
        as a single request when the context exits.

        Example:
            with prs.batch():
                tb = slide.shapes.add_textbox(...)
                tb.text_frame.text = "Hello"
                # Both commands sent here in one request

        Yields:
            self for chaining
        """
        with batch_context(self._buffer):
            yield self

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def render_slide(
        self,
        slide_index: int,
        scale: int = 2,
    ) -> bytes:
        """
        Render a slide as PNG.

        Args:
            slide_index: Zero-based index of the slide to render
            scale: Render scale factor (default 2x)

        Returns:
            PNG image bytes
        """
        # Flush any pending commands first
        self._buffer.flush()

        return self._client.render_slide(
            self._deck_id,
            slide_index,
            scale=scale,
        )

    def render_slide_sync(
        self,
        slide_index: int,
        scale: int = 2,
    ) -> bytes:
        """
        Synchronously render a slide (for development/testing).

        This may not be available in production environments.

        Args:
            slide_index: Zero-based index of the slide to render
            scale: Render scale factor

        Returns:
            PNG image bytes
        """
        # Flush any pending commands first
        self._buffer.flush()

        return self._client.render_slide_sync(
            self._deck_id,
            slide_index,
            scale=scale,
        )

    # -------------------------------------------------------------------------
    # Connection info
    # -------------------------------------------------------------------------

    def get_connection_info(self) -> dict[str, str]:
        """
        Get yhub WebSocket connection info for real-time collaboration.

        Returns:
            Dictionary with wsUrl and authToken
        """
        return self._client.get_connection_info(self._deck_id)

    def __repr__(self) -> str:
        slide_count = len(self._slides) if self._slides else "?"
        return f"<Presentation deck_id='{self._deck_id}' slides={slide_count}>"
