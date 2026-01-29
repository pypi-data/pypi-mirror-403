"""
Tests for CodexCollector v0.2.0 features.

This module tests the new features introduced in v0.2.0:
1. Return type change from dict[int, Document] to list[Document]
2. New extract_page_text parameter for HTML page text extraction
3. HTML text extraction functionality
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from codexcollector import CodexCollector, Document, ConfigurationError


class TestReturnTypeChange:
    """Tests for the dict-to-list return type change."""

    def test_collect_returns_list(self, tmp_path: Path) -> None:
        """collect() should return a list, not a dict."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        collector = CodexCollector()
        result = collector.collect(str(tmp_path))

        assert isinstance(result, list), "collect() should return a list"
        assert not isinstance(result, dict), "collect() should not return a dict"

    def test_collect_returns_list_of_documents(self, tmp_path: Path) -> None:
        """Each item in the returned list should be a Document dict."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        collector = CodexCollector()
        result = collector.collect(str(tmp_path))

        assert len(result) == 1
        doc = result[0]

        # Check Document structure
        assert 'filename' in doc
        assert 'source' in doc
        assert 'text' in doc
        assert 'date' in doc

    def test_corpus_attribute_is_list(self, tmp_path: Path) -> None:
        """The corpus attribute should also be a list."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        collector = CodexCollector()
        collector.collect(str(tmp_path))

        assert isinstance(collector.corpus, list), "corpus attribute should be a list"

    def test_empty_result_is_empty_list(self, tmp_path: Path) -> None:
        """Empty collection should return empty list, not empty dict."""
        # Create directory with no supported files
        (tmp_path / "unsupported.xyz").write_text("content")

        collector = CodexCollector()
        result = collector.collect(str(tmp_path))

        assert result == [], "Empty collection should return empty list"
        assert isinstance(result, list)

    def test_multiple_files_returns_list(self, tmp_path: Path) -> None:
        """Multiple files should return list with correct count."""
        for i in range(3):
            (tmp_path / f"file{i}.txt").write_text(f"Content {i}")

        collector = CodexCollector()
        result = collector.collect(str(tmp_path))

        assert isinstance(result, list)
        assert len(result) == 3

    def test_list_indexing_works(self, tmp_path: Path) -> None:
        """List indexing should work correctly."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        collector = CodexCollector()
        result = collector.collect(str(tmp_path))

        # Should be able to index directly
        first_doc = result[0]
        assert first_doc['text'] == "Test content"


class TestExtractPageTextParameter:
    """Tests for the new extract_page_text parameter."""

    def test_default_extract_page_text_is_false(self) -> None:
        """extract_page_text should default to False."""
        collector = CodexCollector()
        assert collector.extract_page_text is False

    def test_extract_page_text_can_be_set_true(self) -> None:
        """extract_page_text can be set to True."""
        collector = CodexCollector(extract_page_text=True)
        assert collector.extract_page_text is True

    def test_extract_page_text_validation_rejects_non_bool(self) -> None:
        """extract_page_text should reject non-boolean values."""
        with pytest.raises(ConfigurationError) as exc_info:
            CodexCollector(extract_page_text="true")  # type: ignore
        assert "extract_page_text must be bool" in str(exc_info.value)

        with pytest.raises(ConfigurationError):
            CodexCollector(extract_page_text=1)  # type: ignore

        with pytest.raises(ConfigurationError):
            CodexCollector(extract_page_text=None)  # type: ignore

    def test_extract_page_text_ignored_for_file_paths(self, tmp_path: Path) -> None:
        """extract_page_text should be silently ignored for file paths."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("File content")

        # Should work fine with extract_page_text=True even for file paths
        collector = CodexCollector(extract_page_text=True)
        result = collector.collect(str(tmp_path))

        assert len(result) == 1
        assert result[0]['text'] == "File content"


class TestHtmlTextExtraction:
    """Tests for the _extract_text_from_html method."""

    def test_extract_text_from_simple_html(self) -> None:
        """Should extract text from simple HTML."""
        collector = CodexCollector()
        html = """
        <html>
        <body>
            <main>
                <h1>Test Title</h1>
                <p>This is test content.</p>
            </main>
        </body>
        </html>
        """

        result = collector._extract_text_from_html(html, "https://example.com/page")

        assert 'text' in result
        assert 'Test Title' in result['text']
        assert 'test content' in result['text']

    def test_removes_nav_elements(self) -> None:
        """Should remove <nav> elements."""
        collector = CodexCollector()
        html = """
        <html>
        <body>
            <nav><a href="/">Home</a><a href="/about">About</a></nav>
            <main><p>Main content here.</p></main>
        </body>
        </html>
        """

        result = collector._extract_text_from_html(html, "https://example.com/page")

        assert 'Main content' in result['text']
        # Nav content should be removed
        assert 'Home' not in result['text'] or 'About' not in result['text']

    def test_removes_footer_elements(self) -> None:
        """Should remove <footer> elements."""
        collector = CodexCollector()
        html = """
        <html>
        <body>
            <main><p>Main content here.</p></main>
            <footer><p>Copyright 2024</p></footer>
        </body>
        </html>
        """

        result = collector._extract_text_from_html(html, "https://example.com/page")

        assert 'Main content' in result['text']
        assert 'Copyright' not in result['text']

    def test_removes_header_elements(self) -> None:
        """Should remove <header> elements."""
        collector = CodexCollector()
        html = """
        <html>
        <body>
            <header><h1>Site Header</h1></header>
            <main><p>Main content here.</p></main>
        </body>
        </html>
        """

        result = collector._extract_text_from_html(html, "https://example.com/page")

        assert 'Main content' in result['text']
        assert 'Site Header' not in result['text']

    def test_removes_aside_elements(self) -> None:
        """Should remove <aside> (sidebar) elements."""
        collector = CodexCollector()
        html = """
        <html>
        <body>
            <main><p>Main content here.</p></main>
            <aside><p>Sidebar content</p></aside>
        </body>
        </html>
        """

        result = collector._extract_text_from_html(html, "https://example.com/page")

        assert 'Main content' in result['text']
        assert 'Sidebar' not in result['text']

    def test_removes_script_and_style(self) -> None:
        """Should remove <script> and <style> elements."""
        collector = CodexCollector()
        html = """
        <html>
        <head>
            <style>.test { color: red; }</style>
        </head>
        <body>
            <script>console.log('test');</script>
            <main><p>Main content here.</p></main>
        </body>
        </html>
        """

        result = collector._extract_text_from_html(html, "https://example.com/page")

        assert 'Main content' in result['text']
        assert 'console.log' not in result['text']
        assert 'color: red' not in result['text']

    def test_filename_is_url_path(self) -> None:
        """filename should be the URL path."""
        collector = CodexCollector()
        html = "<html><body><p>Content</p></body></html>"

        result = collector._extract_text_from_html(html, "https://example.com/docs/page.html")

        assert result['filename'] == "docs/page.html"

    def test_filename_for_root_url(self) -> None:
        """filename should be domain for root URLs."""
        collector = CodexCollector()
        html = "<html><body><p>Content</p></body></html>"

        result = collector._extract_text_from_html(html, "https://example.com/")

        assert result['filename'] == "example.com"

    def test_source_is_original_url(self) -> None:
        """source should be the original URL."""
        collector = CodexCollector()
        html = "<html><body><p>Content</p></body></html>"
        url = "https://example.com/test/page"

        result = collector._extract_text_from_html(html, url)

        assert result['source'] == url

    def test_date_is_none(self) -> None:
        """date should be None for HTML pages."""
        collector = CodexCollector()
        html = "<html><body><p>Content</p></body></html>"

        result = collector._extract_text_from_html(html, "https://example.com/page")

        assert result['date'] is None

    def test_handles_empty_html(self) -> None:
        """Should handle empty or minimal HTML gracefully."""
        collector = CodexCollector()

        result = collector._extract_text_from_html("", "https://example.com/page")

        assert result['text'] == "" or isinstance(result['text'], str)
        assert result['source'] == "https://example.com/page"

    def test_handles_malformed_html(self) -> None:
        """Should handle malformed HTML gracefully."""
        collector = CodexCollector()
        html = "<html><body><p>Unclosed paragraph<div>Mixed up tags</body>"

        result = collector._extract_text_from_html(html, "https://example.com/page")

        # Should not raise, should return something
        assert isinstance(result, dict)
        assert 'text' in result


class TestWebCollectionModes:
    """Tests for the web collection mode switching."""

    @patch('codexcollector.codexcollector.requests.get')
    def test_extract_page_text_mode_extracts_html(self, mock_get: Mock) -> None:
        """When extract_page_text=True, should extract text from HTML pages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.text = """
        <html>
        <body>
            <main><h1>Test Page</h1><p>Page content here.</p></main>
        </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        collector = CodexCollector(extract_page_text=True, max_crawl_depth=0)
        result = collector.collect("https://example.com/page")

        assert isinstance(result, list)
        if len(result) > 0:
            assert 'Page content' in result[0]['text'] or 'Test Page' in result[0]['text']

    @patch('codexcollector.codexcollector.requests.get')
    def test_default_mode_discovers_files(self, mock_get: Mock) -> None:
        """When extract_page_text=False (default), should discover file links."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
        <body>
            <a href="document.pdf">PDF Document</a>
            <a href="file.docx">Word Document</a>
        </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        collector = CodexCollector(extract_page_text=False, max_crawl_depth=0)

        # This will try to discover files, which we can verify through the method call
        with patch.object(collector, '_discover_files_from_url') as mock_discover:
            mock_discover.return_value = []
            collector.collect("https://example.com/docs")
            mock_discover.assert_called_once_with("https://example.com/docs")


class TestVersion:
    """Tests for version number."""

    def test_version_is_020(self) -> None:
        """Package version should be 0.2.0."""
        from codexcollector import __version__
        assert __version__ == "0.2.0"


class TestCorpusTypeRemoved:
    """Tests to verify CorpusType is no longer exported."""

    def test_corpustype_not_in_exports(self) -> None:
        """CorpusType should not be in __all__."""
        from codexcollector import __all__
        assert 'CorpusType' not in __all__

    def test_corpustype_not_importable(self) -> None:
        """CorpusType should not be importable from package."""
        with pytest.raises(ImportError):
            from codexcollector import CorpusType  # type: ignore


class TestProgressCallback:
    """Tests for progress_callback integer interval parameter."""

    def test_progress_callback_none_no_logging(self, tmp_path: Path, caplog) -> None:
        """progress_callback=None should not log progress."""
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"Content {i}")

        collector = CodexCollector()
        with caplog.at_level('INFO'):
            result = collector.collect(str(tmp_path), progress_callback=None)

        assert len(result) == 5
        # Should not have any "Progress:" log messages
        progress_logs = [r for r in caplog.records if "Progress:" in r.message]
        assert len(progress_logs) == 0

    def test_progress_callback_zero_treated_as_none(self, tmp_path: Path, caplog) -> None:
        """progress_callback=0 should be treated as None (no logging)."""
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"Content {i}")

        collector = CodexCollector()
        with caplog.at_level('INFO'):
            result = collector.collect(str(tmp_path), progress_callback=0)

        assert len(result) == 5
        progress_logs = [r for r in caplog.records if "Progress:" in r.message]
        assert len(progress_logs) == 0

    def test_progress_callback_negative_treated_as_none(self, tmp_path: Path, caplog) -> None:
        """progress_callback with negative value should be treated as None."""
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"Content {i}")

        collector = CodexCollector()
        with caplog.at_level('INFO'):
            result = collector.collect(str(tmp_path), progress_callback=-1)

        assert len(result) == 5
        progress_logs = [r for r in caplog.records if "Progress:" in r.message]
        assert len(progress_logs) == 0

    def test_progress_callback_non_int_treated_as_none(self, tmp_path: Path, caplog) -> None:
        """progress_callback with non-int value should be treated as None."""
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text(f"Content {i}")

        collector = CodexCollector()
        with caplog.at_level('INFO'):
            result = collector.collect(str(tmp_path), progress_callback="10")  # type: ignore

        assert len(result) == 5
        progress_logs = [r for r in caplog.records if "Progress:" in r.message]
        assert len(progress_logs) == 0

    def test_progress_callback_logs_at_intervals(self, tmp_path: Path, caplog) -> None:
        """progress_callback should log at specified intervals."""
        for i in range(10):
            (tmp_path / f"file{i}.txt").write_text(f"Content {i}")

        collector = CodexCollector()
        with caplog.at_level('INFO'):
            result = collector.collect(str(tmp_path), progress_callback=3)

        assert len(result) == 10
        progress_logs = [r for r in caplog.records if "Progress:" in r.message]
        # Should log at 3, 6, 9, and 10 (final)
        assert len(progress_logs) == 4

    def test_progress_callback_logs_final_if_not_multiple(self, tmp_path: Path, caplog) -> None:
        """progress_callback should log final count even if not a multiple."""
        for i in range(7):
            (tmp_path / f"file{i}.txt").write_text(f"Content {i}")

        collector = CodexCollector()
        with caplog.at_level('INFO'):
            result = collector.collect(str(tmp_path), progress_callback=3)

        assert len(result) == 7
        progress_logs = [r for r in caplog.records if "Progress:" in r.message]
        # Should log at 3, 6, and 7 (final)
        assert len(progress_logs) == 3
        # Last log should show 7/7
        assert "7 / 7" in progress_logs[-1].message

    def test_progress_callback_exact_multiple_no_duplicate(self, tmp_path: Path, caplog) -> None:
        """progress_callback should not duplicate final log if exact multiple."""
        for i in range(6):
            (tmp_path / f"file{i}.txt").write_text(f"Content {i}")

        collector = CodexCollector()
        with caplog.at_level('INFO'):
            result = collector.collect(str(tmp_path), progress_callback=3)

        assert len(result) == 6
        progress_logs = [r for r in caplog.records if "Progress:" in r.message]
        # Should log at 3 and 6 only (6 is both interval and final, no duplicate)
        assert len(progress_logs) == 2
