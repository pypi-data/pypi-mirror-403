"""
athena-python-pptx - Drop-in replacement for python-pptx.

This SDK provides a python-pptx-compatible API that connects to PPTX Studio
for real-time collaboration. Use exactly the same code you would with python-pptx:

    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.dml.color import RGBColor

    # Configure via environment variables (recommended):
    #   ATHENA_PPTX_BASE_URL=https://api.pptx-studio.com
    #   ATHENA_PPTX_API_KEY=your-api-key

    # Create a new presentation
    prs = Presentation.create(name="My Presentation")

    # Or upload an existing file
    prs = Presentation.upload("my_presentation.pptx")

    # Or connect to an existing deck
    prs = Presentation(deck_id="deck_123")

    # Work with slides and shapes (same API as python-pptx)
    slide = prs.slides[0]
    shape = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(1))
    shape.text_frame.text = "Hello World!"

    prs.save("output.pptx")

For features not yet implemented, UnsupportedFeatureError is raised with
a clear message explaining what's not supported.
"""

# Main entry point
from .presentation import Presentation

# Slide classes
from .slides import Slide, Slides, SlideLayout, SlideLayouts, SlideMasters, SlideBackground

# Shape classes
from .shapes import (
    Shape,
    Shapes,
    Table,
    TableCell,
    FillFormat,
    LineFormat,
    PlaceholderFormat,
    SlidePlaceholders,
)

# Text classes
from .text import TextFrame, Paragraph, Run, Font

# Error classes
from .errors import (
    PptxSdkError,
    UnsupportedFeatureError,
    RemoteError,
    ConflictError,
    ValidationError,
    ConnectionError,
    AuthenticationError,
    ExportError,
    RenderError,
    UploadError,
)

# Athena-specific decorators and utilities
from .decorators import athena_only, get_athena_functions, is_athena_only

# Documentation generator
from .docgen import generate_docs, generate_docs_json, collect_athena_docs

# Units (also available via pptx.util)
from .units import Inches, Cm, Mm, Pt, Centipoints, Px, Emu, Length

# Enums (legacy exports for backwards compatibility)
from .shapes import MSO_SHAPE
from .text import PP_ALIGN

# DML enums (also available via pptx.enum.dml)
from .enum.dml import (
    MSO_THEME_COLOR,
    MSO_LINE_DASH_STYLE,
    MSO_FILL_TYPE,
    MSO_COLOR_TYPE,
)

# Text enums (also available via pptx.enum.text)
from .enum.text import MSO_ANCHOR, MSO_AUTO_SIZE

# DML color (also available via pptx.dml.color)
from .dml.color import RGBColor

__version__ = "0.1.23"

__all__ = [
    # Main entry point
    "Presentation",
    # Slide classes
    "Slide",
    "Slides",
    "SlideLayout",
    "SlideLayouts",
    "SlideMasters",
    "SlideBackground",
    # Shape classes
    "Shape",
    "Shapes",
    "Table",
    "TableCell",
    "FillFormat",
    "LineFormat",
    "PlaceholderFormat",
    "SlidePlaceholders",
    # Shape type enumeration (legacy)
    "MSO_SHAPE",
    # Text classes
    "TextFrame",
    "Paragraph",
    "Run",
    "Font",
    # Enumerations
    "PP_ALIGN",
    "MSO_SHAPE",
    "MSO_THEME_COLOR",
    "MSO_LINE_DASH_STYLE",
    "MSO_FILL_TYPE",
    "MSO_COLOR_TYPE",
    "MSO_ANCHOR",
    "MSO_AUTO_SIZE",
    # Units
    "Inches",
    "Cm",
    "Mm",
    "Pt",
    "Centipoints",
    "Px",
    "Emu",
    "Length",
    # Color
    "RGBColor",
    # Errors
    "PptxSdkError",
    "UnsupportedFeatureError",
    "RemoteError",
    "ConflictError",
    "ValidationError",
    "ConnectionError",
    "AuthenticationError",
    "ExportError",
    "RenderError",
    "UploadError",
    # Athena-specific decorators
    "athena_only",
    "get_athena_functions",
    "is_athena_only",
    # Documentation generator
    "generate_docs",
    "generate_docs_json",
    "collect_athena_docs",
    # Version
    "__version__",
]
