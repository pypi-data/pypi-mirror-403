"""Type stubs for printwell."""

from enum import IntEnum
from typing import List, Optional, Tuple

# =============================================================================
# Enums
# =============================================================================

class PageSize(IntEnum):
    """Page size presets."""

    A3 = ...
    A4 = ...
    A5 = ...
    Letter = ...
    Legal = ...
    Tabloid = ...

class Orientation(IntEnum):
    """Page orientation."""

    Portrait = ...
    Landscape = ...

class FontWeight(IntEnum):
    """Font weight (100-900)."""

    Thin = 100
    ExtraLight = 200
    Light = 300
    Normal = 400
    Medium = 500
    SemiBold = 600
    Bold = 700
    ExtraBold = 800
    Black = 900

class FontStyle(IntEnum):
    """Font style."""

    Normal = 0
    Italic = 1
    Oblique = 2

class WatermarkPosition(IntEnum):
    """Watermark position on the page."""

    Center = ...
    TopLeft = ...
    TopCenter = ...
    TopRight = ...
    MiddleLeft = ...
    MiddleRight = ...
    BottomLeft = ...
    BottomCenter = ...
    BottomRight = ...

class WatermarkLayer(IntEnum):
    """Watermark layer."""

    Background = ...
    Foreground = ...

class WatermarkPageSelectionType(IntEnum):
    """Page selection for watermarking."""

    All = ...
    Odd = ...
    Even = ...
    First = ...
    Last = ...

class AnnotationType(IntEnum):
    """Annotation types supported by PDFium."""

    Highlight = ...
    Underline = ...
    Strikeout = ...
    Squiggly = ...
    Text = ...
    FreeText = ...
    Line = ...
    Square = ...
    Circle = ...
    Ink = ...
    Stamp = ...
    Link = ...

class EncryptionAlgorithm(IntEnum):
    """Encryption algorithm."""

    Aes256 = ...
    Aes128 = ...
    Rc4_128 = ...

class PdfALevel(IntEnum):
    """PDF/A conformance level."""

    PdfA1b = ...
    PdfA1a = ...
    PdfA2b = ...
    PdfA2u = ...
    PdfA2a = ...
    PdfA3b = ...
    PdfA3u = ...
    PdfA3a = ...

class PdfAIssueSeverity(IntEnum):
    """Severity of a PDF/A compliance issue."""

    Error = ...
    Warning = ...
    Info = ...

class PdfAIssueCategory(IntEnum):
    """Category of a PDF/A compliance issue."""

    Fonts = ...
    Color = ...
    Metadata = ...
    Structure = ...
    Actions = ...
    Encryption = ...
    Annotations = ...
    Transparency = ...
    Attachments = ...

class PdfUALevel(IntEnum):
    """PDF/UA conformance level."""

    PdfUA1 = ...
    PdfUA2 = ...

class PdfUAIssueSeverity(IntEnum):
    """Severity of a PDF/UA compliance issue."""

    Error = ...
    Warning = ...
    Info = ...

class PdfUAIssueCategory(IntEnum):
    """Category of a PDF/UA compliance issue."""

    Structure = ...
    Tags = ...
    AltText = ...
    Language = ...
    ReadingOrder = ...
    Metadata = ...
    Tables = ...
    Headings = ...
    Color = ...
    Fonts = ...
    Navigation = ...

class SignatureLevel(IntEnum):
    """PAdES signature level."""

    PadesB = ...
    PadesT = ...
    PadesLT = ...
    PadesLTA = ...

class MdpPermissions(IntEnum):
    """MDP permissions for certification signatures."""

    NoChanges = ...
    FormFillingAndSigning = ...
    FormFillingSigningAndAnnotations = ...

class FormFieldType(IntEnum):
    """Form field type enumeration."""

    Text = ...
    Checkbox = ...
    Dropdown = ...
    Signature = ...

# =============================================================================
# Core Classes
# =============================================================================

class Margins:
    """Page margins in millimeters."""

    top: float
    right: float
    bottom: float
    left: float

    def __init__(
        self,
        top: float = 10.0,
        right: float = 10.0,
        bottom: float = 10.0,
        left: float = 10.0,
    ) -> None: ...
    @staticmethod
    def uniform(size: float) -> Margins: ...
    @staticmethod
    def symmetric(vertical: float, horizontal: float) -> Margins: ...
    @staticmethod
    def none() -> Margins: ...

class Viewport:
    """Viewport configuration."""

    width: int
    height: int
    device_scale_factor: float

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        device_scale_factor: float = 1.0,
    ) -> None: ...

class PdfMetadata:
    """PDF document metadata."""

    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    keywords: Optional[str]
    creator: Optional[str]
    producer: Optional[str]

    def __init__(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        subject: Optional[str] = None,
        keywords: Optional[str] = None,
        creator: Optional[str] = None,
        producer: Optional[str] = None,
    ) -> None: ...

class CustomFont:
    """Custom font definition."""

    family: str
    data: bytes
    weight: FontWeight
    style: FontStyle

    def __init__(
        self,
        family: str,
        data: bytes,
        weight: FontWeight = FontWeight.Normal,
        style: FontStyle = FontStyle.Normal,
    ) -> None: ...
    @staticmethod
    def from_file(
        family: str,
        path: str,
        weight: FontWeight = FontWeight.Normal,
        style: FontStyle = FontStyle.Normal,
    ) -> CustomFont: ...

class FontOptions:
    """Font options."""

    custom_fonts: List[CustomFont]
    default_sans_serif: str
    default_serif: str
    default_monospace: str
    minimum_font_size: int
    default_font_size: int
    use_system_fonts: bool
    enable_web_fonts: bool

    def __init__(
        self,
        custom_fonts: Optional[List[CustomFont]] = None,
        default_sans_serif: str = "Arial",
        default_serif: str = "Times New Roman",
        default_monospace: str = "Courier New",
        minimum_font_size: int = 0,
        default_font_size: int = 16,
        use_system_fonts: bool = True,
        enable_web_fonts: bool = True,
    ) -> None: ...

class ResourceOptions:
    """Resource loading options."""

    allow_remote: bool
    timeout_ms: int
    max_concurrent: int
    blocked_domains: List[str]
    allowed_domains: List[str]
    block_images: bool
    block_stylesheets: bool
    block_scripts: bool
    block_fonts: bool
    user_agent: Optional[str]
    enable_cache: bool

    def __init__(
        self,
        allow_remote: bool = True,
        timeout_ms: int = 30000,
        max_concurrent: int = 6,
        blocked_domains: Optional[List[str]] = None,
        allowed_domains: Optional[List[str]] = None,
        block_images: bool = False,
        block_stylesheets: bool = False,
        block_scripts: bool = False,
        block_fonts: bool = False,
        user_agent: Optional[str] = None,
        enable_cache: bool = True,
    ) -> None: ...

class RenderOptions:
    """Rendering options."""

    base_url: Optional[str]
    user_stylesheets: List[str]
    viewport: Optional[Viewport]
    resources: Optional[ResourceOptions]
    fonts: Optional[FontOptions]

    def __init__(
        self,
        base_url: Optional[str] = None,
        user_stylesheets: Optional[List[str]] = None,
        viewport: Optional[Viewport] = None,
        resources: Optional[ResourceOptions] = None,
        fonts: Optional[FontOptions] = None,
    ) -> None: ...

class PdfOptions:
    """PDF generation options."""

    page_size: Optional[PageSize]
    page_width_mm: Optional[float]
    page_height_mm: Optional[float]
    margins: Optional[Margins]
    orientation: Optional[Orientation]
    print_background: bool
    scale: float
    page_ranges: Optional[str]
    header_template: Optional[str]
    footer_template: Optional[str]
    prefer_css_page_size: bool
    embed_fonts: bool
    subset_fonts: bool
    metadata: Optional[PdfMetadata]

    def __init__(
        self,
        page_size: Optional[PageSize] = None,
        page_width_mm: Optional[float] = None,
        page_height_mm: Optional[float] = None,
        margins: Optional[Margins] = None,
        orientation: Optional[Orientation] = None,
        print_background: bool = True,
        scale: float = 1.0,
        page_ranges: Optional[str] = None,
        header_template: Optional[str] = None,
        footer_template: Optional[str] = None,
        prefer_css_page_size: bool = False,
        embed_fonts: bool = True,
        subset_fonts: bool = True,
        metadata: Optional[PdfMetadata] = None,
    ) -> None: ...

class PdfResult:
    """PDF conversion result."""

    page_count: int

    def data(self) -> bytes:
        """Get the PDF data as bytes."""
        ...
    def write_to_file(self, path: str) -> None:
        """Write PDF to file."""
        ...
    def __len__(self) -> int: ...

class ElementBoundary:
    """Element boundary in rendered PDF."""

    selector: str
    index: int
    page: int
    x: float
    y: float
    width: float
    height: float

class RendererInfo:
    """Renderer information."""

    printwell_version: str
    chromium_version: str
    skia_version: str
    build_config: str

class Converter:
    """HTML to PDF converter."""

    def __init__(self) -> None: ...
    def html_to_pdf(
        self,
        html: str,
        render_options: Optional[RenderOptions] = None,
        pdf_options: Optional[PdfOptions] = None,
    ) -> PdfResult: ...
    def url_to_pdf(
        self,
        url: str,
        render_options: Optional[RenderOptions] = None,
        pdf_options: Optional[PdfOptions] = None,
    ) -> PdfResult: ...
    def html_to_pdf_with_boundaries(
        self,
        html: str,
        selectors: List[str],
        render_options: Optional[RenderOptions] = None,
        pdf_options: Optional[PdfOptions] = None,
    ) -> Tuple[PdfResult, List[ElementBoundary]]: ...
    def info(self) -> RendererInfo: ...

class ConverterPool:
    """Converter pool for batch processing."""

    max_concurrent: int
    queued_count: int

    def __init__(self, max_concurrent: int) -> None: ...
    def convert_html(
        self,
        html: str,
        render_options: Optional[RenderOptions] = None,
        pdf_options: Optional[PdfOptions] = None,
    ) -> PdfResult: ...
    def convert_batch(self, html_list: List[str]) -> List[PdfResult]: ...

# =============================================================================
# Watermark Types
# =============================================================================

class WatermarkColor:
    """RGBA color for watermarks."""

    r: int
    g: int
    b: int
    a: int

    def __init__(self, r: int, g: int, b: int, a: int = 255) -> None: ...
    @staticmethod
    def red() -> WatermarkColor: ...
    @staticmethod
    def gray() -> WatermarkColor: ...
    @staticmethod
    def black() -> WatermarkColor: ...

class Watermark:
    """Watermark configuration."""

    text: Optional[str]
    image: Optional[bytes]
    position: Optional[WatermarkPosition]
    custom_x: Optional[float]
    custom_y: Optional[float]
    rotation: float
    opacity: float
    font_size: float
    font_name: str
    color: Optional[WatermarkColor]
    layer: WatermarkLayer
    page_selection: WatermarkPageSelectionType
    pages: Optional[List[int]]
    range_start: Optional[int]
    range_end: Optional[int]
    scale: float

    def __init__(
        self,
        text: Optional[str] = None,
        image: Optional[bytes] = None,
        position: Optional[WatermarkPosition] = None,
        custom_x: Optional[float] = None,
        custom_y: Optional[float] = None,
        rotation: float = 0.0,
        opacity: float = 0.5,
        font_size: float = 72.0,
        font_name: str = "Helvetica",
        color: Optional[WatermarkColor] = None,
        layer: WatermarkLayer = WatermarkLayer.Background,
        page_selection: WatermarkPageSelectionType = WatermarkPageSelectionType.All,
        pages: Optional[List[int]] = None,
        range_start: Optional[int] = None,
        range_end: Optional[int] = None,
        scale: float = 1.0,
    ) -> None: ...
    @staticmethod
    def text_watermark(
        text: str,
        position: Optional[WatermarkPosition] = None,
        rotation: float = 45.0,
        opacity: float = 0.3,
        font_size: float = 72.0,
        color: Optional[WatermarkColor] = None,
    ) -> Watermark: ...

# =============================================================================
# Bookmark Types
# =============================================================================

class Bookmark:
    """A bookmark (outline) entry for PDF navigation."""

    title: str
    page: int
    y_position: Optional[float]
    parent_index: int
    open: bool
    level: int

    def __init__(
        self,
        title: str,
        page: int,
        y_position: Optional[float] = None,
        parent_index: int = -1,
        open: bool = True,
        level: int = 0,
    ) -> None: ...
    @staticmethod
    def root(title: str, page: int) -> Bookmark: ...
    @staticmethod
    def child(title: str, page: int, parent_index: int) -> Bookmark: ...

# =============================================================================
# Annotation Types
# =============================================================================

class AnnotationRect:
    """Rectangle for annotation bounds."""

    x: float
    y: float
    width: float
    height: float

    def __init__(self, x: float, y: float, width: float, height: float) -> None: ...

class AnnotationColor:
    """Color for annotations."""

    r: int
    g: int
    b: int
    a: int

    def __init__(self, r: int, g: int, b: int, a: int = 255) -> None: ...
    @staticmethod
    def yellow() -> AnnotationColor: ...
    @staticmethod
    def red() -> AnnotationColor: ...
    @staticmethod
    def green() -> AnnotationColor: ...
    @staticmethod
    def blue() -> AnnotationColor: ...

class Annotation:
    """An annotation to add to a PDF."""

    annotation_type: AnnotationType
    page: int
    rect: AnnotationRect
    color: Optional[AnnotationColor]
    opacity: float
    contents: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    text: Optional[str]
    font_size: float
    points: List[Tuple[float, float]]

    def __init__(
        self,
        annotation_type: AnnotationType,
        page: int,
        rect: AnnotationRect,
        color: Optional[AnnotationColor] = None,
        opacity: float = 1.0,
        contents: Optional[str] = None,
        author: Optional[str] = None,
        subject: Optional[str] = None,
        text: Optional[str] = None,
        font_size: float = 12.0,
        points: Optional[List[Tuple[float, float]]] = None,
    ) -> None: ...
    @staticmethod
    def highlight(
        page: int,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Optional[AnnotationColor] = None,
        opacity: float = 1.0,
    ) -> Annotation: ...
    @staticmethod
    def sticky_note(
        page: int,
        x: float,
        y: float,
        contents: str,
        author: Optional[str] = None,
    ) -> Annotation: ...

class AnnotationInfo:
    """Information about an existing annotation."""

    annotation_type: AnnotationType
    page: int
    rect: AnnotationRect
    color: AnnotationColor
    opacity: float
    contents: Optional[str]
    author: Optional[str]

# =============================================================================
# Encryption Types
# =============================================================================

class Permissions:
    """PDF permission flags."""

    print: bool
    modify: bool
    copy: bool
    annotate: bool
    fill_forms: bool
    extract_accessibility: bool
    assemble: bool
    print_high_quality: bool

    def __init__(
        self,
        print: bool = True,
        modify: bool = True,
        copy: bool = True,
        annotate: bool = True,
        fill_forms: bool = True,
        extract_accessibility: bool = True,
        assemble: bool = True,
        print_high_quality: bool = True,
    ) -> None: ...
    @staticmethod
    def all() -> Permissions: ...
    @staticmethod
    def none() -> Permissions: ...
    @staticmethod
    def print_only() -> Permissions: ...

class EncryptionOptions:
    """Options for PDF encryption."""

    owner_password: str
    user_password: Optional[str]
    permissions: Permissions
    algorithm: EncryptionAlgorithm
    encrypt_metadata: bool

    def __init__(
        self,
        owner_password: str,
        user_password: Optional[str] = None,
        permissions: Optional[Permissions] = None,
        algorithm: Optional[EncryptionAlgorithm] = None,
        encrypt_metadata: bool = True,
    ) -> None: ...

# =============================================================================
# PDF/A Types
# =============================================================================

class PdfAIssue:
    """A PDF/A compliance issue."""

    severity: PdfAIssueSeverity
    category: PdfAIssueCategory
    message: str
    clause: Optional[str]
    page: Optional[int]

class PdfAValidationResult:
    """Result of PDF/A validation."""

    level: PdfALevel
    is_compliant: bool
    issues: List[PdfAIssue]
    error_count: int
    warning_count: int

    def passed(self) -> bool: ...

# =============================================================================
# PDF/UA Types
# =============================================================================

class PdfUAIssue:
    """A PDF/UA compliance issue."""

    severity: PdfUAIssueSeverity
    category: PdfUAIssueCategory
    description: str
    page: int
    clause: Optional[str]
    suggestion: Optional[str]

class PdfUAValidationResult:
    """Result of PDF/UA validation."""

    level: PdfUALevel
    is_compliant: bool
    issues: List[PdfUAIssue]
    pages_checked: int
    tagged_elements: int

    def error_count(self) -> int: ...
    def warning_count(self) -> int: ...

class AccessibilityOptions:
    """Accessibility options for PDF/UA."""

    language: str
    title: str
    generate_placeholder_alt: bool
    include_reading_order: bool
    generate_outline: bool

    def __init__(
        self,
        language: str = "en",
        title: str = "",
        generate_placeholder_alt: bool = False,
        include_reading_order: bool = True,
        generate_outline: bool = True,
    ) -> None: ...

# =============================================================================
# Signing Types
# =============================================================================

class SigningOptions:
    """Options for signing a PDF."""

    reason: Optional[str]
    location: Optional[str]
    contact_info: Optional[str]
    signature_level: SignatureLevel
    timestamp_url: Optional[str]
    field_name: str
    include_chain: bool
    certify: bool
    mdp_permissions: MdpPermissions

    def __init__(
        self,
        reason: Optional[str] = None,
        location: Optional[str] = None,
        contact_info: Optional[str] = None,
        signature_level: Optional[SignatureLevel] = None,
        timestamp_url: Optional[str] = None,
        field_name: str = "Signature",
        include_chain: bool = True,
        certify: bool = False,
        mdp_permissions: Optional[MdpPermissions] = None,
    ) -> None: ...

class SignatureAppearance:
    """Visible signature appearance settings."""

    page: int
    x: float
    y: float
    width: float
    height: float
    show_name: bool
    show_date: bool
    show_reason: bool
    background_image: Optional[bytes]

    def __init__(
        self,
        page: int = 1,
        x: float = 50.0,
        y: float = 50.0,
        width: float = 200.0,
        height: float = 75.0,
        show_name: bool = True,
        show_date: bool = True,
        show_reason: bool = True,
        background_image: Optional[bytes] = None,
    ) -> None: ...

class SignatureVerification:
    """Signature verification result."""

    signer_name: str
    signing_time: Optional[str]
    reason: Optional[str]
    location: Optional[str]
    is_valid: bool
    covers_whole_document: bool
    cert_time_valid: bool
    cert_usage_valid: bool
    cert_warnings: List[str]
    error: Optional[str]

class ExtractedSignature:
    """Extracted signature info from a PDF."""

    sub_filter: str
    reason: Optional[str]
    location: Optional[str]
    signing_time: Optional[str]
    signer_name: Optional[str]

# =============================================================================
# Form Field Types
# =============================================================================

class FormRect:
    """Rectangle for form field positioning."""

    x: float
    y: float
    width: float
    height: float

    def __init__(self, x: float, y: float, width: float, height: float) -> None: ...

class TextField:
    """Text field definition."""

    name: str
    page: int
    rect: FormRect
    default_value: Optional[str]
    max_length: Optional[int]
    multiline: bool
    password: bool
    required: bool
    read_only: bool
    font_size: float
    font_name: str

    def __init__(
        self,
        name: str,
        page: int,
        rect: FormRect,
        default_value: Optional[str] = None,
        max_length: Optional[int] = None,
        multiline: bool = False,
        password: bool = False,
        required: bool = False,
        read_only: bool = False,
        font_size: float = 12.0,
        font_name: Optional[str] = None,
    ) -> None: ...

class FormCheckbox:
    """Checkbox field definition."""

    name: str
    page: int
    rect: FormRect
    checked: bool
    export_value: str

    def __init__(
        self,
        name: str,
        page: int,
        rect: FormRect,
        checked: bool = False,
        export_value: Optional[str] = None,
    ) -> None: ...

class FormDropdown:
    """Dropdown field definition."""

    name: str
    page: int
    rect: FormRect
    options: List[str]
    selected_index: Optional[int]
    editable: bool

    def __init__(
        self,
        name: str,
        page: int,
        rect: FormRect,
        options: List[str],
        selected_index: Optional[int] = None,
        editable: bool = False,
    ) -> None: ...

class FormSignatureField:
    """Signature field definition."""

    name: str
    page: int
    rect: FormRect

    def __init__(self, name: str, page: int, rect: FormRect) -> None: ...

class ValidationRule:
    """Validation rule for a form field."""

    field_name: str
    required: bool
    pattern: Optional[str]
    min_length: Optional[int]
    max_length: Optional[int]
    min_value: Optional[float]
    max_value: Optional[float]
    required_message: Optional[str]
    pattern_message: Optional[str]
    length_message: Optional[str]
    value_message: Optional[str]
    allowed_values: Optional[List[str]]

    def __init__(
        self,
        field_name: str,
        required: bool = False,
        pattern: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        required_message: Optional[str] = None,
        pattern_message: Optional[str] = None,
        length_message: Optional[str] = None,
        value_message: Optional[str] = None,
        allowed_values: Optional[List[str]] = None,
    ) -> None: ...

class FormValidationResult:
    """Result of validating a single form field."""

    field_name: str
    is_valid: bool
    errors: List[str]
    value: Optional[str]

class FormValidationSummary:
    """Summary of all form validation results."""

    total_fields: int
    valid_count: int
    invalid_count: int
    all_valid: bool
    results: List[FormValidationResult]

class FormElementInput:
    """Form element for validation."""

    element_type: str
    id: Optional[str]
    name: str
    default_value: Optional[str]
    required: bool
    checked: bool

    def __init__(
        self,
        name: str,
        element_type: str = "text",
        id: Optional[str] = None,
        default_value: Optional[str] = None,
        required: bool = False,
        checked: bool = False,
    ) -> None: ...

# =============================================================================
# Convenience Functions
# =============================================================================

def html_to_pdf(
    html: str,
    render_options: Optional[RenderOptions] = None,
    pdf_options: Optional[PdfOptions] = None,
) -> PdfResult:
    """Convert HTML to PDF (convenience function)."""
    ...

def url_to_pdf(
    url: str,
    render_options: Optional[RenderOptions] = None,
    pdf_options: Optional[PdfOptions] = None,
) -> PdfResult:
    """Convert URL to PDF (convenience function)."""
    ...

# =============================================================================
# Watermark Functions
# =============================================================================

def add_watermark(pdf_data: bytes, watermark: Watermark) -> bytes:
    """Add a watermark to existing PDF data."""
    ...

def add_watermarks(pdf_data: bytes, watermarks: List[Watermark]) -> bytes:
    """Add multiple watermarks to existing PDF data."""
    ...

# =============================================================================
# Bookmark Functions
# =============================================================================

def add_bookmarks(pdf_data: bytes, bookmarks: List[Bookmark]) -> bytes:
    """Add bookmarks (outline) to existing PDF data."""
    ...

def extract_bookmarks(pdf_data: bytes) -> List[Bookmark]:
    """Extract bookmarks from existing PDF data."""
    ...

# =============================================================================
# Annotation Functions
# =============================================================================

def add_annotations(pdf_data: bytes, annotations: List[Annotation]) -> bytes:
    """Add annotations to existing PDF data."""
    ...

def list_annotations(pdf_data: bytes) -> List[AnnotationInfo]:
    """List annotations in PDF data."""
    ...

def remove_annotations(
    pdf_data: bytes,
    page: Optional[int] = None,
    annotation_types: Optional[List[AnnotationType]] = None,
) -> bytes:
    """Remove annotations from PDF data."""
    ...

# =============================================================================
# Encryption Functions
# =============================================================================

def encrypt_pdf(pdf_data: bytes, options: EncryptionOptions) -> bytes:
    """Encrypt a PDF document with password protection."""
    ...

def decrypt_pdf(pdf_data: bytes, password: str) -> bytes:
    """Decrypt a password-protected PDF document."""
    ...

# =============================================================================
# PDF/A Functions
# =============================================================================

def validate_pdfa(pdf_data: bytes, level: PdfALevel) -> PdfAValidationResult:
    """Validate a PDF against PDF/A requirements."""
    ...

def add_pdfa_metadata(
    pdf_data: bytes,
    level: PdfALevel,
    title: Optional[str] = None,
    author: Optional[str] = None,
) -> bytes:
    """Add PDF/A metadata to a PDF."""
    ...

# =============================================================================
# PDF/UA Functions
# =============================================================================

def validate_pdfua(pdf_data: bytes, level: PdfUALevel) -> PdfUAValidationResult:
    """Validate a PDF for PDF/UA compliance."""
    ...

def add_pdfua_metadata(
    pdf_data: bytes,
    level: PdfUALevel,
    options: Optional[AccessibilityOptions] = None,
) -> bytes:
    """Add PDF/UA metadata to an existing PDF."""
    ...

# =============================================================================
# Signing Functions
# =============================================================================

def sign_pdf(
    pdf_data: bytes,
    cert_data: bytes,
    cert_password: str,
    options: Optional[SigningOptions] = None,
) -> bytes:
    """Sign a PDF document with an invisible signature."""
    ...

def sign_pdf_visible(
    pdf_data: bytes,
    cert_data: bytes,
    cert_password: str,
    options: Optional[SigningOptions] = None,
    appearance: Optional[SignatureAppearance] = None,
) -> bytes:
    """Sign a PDF document with a visible signature."""
    ...

def verify_signatures(pdf_data: bytes) -> List[SignatureVerification]:
    """Verify all signatures in a PDF."""
    ...

def verify_signatures_with_system_trust(pdf_data: bytes) -> List[SignatureVerification]:
    """Verify all signatures in a PDF using the system trust store."""
    ...

def extract_pdf_signatures(pdf_data: bytes) -> List[ExtractedSignature]:
    """Extract all signatures from a PDF (without verification)."""
    ...

# =============================================================================
# Form Functions
# =============================================================================

def add_form_fields(
    pdf_data: bytes,
    text_fields: Optional[List[TextField]] = None,
    checkboxes: Optional[List[FormCheckbox]] = None,
    dropdowns: Optional[List[FormDropdown]] = None,
    signature_fields: Optional[List[FormSignatureField]] = None,
) -> bytes:
    """Add form fields to a PDF document."""
    ...

def validate_form_fields(
    elements: List[FormElementInput],
    rules: List[ValidationRule],
) -> FormValidationSummary:
    """Validate form elements against rules."""
    ...
