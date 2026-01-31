"""
QuestMind - Local VLM server and document processor for Apple Silicon.

Architecture:
- Ingest once: analyze, extract, index
- Query many: retrieve relevant pages/chunks per question
- VLM selective: only for pages needing visual understanding

Supports multiple document types:
- PDF files (PDFIngestor)
- Image collections (ImageIngestor)
- Text files (TextIngestor)

This package provides:
- PDFIngestor: Ingest PDFs into DocumentPacks
- ImageIngestor: Ingest image directories into DocumentPacks
- TextIngestor: Ingest text files into DocumentPacks
- create_ingestor: Factory function to auto-detect document type
- QueryEngine/PDFQueryEngine: Query documents with RAG-style retrieval
- analyze_page: Classify pages as TEXT_NATIVE, SCANNED, MIXED, etc.

Example (PDF - existing API):
    from questmind import PDFIngestor, PDFQueryEngine

    # Ingest once
    ingestor = PDFIngestor()
    pack = ingestor.ingest("document.pdf")

    # Query many times
    engine = PDFQueryEngine()
    result = engine.query(pack, "What is this document about?")
    print(result.answer)

Example (Document-type agnostic - new API):
    from questmind import create_ingestor, QueryEngine

    # Auto-detect and ingest
    pack = create_ingestor("document.pdf").ingest("document.pdf")
    pack = create_ingestor("images/").ingest("images/")
    pack = create_ingestor("readme.md").ingest("readme.md")

    # Query with same engine
    result = QueryEngine().query(pack, "What is this about?")
    print(result.answer)

Server usage (VLM only, no PDF processing):
    from questmind.server import app, load_model

    load_model("mlx-community/Qwen3-VL-30B-A3B-Instruct-4bit")
    # Then run with uvicorn: uvicorn questmind.server:app --host 0.0.0.0 --port 8000
"""

# Lazy import for PDF processor (requires PyMuPDF which may not be installed)
def __getattr__(name):
    """Lazy import for PDF processor components."""
    _pdf_exports = {
        # Enums
        "MediaResolution", "PageType", "DocumentType",
        # Data classes
        "PageAnalysis", "PageData", "DocumentPack", "QueryResult",
        # Functions
        "analyze_page", "extract_native_text", "render_page_to_image",
        "chunk_text", "chunk_text_semantic", "chunk_page_semantic",
        "extract_atoms_from_page", "generate_page_summary",
        "generate_file_id", "create_ingestor",
        # Ingestor classes
        "BaseIngestor", "PDFIngestor", "TextIngestor", "ImageIngestor",
        # Query engine classes
        "PDFQueryEngine", "QueryEngine",
        # Configuration
        "RESOLUTION_CONFIG",
    }
    if name in _pdf_exports:
        from . import pdf_processor
        return getattr(pdf_processor, name)
    raise AttributeError(f"module 'questmind' has no attribute {name!r}")

__version__ = "0.1.0"
__all__ = [
    # Enums
    "MediaResolution",
    "PageType",
    "DocumentType",
    # Data classes
    "PageAnalysis",
    "PageData",
    "DocumentPack",
    "QueryResult",
    # Functions
    "analyze_page",
    "extract_native_text",
    "render_page_to_image",
    "chunk_text",
    "chunk_text_semantic",
    "chunk_page_semantic",
    "extract_atoms_from_page",
    # "extract_page_anchors" - disabled
    "generate_page_summary",
    "generate_file_id",
    "create_ingestor",
    # Ingestor classes
    "BaseIngestor",
    "PDFIngestor",
    "TextIngestor",
    "ImageIngestor",
    # Query engine classes
    "PDFQueryEngine",
    "QueryEngine",
    # Configuration
    "RESOLUTION_CONFIG",
]
