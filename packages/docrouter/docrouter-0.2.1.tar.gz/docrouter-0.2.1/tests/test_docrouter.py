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


# === Tests: Base64 and Chat Content ===
class TestBase64AndChatContent:
    """Tests for get_base64() and to_chat_content() methods."""

    @pytest.fixture
    def png_file(self, tmp_path):
        """Create a minimal valid PNG file."""
        # Minimal 1x1 red PNG
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
            0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x05, 0xFE,
            0xD4, 0xEF, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,  # IEND chunk
            0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        f = tmp_path / "test.png"
        f.write_bytes(png_bytes)
        return f

    @pytest.fixture
    def jpg_file(self, tmp_path):
        """Create a minimal valid JPEG file."""
        # Minimal 1x1 JPEG (simplified)
        try:
            from PIL import Image
            img = Image.new('RGB', (10, 10), color='red')
            f = tmp_path / "test.jpg"
            img.save(f, 'JPEG')
            return f
        except ImportError:
            pytest.skip("Pillow not installed")

    def test_get_base64_image_with_prefix(self, png_file):
        doc = open_document(png_file)
        result = doc.get_base64(mime_prefix=True)
        assert result.startswith('data:image/png;base64,')
        # Check it's valid base64
        import base64
        data_part = result.split(',')[1]
        decoded = base64.b64decode(data_part)
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n'

    def test_get_base64_image_without_prefix(self, png_file):
        doc = open_document(png_file)
        result = doc.get_base64(mime_prefix=False)
        assert not result.startswith('data:')
        # Should be raw base64
        import base64
        decoded = base64.b64decode(result)
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n'

    def test_get_base64_jpg_mime_type(self, jpg_file):
        doc = open_document(jpg_file)
        result = doc.get_base64(mime_prefix=True)
        assert result.startswith('data:image/jpeg;base64,')

    def test_get_base64_unsupported_format(self, txt_file):
        doc = open_document(txt_file)
        with pytest.raises(UnsupportedOperationError):
            doc.get_base64()

    def test_to_chat_content_format(self, png_file):
        doc = open_document(png_file)
        result = doc.to_chat_content()
        assert result['type'] == 'image_url'
        assert 'image_url' in result
        assert 'url' in result['image_url']
        assert result['image_url']['url'].startswith('data:image/png;base64,')

    def test_to_chat_content_unsupported_format(self, txt_file):
        doc = open_document(txt_file)
        with pytest.raises(UnsupportedOperationError):
            doc.to_chat_content()

    def test_get_base64_with_resize(self, jpg_file):
        """Test that max_width/max_height parameters work."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("Pillow not installed")

        doc = open_document(jpg_file)
        # Original is 10x10, resize to max 5x5
        result = doc.get_base64(mime_prefix=False, max_width=5, max_height=5)

        import base64
        decoded = base64.b64decode(result)
        img = Image.open(io.BytesIO(decoded))
        assert img.width <= 5
        assert img.height <= 5


# Import io for the resize test
import io
