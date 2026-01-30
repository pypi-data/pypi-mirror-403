"""
Hybrid PDF Processor - Gemini-style document processing

Architecture:
- Ingest once: analyze, extract, index
- Query many: retrieve relevant pages/chunks per question
- VLM selective: only for pages needing visual understanding

References:
- ColPali (arXiv:2407.01449) - Vision-based document retrieval
- VisRAG (arXiv:2410.10594) - Vision RAG, ICLR 2025
- VDocRAG (arXiv:2504.09795) - Document RAG, CVPR 2025
- Gemini PDF processing (native vision + file caching)

Integration with MLX-VLM:
- Uses generate() for VLM-based OCR when needed
- Leverages existing vision cache for repeated pages
"""

import fitz  # PyMuPDF
import hashlib
import json
import re
import tempfile
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union, Iterator
import time


# =============================================================================
# Configuration
# =============================================================================

class MediaResolution(Enum):
    """
    Controls token budget per page (mirrors Gemini's media_resolution).

    Token counts verified against Gemini API documentation (Jan 2026):
    - LOW:  280 tokens per page (fast, cost-effective)
    - MED:  560 tokens per page (balanced, default)
    - HIGH: 1120 tokens per page (maximum detail)

    Note: Gemini uses 258 tokens per PDF page at default resolution.
    """
    LOW = "low"      # 72 DPI, max 768px  → ~280 tokens
    MED = "medium"   # 150 DPI, max 1536px → ~560 tokens
    HIGH = "high"    # 200 DPI, max 3072px → ~1120 tokens


# Token estimates aligned with Gemini API (verified Jan 2026)
# Source: https://ai.google.dev/gemini-api/docs/gemini-3
RESOLUTION_CONFIG = {
    MediaResolution.LOW:  {"dpi": 72,  "max_dim": 768,  "tokens_est": 280},
    MediaResolution.MED:  {"dpi": 150, "max_dim": 1536, "tokens_est": 560},
    MediaResolution.HIGH: {"dpi": 200, "max_dim": 3072, "tokens_est": 1120},
}


class PageType(Enum):
    """Classification of PDF page content."""
    TEXT_NATIVE = "text_native"      # Has extractable text - use PyMuPDF
    SCANNED = "scanned"              # Image-based - needs VLM OCR
    MIXED = "mixed"                  # Text + significant images
    COMPLEX_TABLE = "complex_table"  # Complex layout - VLM recommended


class DocumentType(Enum):
    """Type of document being processed."""
    PDF = "pdf"                      # PDF file (default)
    IMAGE_COLLECTION = "image_collection"  # Directory of images
    TEXT = "text"                    # Plain text or markdown file


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PageAnalysis:
    """Analysis result for a single PDF page."""
    page_num: int
    page_type: PageType
    char_count: int
    text_coverage: float
    has_images: bool
    image_count: int
    image_area_ratio: float
    has_tables: bool
    needs_vlm: bool
    confidence: float

    def to_dict(self) -> dict:
        d = asdict(self)
        d['page_type'] = self.page_type.value
        return d


@dataclass
class PageData:
    """Processed data for a single page."""
    page_num: int
    page_type: str
    native_text: str
    summary: str = ""
    image_path: Optional[str] = None  # Path to rendered image (if needed)
    vlm_text: Optional[str] = None    # VLM-extracted text (if processed)
    embedding: Optional[List[float]] = None
    image_captions: List[dict] = field(default_factory=list)  # Embedded image captions
    # Each caption dict:
    # {
    #     "figure_label": "Figure 1" or None,
    #     "caption": "This diagram shows the Transformer architecture...",
    #     "surrounding_context": "...stacked self-attention layers...",
    #     "bbox": (x0, y0, x1, y1),
    #     "image_path": "/cache/embedded_images/page_0003_img_00.png"
    # }

    def get_text(self) -> str:
        """Get best available text for this page."""
        return self.vlm_text or self.native_text


@dataclass
class DocumentPack:
    """
    Complete document representation (cached between turns).

    This is what Gemini does with file_id - we cache all artifacts.
    Supports multiple document types: PDF, image collection, text.
    """
    file_id: str
    file_path: str
    file_name: str
    total_pages: int
    created_at: str

    # Document type (pdf, image_collection, text)
    document_type: str = "pdf"  # Default for backward compatibility

    # Page data
    pages: List[PageData] = field(default_factory=list)
    analyses: List[dict] = field(default_factory=list)

    # Statistics
    native_pages: int = 0
    vlm_pages: int = 0

    # Index data (for retrieval)
    chunks: List[dict] = field(default_factory=list)  # {text, page_num, start, end}

    # Visual content detection (for auto-routing to VLM)
    visual_pages: List[int] = field(default_factory=list)  # Pages with significant images/diagrams

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "total_pages": self.total_pages,
            "created_at": self.created_at,
            "document_type": self.document_type,
            "native_pages": self.native_pages,
            "vlm_pages": self.vlm_pages,
            "pages": [asdict(p) for p in self.pages],
            "analyses": self.analyses,
            "chunks": self.chunks,
            "visual_pages": self.visual_pages,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'DocumentPack':
        pages = [PageData(**p) for p in d.pop('pages', [])]
        visual_pages = d.pop('visual_pages', [])
        document_type = d.pop('document_type', 'pdf')  # Default for backward compatibility
        return cls(**d, pages=pages, visual_pages=visual_pages, document_type=document_type)


@dataclass
class QueryResult:
    """Result from querying a document."""
    answer: str
    sources: List[dict]  # [{page_num, text_snippet, relevance}]
    pages_used: List[int]
    method: str  # "text_only", "text_with_vision", "vision_only"
    timing: dict


# =============================================================================
# Page Analysis Functions
# =============================================================================

def analyze_page(page: fitz.Page, page_num: int) -> PageAnalysis:
    """
    Analyze a PDF page to determine optimal processing strategy.

    Classification logic:
    1. Extract native text and measure coverage
    2. Detect and measure image content
    3. Identify table structures
    4. Classify based on thresholds
    """
    rect = page.rect
    page_area = rect.width * rect.height if rect.width > 0 and rect.height > 0 else 1

    # Extract native text
    native_text = page.get_text("text").strip()
    char_count = len(native_text)

    # Get text blocks for coverage
    text_blocks = page.get_text("blocks")
    text_area = sum(
        (b[2] - b[0]) * (b[3] - b[1])
        for b in text_blocks if len(b) > 5 and b[6] == 0
    )
    text_coverage = min(1.0, text_area / page_area)

    # Analyze images
    images = page.get_images(full=True)
    image_count = len(images)

    # Calculate image area
    image_area = 0
    for img in images:
        try:
            img_rect = page.get_image_bbox(img[0])
            if img_rect:
                image_area += abs(img_rect.width * img_rect.height)
        except:
            pass
    image_area_ratio = min(1.0, image_area / page_area)

    # Detect tables
    has_tables = _detect_tables(text_blocks)

    # Classify
    page_type, needs_vlm, confidence = _classify_page(
        char_count=char_count,
        text_coverage=text_coverage,
        image_count=image_count,
        image_area_ratio=image_area_ratio,
        has_tables=has_tables
    )

    return PageAnalysis(
        page_num=page_num,
        page_type=page_type,
        char_count=char_count,
        text_coverage=text_coverage,
        has_images=image_count > 0,
        image_count=image_count,
        image_area_ratio=image_area_ratio,
        has_tables=has_tables,
        needs_vlm=needs_vlm,
        confidence=confidence
    )


def _detect_tables(text_blocks: List) -> bool:
    """Detect table-like structures using alignment heuristics."""
    if len(text_blocks) < 6:
        return False

    x_positions = [round(b[0], -1) for b in text_blocks if len(b) > 5 and b[6] == 0]
    if len(x_positions) < 4:
        return False

    x_counts = Counter(x_positions)
    columns_with_multiple = sum(1 for count in x_counts.values() if count >= 2)
    return columns_with_multiple >= 3


def has_significant_visual_content(page: fitz.Page, analysis: PageAnalysis) -> bool:
    """
    Detect if page has significant visual content requiring VLM for understanding.

    This is separate from needs_vlm (which handles scanned/mixed pages).
    A TEXT_NATIVE page can still have important diagrams/charts that
    need VLM to answer visual questions.

    Criteria:
    - Image area > 20% of page area (significant image coverage)
    - More than 5 distinct images (photo gallery, collage)
    - Complex vector drawings (>50 drawing paths) - likely diagram/chart
    - Figure labels detected ("Figure X", "Fig. X") - explicit figure reference
    """
    # Check image coverage from existing analysis
    if analysis.image_area_ratio > 0.20:
        return True

    # Check image count (multiple images suggests visual-heavy content)
    if analysis.image_count > 5:
        return True

    # Check for vector drawings (diagrams, charts, flowcharts)
    # Lowered threshold from 100 to 50 for simpler diagrams
    try:
        drawings = page.get_drawings()
        if len(drawings) > 50:  # Vector paths = likely diagram
            return True
    except:
        pass

    # Check for figure labels in page text (most reliable for academic papers)
    # Patterns like "Figure 1:", "Figure 1.", "Fig. 1:", "Fig 1."
    try:
        text = page.get_text()
        # Look for figure captions - these indicate significant visual content
        import re
        figure_pattern = r'(?:Figure|Fig\.?)\s*\d+\s*[:\.]'
        if re.search(figure_pattern, text, re.IGNORECASE):
            return True
    except:
        pass

    return False


def is_visual_question(question: str) -> bool:
    """
    Detect if a question is asking about visual content.

    This provides query-level filtering to avoid routing text questions
    to VLM just because the page has some images.
    """
    question_lower = question.lower()

    # Keywords that indicate visual questions
    visual_keywords = [
        # Direct visual references
        'image', 'images', 'picture', 'pictures', 'photo', 'photos',
        'diagram', 'diagrams', 'chart', 'charts', 'graph', 'graphs',
        'figure', 'figures', 'illustration', 'illustrations',
        'drawing', 'drawings', 'sketch', 'sketches',
        'visual', 'visually', 'shown', 'depicted', 'depict',
        'display', 'displayed', 'appear', 'appears', 'look',
        # Layout/spatial questions
        'layout', 'arranged', 'positioned',
        # Color/style questions
        'color', 'colours', 'colored',
    ]

    for keyword in visual_keywords:
        if keyword in question_lower:
            return True

    return False


def _classify_page(
    char_count: int,
    text_coverage: float,
    image_count: int,
    image_area_ratio: float,
    has_tables: bool
) -> Tuple[PageType, bool, float]:
    """Classify page and determine if VLM is needed."""

    MIN_CHARS = 50
    MIN_COVERAGE = 0.05
    HIGH_IMAGE_RATIO = 0.3

    # Good native text, no significant images
    if char_count >= MIN_CHARS and text_coverage >= MIN_COVERAGE:
        if image_area_ratio < HIGH_IMAGE_RATIO:
            return (PageType.TEXT_NATIVE, False, 0.90 if not has_tables else 0.85)
        else:
            return (PageType.MIXED, True, 0.80)

    # Little/no native text
    if char_count < MIN_CHARS:
        if image_count > 0 or image_area_ratio > 0.1:
            return (PageType.SCANNED, True, 0.90)
        else:
            return (PageType.TEXT_NATIVE, False, 0.70)  # Empty page

    # Complex layout
    if has_tables and text_coverage < 0.2:
        return (PageType.COMPLEX_TABLE, True, 0.75)

    return (PageType.TEXT_NATIVE, False, 0.60)


# =============================================================================
# Text Extraction Functions
# =============================================================================

def extract_native_text(page: fitz.Page, format: str = "markdown") -> str:
    """Extract text from PDF page using PyMuPDF."""
    if format == "text":
        return page.get_text("text")
    elif format == "markdown":
        return _extract_markdown(page)
    elif format == "html":
        return page.get_text("html")
    else:
        return page.get_text("text")


def _extract_markdown(page: fitz.Page) -> str:
    """Extract text with basic markdown formatting."""
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

    lines = []
    base_size = _get_base_font_size(blocks)

    for block in blocks:
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            text_parts = []
            line_size = 0

            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue

                size = span.get("size", 12)
                line_size = max(line_size, size)
                flags = span.get("flags", 0)

                # Apply formatting
                if flags & 2**1:  # Italic
                    text = f"*{text}*"
                if flags & 2**4:  # Bold
                    text = f"**{text}**"

                text_parts.append(text)

            line_text = " ".join(text_parts)
            if not line_text:
                continue

            # Detect headings
            if line_size > base_size * 1.5:
                line_text = f"## {line_text}"
            elif line_size > base_size * 1.2:
                line_text = f"### {line_text}"

            # Detect list items
            stripped = line_text.lstrip()
            if stripped.startswith(("•", "●", "○", "■", "–", "—")):
                line_text = f"- {stripped[1:].strip()}"

            lines.append(line_text)

    return "\n".join(lines)


def _get_base_font_size(blocks: List) -> float:
    """Determine most common font size."""
    sizes = []
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                sizes.append(round(span.get("size", 12)))

    if not sizes:
        return 12.0

    return float(Counter(sizes).most_common(1)[0][0])


def normalize_text(text: str) -> str:
    """
    Normalize text by fixing common PDF extraction issues.

    - Removes hyphenation at line breaks (e.g., "tacti-\\ncal" -> "tactical")
    - Collapses multiple whitespace to single space
    - Preserves paragraph breaks (double newlines)
    """
    import re

    # Fix hyphenated line breaks: word-\n continuation -> word continuation
    # Pattern: lowercase letter, hyphen, newline, lowercase letter
    text = re.sub(r'([a-z])-\n([a-z])', r'\1\2', text)

    # Also handle hyphen followed by space+newline or just spaces
    text = re.sub(r'([a-z])-\s*\n\s*([a-z])', r'\1\2', text)

    # Collapse multiple spaces to single space (but preserve newlines)
    text = re.sub(r'[ \t]+', ' ', text)

    # Collapse more than 2 newlines to 2 (paragraph separator)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


# =============================================================================
# Page Rendering Functions
# =============================================================================

def render_page_to_image(
    page: fitz.Page,
    resolution: MediaResolution = MediaResolution.MED,
    output_path: Optional[str] = None
) -> str:
    """
    Render PDF page to image at specified resolution.

    Args:
        page: PyMuPDF page object
        resolution: LOW/MED/HIGH controls DPI and max dimensions
        output_path: Optional output path (generates temp file if None)

    Returns:
        Path to rendered image
    """
    config = RESOLUTION_CONFIG[resolution]
    dpi = config["dpi"]
    max_dim = config["max_dim"]

    # Calculate scale
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    # Resize if needed
    if max(pix.width, pix.height) > max_dim:
        scale = max_dim / max(pix.width, pix.height)
        new_mat = fitz.Matrix(dpi / 72 * scale, dpi / 72 * scale)
        pix = page.get_pixmap(matrix=new_mat)

    # Save
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".png")

    pix.save(output_path)
    return output_path


# =============================================================================
# Embedded Image Extraction Functions
# =============================================================================

def extract_embedded_images(
    doc: fitz.Document,
    page: fitz.Page,
    page_num: int,
    output_dir: Path,
    min_size: int = 100,  # Skip images smaller than 100x100
    min_area_ratio: float = 0.02,  # Skip images < 2% of page area
) -> List[dict]:
    """
    Extract significant embedded images from a PDF page.

    Filters out small images (icons, bullets) based on size and page area ratio.
    Saves extracted images to output_dir.

    Args:
        doc: PyMuPDF Document object
        page: PyMuPDF Page object
        page_num: 1-based page number
        output_dir: Directory to save extracted images
        min_size: Minimum width/height in pixels (default: 100)
        min_area_ratio: Minimum fraction of page area (default: 0.02 = 2%)

    Returns:
        List of dicts with keys:
        - xref: Image reference ID
        - path: Path to saved image file
        - bbox: (x0, y0, x1, y1) bounding box on page
        - width, height: Image dimensions
        - area_ratio: Fraction of page area
    """
    page_rect = page.rect
    page_area = page_rect.width * page_rect.height if page_rect.width > 0 and page_rect.height > 0 else 1

    images = page.get_images(full=True)
    extracted = []

    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for img_index, img in enumerate(images):
        xref = img[0]

        try:
            # Get image info
            base_image = doc.extract_image(xref)
            if not base_image:
                continue

            img_bytes = base_image["image"]
            img_ext = base_image["ext"]
            width = base_image["width"]
            height = base_image["height"]

            # Filter: too small dimensions
            if width < min_size or height < min_size:
                continue

            # Get bounding box on page
            # Note: get_image_bbox can return multiple rects if image appears multiple times
            try:
                bbox_list = page.get_image_rects(xref)
                if not bbox_list:
                    continue
                bbox = bbox_list[0]  # Take first occurrence
            except Exception:
                # Fallback to older API
                bbox = page.get_image_bbox(xref)
                if not bbox:
                    continue

            # Filter: too small area ratio
            img_area = abs(bbox.width * bbox.height)
            area_ratio = img_area / page_area
            if area_ratio < min_area_ratio:
                continue

            # Save image
            img_path = output_dir / f"page_{page_num:04d}_img_{img_index:02d}.{img_ext}"
            img_path.write_bytes(img_bytes)

            extracted.append({
                "xref": xref,
                "path": str(img_path),
                "bbox": (bbox.x0, bbox.y0, bbox.x1, bbox.y1),
                "width": width,
                "height": height,
                "area_ratio": area_ratio,
            })

        except Exception as e:
            # Skip problematic images (corrupted, unsupported format, etc.)
            continue

    return extracted


def extract_vector_figures(
    page: fitz.Page,
    page_num: int,
    output_dir: Path,
    min_paths: int = 50,  # Minimum vector paths to consider a figure
    min_area_ratio: float = 0.05,  # Minimum 5% of page area
    render_scale: float = 2.0,  # Render at 2x for quality
) -> List[dict]:
    """
    Extract vector graphics figures (charts, graphs, diagrams) from a PDF page.

    Many figures in academic papers (especially charts and graphs from matplotlib,
    R, or LaTeX) are vector graphics, not embedded raster images. This function
    detects regions with significant vector drawing paths and renders them.

    Args:
        page: PyMuPDF Page object
        page_num: 1-based page number
        output_dir: Directory to save rendered images
        min_paths: Minimum number of drawing paths to consider a figure (default: 50)
        min_area_ratio: Minimum fraction of page area (default: 0.05 = 5%)
        render_scale: Scale factor for rendering (default: 2.0 for quality)

    Returns:
        List of dicts with keys:
        - path: Path to rendered image file
        - bbox: (x0, y0, x1, y1) bounding box of the drawing region (for label detection)
        - area_ratio: Fraction of page area
        - path_count: Number of vector paths in the region
        - is_vector: True (to distinguish from raster images)
    """
    page_rect = page.rect
    page_area = page_rect.width * page_rect.height if page_rect.width > 0 and page_rect.height > 0 else 1

    drawings = page.get_drawings()
    if len(drawings) < min_paths:
        return []

    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find bounding box of all drawings
    # Filter out very small decorative elements
    significant_drawings = [d for d in drawings if d['rect'].width > 5 and d['rect'].height > 5]
    if len(significant_drawings) < min_paths:
        return []

    min_x = min(d['rect'].x0 for d in significant_drawings)
    min_y = min(d['rect'].y0 for d in significant_drawings)
    max_x = max(d['rect'].x1 for d in significant_drawings)
    max_y = max(d['rect'].y1 for d in significant_drawings)

    drawing_rect = fitz.Rect(min_x, min_y, max_x, max_y)
    drawing_area = drawing_rect.width * drawing_rect.height
    area_ratio = drawing_area / page_area

    if area_ratio < min_area_ratio:
        return []

    extracted = []

    try:
        # Add margin around the drawing region and space for caption below
        margin = 10
        caption_space = 80  # Space for figure caption in rendered image
        clip = fitz.Rect(
            max(page_rect.x0, drawing_rect.x0 - margin),
            max(page_rect.y0, drawing_rect.y0 - margin),
            min(page_rect.x1, drawing_rect.x1 + margin),
            min(page_rect.y1, drawing_rect.y1 + caption_space)
        )

        # Render the region
        mat = fitz.Matrix(render_scale, render_scale)
        pix = page.get_pixmap(matrix=mat, clip=clip)

        img_path = output_dir / f"page_{page_num:04d}_vector_00.png"
        pix.save(str(img_path))

        # Return the DRAWING bbox (not clip bbox) for label detection
        # The drawing_rect is where the actual figure is - labels are searched
        # relative to this, not the expanded clip region
        extracted.append({
            "path": str(img_path),
            "bbox": (drawing_rect.x0, drawing_rect.y0, drawing_rect.x1, drawing_rect.y1),
            "width": pix.width,
            "height": pix.height,
            "area_ratio": area_ratio,
            "path_count": len(significant_drawings),
            "is_vector": True,
        })

    except Exception as e:
        # Skip on error
        pass

    return extracted


def find_figure_label(
    page: fitz.Page,
    bbox: tuple,
    search_margin: float = 80,  # pixels above/below image (increased for varied layouts)
) -> Optional[str]:
    """
    Search for 'Figure X' or 'Fig. X' labels near an image.

    Searches in multiple regions:
    1. Below the image (full page width for multi-column shared captions)
    2. Above the image
    3. Inside the image bbox (for vector figures with embedded captions)
    4. Bottom portion of the image (captions often at bottom of figure)

    Args:
        page: PyMuPDF Page object
        bbox: Image bounding box as (x0, y0, x1, y1)
        search_margin: Pixels to search above/below the image

    Returns:
        Label string like "Figure 1" or None if not found.
    """
    x0, y0, x1, y1 = bbox
    page_rect = page.rect

    # Search regions in priority order:
    # 1. Below image (full page width to handle multi-column shared captions)
    # 2. Bottom portion of image FULL WIDTH (captions may be in margin but at figure's Y level)
    # 3. Inside image bbox (for vector figures with embedded captions)
    # 4. Above image (narrower, just around the image)
    height = y1 - y0
    search_regions = [
        fitz.Rect(page_rect.x0, y1, page_rect.x1, y1 + search_margin),  # Below, full width
        fitz.Rect(page_rect.x0, y1 - height * 0.15, page_rect.x1, y1 + 10),  # Bottom 15% + margin, FULL WIDTH
        fitz.Rect(x0, y0, x1, y1),  # Inside entire bbox
        fitz.Rect(x0 - 20, y0 - search_margin, x1 + 20, y0),  # Above, narrow
    ]

    # Pattern to match "Figure 1", "Fig. 2", "FIGURE 3", etc.
    figure_pattern = re.compile(r'(Figure|Fig\.?)\s*(\d+)', re.IGNORECASE)

    for region in search_regions:
        # Clip region to page bounds
        region = region & page_rect
        if region.is_empty:
            continue

        text = page.get_text("text", clip=region)
        match = figure_pattern.search(text)
        if match:
            return f"Figure {match.group(2)}"

    return None


def extract_figure_context(
    page: fitz.Page,
    bbox: tuple,
    context_chars: int = 200,
) -> str:
    """
    Extract text surrounding a figure for context grounding.

    This helps the VLM understand what the figure is about,
    even without a formal caption in the document.

    Per NVIDIA/Vespa research recommendations, surrounding text context
    improves VLM understanding and caption quality.

    Args:
        page: PyMuPDF Page object
        bbox: Image bounding box as (x0, y0, x1, y1)
        context_chars: Number of characters to extract before/after (default: 200)

    Returns:
        Combined context string from before and after the figure.
    """
    x0, y0, x1, y1 = bbox
    page_rect = page.rect

    # Region above the figure (text that leads into it)
    above_region = fitz.Rect(
        page_rect.x0, max(page_rect.y0, y0 - 100),
        page_rect.x1, y0
    )

    # Region below the figure (text that follows)
    below_region = fitz.Rect(
        page_rect.x0, y1,
        page_rect.x1, min(page_rect.y1, y1 + 100)
    )

    above_text = page.get_text("text", clip=above_region).strip()
    below_text = page.get_text("text", clip=below_region).strip()

    # Take last N chars from above, first N chars from below
    above_context = above_text[-context_chars:] if above_text else ""
    below_context = below_text[:context_chars] if below_text else ""

    # Clean up partial words at boundaries
    if above_context and not above_context[0].isupper():
        # Find first space and trim partial word
        space_idx = above_context.find(' ')
        if space_idx > 0:
            above_context = above_context[space_idx+1:]

    if below_context and below_context:
        # Find last space and trim partial word at end
        last_space = below_context.rfind(' ')
        if last_space > context_chars * 0.8:  # Only trim if near the end
            below_context = below_context[:last_space]

    # Combine contexts
    parts = []
    if above_context:
        parts.append(above_context)
    if below_context:
        parts.append(below_context)

    return " [...] ".join(parts) if parts else ""


# =============================================================================
# Chunking Functions (for RAG)
# =============================================================================

def chunk_text(
    text: str,
    page_num: int,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[dict]:
    """
    Split text into overlapping chunks for retrieval.

    Returns list of {text, page_num, start_char, end_char}
    """
    # Normalize text to fix hyphenated line breaks (e.g., "tacti-\ncal" -> "tactical")
    text = normalize_text(text)

    if not text or len(text) <= chunk_size:
        return [{"text": text, "page_num": page_num, "start": 0, "end": len(text)}]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at sentence/paragraph boundary
        if end < len(text):
            for sep in ['\n\n', '\n', '. ', ', ']:
                last_sep = text[start:end].rfind(sep)
                if last_sep > chunk_size // 2:
                    end = start + last_sep + len(sep)
                    break

        chunks.append({
            "text": text[start:end].strip(),
            "page_num": page_num,
            "start": start,
            "end": end
        })

        # Ensure we always make forward progress
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 1
        start = next_start

        # Stop if we've reached the end
        if end >= len(text):
            break

    return chunks


def extract_atoms_from_page(page) -> List[dict]:
    """
    Extract structure-aware atoms from a PyMuPDF page.

    Atoms are the smallest semantic units that should never be split:
    - Headings (larger font or bold)
    - List items (bullet points, numbered)
    - Paragraphs (regular text blocks)
    - Bold-lead paragraphs (like "Empathy. Description...")

    Returns:
        List of atom dicts with text, kind, is_hard_boundary, start_char, end_char
    """
    page_dict = page.get_text("dict")
    atoms = []
    char_pos = 0

    for block in page_dict.get('blocks', []):
        if block.get('type') != 0:  # Skip non-text blocks (images)
            continue

        # Extract text and font info from block
        text_parts = []
        sizes = set()
        flags_set = set()
        has_bold_lead = False

        for line in block.get('lines', []):
            for span in line.get('spans', []):
                text_parts.append(span['text'])
                sizes.add(round(span['size'], 1))
                flags_set.add(span['flags'])
                # Check if first span is bold (flags & 16 or flags == 20)
                if not has_bold_lead and len(text_parts) == 1:
                    has_bold_lead = (span['flags'] & 16) or span['flags'] == 20

        full_text = ' '.join(text_parts).strip()
        if not full_text or len(full_text) < 5:
            continue

        # Skip headers/footers (usually at very top/bottom with small font)
        bbox = block.get('bbox', (0, 0, 0, 0))
        y_pos = bbox[1]
        page_height = page_dict.get('height', 792)
        if y_pos < 50 or y_pos > page_height - 50:
            if max(sizes) <= 8.5:
                continue  # Skip small text in header/footer areas

        # Determine atom kind
        max_size = max(sizes) if sizes else 9.0
        is_bold = 20 in flags_set or (16 in flags_set)

        # Detect heading (larger font or standalone bold)
        is_heading = max_size >= 12 or (is_bold and max_size >= 10 and len(full_text) < 100)

        # Detect list items
        is_list = (
            full_text.startswith(('•', '●', '○', '▪', '-', '–', '—', '*')) or
            any(full_text.startswith(f"{n}.") for n in range(1, 100)) or
            any(full_text.startswith(f"{n})") for n in range(1, 100))
        )

        # Detect bold-lead paragraphs (characteristic name. description)
        # These have bold flags mixed with regular (like "Empathy. They can imagine...")
        is_bold_lead = has_bold_lead and 4 in flags_set and not is_heading

        if is_heading:
            kind = "heading"
        elif is_list:
            kind = "list"
        elif is_bold_lead:
            kind = "bold_lead"  # Keep these together
        else:
            kind = "paragraph"

        atoms.append({
            "text": full_text,
            "kind": kind,
            "is_hard_boundary": is_heading,  # Headings are hard boundaries
            "start_char": char_pos,
            "end_char": char_pos + len(full_text),
            "font_size": max_size,
        })
        char_pos += len(full_text) + 1

    return atoms


def extract_page_anchors(page, page_num: int) -> List[dict]:
    """
    Extract page anchors: large-font text and text in top 15% of page.

    Page anchors are high-signal text elements that should be boosted
    in retrieval:
    - Large font text (>=12pt): titles, section headers, key terms
    - Top 15% of page: page titles, chapter headers, document titles

    These anchors help with questions about document structure, titles,
    and locating specific sections.

    Returns:
        List of anchor chunks with is_anchor=True
    """
    page_dict = page.get_text("dict")
    page_height = page_dict.get('height', 792)
    top_threshold = page_height * 0.15  # Top 15% of page

    anchors = []
    anchor_texts = set()  # Avoid duplicates

    for block in page_dict.get('blocks', []):
        if block.get('type') != 0:  # Skip non-text blocks (images)
            continue

        bbox = block.get('bbox', (0, 0, 0, 0))
        block_y = bbox[1]  # Top of block

        for line in block.get('lines', []):
            for span in line.get('spans', []):
                text = span.get('text', '').strip()
                font_size = span.get('size', 0)
                span_y = line.get('bbox', (0, block_y, 0, 0))[1]

                # Skip empty or very short text
                if not text or len(text) < 3:
                    continue

                # Skip if already captured
                if text in anchor_texts:
                    continue

                # Anchor criteria: large font OR in top 15%
                is_large_font = font_size >= 12
                is_top_area = span_y < top_threshold

                if is_large_font or is_top_area:
                    anchor_texts.add(text)
                    anchors.append({
                        "text": text,
                        "page_num": page_num,
                        "start": 0,
                        "end": len(text),
                        "is_anchor": True,
                        "anchor_type": "large_font" if is_large_font else "top_area",
                        "font_size": font_size,
                    })

    return anchors


def chunk_atoms_semantic(
    atoms: List[dict],
    page_num: int,
    embed_model,
    theta: float = 0.78,
    max_tokens: int = 650,
    min_tokens: int = 180,
) -> List[dict]:
    """
    Semantic chunking using centroid-based similarity on structure-aware atoms.

    Key improvements over naive sentence-based chunking:
    1. Never splits mid-atom (preserves structure)
    2. Compares next atom vs chunk centroid (more stable)
    3. Respects hard boundaries (headings)
    4. Keeps lists and bold-lead items together
    5. Uses token budget, not character count

    Reference: Third-party review feedback for Option A+

    Args:
        atoms: List of atoms from extract_atoms_from_page
        page_num: Page number for metadata
        embed_model: SentenceTransformer model
        theta: Similarity threshold (0.78 works well with centroid)
        max_tokens: Maximum tokens per chunk
        min_tokens: Minimum tokens before allowing semantic splits

    Returns:
        List of chunk dicts
    """
    import numpy as np

    if not atoms:
        return []

    # Embed all atoms in batch
    texts = [a["text"] for a in atoms]
    embs = embed_model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def estimate_tokens(text: str) -> int:
        """Rough token estimate: ~4 chars per token for English."""
        return max(1, len(text) // 4)

    def cosine_sim(a, b):
        norm = np.linalg.norm(b)
        if norm < 1e-9:
            return 0.0
        return float(np.dot(a, b / norm))

    chunks = []
    cur_atom_ids = [0]
    cur_text = atoms[0]["text"]
    cur_tokens = estimate_tokens(cur_text)
    cur_centroid = embs[0].copy()

    def flush_chunk():
        nonlocal cur_atom_ids, cur_text, cur_tokens, cur_centroid
        if not cur_text.strip():
            return

        # Determine chunk kind
        kinds = [atoms[i]["kind"] for i in cur_atom_ids]
        if len(set(kinds)) == 1:
            chunk_kind = kinds[0]
        elif "heading" in kinds:
            chunk_kind = "section"
        else:
            chunk_kind = "mixed"

        chunks.append({
            "text": cur_text.strip(),
            "page_num": page_num,
            "start": atoms[cur_atom_ids[0]]["start_char"],
            "end": atoms[cur_atom_ids[-1]]["end_char"],
            "kind": chunk_kind,
            "atom_count": len(cur_atom_ids),
            "token_est": cur_tokens,
        })

    # Track if we're in a "definition list" section (heading followed by bold_lead items)
    in_definition_section = False
    definition_section_start = -1

    for i in range(1, len(atoms)):
        atom = atoms[i]
        atom_tokens = estimate_tokens(atom["text"])
        sim = cosine_sim(embs[i], cur_centroid)

        # Hard boundaries always split (new heading)
        if atom.get("is_hard_boundary"):
            flush_chunk()
            cur_atom_ids = [i]
            cur_text = atom["text"]
            cur_tokens = atom_tokens
            cur_centroid = embs[i].copy()
            # Start tracking potential definition section
            in_definition_section = True
            definition_section_start = i
            continue

        # List and bold-lead items: try VERY hard to keep together
        is_cohesive = atom["kind"] in ("list", "bold_lead")

        # Check if we're in a definition section with multiple bold_lead items
        # Look at ALL atoms since section start to detect pattern
        atoms_since_section = range(definition_section_start + 1, i + 1) if in_definition_section else []
        bold_leads_in_section = sum(1 for j in atoms_since_section if j < len(atoms) and atoms[j]["kind"] == "bold_lead")
        in_definition_list = in_definition_section and (is_cohesive or bold_leads_in_section >= 2)

        # Check if current chunk contains similar cohesive items (same series)
        cur_kinds = [atoms[j]["kind"] for j in cur_atom_ids]
        in_cohesive_series = is_cohesive and any(k in ("list", "bold_lead") for k in cur_kinds)

        # Check if we should split
        # For definition lists (like "Empathy. ...", "Optimism. ..."), use very high limit
        # This keeps all items in the same list together
        if in_definition_list and bold_leads_in_section >= 3:
            # Multiple bold_lead items = likely a definition list, keep very together
            effective_max = max_tokens * 4
        elif in_definition_list:
            effective_max = max_tokens * 3
        elif in_cohesive_series:
            effective_max = max_tokens * 2
        else:
            effective_max = max_tokens

        would_exceed = (cur_tokens + atom_tokens) > effective_max
        low_sim = sim < theta

        should_split = False
        if would_exceed:
            should_split = True
        elif low_sim and cur_tokens >= min_tokens and not is_cohesive and not in_definition_list:
            should_split = True

        if should_split:
            flush_chunk()
            cur_atom_ids = [i]
            cur_text = atom["text"]
            cur_tokens = atom_tokens
            cur_centroid = embs[i].copy()
        else:
            cur_atom_ids.append(i)
            # Join with newline for lists, space for paragraphs
            separator = "\n" if atom["kind"] == "list" else " "
            cur_text += separator + atom["text"]
            cur_tokens += atom_tokens
            # Update centroid (running sum of normalized vectors)
            cur_centroid = cur_centroid + embs[i]

    # Flush final chunk
    flush_chunk()

    return chunks


def chunk_text_semantic(
    text: str,
    page_num: int,
    embed_model,
    similarity_threshold: float = 0.78,
    min_chunk_chars: int = 100,
    max_chunk_chars: int = 500,
) -> List[dict]:
    """
    Semantic chunking fallback when page object not available.

    Uses sentence-based grouping with centroid similarity.
    Prefer chunk_page_semantic() when you have the PyMuPDF page object.
    """
    import numpy as np
    import re

    if not text or len(text.strip()) < min_chunk_chars:
        return [{"text": text.strip(), "page_num": page_num, "start": 0, "end": len(text)}]

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    if len(sentences) <= 1:
        return [{"text": text.strip(), "page_num": page_num, "start": 0, "end": len(text)}]

    # Embed all sentences
    embeddings = embed_model.encode(sentences, normalize_embeddings=True, show_progress_bar=False)

    def estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    max_tokens = max_chunk_chars // 4  # Convert to tokens
    min_tokens = min_chunk_chars // 4

    chunks = []
    cur_sentences = [sentences[0]]
    cur_centroid = embeddings[0].copy()
    cur_tokens = estimate_tokens(sentences[0])
    current_start = 0

    for i in range(1, len(sentences)):
        sent_tokens = estimate_tokens(sentences[i])

        # Compare to centroid, not previous sentence
        norm = np.linalg.norm(cur_centroid)
        sim = float(np.dot(embeddings[i], cur_centroid / (norm + 1e-9))) if norm > 1e-9 else 0

        should_split = False
        if cur_tokens + sent_tokens > max_tokens:
            should_split = True
        elif sim < similarity_threshold and cur_tokens >= min_tokens:
            should_split = True

        if should_split:
            chunk_text = " ".join(cur_sentences)
            chunks.append({
                "text": chunk_text,
                "page_num": page_num,
                "start": current_start,
                "end": current_start + len(chunk_text),
                "token_est": cur_tokens,
            })
            current_start += len(chunk_text) + 1
            cur_sentences = [sentences[i]]
            cur_centroid = embeddings[i].copy()
            cur_tokens = sent_tokens
        else:
            cur_sentences.append(sentences[i])
            cur_centroid = cur_centroid + embeddings[i]
            cur_tokens += sent_tokens

    # Final chunk
    if cur_sentences:
        chunk_text = " ".join(cur_sentences)
        chunks.append({
            "text": chunk_text,
            "page_num": page_num,
            "start": current_start,
            "end": current_start + len(chunk_text),
            "token_est": cur_tokens,
        })

    return chunks


def chunk_page_semantic(
    page,
    page_num: int,
    embed_model,
    theta: float = 0.78,
    max_tokens: int = 650,
    min_tokens: int = 180,
) -> List[dict]:
    """
    Structure-aware semantic chunking for a PyMuPDF page.

    This is the preferred method when you have the page object.
    Uses PDF structure (blocks, fonts) to create atoms, then groups
    them semantically using centroid similarity.

    Args:
        page: PyMuPDF page object
        page_num: Page number for metadata
        embed_model: SentenceTransformer model
        theta: Similarity threshold
        max_tokens: Maximum tokens per chunk
        min_tokens: Minimum tokens before allowing splits

    Returns:
        List of chunk dicts with text, page_num, start, end, kind
    """
    atoms = extract_atoms_from_page(page)

    if not atoms:
        return []

    # If only one atom, return it as a single chunk
    if len(atoms) == 1:
        return [{
            "text": atoms[0]["text"],
            "page_num": page_num,
            "start": 0,
            "end": len(atoms[0]["text"]),
            "kind": atoms[0]["kind"],
            "atom_count": 1,
        }]

    return chunk_atoms_semantic(
        atoms, page_num, embed_model,
        theta=theta, max_tokens=max_tokens, min_tokens=min_tokens
    )


def generate_page_summary(text: str, max_length: int = 150) -> str:
    """
    Generate a brief summary of page content.

    For now, uses first N chars. Can be replaced with LLM summarization.
    """
    if not text:
        return "(empty page)"

    # Clean and truncate
    clean = " ".join(text.split())
    if len(clean) <= max_length:
        return clean

    # Try to break at sentence
    truncated = clean[:max_length]
    last_period = truncated.rfind('. ')
    if last_period > max_length // 2:
        return truncated[:last_period + 1]

    return truncated + "..."


# =============================================================================
# File ID Generation
# =============================================================================

def generate_file_id(file_path: str) -> str:
    """Generate unique file ID from path and content hash."""
    path = Path(file_path)

    # Hash first 64KB + file size for uniqueness
    with open(file_path, "rb") as f:
        content_sample = f.read(65536)

    file_size = path.stat().st_size
    hash_input = f"{path.name}:{file_size}:{content_sample[:1000].hex()}"

    return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


# =============================================================================
# Document Ingestion (The "Ingest Once" Phase)
# =============================================================================

class BaseIngestor:
    """
    Base class for document ingestion.

    Provides common functionality for all document types:
    - Caching (save/load DocumentPack)
    - Embedding model loading
    - Chunking configuration

    Subclasses must implement the ingest() method.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        cache_dir: Optional[str] = None,
        chunking_method: str = "fixed",  # "fixed" or "semantic"
        semantic_threshold: float = 0.80,
        precompute_embeddings: bool = False,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize base ingestor.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            cache_dir: Directory for caching processed documents
            chunking_method: "fixed" or "semantic"
            semantic_threshold: Threshold for semantic chunking
            precompute_embeddings: Pre-compute embeddings during ingestion
            embedding_model: Model for embeddings
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "questmind_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.chunking_method = chunking_method
        self.semantic_threshold = semantic_threshold
        self.precompute_embeddings = precompute_embeddings
        self.embedding_model = embedding_model
        self._embed_model = None

    def ingest(self, source: str, **kwargs) -> DocumentPack:
        """
        Ingest a document from source.

        Args:
            source: Path to document (file or directory)
            **kwargs: Ingestor-specific options

        Returns:
            DocumentPack with processed content
        """
        raise NotImplementedError("Subclasses must implement ingest()")

    def _load_embed_model(self):
        """Lazy load embedding model for semantic chunking and embeddings."""
        if self._embed_model is None:
            from sentence_transformers import SentenceTransformer
            print(f"Loading embedding model: {self.embedding_model}")
            self._embed_model = SentenceTransformer(self.embedding_model)
        return self._embed_model

    def _cache_path(self, file_id: str) -> Path:
        """Get cache file path for a document."""
        return self.cache_dir / file_id / "doc_pack.json"

    def _load_from_cache(self, file_id: str) -> Optional[DocumentPack]:
        """Load DocumentPack from cache if available."""
        cache_file = self._cache_path(file_id)
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    return DocumentPack.from_dict(json.load(f))
            except:
                return None
        return None

    def _save_to_cache(self, pack: DocumentPack):
        """Save DocumentPack to cache."""
        cache_file = self._cache_path(pack.file_id)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(pack.to_dict(), f, indent=2)

    def clear_cache(self, file_id: Optional[str] = None):
        """Clear cache for specific file or all files."""
        if file_id:
            cache_dir = self.cache_dir / file_id
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
        else:
            if self.cache_dir.exists():
                import shutil
                shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_file_id(self, source: str) -> str:
        """Generate unique ID for a source path."""
        path = Path(source)
        if path.is_file():
            return generate_file_id(source)
        elif path.is_dir():
            # For directories, hash the directory name + file list
            files = sorted(str(f) for f in path.rglob("*") if f.is_file())
            hash_input = f"{path.name}:{len(files)}:{':'.join(files[:10])}"
            return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        else:
            # Fallback for other sources
            return hashlib.sha256(source.encode()).hexdigest()[:16]


class TextIngestor(BaseIngestor):
    """
    Ingests text files (plain text, markdown, etc.) into a DocumentPack.

    Each section (separated by section_delimiter) becomes a page/unit.
    All content is text-native, no VLM needed.
    """

    def __init__(
        self,
        section_delimiter: str = "\n\n",
        min_section_chars: int = 50,
        **kwargs
    ):
        """
        Initialize text ingestor.

        Args:
            section_delimiter: Delimiter to split text into sections
            min_section_chars: Minimum characters for a section to be kept
            **kwargs: Passed to BaseIngestor
        """
        super().__init__(**kwargs)
        self.section_delimiter = section_delimiter
        self.min_section_chars = min_section_chars

    def ingest(
        self,
        text_path: str,
        progress_callback: Optional[callable] = None
    ) -> DocumentPack:
        """
        Ingest a text file into DocumentPack.

        Args:
            text_path: Path to text file
            progress_callback: Optional callback(current, total, status)

        Returns:
            DocumentPack with text content
        """
        text_path = str(text_path)
        file_id = self._generate_file_id(text_path)

        # Check cache
        cached = self._load_from_cache(file_id)
        if cached:
            if progress_callback:
                progress_callback(cached.total_pages, cached.total_pages, "Loaded from cache")
            return cached

        # Read text file
        with open(text_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into sections
        sections = content.split(self.section_delimiter)
        sections = [s.strip() for s in sections if len(s.strip()) >= self.min_section_chars]

        if not sections:
            sections = [content.strip()] if content.strip() else [""]

        num_sections = len(sections)

        # Create pack
        pack = DocumentPack(
            file_id=file_id,
            file_path=text_path,
            file_name=Path(text_path).name,
            total_pages=num_sections,
            created_at=datetime.now().isoformat(),
            document_type="text",
            native_pages=num_sections,
            vlm_pages=0,
        )

        if progress_callback:
            progress_callback(0, num_sections, "Processing sections...")

        # Process each section as a "page"
        for i, section_text in enumerate(sections):
            if progress_callback and i % 10 == 0:
                progress_callback(i, num_sections, f"Processing section {i+1}...")

            # Create chunks
            chunks = chunk_text(section_text, i + 1, self.chunk_size, self.chunk_overlap)
            pack.chunks.extend(chunks)

            # Create page data (section)
            page_data = PageData(
                page_num=i + 1,
                page_type="text_native",
                native_text=section_text,
                summary=section_text[:200] + "..." if len(section_text) > 200 else section_text,
                image_path=None,
                vlm_text=None,
            )
            pack.pages.append(page_data)

        # Precompute embeddings if requested
        if self.precompute_embeddings and pack.chunks:
            self._precompute_embeddings(pack, progress_callback)

        # Save to cache
        self._save_to_cache(pack)

        if progress_callback:
            progress_callback(num_sections, num_sections, "Complete")

        return pack

    def _precompute_embeddings(self, pack: DocumentPack, progress_callback: Optional[callable] = None):
        """Precompute chunk embeddings and BM25 index."""
        import re
        from rank_bm25 import BM25Okapi

        num_chunks = len(pack.chunks)
        if progress_callback:
            progress_callback(0, num_chunks, f"Computing embeddings for {num_chunks} chunks...")

        embed_model = self._load_embed_model()
        chunk_texts = [c["text"] for c in pack.chunks]
        pack._chunk_embeddings = embed_model.encode(chunk_texts, show_progress_bar=False)

        # Build BM25 index
        def tokenize(text: str) -> list:
            tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
            return [t for t in tokens if len(t) > 2]

        tokenized_corpus = [tokenize(c["text"]) for c in pack.chunks]
        pack._bm25_index = BM25Okapi(tokenized_corpus)
        pack._bm25_corpus_id = pack.file_id


class ImageIngestor(BaseIngestor):
    """
    Ingests a directory of images into a DocumentPack.

    Each image becomes a page/unit. All pages need VLM for understanding.
    For image collections, all images are sent to VLM on every query.
    Use vllm-mlx server mode with prefix caching for good multi-turn performance.
    """

    # Supported image extensions
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

    def __init__(
        self,
        **kwargs
    ):
        """
        Initialize image ingestor.

        Args:
            **kwargs: Passed to BaseIngestor
        """
        super().__init__(**kwargs)

    def ingest(
        self,
        image_dir: str,
        extensions: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> DocumentPack:
        """
        Ingest an image directory into DocumentPack.

        Args:
            image_dir: Path to directory containing images
            extensions: List of extensions to include (default: all supported)
            progress_callback: Optional callback(current, total, status)

        Returns:
            DocumentPack with image content
        """
        image_dir = str(image_dir)
        dir_path = Path(image_dir)

        if not dir_path.is_dir():
            raise ValueError(f"Image directory not found: {image_dir}")

        file_id = self._generate_file_id(image_dir)

        # Check cache
        cached = self._load_from_cache(file_id)
        if cached:
            if progress_callback:
                progress_callback(cached.total_pages, cached.total_pages, "Loaded from cache")
            return cached

        # Find all images
        valid_extensions = set(extensions) if extensions else self.IMAGE_EXTENSIONS
        image_files = sorted([
            f for f in dir_path.iterdir()
            if f.is_file() and f.suffix.lower() in valid_extensions
        ])

        num_images = len(image_files)

        # Create pack
        pack = DocumentPack(
            file_id=file_id,
            file_path=image_dir,
            file_name=dir_path.name,
            total_pages=num_images,
            created_at=datetime.now().isoformat(),
            document_type="image_collection",
            native_pages=0,
            vlm_pages=num_images,  # All pages need VLM
            visual_pages=list(range(1, num_images + 1)),  # All pages are visual
        )

        if progress_callback:
            progress_callback(0, num_images, "Processing images...")

        # Process each image
        for i, image_path in enumerate(image_files):
            if progress_callback and i % 5 == 0:
                progress_callback(i, num_images, f"Processing image {i+1}...")

            # Create page data (image)
            page_data = PageData(
                page_num=i + 1,
                page_type="image",  # Custom type for images
                native_text=image_path.name,  # Filename as basic text
                summary=f"Image: {image_path.name}",
                image_path=str(image_path),
                vlm_text=None,
            )
            pack.pages.append(page_data)

        # Create chunks from filenames (for basic retrieval if needed)
        self._rebuild_chunks(pack)

        # Precompute embeddings if requested
        if self.precompute_embeddings and pack.chunks:
            self._precompute_embeddings(pack, progress_callback)

        # Save to cache
        self._save_to_cache(pack)

        if progress_callback:
            progress_callback(num_images, num_images, "Complete")

        return pack

    def _rebuild_chunks(self, pack: DocumentPack):
        """Rebuild chunks from page data (after captioning)."""
        pack.chunks = []
        for page_data in pack.pages:
            if page_data.vlm_text:
                # Use caption as chunk text
                chunk_text_content = f"[Image {page_data.page_num}: {Path(page_data.image_path).name}] {page_data.vlm_text}"
            else:
                chunk_text_content = f"[Image {page_data.page_num}: {page_data.native_text}]"

            pack.chunks.append({
                "text": chunk_text_content,
                "page_num": page_data.page_num,
                "start": 0,
                "end": len(chunk_text_content),
                "is_image": True,
                "image_path": page_data.image_path,
            })

    def _precompute_embeddings(self, pack: DocumentPack, progress_callback: Optional[callable] = None):
        """Precompute chunk embeddings and BM25 index."""
        import re
        from rank_bm25 import BM25Okapi

        num_chunks = len(pack.chunks)
        if progress_callback:
            progress_callback(0, num_chunks, f"Computing embeddings for {num_chunks} chunks...")

        embed_model = self._load_embed_model()
        chunk_texts = [c["text"] for c in pack.chunks]
        pack._chunk_embeddings = embed_model.encode(chunk_texts, show_progress_bar=False)

        # Build BM25 index
        def tokenize(text: str) -> list:
            tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
            return [t for t in tokens if len(t) > 2]

        tokenized_corpus = [tokenize(c["text"]) for c in pack.chunks]
        pack._bm25_index = BM25Okapi(tokenized_corpus)
        pack._bm25_corpus_id = pack.file_id


def _detect_document_type(source: str) -> str:
    """
    Auto-detect document type from source path.

    Args:
        source: Path to file or directory

    Returns:
        Document type string: "pdf", "image_collection", or "text"
    """
    path = Path(source)

    if path.is_dir():
        return "image_collection"

    if not path.is_file():
        raise ValueError(f"Source not found: {source}")

    ext = path.suffix.lower()

    if ext == ".pdf":
        return "pdf"
    elif ext in ImageIngestor.IMAGE_EXTENSIONS:
        # Single image - treat as image collection of 1
        return "image_collection"
    else:
        # Default to text for unknown extensions
        return "text"


def create_ingestor(
    source: str,
    document_type: Optional[str] = None,
    **kwargs
) -> BaseIngestor:
    """
    Factory function to create appropriate ingestor for a source.

    Args:
        source: Path to document (file or directory)
        document_type: Optional type override ("pdf", "image_collection", "text")
        **kwargs: Passed to ingestor constructor

    Returns:
        Appropriate ingestor instance

    Example:
        >>> ingestor = create_ingestor("document.pdf")
        >>> pack = ingestor.ingest("document.pdf")

        >>> ingestor = create_ingestor("images/")
        >>> pack = ingestor.ingest("images/")
    """
    if document_type is None:
        document_type = _detect_document_type(source)

    if document_type == "pdf":
        return PDFIngestor(**kwargs)
    elif document_type == "image_collection":
        return ImageIngestor(**kwargs)
    elif document_type == "text":
        return TextIngestor(**kwargs)
    else:
        raise ValueError(f"Unknown document type: {document_type}")


class PDFIngestor(BaseIngestor):
    """
    Ingests a PDF into a DocumentPack for multi-turn querying.

    This is the "ingest once" phase of the Gemini-style pipeline.
    Creates: text, page images, summaries, chunks, embeddings.
    """

    def __init__(
        self,
        resolution: MediaResolution = MediaResolution.MED,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        cache_dir: Optional[str] = None,
        chunking_method: str = "fixed",  # "fixed" or "semantic"
        semantic_threshold: float = 0.80,
        caption_images: bool = False,  # Enable VLM captioning of embedded images
        caption_model: str = "HuggingFaceTB/SmolVLM-500M-Instruct",  # 3x faster (124ms vs 381ms)
        caption_server_url: Optional[str] = None,  # vllm-mlx server URL for parallel captioning
        caption_max_concurrent: int = 4,  # Max concurrent caption requests
        preload_caption_model: bool = False,  # Load caption model immediately
        precompute_embeddings: bool = False,  # Precompute chunk embeddings during ingestion
        embedding_model: str = "all-MiniLM-L6-v2",  # Model for chunk embeddings
    ):
        # Initialize base class with common parameters
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            cache_dir=cache_dir,
            chunking_method=chunking_method,
            semantic_threshold=semantic_threshold,
            precompute_embeddings=precompute_embeddings,
            embedding_model=embedding_model,
        )

        # PDF-specific configuration
        self.resolution = resolution
        self.caption_images = caption_images
        self.caption_model = caption_model
        self.caption_server_url = caption_server_url
        self.caption_max_concurrent = caption_max_concurrent
        self._caption_model = None
        self._caption_processor = None

        # Preload caption model if requested (avoids cold start on first ingest)
        if preload_caption_model and caption_images:
            self._load_caption_model()

    def _load_caption_model(self):
        """
        Lazy load VLM for image captioning.

        Uses Qwen3-VL-2B-4bit by default:
        - ~130ms TTFT, 162 tok/s generation
        - 2GB memory footprint
        - Most reliable for captioning tasks
        """
        if self._caption_model is None:
            from questmind.inference import load
            self._caption_model, self._caption_processor = load(self.caption_model)
        return self._caption_model, self._caption_processor

    def _caption_image(
        self,
        image_path: str,
        figure_label: Optional[str] = None,
        surrounding_context: Optional[str] = None,
    ) -> str:
        """
        Generate caption for an extracted image using VLM.

        Uses surrounding text context (per NVIDIA/Vespa research) to
        ground the VLM's understanding of what the figure represents.

        Args:
            image_path: Path to the image file
            figure_label: Optional "Figure X" label if detected
            surrounding_context: Text from before/after the figure

        Returns:
            Generated caption (2-3 sentences)
        """
        from questmind.inference import generate, apply_chat_template

        model, processor = self._load_caption_model()

        # Build context-aware prompt (research-backed approach)
        prompt_parts = []

        if figure_label:
            prompt_parts.append(f"This is {figure_label} from a technical document.")
        else:
            prompt_parts.append("This is an image from a technical document.")

        if surrounding_context:
            # Truncate context if too long
            ctx = surrounding_context[:300] if len(surrounding_context) > 300 else surrounding_context
            prompt_parts.append(f"Context: \"{ctx}\"")

        prompt_parts.append(
            "Describe what this figure shows in 2-3 sentences. "
            "Focus on the key components, relationships, and labels visible."
        )

        user_prompt = " ".join(prompt_parts)

        # Format prompt with image tokens (required for Qwen3-VL)
        formatted_prompt = apply_chat_template(
            processor,
            model.config,
            user_prompt,
            num_images=1,
        )

        result = generate(
            model,
            processor,
            image=image_path,
            prompt=formatted_prompt,
            max_tokens=150,
            verbose=False,
        )

        # Extract text from GenerationResult
        caption = result.text if hasattr(result, 'text') else str(result)
        return caption.strip()

    def _build_caption_prompt(
        self,
        figure_label: Optional[str] = None,
        surrounding_context: Optional[str] = None,
        for_batch: bool = False,
    ) -> str:
        """Build the caption prompt text (shared between local and server modes).

        Args:
            figure_label: Optional figure label like "Figure 1"
            surrounding_context: Text from around the figure
            for_batch: If True, use shorter prompt for batch processing compatibility
        """
        if for_batch:
            # Shorter prompt works better with batch_generate to avoid state issues
            if figure_label:
                return f"This is {figure_label} from a technical document. Describe in 2-3 sentences."
            else:
                return "This is an image from a technical document. Describe in 2-3 sentences."

        # Full prompt for single-image captioning (more context helps quality)
        prompt_parts = []

        if figure_label:
            prompt_parts.append(f"This is {figure_label} from a technical document.")
        else:
            prompt_parts.append("This is an image from a technical document.")

        if surrounding_context:
            ctx = surrounding_context[:300] if len(surrounding_context) > 300 else surrounding_context
            prompt_parts.append(f"Context: \"{ctx}\"")

        prompt_parts.append(
            "Describe what this figure shows in 2-3 sentences. "
            "Focus on the key components, relationships, and labels visible."
        )

        return " ".join(prompt_parts)

    def _caption_images_batch(
        self,
        image_requests: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Caption multiple images in a single batch using mlx-vlm's batch_generate.

        This is more efficient than sequential captioning as it:
        1. Groups images by shape for efficient batch processing
        2. Processes all images in parallel on the GPU
        3. Shares computation across the batch

        Requires patched mlx-vlm with fixed _deepstack_process for batching.

        Args:
            image_requests: List of dicts with keys:
                - path: image file path
                - figure_label: Optional figure label
                - surrounding_context: Optional surrounding text

        Returns:
            List of captions in same order as requests
        """
        from questmind.inference import batch_generate

        model, processor = self._load_caption_model()

        # Build RAW prompts (batch_generate formats them internally)
        images = []
        prompts = []

        for req in image_requests:
            images.append(req["path"])
            # Raw prompt - batch_generate will apply chat template
            # Use shorter prompt format for batch compatibility
            prompts.append(self._build_caption_prompt(
                req.get("figure_label"),
                req.get("surrounding_context"),
                for_batch=True,
            ))

        # Batch size limit: Model produces incorrect outputs for items 0-8 when batch >= 10
        # This appears to be a Qwen3-VL model issue, not a vision-related bug
        # Safe limit is 8 (verified working for both text and vision batches)
        MAX_BATCH = 8
        all_captions = []

        for batch_start in range(0, len(images), MAX_BATCH):
            batch_end = min(batch_start + MAX_BATCH, len(images))
            batch_images = images[batch_start:batch_end]
            batch_prompts = prompts[batch_start:batch_end]

            # Run batch generation with uniform_size for true single-batch processing
            result = batch_generate(
                model,
                processor,
                images=batch_images,
                prompts=batch_prompts,
                max_tokens=150,
                verbose=False,
                uniform_size=(1024, 1024),  # Force all images to same size for single batch
            )

            # Extract captions from result
            for i, text in enumerate(result.texts):
                caption = text.strip() if text else f"[{image_requests[batch_start + i].get('figure_label') or 'Image'}]"
                all_captions.append(caption)

        return all_captions

    async def _caption_image_async(
        self,
        session,
        image_path: str,
        figure_label: Optional[str] = None,
        surrounding_context: Optional[str] = None,
    ) -> str:
        """
        Generate caption using vllm-mlx server (async HTTP request).

        Args:
            session: aiohttp ClientSession
            image_path: Path to the image file
            figure_label: Optional "Figure X" label if detected
            surrounding_context: Text from before/after the figure

        Returns:
            Generated caption
        """
        import base64

        # Read and encode image as base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Determine image type from extension
        ext = Path(image_path).suffix.lower()
        media_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(ext, "image/png")

        prompt = self._build_caption_prompt(figure_label, surrounding_context)

        # Build OpenAI-compatible request
        payload = {
            "model": self.caption_model.split("/")[-1],  # Extract model name
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 150,
            "stream": False,
        }

        url = f"{self.caption_server_url.rstrip('/')}/v1/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(f"Caption server error: {response.status} - {error_text}")

            result = await response.json()
            return result["choices"][0]["message"]["content"].strip()

    async def _caption_images_parallel(
        self,
        image_requests: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Caption multiple images in parallel using vllm-mlx server.

        Args:
            image_requests: List of dicts with keys:
                - path: image file path
                - figure_label: Optional figure label
                - surrounding_context: Optional surrounding text

        Returns:
            List of captions in same order as requests
        """
        import asyncio
        try:
            import aiohttp
        except ImportError:
            raise ImportError(
                "aiohttp is required for parallel captioning. "
                "Install with: pip install aiohttp"
            )

        semaphore = asyncio.Semaphore(self.caption_max_concurrent)

        async def caption_with_semaphore(session, req):
            async with semaphore:
                try:
                    return await self._caption_image_async(
                        session,
                        req["path"],
                        req.get("figure_label"),
                        req.get("surrounding_context"),
                    )
                except Exception as e:
                    # Return fallback on error
                    label = req.get("figure_label") or "Image"
                    return f"[{label}]"

        async with aiohttp.ClientSession() as session:
            tasks = [
                caption_with_semaphore(session, req)
                for req in image_requests
            ]
            return await asyncio.gather(*tasks)

    def _run_parallel_captioning(
        self,
        image_requests: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Run parallel captioning (sync wrapper for async method).

        Args:
            image_requests: List of image caption requests

        Returns:
            List of captions
        """
        import asyncio

        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, we need to use a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._caption_images_parallel(image_requests)
                )
                return future.result()
        except RuntimeError:
            # No running loop, we can use asyncio.run directly
            return asyncio.run(self._caption_images_parallel(image_requests))

    def ingest(
        self,
        pdf_path: str,
        max_pages: Optional[int] = None,
        render_all_pages: bool = False,
        progress_callback: Optional[callable] = None
    ) -> DocumentPack:
        """
        Ingest PDF into DocumentPack.

        Args:
            pdf_path: Path to PDF file
            max_pages: Limit pages processed
            render_all_pages: If True, render all pages (not just VLM-needed)
            progress_callback: Optional callback(current, total, status)

        Returns:
            DocumentPack with all extracted data
        """
        pdf_path = str(pdf_path)
        file_id = generate_file_id(pdf_path)

        # Check cache
        cached = self._load_from_cache(file_id)
        if cached:
            if progress_callback:
                progress_callback(cached.total_pages, cached.total_pages, "Loaded from cache")
            return cached

        doc = fitz.open(pdf_path)
        num_pages = min(len(doc), max_pages) if max_pages else len(doc)

        # Create pack
        pack = DocumentPack(
            file_id=file_id,
            file_path=pdf_path,
            file_name=Path(pdf_path).name,
            total_pages=num_pages,
            created_at=datetime.now().isoformat()
        )

        # Phase 1: Analyze all pages
        if progress_callback:
            progress_callback(0, num_pages, "Analyzing pages...")

        analyses = []
        for i in range(num_pages):
            analysis = analyze_page(doc[i], i + 1)
            analyses.append(analysis)
            pack.analyses.append(analysis.to_dict())

        pack.native_pages = sum(1 for a in analyses if not a.needs_vlm)
        pack.vlm_pages = sum(1 for a in analyses if a.needs_vlm)

        # Detect pages with significant visual content (for auto-routing)
        for i, analysis in enumerate(analyses):
            if has_significant_visual_content(doc[i], analysis):
                pack.visual_pages.append(i + 1)

        # Phase 2: Process each page
        if progress_callback:
            progress_callback(0, num_pages, "Extracting content...")

        for i, analysis in enumerate(analyses):
            if progress_callback and i % 10 == 0:
                progress_callback(i, num_pages, f"Processing page {i+1}...")

            page = doc[i]

            # Extract native text
            native_text = extract_native_text(page, "markdown")

            # Generate summary
            summary = generate_page_summary(native_text)

            # Render image if needed (VLM pages, visual content pages, or render_all)
            image_path = None
            page_num = i + 1
            needs_image = (
                analysis.needs_vlm or
                render_all_pages or
                page_num in pack.visual_pages  # Also render visual content pages
            )
            if needs_image:
                img_dir = self.cache_dir / file_id / "images"
                img_dir.mkdir(parents=True, exist_ok=True)
                image_path = str(img_dir / f"page_{page_num:04d}.png")
                render_page_to_image(page, self.resolution, image_path)

            # Extract embedded images (captioning happens in batch later if server mode)
            image_captions = []
            extracted_images = []
            if self.caption_images:
                embed_img_dir = self.cache_dir / file_id / "embedded_images"
                embed_img_dir.mkdir(parents=True, exist_ok=True)

                # Extract raster images first (if page has images)
                if analysis.image_count > 0:
                    extracted_images = extract_embedded_images(
                        doc, page, page_num, embed_img_dir
                    )

                # Also try vector figures (charts, graphs from matplotlib/LaTeX)
                # These aren't counted in image_count but are significant figures
                if not extracted_images:
                    extracted_images = extract_vector_figures(
                        page, page_num, embed_img_dir
                    )

                # Prepare image metadata (captioning done later for parallel mode)
                for img_info in extracted_images:
                    figure_label = find_figure_label(page, img_info["bbox"])
                    surrounding_context = extract_figure_context(page, img_info["bbox"])

                    image_captions.append({
                        "figure_label": figure_label,
                        "caption": None,  # Will be filled in later
                        "surrounding_context": surrounding_context,
                        "bbox": img_info["bbox"],
                        "image_path": img_info["path"],
                    })

            # Create chunks (semantic or fixed)
            if self.chunking_method == "semantic":
                # Use structure-aware chunking with page object
                chunks = chunk_page_semantic(
                    page,
                    i + 1,
                    self._load_embed_model(),
                    theta=self.semantic_threshold,
                    max_tokens=self.chunk_size // 4,  # Convert chars to tokens
                    min_tokens=100 // 4,
                )
            else:
                chunks = chunk_text(native_text, i + 1, self.chunk_size, self.chunk_overlap)
            pack.chunks.extend(chunks)

            # Extract and add page anchors (large font + top 15%)
            # DISABLED: anchors creating noise, need different approach
            # anchors = extract_page_anchors(page, i + 1)
            # pack.chunks.extend(anchors)

            # Create page data
            page_data = PageData(
                page_num=i + 1,
                page_type=analysis.page_type.value,
                native_text=native_text,
                summary=summary,
                image_path=image_path,
                image_captions=image_captions,
            )
            pack.pages.append(page_data)

        doc.close()

        # Phase 3: Caption all extracted images
        if self.caption_images:
            # Collect all images that need captioning across all pages
            all_caption_requests = []
            caption_indices = []  # (page_idx, caption_idx) for each request

            for page_idx, page_data in enumerate(pack.pages):
                for caption_idx, caption_info in enumerate(page_data.image_captions):
                    if caption_info["caption"] is None:
                        all_caption_requests.append({
                            "path": caption_info["image_path"],
                            "figure_label": caption_info["figure_label"],
                            "surrounding_context": caption_info["surrounding_context"],
                        })
                        caption_indices.append((page_idx, caption_idx))

            if all_caption_requests:
                num_images = len(all_caption_requests)

                if self.caption_server_url:
                    # Async parallel captioning via vllm-mlx server
                    if progress_callback:
                        progress_callback(0, num_images, f"Captioning {num_images} images (server)...")
                    captions = self._run_parallel_captioning(all_caption_requests)

                elif num_images > 1:
                    # Batch captioning via mlx-vlm batch_generate (efficient for multiple images)
                    if progress_callback:
                        progress_callback(0, num_images, f"Captioning {num_images} images (batch)...")
                    try:
                        captions = self._caption_images_batch(all_caption_requests)
                    except Exception as e:
                        # Fallback to sequential on error
                        if progress_callback:
                            progress_callback(0, num_images, f"Batch failed, falling back to sequential...")
                        captions = []
                        for idx, req in enumerate(all_caption_requests):
                            try:
                                caption = self._caption_image(
                                    req["path"],
                                    req["figure_label"],
                                    req["surrounding_context"]
                                )
                            except Exception:
                                caption = f"[{req['figure_label'] or 'Image'}]"
                            captions.append(caption)
                else:
                    # Single image - use direct generation
                    if progress_callback:
                        progress_callback(0, 1, "Captioning 1 image...")
                    req = all_caption_requests[0]
                    try:
                        captions = [self._caption_image(
                            req["path"],
                            req["figure_label"],
                            req["surrounding_context"]
                        )]
                    except Exception:
                        captions = [f"[{req['figure_label'] or 'Image'}]"]

                # Update page data with captions
                for (page_idx, caption_idx), caption in zip(caption_indices, captions):
                    pack.pages[page_idx].image_captions[caption_idx]["caption"] = caption

        # Phase 4: Create searchable chunks from image captions
        # This makes figure captions searchable via BM25 and semantic retrieval
        # Critical for queries like "What does Figure 1 show?" to find the right page
        for page_data in pack.pages:
            for img_cap in page_data.image_captions:
                if img_cap.get("caption"):
                    label = img_cap["figure_label"] or "Image"
                    # Format: "[Figure 1 on Page 3]: The Transformer architecture..."
                    caption_text = f"[{label} on Page {page_data.page_num}]: {img_cap['caption']}"

                    pack.chunks.append({
                        "text": caption_text,
                        "page_num": page_data.page_num,
                        "start": 0,
                        "end": len(caption_text),
                        "is_image_caption": True,
                        "figure_label": img_cap["figure_label"],
                        "image_path": img_cap.get("image_path"),
                        "bbox": img_cap.get("bbox"),
                    })

        # Phase 5: Precompute chunk embeddings and BM25 index (speeds up first query)
        if self.precompute_embeddings and pack.chunks:
            import re
            from rank_bm25 import BM25Okapi

            num_chunks = len(pack.chunks)
            if progress_callback:
                progress_callback(0, num_chunks, f"Computing embeddings for {num_chunks} chunks...")

            # Compute embeddings (~1000ms savings on first query)
            embed_model = self._load_embed_model()
            chunk_texts = [c["text"] for c in pack.chunks]
            pack._chunk_embeddings = embed_model.encode(chunk_texts, show_progress_bar=False)

            # Build BM25 index (~200-300ms savings on first query)
            def tokenize(text: str) -> list:
                tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
                return [t for t in tokens if len(t) > 2]

            tokenized_corpus = [tokenize(c["text"]) for c in pack.chunks]
            pack._bm25_index = BM25Okapi(tokenized_corpus)
            pack._bm25_corpus_id = pack.file_id

            if progress_callback:
                progress_callback(num_chunks, num_chunks, "Embeddings and BM25 index computed")

        # Save to cache
        self._save_to_cache(pack)

        if progress_callback:
            progress_callback(num_pages, num_pages, "Complete")

        return pack


# =============================================================================
# Query Pipeline (The "Query Many" Phase)
# =============================================================================

class PDFQueryEngine:
    """
    Query engine for DocumentPack with retrieval.

    This is the "query many" phase - retrieves relevant content
    and optionally uses VLM for visual pages.
    """

    def __init__(
        self,
        model_path: str = "mlx-community/Qwen3-VL-30B-A3B-Instruct-4bit",
        top_k_chunks: int = 8,
        top_k_pages: int = 3,
        resolution: MediaResolution = MediaResolution.MED,
        use_reranker: bool = False,
        reranker_model: str = "Qwen/Qwen3-Reranker-0.6B",
        reranker_backend: str = "qwen3",  # "qwen3" (pointwise) or "jina" (listwise, 5-7x faster for ≤30 docs)
        rerank_top_n: int = 50,  # Retrieve top-N, then rerank to top_k_chunks
        preload_vlm: bool = False,  # Start loading VLM in background immediately
        preload_reranker: bool = False,  # Start loading reranker in background immediately
        bm25_weight: float = 0.3,  # Weight for BM25 (exact keyword matching) in hybrid retrieval
        embedding_weight: float = 0.7,  # Weight for embeddings (semantic similarity) in hybrid retrieval
        server_url: Optional[str] = None,  # vllm-mlx server URL for prefix caching (e.g., "http://localhost:8000")
    ):
        self.model_path = model_path
        self.top_k_chunks = top_k_chunks
        self.top_k_pages = top_k_pages
        self.resolution = resolution
        self.use_reranker = use_reranker
        self.reranker_model = reranker_model
        self.reranker_backend = reranker_backend
        # Jina reranker is faster for ≤30 docs; adjust default if using jina
        self.rerank_top_n = rerank_top_n if reranker_backend != "jina" or rerank_top_n <= 30 else 20

        # Hybrid retrieval weights (BM25 + embeddings)
        self.bm25_weight = bm25_weight
        self.embedding_weight = embedding_weight

        # Server mode for prefix caching (vllm-mlx)
        self.server_url = server_url.rstrip('/') if server_url else None

        # Lazy-loaded VLM (not needed when using server)
        self._model = None
        self._processor = None
        self._vlm_loading = False  # True while background loading
        self._vlm_lock = None  # Thread lock for VLM loading

        # Lazy-loaded embedding model
        self._embed_model = None

        # Lazy-loaded reranker model (Qwen3-Reranker or Jina)
        self._reranker_model = None
        self._reranker_tokenizer = None
        self._reranker_yes_id = None
        self._reranker_no_id = None
        self._jina_reranker = None  # Jina MLX reranker instance
        self._reranker_loading = False  # True while background loading
        self._last_rerank_time = 0  # Track reranking time for reporting

        # BM25 index for hybrid retrieval
        self._bm25_index = None
        self._bm25_corpus_id = None

        # Start background VLM loading if requested (skip if using server)
        if preload_vlm and not self.server_url:
            self._start_vlm_preload()

        # Start background reranker loading if requested
        if preload_reranker and use_reranker:
            self._start_reranker_preload()

    def _start_vlm_preload(self):
        """Start loading VLM in a background thread."""
        import threading

        if self._model is not None or self._vlm_loading:
            return  # Already loaded or loading

        # Pre-import modules in main thread to avoid thread-safety issues
        # with transformers/tokenizers lazy imports
        try:
            from questmind.inference import load as _load
            import transformers  # noqa: F401 - Force full import
        except ImportError as e:
            print(f"[Background] VLM preload skipped (import error): {e}")
            return

        self._vlm_lock = threading.Lock()
        self._vlm_loading = True

        def load_vlm_background():
            try:
                from questmind.inference import load
                print(f"[Background] Loading VLM: {self.model_path}")
                model, processor = load(self.model_path)
                with self._vlm_lock:
                    self._model = model
                    self._processor = processor
                    self._vlm_loading = False
                print(f"[Background] VLM loaded successfully")
            except Exception as e:
                print(f"[Background] VLM loading failed: {e}")
                self._vlm_loading = False

        thread = threading.Thread(target=load_vlm_background, daemon=True)
        thread.start()

    def _start_reranker_preload(self):
        """Start loading reranker in a background thread."""
        import threading

        self._reranker_loading = True

        def load_reranker_background():
            try:
                # Load directly without checking _reranker_loading (we're the one loading)
                if self.reranker_backend == "jina":
                    self._load_jina_reranker_impl()
                else:
                    self._load_reranker_impl()
                self._reranker_loading = False
                print(f"[Background] Reranker loaded successfully")
            except Exception as e:
                print(f"[Background] Reranker loading failed: {e}")
                self._reranker_loading = False

        thread = threading.Thread(target=load_reranker_background, daemon=True)
        thread.start()

    def _load_vlm(self):
        """Load VLM, waiting for background load if in progress."""
        if self._model is not None:
            return  # Already loaded

        # If background loading is in progress, wait for it
        if self._vlm_loading and self._vlm_lock:
            print("Waiting for background VLM load to complete...")
            # Spin-wait for background load to finish
            import time
            while self._vlm_loading:
                time.sleep(0.1)
            if self._model is not None:
                return  # Background load succeeded

        # Load synchronously if not already loaded
        from questmind.inference import load
        print(f"Loading VLM: {self.model_path}")
        self._model, self._processor = load(self.model_path)

    # =========================================================================
    # Server Mode Methods (vllm-mlx with prefix caching)
    # =========================================================================

    def _query_server_streaming(
        self,
        messages: List[dict],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> Iterator[dict]:
        """
        Stream responses from vllm-mlx server.

        Yields chunks with 'content' and 'usage' fields.
        Server provides prefix caching for 10-28x speedup on repeated prefixes.
        """
        import json
        import urllib.request
        import urllib.error

        url = f"{self.server_url}/v1/chat/completions"
        payload = json.dumps({
            "model": self.model_path,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},  # Request usage stats in final chunk
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            yield chunk
                        except json.JSONDecodeError:
                            continue
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to server {self.server_url}: {e}")

    def _query_server(
        self,
        messages: List[dict],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> Tuple[str, dict]:
        """
        Query vllm-mlx server (non-streaming).

        Returns: (response_text, usage_dict)
        """
        import json
        import urllib.request
        import urllib.error

        url = f"{self.server_url}/v1/chat/completions"
        payload = json.dumps({
            "model": self.model_path,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                data = json.loads(response.read().decode('utf-8'))
                text = data['choices'][0]['message']['content']
                usage = data.get('usage', {})
                return text, usage
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to server {self.server_url}: {e}")

    def _encode_image_base64(self, image_path: str) -> str:
        """Encode image to base64 data URL for server API."""
        import base64
        import mimetypes

        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "image/png"

        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        return f"data:{mime_type};base64,{image_data}"

    def _load_embedder(self):
        if self._embed_model is None:
            from sentence_transformers import SentenceTransformer
            print("Loading embedding model: all-MiniLM-L6-v2")
            self._embed_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _load_reranker(self):
        """Load Qwen3-Reranker for cross-encoder reranking."""
        # Wait for background loading if in progress
        if self._reranker_loading:
            import time
            print("Waiting for background reranker load to complete...")
            while self._reranker_loading:
                time.sleep(0.1)
            if self._reranker_model is not None:
                return  # Background load completed

        self._load_reranker_impl()

    def _load_reranker_impl(self):
        """Actual Qwen3-Reranker loading implementation."""
        if self._reranker_model is None:
            from mlx_lm import load
            print(f"Loading reranker: {self.reranker_model}")
            self._reranker_model, self._reranker_tokenizer = load(self.reranker_model)
            self._reranker_yes_id = self._reranker_tokenizer.convert_tokens_to_ids("yes")
            self._reranker_no_id = self._reranker_tokenizer.convert_tokens_to_ids("no")

    def _load_jina_reranker(self):
        """Load jina-reranker-v3-mlx for fast listwise reranking."""
        # Wait for background loading if in progress
        if self._reranker_loading:
            import time
            print("Waiting for background reranker load to complete...")
            while self._reranker_loading:
                time.sleep(0.1)
            if self._jina_reranker is not None:
                return  # Background load completed

        self._load_jina_reranker_impl()

    def _load_jina_reranker_impl(self):
        """Actual jina-reranker-v3-mlx loading implementation."""
        if self._jina_reranker is None:
            import os
            import sys
            from huggingface_hub import snapshot_download

            print("Loading reranker: jinaai/jina-reranker-v3-mlx")
            # Download model if needed
            model_path = snapshot_download("jinaai/jina-reranker-v3-mlx")

            # Add model path to sys.path to import rerank.py
            if model_path not in sys.path:
                sys.path.insert(0, model_path)

            # Import and instantiate the MLXReranker
            from rerank import MLXReranker
            projector_path = os.path.join(model_path, "projector.safetensors")
            self._jina_reranker = MLXReranker(model_path=model_path, projector_path=projector_path)

            # Remove from sys.path to avoid pollution
            if model_path in sys.path:
                sys.path.remove(model_path)

    def _rerank_score(self, query: str, document: str) -> float:
        """
        Compute relevance score for a query-document pair using Qwen3-Reranker.

        Uses "yes/no" token prediction - the model judges if the document
        is relevant to the query and outputs probability of "yes".

        Returns:
            Score between 0 and 1 (higher = more relevant)
        """
        import mlx.core as mx

        self._load_reranker()

        # Format prompt for Qwen3-Reranker
        instruction = "Given a query, retrieve relevant passages that answer the query"
        content = f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {document}"

        prompt = (
            "<|im_start|>system\n"
            "Judge whether the Document meets the requirements based on the Query and the Instruct provided. "
            "Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n"
            "<|im_start|>user\n"
            f"{content}<|im_end|>\n"
            "<|im_start|>assistant\n"
            "<think>\n\n</think>\n\n"
        )

        # Tokenize and get logits
        tokens = self._reranker_tokenizer.encode(prompt, add_special_tokens=False)
        input_ids = mx.array([tokens])
        logits = self._reranker_model(input_ids)

        # Get logits for yes/no tokens at last position
        last_logits = logits[0, -1, :]
        yes_logit = last_logits[self._reranker_yes_id]
        no_logit = last_logits[self._reranker_no_id]

        # Softmax to get probability
        logits_pair = mx.array([no_logit, yes_logit])
        probs = mx.softmax(logits_pair)
        score = float(probs[1])  # Probability of "yes"

        return score

    def _rerank_chunks(self, query: str, chunks: List[dict], top_k: int) -> List[dict]:
        """
        Rerank chunks using cross-encoder and return top-k.

        Args:
            query: The search query
            chunks: List of chunk dicts with "text" field
            top_k: Number of top chunks to return

        Returns:
            Top-k chunks sorted by reranker score
        """
        if not chunks:
            return []

        # Dispatch to appropriate backend
        if self.reranker_backend == "jina":
            return self._rerank_chunks_jina(query, chunks, top_k)

        # Default: Qwen3-Reranker (pointwise)
        scored = []
        for chunk in chunks:
            score = self._rerank_score(query, chunk["text"])
            scored.append({**chunk, "rerank_score": score})

        # Sort by reranker score and return top-k
        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_k]

    def _rerank_chunks_jina(self, query: str, chunks: List[dict], top_k: int) -> List[dict]:
        """
        Rerank chunks using jina-reranker-v3-mlx (listwise, 5-7x faster for ≤30 docs).

        Args:
            query: The search query
            chunks: List of chunk dicts with "text" field
            top_k: Number of top chunks to return

        Returns:
            Top-k chunks sorted by reranker score
        """
        self._load_jina_reranker()

        # Extract document texts
        documents = [chunk["text"] for chunk in chunks]

        # Rerank using jina's listwise approach (all docs in one forward pass)
        results = self._jina_reranker.rerank(query, documents, top_n=top_k)

        # Map results back to original chunk dicts with scores
        scored_chunks = []
        for result in results:
            original_idx = result["index"]
            scored_chunks.append({
                **chunks[original_idx],
                "rerank_score": result["relevance_score"]
            })

        return scored_chunks

    # Note: Query decomposition methods were tested but caused regression.
    # See TODO/HybridPDFProcessor-Optimization-Plan.md section 6.2 for details.
    # Removed: _is_synthesis_question, _decompose_query, _retrieve_multihop

    def _ensure_entity_coverage(
        self,
        pack: DocumentPack,
        question: str,
        retrieved_chunks: List[dict],
    ) -> List[dict]:
        """
        Ensure key entities from question appear in retrieved chunks.

        For comparison questions like "What parallels between Edison and Aravind?",
        if only Edison chunks are retrieved, this does targeted BM25 retrieval
        for "Aravind" to ensure both sides are covered.

        Returns:
            Extended chunk list with additional entity-specific chunks
        """
        import re

        # Extract key entities:
        # 1. Capitalized words/phrases (proper nouns)
        # 2. Quoted terms
        entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', question))
        entities.update(re.findall(r'"([^"]+)"', question))

        # Filter out common words that aren't meaningful entities
        common_words = {
            'What', 'How', 'Why', 'When', 'Where', 'Which', 'Who',
            'Does', 'Did', 'Is', 'Are', 'Was', 'Were', 'The', 'This',
            'According', 'Based', 'Using', 'From', 'About',
        }
        entities = {e for e in entities if e not in common_words and len(e) > 2}

        if not entities:
            return retrieved_chunks

        # Check which entities are missing from retrieved text
        retrieved_text = " ".join(c["text"].lower() for c in retrieved_chunks)
        missing = [e for e in entities if e.lower() not in retrieved_text]

        if not missing:
            return retrieved_chunks

        # Targeted BM25 retrieval for missing entities
        self._build_bm25_index(pack)

        for entity in missing[:2]:  # Max 2 additional entity retrievals
            query_tokens = re.findall(r'\b[a-z0-9]+\b', entity.lower())
            query_tokens = [t for t in query_tokens if len(t) > 2]

            if not query_tokens:
                continue

            import numpy as np
            bm25_scores = np.array(self._bm25_index.get_scores(query_tokens))
            top_idx = int(np.argmax(bm25_scores))

            # Only add if score is meaningful (entity actually appears)
            if bm25_scores[top_idx] > 0.5:
                chunk = pack.chunks[top_idx].copy()
                chunk["score"] = float(bm25_scores[top_idx])
                chunk["entity_coverage"] = entity
                retrieved_chunks.append(chunk)

        return retrieved_chunks

    def _build_bm25_index(self, pack: DocumentPack):
        """
        Build BM25 index from document chunks.

        BM25 catches exact keyword matches that dense embeddings miss.
        Used for hybrid retrieval (BM25 + embeddings + RRF fusion).
        """
        # Check if already built for this document (on engine)
        if self._bm25_corpus_id == pack.file_id and self._bm25_index is not None:
            return

        # Check if precomputed during ingestion (on pack)
        if hasattr(pack, '_bm25_index') and pack._bm25_index is not None:
            if hasattr(pack, '_bm25_corpus_id') and pack._bm25_corpus_id == pack.file_id:
                self._bm25_index = pack._bm25_index
                self._bm25_corpus_id = pack.file_id
                return

        from rank_bm25 import BM25Okapi
        import re

        # Tokenize chunks: lowercase, split on non-alphanumeric, filter short tokens
        def tokenize(text: str) -> List[str]:
            tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
            return [t for t in tokens if len(t) > 2]

        tokenized_corpus = [tokenize(c["text"]) for c in pack.chunks]
        self._bm25_index = BM25Okapi(tokenized_corpus)
        self._bm25_corpus_id = pack.file_id

    def _should_use_vlm(
        self,
        pack: DocumentPack,
        question: str,
        relevant_pages: List[int],
        visual_pages_set: set,
        question_is_visual: bool,
        force_vision: bool = False,
    ) -> Tuple[bool, str]:
        """
        Determine if VLM should be used for this query.

        Routes based on document type and content:
        - text: Never use VLM (pure text, no visual content)
        - image_collection: Always use VLM (all content is visual)
        - pdf: Use VLM for scanned/mixed pages or visual questions about visual pages

        Args:
            pack: The document pack
            question: User's question
            relevant_pages: List of relevant page numbers
            visual_pages_set: Set of page numbers with visual content
            question_is_visual: Whether the question asks about visual content
            force_vision: Override to always use VLM

        Returns:
            Tuple of (needs_vision, reason_string)
        """
        # Rule 0: Force vision override
        if force_vision:
            return True, "forced"

        # Rule 1: Text documents never need VLM
        if pack.document_type == "text":
            return False, ""

        # Rule 2: Image collections always need VLM
        if pack.document_type == "image_collection":
            return True, f"Image collection with {pack.total_pages} images"

        # Rule 3: PDF - check for scanned/mixed pages
        for p in relevant_pages:
            if 1 <= p <= len(pack.pages):
                page_type = pack.pages[p-1].page_type
                if page_type in ["scanned", "mixed", "complex_table"]:
                    return True, f"Page {p} is {page_type}, needs VLM for OCR"

        # Rule 4: PDF - visual question about visual pages
        relevant_pages_set = set(relevant_pages)
        visual_overlap = relevant_pages_set & visual_pages_set
        if visual_overlap and question_is_visual:
            return True, f"Visual question + pages {sorted(visual_overlap)} have visual content"

        # Default: no VLM needed
        return False, ""

    def query(
        self,
        pack: DocumentPack,
        question: str,
        force_vision: bool = False,
        specific_pages: Optional[List[int]] = None
    ) -> QueryResult:
        """
        Query a DocumentPack.

        Args:
            pack: The ingested document
            question: User's question
            force_vision: If True, always use VLM even for text pages
            specific_pages: If set, only consider these pages

        Returns:
            QueryResult with answer and sources
        """
        timing = {"retrieval": 0, "vlm": 0, "total": 0}
        start_total = time.perf_counter()

        # Check if this is a visual question before retrieval
        question_is_visual = is_visual_question(question)
        visual_pages_set = set(pack.visual_pages) if pack.visual_pages else set()

        # For image collections, skip retrieval - all images are sent to VLM
        # Images ARE the content, no text-based retrieval needed
        if pack.document_type == "image_collection":
            relevant_chunks = pack.chunks  # All chunks
            relevant_pages = list(range(1, pack.total_pages + 1))  # All pages
            timing["retrieval"] = 0
            timing["embedding"] = 0
            timing["bm25"] = 0
            timing["rerank"] = 0
        else:
            # Step 1: Retrieve relevant content (for PDFs and text)
            start_retrieval = time.perf_counter()
            relevant_chunks = self._retrieve_chunks(
                pack, question, specific_pages,
                bm25_weight=self.bm25_weight,
                embedding_weight=self.embedding_weight,
                visual_boost_pages=visual_pages_set if question_is_visual else None
            )

            # Step 1.5: Ensure entity coverage for comparison questions
            # If question mentions "Edison + Aravind" but only Edison chunks retrieved,
            # do targeted retrieval for Aravind
            relevant_chunks = self._ensure_entity_coverage(pack, question, relevant_chunks)

            relevant_pages = self._get_relevant_pages(pack, relevant_chunks)
            timing["retrieval"] = time.perf_counter() - start_retrieval
            timing["embedding"] = getattr(self, '_last_embedding_time', 0)  # Captured during _retrieve_chunks
        timing["bm25"] = getattr(self, '_last_bm25_time', 0)  # Captured during _retrieve_chunks
        timing["rerank"] = self._last_rerank_time  # Captured during _retrieve_chunks

        # Step 2: Determine if we need vision (document-type aware routing)
        needs_vision, vlm_reason = self._should_use_vlm(
            pack, question, relevant_pages[:self.top_k_pages],
            visual_pages_set, question_is_visual, force_vision
        )

        # Log auto-routing decision
        if vlm_reason and vlm_reason != "forced":
            print(f"[Auto-VLM] {vlm_reason}")

        # Determine pages to use for VLM queries
        # For image collections, send ALL images (they are the content)
        # Use vllm-mlx server mode with prefix caching for multi-turn performance
        pages_for_vlm = relevant_pages
        if pack.document_type == "image_collection":
            pages_for_vlm = list(range(1, pack.total_pages + 1))

        # Step 3: Build context and generate answer
        if needs_vision:
            self._load_vlm()
            start_vlm = time.perf_counter()

            answer, sources, gen_timing = self._query_with_vision(
                pack, question, relevant_chunks, pages_for_vlm
            )
            timing["vlm"] = time.perf_counter() - start_vlm
            method = "text_with_vision"
        else:
            start_llm = time.perf_counter()
            answer, sources, gen_timing = self._query_text_only(
                pack, question, relevant_chunks
            )
            timing["llm"] = time.perf_counter() - start_llm
            method = "text_only"

        # Add generation timing details (TTFT, tokens, tps)
        timing.update(gen_timing)
        timing["total"] = time.perf_counter() - start_total

        # Determine which pages were actually used
        if needs_vision:
            actual_pages_used = pages_for_vlm
        else:
            actual_pages_used = relevant_pages[:self.top_k_pages]

        return QueryResult(
            answer=answer,
            sources=sources,
            pages_used=actual_pages_used,
            method=method,
            timing=timing
        )

    def _retrieve_chunks(
        self,
        pack: DocumentPack,
        question: str,
        specific_pages: Optional[List[int]] = None,
        use_hybrid: bool = True,
        bm25_weight: float = 0.3,
        embedding_weight: float = 0.7,
        visual_boost_pages: Optional[set] = None,
    ) -> List[dict]:
        """
        Retrieve relevant chunks using hybrid BM25 + semantic similarity with RRF fusion.

        Hybrid retrieval combines:
        - BM25: Catches exact keyword matches (e.g., "lycra", "union", "tactical")
        - Embeddings: Catches semantic similarity (synonyms, paraphrases)
        - RRF fusion: Reciprocal Rank Fusion to combine both rankings

        Also includes adjacent chunks from the same page to handle
        content that spans chunk boundaries.

        Args:
            visual_boost_pages: Set of page numbers to boost for visual questions.
                               Chunks from these pages get a 1.5x score multiplier.
        """
        import numpy as np
        import re

        self._load_embedder()

        # Track embedding search time
        embed_start = time.perf_counter()

        # Get or compute chunk embeddings (cached on pack object)
        if not hasattr(pack, '_chunk_embeddings') or pack._chunk_embeddings is None:
            chunk_texts = [c["text"] for c in pack.chunks]
            pack._chunk_embeddings = self._embed_model.encode(chunk_texts, show_progress_bar=False)

        # Embed question
        q_embedding = self._embed_model.encode([question], show_progress_bar=False)[0]

        # Compute embedding similarities
        embedding_scores = np.dot(pack._chunk_embeddings, q_embedding)

        self._last_embedding_time = time.perf_counter() - embed_start

        # Track BM25 search time
        bm25_start = time.perf_counter()

        # Compute BM25 scores if hybrid mode enabled
        if use_hybrid:
            try:
                self._build_bm25_index(pack)
                query_tokens = re.findall(r'\b[a-z0-9]+\b', question.lower())
                query_tokens = [t for t in query_tokens if len(t) > 2]
                bm25_scores = np.array(self._bm25_index.get_scores(query_tokens))
            except Exception as e:
                # Fallback to embedding-only if BM25 fails
                print(f"BM25 failed, using embedding-only: {e}")
                use_hybrid = False
                bm25_scores = np.zeros(len(pack.chunks))
        else:
            bm25_scores = np.zeros(len(pack.chunks))

        self._last_bm25_time = time.perf_counter() - bm25_start

        # RRF fusion: combine rankings
        if use_hybrid and bm25_scores.max() > 0:
            # Normalize scores to [0, 1]
            emb_norm = embedding_scores.copy()
            bm25_norm = bm25_scores.copy()

            if emb_norm.max() > 0:
                emb_norm = emb_norm / emb_norm.max()
            if bm25_norm.max() > 0:
                bm25_norm = bm25_norm / bm25_norm.max()

            # RRF: 1/(k + rank) where k=60 is standard
            k = 60
            emb_ranks = np.argsort(np.argsort(-embedding_scores))  # Rank positions
            bm25_ranks = np.argsort(np.argsort(-bm25_scores))

            rrf_scores = (
                embedding_weight * (1.0 / (k + emb_ranks)) +
                bm25_weight * (1.0 / (k + bm25_ranks))
            )

            # Use RRF scores for ranking
            final_scores = rrf_scores

            # Anchor boost: disabled - caused performance regression
            # TODO: revisit with different approach (supplementary context, not boosting)
            # anchor_boost = 1.3
            # bm25_threshold = 0.5  # Only boost if BM25 shows keyword relevance
            # for idx, chunk in enumerate(pack.chunks):
            #     if chunk.get("is_anchor") and bm25_norm[idx] > bm25_threshold:
            #         final_scores[idx] *= anchor_boost
        else:
            # Embedding-only mode
            final_scores = embedding_scores

        # Visual page boost: for visual questions, boost chunks from pages with visual content
        # This helps retrieve pages with diagrams/charts that might not match on text
        if visual_boost_pages:
            visual_boost = 1.5  # 50% boost for visual pages
            for idx, chunk in enumerate(pack.chunks):
                if chunk["page_num"] in visual_boost_pages:
                    final_scores[idx] *= visual_boost

        # Figure caption boost: when query mentions "Figure X", strongly boost matching caption chunks
        # This ensures queries like "What does Figure 1 show?" retrieve the caption for Figure 1
        fig_match = re.search(r'(?:figure|fig\.?)\s*(\d+)', question, re.IGNORECASE)
        if fig_match:
            target_figure = f"Figure {fig_match.group(1)}"
            figure_boost = 3.0  # Strong boost to ensure caption ranks highly
            for idx, chunk in enumerate(pack.chunks):
                if chunk.get("is_image_caption") and chunk.get("figure_label") == target_figure:
                    final_scores[idx] *= figure_boost

        # Get top-k indices
        top_indices = np.argsort(final_scores)[::-1]

        # Build index mapping for adjacent chunk lookup
        chunk_by_page = {}
        for idx, chunk in enumerate(pack.chunks):
            page = chunk["page_num"]
            if page not in chunk_by_page:
                chunk_by_page[page] = []
            chunk_by_page[page].append(idx)

        # Determine how many candidates to collect
        # If using reranker, get more candidates first, then rerank
        candidates_to_collect = self.rerank_top_n if self.use_reranker else self.top_k_chunks

        # Collect candidate matches
        candidate_matches = []
        for idx in top_indices:
            if len(candidate_matches) >= candidates_to_collect:
                break

            chunk = pack.chunks[idx]
            if specific_pages and chunk["page_num"] not in specific_pages:
                continue

            candidate_matches.append(idx)

        # Apply cross-encoder reranking if enabled
        if self.use_reranker and len(candidate_matches) > self.top_k_chunks:
            # Get chunk texts for reranking
            rerank_start = time.perf_counter()
            candidate_chunks = [pack.chunks[idx] for idx in candidate_matches]
            reranked = self._rerank_chunks(question, candidate_chunks, self.top_k_chunks)

            # Map back to indices
            reranked_texts = {c["text"] for c in reranked}
            top_matches = [idx for idx in candidate_matches if pack.chunks[idx]["text"] in reranked_texts][:self.top_k_chunks]
            self._last_rerank_time = time.perf_counter() - rerank_start
        else:
            top_matches = candidate_matches[:self.top_k_chunks]
            self._last_rerank_time = 0

        # Now expand ALL top matches to include adjacent chunks (2 on each side)
        selected_indices = set(top_matches)
        for idx in top_matches:
            page_chunks = chunk_by_page.get(pack.chunks[idx]["page_num"], [])
            chunk_pos = page_chunks.index(idx) if idx in page_chunks else -1
            if chunk_pos >= 0:
                # Add up to 2 previous chunks on same page
                for offset in [1, 2]:
                    if chunk_pos >= offset:
                        selected_indices.add(page_chunks[chunk_pos - offset])
                # Add up to 2 next chunks on same page
                for offset in [1, 2]:
                    if chunk_pos + offset < len(page_chunks):
                        selected_indices.add(page_chunks[chunk_pos + offset])

        # Build scored chunks list, sorted by final score
        scored_chunks = []
        for idx in selected_indices:
            chunk = pack.chunks[idx]
            scored_chunks.append({
                **chunk,
                "score": float(final_scores[idx]),
                "embedding_score": float(embedding_scores[idx]),
                "bm25_score": float(bm25_scores[idx]) if use_hybrid else 0.0,
            })

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        return scored_chunks

    def _get_relevant_pages(
        self,
        pack: DocumentPack,
        chunks: List[dict]
    ) -> List[int]:
        """Get unique pages from chunks, ordered by relevance."""
        seen = set()
        pages = []
        for chunk in chunks:
            pn = chunk["page_num"]
            if pn not in seen:
                seen.add(pn)
                pages.append(pn)
        return pages

    def _query_text_only(
        self,
        pack: DocumentPack,
        question: str,
        chunks: List[dict]
    ) -> Tuple[str, List[dict]]:
        """
        Answer using VLM (text-only mode) with two-pass extraction.

        Uses a two-pass approach:
        1. Extract all relevant facts from the chunks
        2. Generate final answer using extracted facts

        This prevents generation from dropping details when retrieval is correct.
        Uses the same VLM model as vision queries for unified model loading.

        If server_url is set, uses vllm-mlx server for prefix caching benefits.
        """
        import re

        # Build context from chunks
        context_parts = []
        sources = []

        for chunk in chunks[:self.top_k_chunks]:
            context_parts.append(f"[Page {chunk['page_num']}]: {chunk['text']}")
            sources.append({
                "page_num": chunk["page_num"],
                "text_snippet": chunk["text"][:100] + "...",
                "relevance": chunk.get("score", 0)
            })

        context = "\n\n".join(context_parts)

        # Pass 1: Extract relevant facts
        extract_messages = [
            {
                'role': 'system',
                'content': 'You are a precise fact extractor. Given document excerpts and a question, '
                           'extract ALL facts that could be relevant to answering the question. '
                           'Quote exact phrases where possible. Be thorough - do not skip any potentially relevant details. '
                           'Pay special attention to: (1) specific numbers and metrics, (2) comparisons and improvements over baselines, '
                           '(3) claims about state-of-the-art or best results, (4) training costs or efficiency gains. '
                           'Output a bullet list of facts. Do not answer the question yet.'
            },
            {
                'role': 'user',
                'content': f'Document excerpts:\n\n{context}\n\nQuestion: {question}\n\n'
                           'Extract all relevant facts from the excerpts. Include any comparative claims '
                           '(e.g., "X% improvement over Y", "better than previous best by Z"):'
            }
        ]

        vlm_timing = {}
        start_time = time.perf_counter()

        # Use server mode if available (prefix caching)
        if self.server_url:
            return self._query_text_only_server(
                question, context, extract_messages, sources, start_time
            )

        # Direct MLX-VLM mode
        from questmind.inference import stream_generate
        self._load_vlm()

        extract_prompt = self._processor.apply_chat_template(
            extract_messages, add_generation_prompt=True, tokenize=False
        )

        first_token_time = None

        # Pass 1: Extract facts (stream to get TTFT)
        extracted_facts = ""
        for response in stream_generate(
            self._model,
            self._processor,
            extract_prompt,
            max_tokens=600
        ):
            if first_token_time is None:
                first_token_time = time.perf_counter()
                # True TTFT: time from request to first token
                vlm_timing["ttft"] = first_token_time - start_time

            extracted_facts += response.text if hasattr(response, 'text') else str(response)
            # Capture metrics
            if hasattr(response, 'prompt_tokens'):
                vlm_timing["extract_prompt_tokens"] = response.prompt_tokens
            if hasattr(response, 'generation_tokens'):
                vlm_timing["extract_gen_tokens"] = response.generation_tokens

        # Strip thinking blocks from extraction
        extracted_facts = re.sub(r'<think>.*?</think>\s*', '', extracted_facts, flags=re.DOTALL)
        extracted_facts = re.sub(r'<think>.*$', '', extracted_facts, flags=re.DOTALL)
        extracted_facts = extracted_facts.strip()

        # Pass 2: Generate final answer using extracted facts
        answer_messages = [
            {
                'role': 'system',
                'content': 'Answer the question using the extracted facts provided. '
                           'Be complete but concise. Include all relevant details from the facts. '
                           'When metrics are involved, always include comparative improvements '
                           '(e.g., "X achieved Y, improving over previous best by Z"). '
                           'Answer directly without showing your thinking process.'
            },
            {
                'role': 'user',
                'content': f'Extracted facts from the document:\n{extracted_facts}\n\n'
                           f'Question: {question}\n\n'
                           'Provide a complete answer. Include any comparative claims or improvements mentioned in the facts:'
            }
        ]

        answer_prompt = self._processor.apply_chat_template(
            answer_messages, add_generation_prompt=True, tokenize=False
        )

        # Pass 2: Generate answer (stream for metrics)
        answer = ""
        for response in stream_generate(
            self._model,
            self._processor,
            answer_prompt,
            max_tokens=500
        ):
            answer += response.text if hasattr(response, 'text') else str(response)
            # Capture final metrics from answer pass
            if hasattr(response, 'prompt_tokens'):
                vlm_timing["answer_prompt_tokens"] = response.prompt_tokens
            if hasattr(response, 'generation_tokens'):
                vlm_timing["answer_gen_tokens"] = response.generation_tokens
            if hasattr(response, 'prompt_tps'):
                vlm_timing["prompt_tps"] = response.prompt_tps
            if hasattr(response, 'generation_tps'):
                vlm_timing["generation_tps"] = response.generation_tps
            if hasattr(response, 'peak_memory'):
                vlm_timing["peak_memory_gb"] = response.peak_memory

        # Strip any thinking blocks if present (safety for thinking models)
        answer = re.sub(r'<think>.*?</think>\s*', '', answer, flags=re.DOTALL)
        answer = re.sub(r'<think>.*$', '', answer, flags=re.DOTALL)
        answer = answer.strip()

        return answer, sources, vlm_timing

    def _query_text_only_server(
        self,
        question: str,
        context: str,
        extract_messages: List[dict],
        sources: List[dict],
        start_time: float
    ) -> Tuple[str, List[dict], dict]:
        """
        Text-only query using vllm-mlx server (prefix caching enabled).

        Two-pass approach same as direct mode, but benefits from server's
        prefix caching for repeated system prompts.
        """
        import re

        vlm_timing = {"server_mode": True}
        first_token_time = None

        # Pass 1: Extract facts via server (streaming)
        extracted_facts = ""
        for chunk in self._query_server_streaming(extract_messages, max_tokens=600):
            if first_token_time is None:
                first_token_time = time.perf_counter()
                vlm_timing["ttft"] = first_token_time - start_time

            # Extract content from streaming chunk
            if 'choices' in chunk and chunk['choices']:
                delta = chunk['choices'][0].get('delta', {})
                content = delta.get('content', '')
                if content:
                    extracted_facts += content

            # Capture usage from final chunk (only present when include_usage=true)
            if chunk.get('usage'):
                vlm_timing["extract_prompt_tokens"] = chunk['usage'].get('prompt_tokens', 0)
                vlm_timing["extract_gen_tokens"] = chunk['usage'].get('completion_tokens', 0)

        # Strip thinking blocks
        extracted_facts = re.sub(r'<think>.*?</think>\s*', '', extracted_facts, flags=re.DOTALL)
        extracted_facts = re.sub(r'<think>.*$', '', extracted_facts, flags=re.DOTALL)
        extracted_facts = extracted_facts.strip()

        # Pass 2: Generate answer
        answer_messages = [
            {
                'role': 'system',
                'content': 'Answer the question using the extracted facts provided. '
                           'Be complete but concise. Include all relevant details from the facts. '
                           'When metrics are involved, always include comparative improvements '
                           '(e.g., "X achieved Y, improving over previous best by Z"). '
                           'Answer directly without showing your thinking process.'
            },
            {
                'role': 'user',
                'content': f'Extracted facts from the document:\n{extracted_facts}\n\n'
                           f'Question: {question}\n\n'
                           'Provide a complete answer. Include any comparative claims or improvements mentioned in the facts:'
            }
        ]

        answer = ""
        for chunk in self._query_server_streaming(answer_messages, max_tokens=500):
            if 'choices' in chunk and chunk['choices']:
                delta = chunk['choices'][0].get('delta', {})
                content = delta.get('content', '')
                if content:
                    answer += content

            # Capture usage from final chunk (only present when include_usage=true)
            if chunk.get('usage'):
                vlm_timing["answer_prompt_tokens"] = chunk['usage'].get('prompt_tokens', 0)
                vlm_timing["answer_gen_tokens"] = chunk['usage'].get('completion_tokens', 0)

        # Strip thinking blocks
        answer = re.sub(r'<think>.*?</think>\s*', '', answer, flags=re.DOTALL)
        answer = re.sub(r'<think>.*$', '', answer, flags=re.DOTALL)
        answer = answer.strip()

        # Calculate TPS from usage data (combine both passes)
        total_prompt_tokens = vlm_timing.get("extract_prompt_tokens", 0) + vlm_timing.get("answer_prompt_tokens", 0)
        total_gen_tokens = vlm_timing.get("extract_gen_tokens", 0) + vlm_timing.get("answer_gen_tokens", 0)
        elapsed = time.perf_counter() - start_time

        if total_prompt_tokens > 0 and elapsed > 0:
            # For server mode, we can't accurately measure prompt TPS since it includes network latency
            # Use total tokens and time for a combined estimate
            vlm_timing["prompt_tokens"] = total_prompt_tokens
            vlm_timing["generation_tokens"] = total_gen_tokens
            # Calculate generation TPS (more meaningful for streaming)
            if total_gen_tokens > 0:
                vlm_timing["generation_tps"] = total_gen_tokens / elapsed

        return answer, sources, vlm_timing

    def _query_with_vision(
        self,
        pack: DocumentPack,
        question: str,
        chunks: List[dict],
        pages: List[int],
        max_images: Optional[int] = None
    ) -> Tuple[str, List[dict]]:
        """
        Answer using VLM for visual pages.

        If server_url is set, uses vllm-mlx server with base64 images.

        Args:
            max_images: Override for max images (None = use self.top_k_pages)
        """
        # Collect page images
        image_paths = []
        sources = []

        # For image collections, use all passed pages (images are the content)
        # For PDFs, use top_k_pages limit
        if max_images is not None:
            page_limit = max_images
        elif pack.document_type == "image_collection":
            page_limit = len(pages)  # Use all passed pages
        else:
            page_limit = self.top_k_pages

        for page_num in pages[:page_limit]:
            page_data = pack.pages[page_num - 1]

            if page_data.image_path and Path(page_data.image_path).exists():
                image_paths.append(page_data.image_path)
                sources.append({
                    "page_num": page_num,
                    "text_snippet": page_data.summary,
                    "relevance": 1.0
                })

        if not image_paths:
            # Fall back to text-only
            return self._query_text_only(pack, question, chunks)

        # Build text context
        text_context = []
        for chunk in chunks[:3]:  # Top 3 relevant chunks
            snippet = chunk["text"][:300]
            text_context.append(f"Page {chunk['page_num']}: {snippet}")
        context_str = "\n".join(text_context)

        prompt_text = f"""Question: {question}

Relevant text context from these pages:
{context_str}

Instructions:
- Focus on what is actually shown in the figure/diagram, not general knowledge
- If the question asks about "types" or "kinds", identify distinct components or categories visible in the figure
- For architecture diagrams, distinguish between structural components (where things are used) vs mechanisms (how they work)
- Be specific and reference what you see in the image

Based on the images and text context above, provide a specific answer:"""

        start_time = time.perf_counter()

        # Use server mode if available
        if self.server_url:
            return self._query_with_vision_server(
                image_paths, prompt_text, sources, start_time
            )

        # Direct MLX-VLM mode
        from questmind.inference import stream_generate
        self._load_vlm()

        # Build VLM prompt
        content = [{"type": "image", "image": img} for img in image_paths]
        content.append({"type": "text", "text": prompt_text})

        messages = [{"role": "user", "content": content}]
        prompt = self._processor.apply_chat_template(messages, add_generation_prompt=True)

        vlm_timing = {"num_images": len(image_paths)}
        answer = ""
        first_token_time = None

        for response in stream_generate(
            self._model, self._processor, prompt,
            image=image_paths,
            max_tokens=1000
        ):
            if first_token_time is None:
                first_token_time = time.perf_counter()
                vlm_timing["ttft"] = first_token_time - start_time

            answer += response.text if hasattr(response, 'text') else str(response)

            if hasattr(response, 'prompt_tokens'):
                vlm_timing["prompt_tokens"] = response.prompt_tokens
            if hasattr(response, 'prompt_tps'):
                vlm_timing["prompt_tps"] = response.prompt_tps
            if hasattr(response, 'generation_tokens'):
                vlm_timing["generation_tokens"] = response.generation_tokens
            if hasattr(response, 'generation_tps'):
                vlm_timing["generation_tps"] = response.generation_tps
            if hasattr(response, 'peak_memory'):
                vlm_timing["peak_memory_gb"] = response.peak_memory

        return answer, sources, vlm_timing

    def _query_with_vision_server(
        self,
        image_paths: List[str],
        prompt_text: str,
        sources: List[dict],
        start_time: float
    ) -> Tuple[str, List[dict], dict]:
        """
        Vision query using vllm-mlx server with base64 images.

        Server mode with images - benefits from prefix caching for system prompts.
        """
        vlm_timing = {"num_images": len(image_paths), "server_mode": True}
        first_token_time = None

        # Build multimodal content with base64 images
        content = []
        for img_path in image_paths:
            image_url = self._encode_image_base64(img_path)
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        content.append({"type": "text", "text": prompt_text})

        messages = [{"role": "user", "content": content}]

        answer = ""
        for chunk in self._query_server_streaming(messages, max_tokens=1000):
            if first_token_time is None:
                first_token_time = time.perf_counter()
                vlm_timing["ttft"] = first_token_time - start_time

            if 'choices' in chunk and chunk['choices']:
                delta = chunk['choices'][0].get('delta', {})
                text = delta.get('content', '')
                if text:
                    answer += text

            # Capture usage from final chunk (only present when include_usage=true)
            if chunk.get('usage'):
                vlm_timing["prompt_tokens"] = chunk['usage'].get('prompt_tokens', 0)
                vlm_timing["generation_tokens"] = chunk['usage'].get('completion_tokens', 0)

        # Calculate TPS from usage data
        elapsed = time.perf_counter() - start_time
        gen_tokens = vlm_timing.get("generation_tokens", 0)
        if gen_tokens > 0 and elapsed > 0:
            vlm_timing["generation_tps"] = gen_tokens / elapsed

        return answer, sources, vlm_timing

    def get_page_text(self, pack: DocumentPack, page_num: int) -> str:
        """Get full text for a specific page."""
        if 1 <= page_num <= len(pack.pages):
            return pack.pages[page_num - 1].get_text()
        return ""

    def get_page_image(
        self,
        pack: DocumentPack,
        page_num: int,
        resolution: Optional[MediaResolution] = None
    ) -> Optional[str]:
        """Get or render image for a specific page."""
        if not (1 <= page_num <= len(pack.pages)):
            return None

        page_data = pack.pages[page_num - 1]

        # Return cached if exists and resolution matches
        if page_data.image_path and Path(page_data.image_path).exists():
            return page_data.image_path

        # Render on demand
        resolution = resolution or self.resolution
        doc = fitz.open(pack.file_path)
        page = doc[page_num - 1]

        img_path = tempfile.mktemp(suffix=".png")
        render_page_to_image(page, resolution, img_path)

        doc.close()
        return img_path


# =============================================================================
# Aliases for Document-Type Agnostic API
# =============================================================================

# QueryEngine is an alias for PDFQueryEngine (works for all document types)
# The engine routes to VLM based on document_type in DocumentPack
QueryEngine = PDFQueryEngine
