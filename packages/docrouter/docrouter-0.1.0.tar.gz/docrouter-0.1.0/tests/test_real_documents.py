"""Tests with real documents: tables, math, structured content."""
import pytest
from pathlib import Path

from docrouter import open_document, UnsupportedOperationError

FIXTURES = Path(__file__).parent / 'fixtures'

# === PDF Tests ===
class TestPDFAttentionPaper:
    """Test with 'Attention Is All You Need' paper - has math and tables."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'attention_paper.pdf')

    def test_info(self, doc):
        info = doc.info()
        assert info['doc_type'] == 'pdf'
        assert info['unit_type'] == 'page'
        assert info['unit_count'] == 15
        assert info['has_text'] is True

    def test_extracts_title_and_authors(self, doc):
        text = doc.get_unit_text(0)['text']
        assert 'Attention Is All You Need' in text
        assert 'Vaswani' in text
        assert 'Google' in text

    def test_extracts_math_formulas(self, doc):
        """Check that math notation is extracted."""
        full_text = doc.get_text()
        # The paper has formulas like softmax, sqrt(d_k), etc.
        assert 'softmax' in full_text.lower()
        assert 'Attention' in full_text
        # Check for mathematical notation remnants
        assert 'd' in full_text  # d_k dimension
        assert 'Q' in full_text or 'K' in full_text or 'V' in full_text  # QKV matrices

    def test_extracts_tables(self, doc):
        """Check table data is extracted (BLEU scores table)."""
        full_text = doc.get_text()
        # Paper has BLEU scores table
        assert 'BLEU' in full_text
        # Should have model performance numbers
        assert '28' in full_text  # BLEU score ~28.4 for EN-DE

    def test_search_finds_transformer(self, doc):
        result = doc.search('Transformer', max_hits=10)
        assert len(result['hits']) > 0
        # Transformer is mentioned many times
        assert len(result['hits']) >= 3

    def test_search_finds_attention_mechanism(self, doc):
        result = doc.search('self-attention', max_hits=5)
        assert len(result['hits']) > 0

    def test_render_page(self, doc):
        """Test PDF page rendering."""
        result = doc.render_page(0, dpi=72)
        assert result['page_index'] == 0
        assert result['dpi'] == 72
        assert result['image_format'] == 'png'
        assert Path(result['image_path']).exists()
        # Check it's a valid PNG
        img_bytes = Path(result['image_path']).read_bytes()
        assert img_bytes[:8] == b'\x89PNG\r\n\x1a\n'


class TestPDFBarclaysReport:
    """Test with Barclays Annual Report - has financial tables."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'barclays_annual_report.pdf')

    def test_info(self, doc):
        info = doc.info()
        assert info['doc_type'] == 'pdf'
        assert info['unit_count'] == 25
        assert 'Barclays' in info.get('title', '')

    def test_extracts_financial_data(self, doc):
        """Check financial figures are extracted."""
        full_text = doc.get_text()
        # Should have currency symbols or amounts
        assert '£' in full_text or 'GBP' in full_text or '$' in full_text
        # Should have percentages
        assert '%' in full_text

    def test_extracts_kpis(self, doc):
        """Check KPI terms are present."""
        full_text = doc.get_text().lower()
        # Financial reports typically have these terms
        financial_terms = ['revenue', 'income', 'expense', 'return', 'capital']
        found = [t for t in financial_terms if t in full_text]
        assert len(found) >= 3, f"Only found: {found}"

    def test_search_financial_terms(self, doc):
        """Search for financial terminology."""
        result = doc.search('operating', max_hits=10)
        assert len(result['hits']) > 0
        # Check snippets contain context
        for hit in result['hits']:
            assert len(hit['snippet']) > 0

    def test_unit_mode_returns_full_page(self, doc):
        """Test unit mode returns complete page text."""
        result = doc.search('Barclays', mode='unit', max_hits=1)
        if result['hits']:
            hit = result['hits'][0]
            page_text = doc.get_unit_text(hit['unit_index'])['text']
            assert hit['snippet'] == page_text


# === DOCX Tests ===
class TestDocxWithTables:
    """Test DOCX with tables."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'report_with_tables.docx')

    def test_info(self, doc):
        info = doc.info()
        assert info['doc_type'] == 'docx'
        assert info['unit_type'] == 'section'
        assert info['has_text'] is True

    def test_extracts_table_data(self, doc):
        """Check table content is extracted."""
        text = doc.get_text()
        # Table headers
        assert 'Region' in text
        assert 'Q1 2024' in text or 'Q1' in text
        # Table data
        assert 'North America' in text
        assert 'Europe' in text
        assert 'Asia Pacific' in text
        # Values - tables are extracted with | separators
        assert '$12.5M' in text or '12.5M' in text or '12.5' in text

    def test_extracts_headings(self, doc):
        text = doc.get_text()
        assert 'Quarterly Results Report' in text
        assert 'Revenue by Region' in text
        assert 'Key Metrics' in text

    def test_search_in_table(self, doc):
        """Search should find content within tables."""
        result = doc.search('Europe', max_hits=5)
        assert len(result['hits']) > 0

    def test_render_page_unsupported(self, doc):
        with pytest.raises(UnsupportedOperationError):
            doc.render_page(0)


# === PPTX Tests ===
class TestPptxWithTables:
    """Test PPTX with slides and tables."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'ml_report.pptx')

    def test_info(self, doc):
        info = doc.info()
        assert info['doc_type'] == 'pptx'
        assert info['unit_type'] == 'slide'
        assert info['unit_count'] == 3
        assert info['has_text'] is True

    def test_extracts_slide_content(self, doc):
        text = doc.get_text()
        assert 'Machine Learning Performance Report' in text
        assert 'Model Comparison Study' in text

    def test_extracts_table_data(self, doc):
        """Check table content from slides."""
        text = doc.get_text()
        # Table headers
        assert 'Model' in text
        assert 'Accuracy' in text
        # Table data
        assert 'GPT-4' in text
        assert 'Claude-3' in text
        assert '94.2%' in text or '94.2' in text

    def test_extracts_speaker_notes(self, doc):
        """Check speaker notes are extracted."""
        text = doc.get_text()
        assert 'Speaker notes' in text or 'latency varies' in text

    def test_slide_unit_text(self, doc):
        """Each slide should be a separate unit."""
        slide0 = doc.get_unit_text(0)['text']
        slide1 = doc.get_unit_text(1)['text']
        slide2 = doc.get_unit_text(2)['text']
        # Different slides have different content
        assert 'Performance Report' in slide0
        assert 'GPT-4' in slide1 or 'Model' in slide1
        assert 'Conclusions' in slide2


# === HTML Tests ===
class TestHtmlWithTables:
    """Test HTML with tables and math."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'science_report.html')

    def test_info(self, doc):
        info = doc.info()
        assert info['doc_type'] == 'html'
        assert info['title'] == 'Scientific Report'
        assert info['has_text'] is True

    def test_strips_script_and_style(self, doc):
        """Scripts and styles should be removed."""
        text = doc.get_text()
        assert 'console.log' not in text
        assert '.hidden' not in text
        assert '<script>' not in text

    def test_extracts_table_data(self, doc):
        """Check table content."""
        text = doc.get_text()
        assert 'BLEU Score' in text
        assert 'WMT 2014' in text
        assert '28.4' in text
        assert '41.0' in text

    def test_extracts_math_notation(self, doc):
        """Check math formulas are preserved as text."""
        text = doc.get_text()
        assert 'softmax' in text
        assert 'sqrt' in text or 'd_k' in text
        assert 'Attention(Q, K, V)' in text or 'Attention' in text

    def test_preserves_structure(self, doc):
        text = doc.get_text()
        assert 'Transformer Architecture Analysis' in text
        assert 'Performance Results' in text
        assert 'Mathematical Details' in text


# === Markdown Tests ===
class TestMarkdownWithTables:
    """Test Markdown with tables and math."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'training_results.md')

    def test_info(self, doc):
        info = doc.info()
        assert info['doc_type'] == 'markdown'
        assert info['title'] == 'Neural Network Training Results'
        assert info['has_text'] is True

    def test_extracts_table_content(self, doc):
        """Markdown tables should be in text."""
        text = doc.get_text()
        # Table headers
        assert 'Model' in text
        assert 'Params' in text
        assert 'Test Accuracy' in text
        # Table data
        assert 'ResNet-50' in text
        assert 'ViT-B/16' in text
        assert '25.6M' in text
        assert '76.1%' in text

    def test_extracts_math_formulas(self, doc):
        """Check math expressions are preserved."""
        text = doc.get_text()
        assert 'L = -sum' in text or 'cross-entropy' in text.lower()
        assert 'y_i' in text or 'log' in text

    def test_extracts_lists(self, doc):
        """Check list items."""
        text = doc.get_text()
        assert 'Learning rate: 0.001' in text
        assert 'Batch size: 256' in text


# === CSV Tests ===
class TestCSV:
    """Test CSV as plain text."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'model_metrics.csv')

    def test_info(self, doc):
        info = doc.info()
        assert info['doc_type'] == 'text'  # CSV is treated as text
        assert info['has_text'] is True

    def test_extracts_csv_content(self, doc):
        text = doc.get_text()
        # Headers
        assert 'Model' in text
        assert 'Accuracy' in text
        assert 'F1' in text
        # Data
        assert 'BERT-base' in text
        assert 'RoBERTa' in text
        assert '89.2' in text

    def test_search_csv(self, doc):
        result = doc.search('RoBERTa')
        assert len(result['hits']) == 1


# === Plain Text Tests ===
class TestPlainText:
    """Test plain text with structure."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'experiment_log.txt')

    def test_extracts_structured_text(self, doc):
        text = doc.get_text()
        assert 'EXPERIMENT LOG' in text
        assert 'CONFIGURATION:' in text
        assert 'RESULTS:' in text
        assert 'transformer-xl' in text
        assert 'perplexity' in text

    def test_search_finds_metrics(self, doc):
        result = doc.search('perplexity', max_hits=10)
        assert len(result['hits']) >= 5  # One per epoch


# === Image Tests ===
class TestImage:
    """Test image handling (no OCR)."""

    @pytest.fixture
    def doc(self):
        return open_document(FIXTURES / 'test_image.jpg')

    def test_info(self, doc):
        info = doc.info()
        assert info['doc_type'] == 'image'
        assert info['unit_type'] == 'none'
        assert info['unit_count'] == 0
        assert info['has_text'] is False
        assert info['width'] == 1600
        assert info['height'] == 900

    def test_no_text(self, doc):
        assert doc.get_text() == ''

    def test_search_returns_empty(self, doc):
        result = doc.search('anything')
        assert result['hits'] == []

    def test_get_bytes_returns_image(self, doc):
        raw = doc.get_bytes()
        # JPEG magic bytes
        assert raw[:2] == b'\xff\xd8'

    def test_render_page_unsupported(self, doc):
        with pytest.raises(UnsupportedOperationError):
            doc.render_page(0)


# === Cross-format Search Tests ===
class TestSearchAcrossFormats:
    """Test search behavior across different formats."""

    @pytest.mark.parametrize("filename,query,min_hits", [
        ('attention_paper.pdf', 'attention', 5),
        ('barclays_annual_report.pdf', 'Barclays', 3),
        ('report_with_tables.docx', 'Revenue', 1),
        ('ml_report.pptx', 'Model', 2),
        ('science_report.html', 'attention', 1),
        ('training_results.md', 'accuracy', 1),
    ])
    def test_search_finds_content(self, filename, query, min_hits):
        doc = open_document(FIXTURES / filename)
        result = doc.search(query, max_hits=20)
        assert len(result['hits']) >= min_hits, f"Expected >= {min_hits} hits for '{query}' in {filename}, got {len(result['hits'])}"

    @pytest.mark.parametrize("filename", [
        'attention_paper.pdf',
        'report_with_tables.docx',
        'ml_report.pptx',
        'science_report.html',
        'training_results.md',
        'experiment_log.txt',
    ])
    def test_window_vs_unit_mode(self, filename):
        """Window mode snippets should be smaller than unit mode."""
        doc = open_document(FIXTURES / filename)
        text = doc.get_text()
        if not text.strip():
            pytest.skip("No text content")

        # Find a common word
        words = text.split()
        if not words:
            pytest.skip("No words")
        query = words[min(10, len(words)-1)]  # Pick word near start

        window = doc.search(query, before=50, after=50, max_hits=1, mode='window')
        unit = doc.search(query, max_hits=1, mode='unit')

        if window['hits'] and unit['hits']:
            # Window snippet should be bounded
            assert len(window['hits'][0]['snippet']) <= 50 + len(query) + 50 + 50


# === Edge Cases ===
class TestEdgeCases:
    """Edge cases and robustness tests."""

    def test_pdf_empty_page_search(self):
        """Search should handle pages with minimal text."""
        doc = open_document(FIXTURES / 'barclays_annual_report.pdf')
        # Search for something unlikely
        result = doc.search('xyznonexistent123')
        assert result['hits'] == []

    def test_search_case_sensitivity(self):
        doc = open_document(FIXTURES / 'attention_paper.pdf')
        upper = doc.search('ATTENTION', case_sensitive=True)
        lower = doc.search('attention', case_sensitive=True)
        insensitive = doc.search('attention', case_sensitive=False)
        # Case insensitive should find more or equal
        assert len(insensitive['hits']) >= len(lower['hits'])

    def test_search_unit_range(self):
        """Test restricting search to unit range."""
        doc = open_document(FIXTURES / 'attention_paper.pdf')
        # Search only first 3 pages
        result = doc.search('attention', unit_start=0, unit_end=2, max_hits=50)
        for hit in result['hits']:
            assert hit['unit_index'] <= 2

    def test_chunking_deterministic(self):
        """Same document should produce same chunks."""
        doc1 = open_document(FIXTURES / 'training_results.md')
        doc2 = open_document(FIXTURES / 'training_results.md')
        assert doc1.info()['unit_count'] == doc2.info()['unit_count']
        for i in range(doc1.info()['unit_count']):
            assert doc1.get_unit_text(i)['text'] == doc2.get_unit_text(i)['text']
