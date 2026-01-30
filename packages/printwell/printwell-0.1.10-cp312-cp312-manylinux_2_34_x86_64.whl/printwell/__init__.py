"""
Printwell: High-fidelity HTML to PDF conversion using Chromium.

Example:
    >>> from printwell import Converter, PdfOptions, PageSize
    >>> converter = Converter()
    >>> result = converter.html_to_pdf("<h1>Hello, World!</h1>")
    >>> result.write_to_file("output.pdf")
"""

from printwell._native import (
    # Annotation types and functions
    Annotation,
    AnnotationColor,
    AnnotationInfo,
    AnnotationRect,
    AnnotationType,
    # Bookmark types and functions
    Bookmark,
    # Converter classes
    Converter,
    ConverterPool,
    # Font types
    CustomFont,
    ElementBoundary,
    FontOptions,
    FontStyle,
    FontWeight,
    # Options classes
    Margins,
    Orientation,
    # Enums
    PageSize,
    PdfMetadata,
    PdfOptions,
    # Result classes
    PdfResult,
    RendererInfo,
    RenderOptions,
    ResourceOptions,
    Viewport,
    Watermark,
    WatermarkColor,
    WatermarkLayer,
    WatermarkPageSelectionType,
    # Watermark types and functions
    WatermarkPosition,
    # Functions
    add_annotations,
    add_bookmarks,
    add_watermark,
    add_watermarks,
    extract_bookmarks,
    # Convenience functions
    html_to_pdf,
    list_annotations,
    remove_annotations,
    url_to_pdf,
)

__all__ = [
    # Enums
    "PageSize",
    "Orientation",
    # Font types
    "FontWeight",
    "FontStyle",
    "CustomFont",
    # Options classes
    "Margins",
    "Viewport",
    "PdfMetadata",
    "PdfOptions",
    "ResourceOptions",
    "FontOptions",
    "RenderOptions",
    # Result classes
    "PdfResult",
    "ElementBoundary",
    "RendererInfo",
    # Converter classes
    "Converter",
    "ConverterPool",
    # Convenience functions
    "html_to_pdf",
    "url_to_pdf",
    # Watermark types and functions
    "WatermarkPosition",
    "WatermarkLayer",
    "WatermarkPageSelectionType",
    "WatermarkColor",
    "Watermark",
    "add_watermark",
    "add_watermarks",
    # Bookmark types and functions
    "Bookmark",
    "add_bookmarks",
    "extract_bookmarks",
    # Annotation types and functions
    "AnnotationType",
    "AnnotationRect",
    "AnnotationColor",
    "Annotation",
    "AnnotationInfo",
    "add_annotations",
    "list_annotations",
    "remove_annotations",
]

__version__ = "0.1.0"
