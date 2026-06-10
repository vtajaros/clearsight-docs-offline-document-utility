"""
Tests for the BookmarkService.
"""
import re
import hashlib
from pathlib import Path
import pytest
from services.bookmark_service import BookmarkService, BookmarkNode

def _make_empty_pdf(tmp_path: Path, name: str = "empty.pdf", pages: int = 1) -> Path:
    """Create a minimal PDF with no text (simulates scanned PDF)."""
    import fitz
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page()
    out = tmp_path / name
    doc.save(str(out))
    doc.close()
    return out

def _make_toc_pdf(tmp_path: Path, name: str = "toc.pdf") -> Path:
    """Create a 3-page PDF with a known 3-level TOC."""
    import fitz
    doc = fitz.open()
    for _ in range(3):
        doc.new_page()
    doc.set_toc([
        [1, "Chapter 1", 1],
        [2, "Section 1.1", 2],
        [3, "Subsection 1.1.1", 3],
    ])
    out = tmp_path / name
    doc.save(str(out))
    doc.close()
    return out

def _make_text_pdf(tmp_path: Path, name: str = "text.pdf") -> Path:
    """Create a PDF with text at 3 distinct heading sizes plus body text.

    Structure:
      Page 1-2: Front cover (empty)
      Page 3:  "Chapter One"       at 24pt  (H1 candidate)
      Page 4:  "Section Overview"  at 18pt  (H2 candidate)
      Page 5:  "Subsection Detail" at 12pt  (H3 candidate)
      Pages 6-10: body text        at 10pt  (exceeds threshold,
                                             must be excluded as body text)
      Page 11-12: Back cover (empty)
    """
    import fitz
    doc = fitz.open()

    # Front cover
    doc.new_page(width=612, height=792)
    doc.new_page(width=612, height=792)

    heading_pages = [
        (24.0, "Chapter One"),
        (18.0, "Section Overview"),
        (12.0, "Subsection Detail"),
    ]
    for size, text in heading_pages:
        page = doc.new_page(width=612, height=792)
        rc = page.insert_textbox(
            fitz.Rect(50, 50, 550, 200),
            text,
            fontsize=size,
            fontname="helv",
        )
        assert rc > 0, f"Text '{text}' was clipped in fixture — increase rect"

    for i in range(5):
        page = doc.new_page(width=612, height=792)
        rc = page.insert_textbox(
            fitz.Rect(50, 50, 550, 700),
            f"Body paragraph {i + 1}.\n" * 20,
            fontsize=10.0,
            fontname="helv",
        )
        assert rc > 0, "Body text was clipped in fixture — increase rect"

    # Back cover
    doc.new_page(width=612, height=792)
    doc.new_page(width=612, height=792)

    out = tmp_path / name
    doc.save(str(out))
    doc.close()
    return out


def _make_running_header_pdf(tmp_path: Path, name: str = "running.pdf") -> Path:
    """PDF where 'Chapter 1' at 24pt appears on pages 3, 4, 5.
    'Introduction' at 18pt appears only on page 3.
    'Chapter 1' on the same page appears twice in the raw spans
    (to test same-title-same-page deduplication).
    """
    import fitz
    doc = fitz.open()
    for i in range(8):
        page = doc.new_page(width=612, height=792)

        if 1 < i < 5:
            # Running header — same title, different pages (on pages 3, 4, 5)
            rc = page.insert_textbox(
                fitz.Rect(50, 50, 550, 100),
                "Chapter 1",
                fontsize=24.0,
                fontname="helv",
            )
            assert rc > 0
            
        # Insert dummy spans to exceed the 10-line heuristic threshold
        # Using size 10.0 classifies it as body text, preventing
        # it from being a heading while successfully breaking consecutive spans
        page.insert_textbox(
            fitz.Rect(50, 300, 550, 450),
            "Dummy line 1.\nDummy line 2.\nDummy line 3.\n",
            fontsize=10.0,
            fontname="helv"
        )

        if i == 2:
            # Second "Chapter 1" block on page 3 — same title, same page
            # This should be deduped to one entry for page 3
            rc2 = page.insert_textbox(
                fitz.Rect(50, 500, 550, 550),
                "Chapter 1",
                fontsize=24.0,
                fontname="helv",
            )
            assert rc2 > 0
            # Unique heading only on page 3
            rc3 = page.insert_textbox(
                fitz.Rect(50, 600, 550, 650),
                "Introduction",
                fontsize=18.0,
                fontname="helv",
            )
            assert rc3 > 0

    out = tmp_path / name
    doc.save(str(out))
    doc.close()
    return out

@pytest.fixture
def svc() -> BookmarkService:
    return BookmarkService()

@pytest.fixture
def empty_pdf(tmp_path):
    return _make_empty_pdf(tmp_path)

@pytest.fixture
def toc_pdf(tmp_path):
    return _make_toc_pdf(tmp_path)

@pytest.fixture
def text_pdf(tmp_path):
    return _make_text_pdf(tmp_path)

@pytest.fixture
def running_header_pdf(tmp_path):
    return _make_running_header_pdf(tmp_path)


class TestBuildFlattenRoundtrip:

    def test_normal_3_level_roundtrip(self, svc):
        """A well-formed 3-level TOC survives a build→flatten round-trip."""
        flat_toc = [
            [1, "Chapter 1", 1],
            [2, "Section 1.1", 2],
            [3, "Subsection 1.1.1", 3],
            [1, "Chapter 2", 4],
        ]
        tree = svc._build_tree(flat_toc)
        result = svc._flatten_tree(tree)
        assert result == flat_toc

    def test_level_jump_no_crash(self, svc):
        """Level jump from 1 to 3 (skipping 2) must not raise."""
        flat_toc = [
            [1, "Chapter 1", 1],
            [3, "Deep Section", 2],
            [1, "Chapter 2", 3],
        ]
        tree = svc._build_tree(flat_toc)
        flat_result = svc._flatten_tree(tree)
        titles = [entry[1] for entry in flat_result]
        assert "Chapter 1" in titles
        assert "Deep Section" in titles
        assert "Chapter 2" in titles
        # Levels in output must all be valid (1-3)
        for entry in flat_result:
            assert 1 <= entry[0] <= 3

    def test_empty_input_build(self, svc):
        assert svc._build_tree([]) == []

    def test_empty_input_flatten(self, svc):
        assert svc._flatten_tree([]) == []

    def test_single_node_roundtrip(self, svc):
        flat_toc = [[1, "Only Chapter", 1]]
        tree = svc._build_tree(flat_toc)
        result = svc._flatten_tree(tree)
        assert result == flat_toc


class TestGetBookmarks:

    def test_pdf_with_toc_returns_correct_tree(self, svc, toc_pdf):
        result = svc.get_bookmarks(str(toc_pdf))
        assert len(result) == 1
        ch1 = result[0]
        assert ch1.title == "Chapter 1"
        assert ch1.level == 1
        assert ch1.page == 1
        assert len(ch1.children) == 1
        sec = ch1.children[0]
        assert sec.title == "Section 1.1"
        assert sec.level == 2
        assert len(sec.children) == 1
        assert sec.children[0].title == "Subsection 1.1.1"
        assert sec.children[0].level == 3

    def test_pdf_without_toc_returns_empty_list(self, svc, empty_pdf):
        result = svc.get_bookmarks(str(empty_pdf))
        assert result == []
        assert isinstance(result, list)

    def test_nonexistent_file_raises(self, svc, tmp_path):
        with pytest.raises(Exception):
            svc.get_bookmarks(str(tmp_path / "does_not_exist.pdf"))


class TestWriteBookmarks:

    def _make_test_tree(self) -> list[BookmarkNode]:
        return [
            BookmarkNode(
                title="Chapter 1", page=1, level=1,
                children=[
                    BookmarkNode(title="Section 1.1", page=1,
                                 level=2, children=[])
                ]
            ),
            BookmarkNode(title="Chapter 2", page=2, level=1, children=[]),
        ]

    def test_round_trip_equality(self, svc, empty_pdf, tmp_path):
        """Write a known tree then read it back — titles and levels match."""
        out = tmp_path / "output.pdf"
        bookmarks = self._make_test_tree()
        svc.write_bookmarks(str(empty_pdf), bookmarks, str(out))
        assert out.exists()
        result = svc.get_bookmarks(str(out))
        assert len(result) == 2
        assert result[0].title == "Chapter 1"
        assert result[0].level == 1
        assert len(result[0].children) == 1
        assert result[0].children[0].title == "Section 1.1"
        assert result[1].title == "Chapter 2"

    def test_source_file_not_modified(self, svc, empty_pdf, tmp_path):
        """Source PDF bytes must be identical before and after the call."""
        original_hash = hashlib.md5(empty_pdf.read_bytes()).hexdigest()
        out = tmp_path / "output.pdf"
        svc.write_bookmarks(str(empty_pdf), self._make_test_tree(), str(out))
        after_hash = hashlib.md5(empty_pdf.read_bytes()).hexdigest()
        assert original_hash == after_hash, (
            "Source file was modified by write_bookmarks"
        )

    def test_output_is_valid_pdf(self, svc, empty_pdf, tmp_path):
        """Output file must be a valid PDF (starts with %PDF header)."""
        out = tmp_path / "output.pdf"
        svc.write_bookmarks(str(empty_pdf), self._make_test_tree(), str(out))
        header = out.read_bytes()[:4]
        assert header == b"%PDF"

    def test_same_path_raises_value_error(self, svc, empty_pdf):
        """Identical source and output path must raise ValueError."""
        with pytest.raises(ValueError):
            svc.write_bookmarks(
                str(empty_pdf), self._make_test_tree(), str(empty_pdf)
            )

    def test_output_file_created(self, svc, empty_pdf, tmp_path):
        """Output file must be created at the specified path."""
        out = tmp_path / "created.pdf"
        assert not out.exists()
        svc.write_bookmarks(str(empty_pdf), self._make_test_tree(), str(out))
        assert out.exists()


class TestExtractHeadings:

    def test_empty_pdf_returns_no_text_layer(self, svc, empty_pdf):
        """PDF with no text spans returns ([], False)."""
        nodes, has_text = svc.extract_headings(str(empty_pdf))
        assert nodes == []
        assert has_text is False

    def test_text_pdf_has_text_layer(self, svc, text_pdf):
        """PDF with real text returns has_text_layer=True."""
        nodes, has_text = svc.extract_headings(str(text_pdf))
        assert has_text is True

    def test_text_pdf_returns_headings(self, svc, text_pdf):
        """Heading spans produce non-empty bookmark nodes."""
        nodes, has_text = svc.extract_headings(str(text_pdf))
        assert has_text is True
        assert len(nodes) > 0

    def test_all_levels_valid(self, svc, text_pdf):
        """Every returned node must have level in {1, 2, 3}."""
        nodes, _ = svc.extract_headings(str(text_pdf))

        def check(nodelist):
            for n in nodelist:
                assert n.level in (1, 2, 3), (
                    f"Invalid level {n.level} on node '{n.title}'"
                )
                check(n.children)

        check(nodes)

    def test_body_text_not_in_headings(self, svc, text_pdf):
        """10pt body text at 70% page frequency must be excluded."""
        nodes, _ = svc.extract_headings(str(text_pdf))

        def collect_titles(nodelist):
            titles = []
            for n in nodelist:
                titles.append(n.title)
                titles.extend(collect_titles(n.children))
            return titles

        titles = collect_titles(nodes)
        assert not any("Body paragraph" in t for t in titles), (
            "Body text incorrectly classified as heading"
        )

    def test_dedup_same_title_same_page(self, svc, running_header_pdf):
        """'Chapter 1' appears twice on page 1 in raw spans.
        After dedup, page 1 should contribute exactly one entry."""
        nodes, has_text = svc.extract_headings(str(running_header_pdf))
        assert has_text is True

        def collect_all(nodelist):
            flat = []
            for n in nodelist:
                flat.append((n.title, n.page))
                flat.extend(collect_all(n.children))
            return flat

        entries = collect_all(nodes)
        # No (title, page) pair should appear more than once
        assert len(entries) == len(set(entries)), (
            f"Duplicate entries found: {entries}"
        )

    def test_same_title_different_pages_deduplicated(self, svc,
                                                     running_header_pdf):
        """'Chapter 1' on nearby pages (within 15 pages) is deduplicated."""
        nodes, _ = svc.extract_headings(str(running_header_pdf))

        def collect_all(nodelist):
            flat = []
            for n in nodelist:
                flat.append((n.title, n.page))
                flat.extend(collect_all(n.children))
            return flat

        entries = collect_all(nodes)
        chapter_pages = [p for t, p in entries if t == "Chapter 1"]
        print("DEBUG ENTRIES:", entries)
        # Should appear on only 1 page because they are within 15 pages and deduplicated
        assert len(set(chapter_pages)) == 1, (
            f"Expected Chapter 1 on 1 page, got pages: {chapter_pages}"
        )
