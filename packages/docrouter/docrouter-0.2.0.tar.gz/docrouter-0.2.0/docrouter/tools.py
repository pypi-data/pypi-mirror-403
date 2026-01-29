"""Tool wrappers for LLM/agent integration with document registry."""
__all__ = [
    'open_document_tool', 'get_file_path_tool', 'get_bytes_tool', 'search_tool',
    'render_page_tool', 'get_text_tool', 'get_unit_text_tool', 'close_document_tool',
    'list_documents', 'clear_registry'
]

from docrouter import (
    open_document, DocumentHandle, DocRouterError,
    UnsupportedFileTypeError, UnsupportedOperationError, ParseError
)
from typing import Any

# === Registry ===
_registry: dict[str, DocumentHandle] = {}

def _get(doc_id: str) -> DocumentHandle:
    """Get document by ID or raise."""
    if doc_id not in _registry:
        raise KeyError(f"document not found: {doc_id}")
    return _registry[doc_id]

def _wrap_error(e: Exception) -> dict:
    """Convert exception to error dict."""
    return {'error': {'type': type(e).__name__, 'message': str(e)}}

def _try(fn) -> dict | Any:
    """Execute fn, returning error dict on exception."""
    try:
        return fn()
    except Exception as e:
        return _wrap_error(e)

# === Tool functions ===
def open_document_tool(inp, filename: str | None = None) -> dict:
    """Open document and register it. Returns {document_id, info}."""
    def do():
        h = open_document(inp, filename)
        _registry[h.document_id] = h
        return {'document_id': h.document_id, 'info': h.info()}
    return _try(do)

def get_file_path_tool(document_id: str) -> dict:
    """Get path to original file."""
    def do():
        h = _get(document_id)
        return {'document_id': document_id, 'file_path': h.get_file_path()}
    return _try(do)

def get_bytes_tool(document_id: str) -> dict | bytes:
    """Get original file bytes. Returns bytes on success, error dict on failure."""
    def do():
        return _get(document_id).get_bytes()
    return _try(do)

def get_text_tool(document_id: str) -> dict:
    """Get full document text."""
    def do():
        h = _get(document_id)
        return {'document_id': document_id, 'text': h.get_text()}
    return _try(do)

def get_unit_text_tool(document_id: str, unit_index: int) -> dict:
    """Get text for specific unit."""
    def do():
        return _get(document_id).get_unit_text(unit_index)
    return _try(do)

def search_tool(document_id: str, query: str, *, before: int = 300, after: int = 300,
                max_hits: int = 5, mode: str = 'window', unit_start: int | None = None,
                unit_end: int | None = None, case_sensitive: bool = False) -> dict:
    """Search document for literal substring."""
    def do():
        return _get(document_id).search(
            query, before=before, after=after, max_hits=max_hits,
            mode=mode, unit_start=unit_start, unit_end=unit_end, case_sensitive=case_sensitive
        )
    return _try(do)

def render_page_tool(document_id: str, page_index: int, *, dpi: int = 150,
                     image_format: str = 'png') -> dict:
    """Render PDF page to image. Returns {document_id, image_path, ...}."""
    def do():
        return _get(document_id).render_page(page_index, dpi=dpi, image_format=image_format)
    return _try(do)

def close_document_tool(document_id: str) -> dict:
    """Close and unregister document."""
    def do():
        if document_id in _registry:
            del _registry[document_id]
        return {'document_id': document_id, 'closed': True}
    return _try(do)

# === Registry utilities ===
def list_documents() -> list[dict]:
    """List all registered documents."""
    return [{'document_id': k, **v.info()} for k, v in _registry.items()]

def clear_registry() -> None:
    """Clear all registered documents."""
    _registry.clear()
