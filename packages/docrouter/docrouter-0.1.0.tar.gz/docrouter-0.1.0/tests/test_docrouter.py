"""Tests for docrouter."""
import pytest
import tempfile
from pathlib import Path

from docrouter import (
    open_document, DocumentHandle, DocRouterError,
    UnsupportedFileTypeError, UnsupportedOperationError, ParseError, _chunk
)
from docrouter import tools

# === Fixtures ===
@pytest.fixture
def txt_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello world.\n\nThis is a test document.\n\nIt has multiple paragraphs.")
    return f

@pytest.fixture
def md_file(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("# My Title\n\nSome **bold** text.\n\n## Section\n\nMore content here.")
    return f

@pytest.fixture
def html_file(tmp_path):
    f = tmp_path / "test.html"
    f.write_text("<html><head><title>Test Page</title></head><body><h1>Hello</h1><p>World</p></body></html>")
    return f

@pytest.fixture
def long_txt_file(tmp_path):
    """Create a file with multiple chunks worth of content."""
    f = tmp_path / "long.txt"
    content = "\n\n".join([f"Paragraph {i}. " + "Lorem ipsum dolor sit amet. " * 50 for i in range(20)])
    f.write_text(content)
    return f

# === Tests: _chunk utility ===
class TestChunk:
    def test_empty(self):
        assert _chunk('') == ['']

    def test_short(self):
        assert _chunk('Hello world') == ['Hello world']

    def test_paragraphs(self):
        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = _chunk(text, target=20)
        assert len(chunks) >= 1
        assert 'Para 1' in chunks[0]

    def test_deterministic(self):
        text = "A" * 5000
        c1 = _chunk(text)
        c2 = _chunk(text)
        assert c1 == c2

# === Tests: TxtDoc ===
class TestTxtDoc:
    def test_open(self, txt_file):
        doc = open_document(txt_file)
        assert isinstance(doc, DocumentHandle)
        assert doc.document_id.startswith('doc_')

    def test_info(self, txt_file):
        doc = open_document(txt_file)
        info = doc.info()
        assert info['doc_type'] == 'text'
        assert info['mime_type'] == 'text/plain'
        assert info['unit_type'] == 'chunk'
        assert info['unit_count'] >= 1
        assert info['has_text'] is True
        assert info['filename'] == 'test.txt'

    def test_get_text(self, txt_file):
        doc = open_document(txt_file)
        text = doc.get_text()
        assert 'Hello world' in text
        assert 'multiple paragraphs' in text

    def test_get_bytes(self, txt_file):
        doc = open_document(txt_file)
        raw = doc.get_bytes()
        assert b'Hello world' in raw

    def test_get_file_path(self, txt_file):
        doc = open_document(txt_file)
        path = doc.get_file_path()
        assert Path(path).exists()

    def test_get_unit_text(self, txt_file):
        doc = open_document(txt_file)
        result = doc.get_unit_text(0)
        assert result['document_id'] == doc.document_id
        assert result['unit_index'] == 0
        assert result['unit_type'] == 'chunk'
        assert 'text' in result

    def test_open_from_bytes(self, txt_file):
        raw = txt_file.read_bytes()
        doc = open_document(raw, filename='test.txt')
        assert 'Hello world' in doc.get_text()

# === Tests: MdDoc ===
class TestMdDoc:
    def test_open(self, md_file):
        doc = open_document(md_file)
        info = doc.info()
        assert info['doc_type'] == 'markdown'
        assert info['title'] == 'My Title'

    def test_text(self, md_file):
        doc = open_document(md_file)
        text = doc.get_text()
        assert '# My Title' in text
        assert 'bold' in text

# === Tests: HtmlDoc ===
class TestHtmlDoc:
    def test_open(self, html_file):
        try:
            doc = open_document(html_file)
            info = doc.info()
            assert info['doc_type'] == 'html'
            assert info['title'] == 'Test Page'
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

    def test_text_strips_tags(self, html_file):
        try:
            doc = open_document(html_file)
            text = doc.get_text()
            assert '<h1>' not in text
            assert 'Hello' in text
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

# === Tests: Search ===
class TestSearch:
    def test_basic_search(self, txt_file):
        doc = open_document(txt_file)
        result = doc.search('test')
        assert result['document_id'] == doc.document_id
        assert result['query'] == 'test'
        assert result['mode'] == 'window'
        assert len(result['hits']) >= 1
        hit = result['hits'][0]
        assert 'unit_index' in hit
        assert 'match_start' in hit
        assert 'match_end' in hit
        assert 'snippet' in hit

    def test_case_insensitive(self, txt_file):
        doc = open_document(txt_file)
        result = doc.search('HELLO')
        assert len(result['hits']) >= 1

    def test_case_sensitive(self, txt_file):
        doc = open_document(txt_file)
        result = doc.search('HELLO', case_sensitive=True)
        assert len(result['hits']) == 0

    def test_max_hits(self, long_txt_file):
        doc = open_document(long_txt_file)
        result = doc.search('Lorem', max_hits=3)
        assert len(result['hits']) <= 3

    def test_unit_mode(self, txt_file):
        doc = open_document(txt_file)
        result = doc.search('test', mode='unit')
        assert result['mode'] == 'unit'
        # In unit mode, snippet should be the full unit text
        if result['hits']:
            hit = result['hits'][0]
            unit_text = doc.get_unit_text(hit['unit_index'])['text']
            assert hit['snippet'] == unit_text

    def test_no_hits(self, txt_file):
        doc = open_document(txt_file)
        result = doc.search('xyznotfound')
        assert len(result['hits']) == 0

    def test_window_context(self, txt_file):
        doc = open_document(txt_file)
        result = doc.search('test', before=5, after=5)
        if result['hits']:
            snippet = result['hits'][0]['snippet']
            assert len(snippet) <= 5 + 4 + 5 + 50  # before + len('test') + after + buffer

# === Tests: render_page ===
class TestRenderPage:
    def test_unsupported_for_txt(self, txt_file):
        doc = open_document(txt_file)
        with pytest.raises(UnsupportedOperationError):
            doc.render_page(0)

# === Tests: Errors ===
class TestErrors:
    def test_unsupported_file_type(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("data")
        with pytest.raises(UnsupportedFileTypeError):
            open_document(f)

    def test_bytes_without_filename(self):
        with pytest.raises(ValueError):
            open_document(b"hello")

    def test_invalid_unit_index(self, txt_file):
        doc = open_document(txt_file)
        with pytest.raises(IndexError):
            doc.get_unit_text(9999)

# === Tests: Tools ===
class TestTools:
    def setup_method(self):
        tools.clear_registry()

    def test_open_and_search(self, txt_file):
        result = tools.open_document_tool(str(txt_file))
        assert 'document_id' in result
        assert 'info' in result
        doc_id = result['document_id']

        search_result = tools.search_tool(doc_id, 'test')
        assert search_result['document_id'] == doc_id
        assert 'hits' in search_result

    def test_close_document(self, txt_file):
        result = tools.open_document_tool(str(txt_file))
        doc_id = result['document_id']

        close_result = tools.close_document_tool(doc_id)
        assert close_result['closed'] is True

        # Should now fail
        get_result = tools.get_text_tool(doc_id)
        assert 'error' in get_result

    def test_list_documents(self, txt_file, md_file):
        tools.open_document_tool(str(txt_file))
        tools.open_document_tool(str(md_file))
        docs = tools.list_documents()
        assert len(docs) == 2

    def test_error_returns_dict(self):
        result = tools.get_text_tool('nonexistent')
        assert 'error' in result
        assert result['error']['type'] == 'KeyError'
