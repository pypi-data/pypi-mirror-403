"""Edge case tests for mdstruct."""

from pathlib import Path

import pytest

from mdstruct.core import join_markdown, split_markdown

FIXTURES_DIR = Path(__file__).parent / "fixtures"
INPUTS_DIR = FIXTURES_DIR / "inputs"


class TestCodeBlocks:
    """Test handling of code blocks."""

    def test_ignores_headers_in_code_blocks(self, actual_path):
        """Headers inside code blocks should be ignored."""
        input_file = INPUTS_DIR / "code-blocks.md"
        output_dir = actual_path / "split"

        split_markdown(input_file, output_dir, level=2)

        # Should only have real headers, not ones in code blocks
        files = list(output_dir.rglob("*.md"))
        file_names = [f.name for f in files]

        # Should have files for real headers
        assert any("real-subheader" in name for name in file_names)

        # Deep Header is H3, but gets bumped to H2 in the split file (at level 2)
        subheader_file = next((f for f in files if "real-subheader" in f.name), None)
        assert subheader_file is not None
        content = subheader_file.read_text()
        assert "## Deep Header" in content  # H3 becomes H2 after bumping

        # Verify code blocks are preserved with fake headers (in either file)
        all_content = "".join([f.read_text() for f in files])
        assert "# This is not a header" in all_content
        assert "// # Fake header in code" in all_content

    def test_code_blocks_roundtrip(self, actual_path):
        """Code blocks should be preserved in round-trip."""
        input_file = INPUTS_DIR / "code-blocks.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=2)
        join_markdown(split_dir, output_file)

        input_file.read_text()
        result = output_file.read_text()

        # Code blocks should be preserved
        assert "```python" in result
        assert "~~~javascript" in result
        assert "# This is not a header" in result


class TestSpecialCharacters:
    """Test headers with special characters."""

    def test_special_chars_in_headers(self, actual_path):
        """Headers with special characters should be handled correctly."""
        input_file = INPUTS_DIR / "special-chars.md"
        output_dir = actual_path / "split"

        split_markdown(input_file, output_dir, level=2)

        # Check directory names (H1s become directories)
        dirs = [d.name for d in output_dir.iterdir() if d.is_dir()]
        assert any("header-with-bold-and-italic" in name for name in dirs)
        assert any("header-with-emoji" in name for name in dirs)

        # Check file names (H2s become files)
        files = list(output_dir.rglob("*.md"))
        file_names = [f.name for f in files]
        assert any("header-with-code-inline" in name for name in file_names)
        assert any("special-chars-symbols" in name for name in file_names)

    def test_special_chars_roundtrip(self, actual_path):
        """Special characters should be preserved in round-trip."""
        input_file = INPUTS_DIR / "special-chars.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=2)
        join_markdown(split_dir, output_file)

        input_file.read_text()
        result = output_file.read_text()

        # Special chars and formatting should be preserved in content
        assert "**Bold**" in result
        assert "*Italic*" in result
        assert "`code`" in result
        assert "[Link](https://example.com)" in result
        assert "🚀" in result


class TestEmptySections:
    """Test handling of empty sections."""

    def test_empty_sections_created(self, actual_path):
        """Empty sections should create files."""
        input_file = INPUTS_DIR / "empty-sections.md"
        output_dir = actual_path / "split"

        split_markdown(input_file, output_dir, level=2)

        files = list(output_dir.rglob("*.md"))
        file_names = [f.name for f in files]

        # Should have files for empty sections
        assert any("empty-subsection" in name for name in file_names)
        assert any("another-empty" in name for name in file_names)

    def test_empty_sections_roundtrip(self, actual_path):
        """Empty sections should be preserved in round-trip."""
        input_file = INPUTS_DIR / "empty-sections.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=2)
        join_markdown(split_dir, output_file)

        input_file.read_text()
        result = output_file.read_text()

        # Empty section headers should be preserved
        assert "## Empty Subsection" in result
        assert "## Another Empty" in result
        assert "## Yet Another Empty" in result


class TestDeepNesting:
    """Test deep heading nesting."""

    def test_deep_nesting_split(self, actual_path):
        """Should handle all 6 levels of headers."""
        input_file = INPUTS_DIR / "deep-nesting.md"
        output_dir = actual_path / "split"

        # Split at level 6 (all levels)
        split_markdown(input_file, output_dir, level=6)

        # Should have deeply nested directories
        assert any(output_dir.rglob("*/*/*/*/*/*.md"))

    def test_deep_nesting_roundtrip(self, actual_path):
        """Deep nesting should be preserved."""
        input_file = INPUTS_DIR / "deep-nesting.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=3)
        join_markdown(split_dir, output_file)

        input_file.read_text()
        result = output_file.read_text()

        # All header levels should be preserved
        assert "# Level 1" in result
        assert "## Level 2" in result
        assert "### Level 3" in result
        assert "#### Level 4" in result
        assert "##### Level 5" in result
        assert "###### Level 6" in result


class TestTrailingHashes:
    """Test headers with trailing hashes."""

    def test_trailing_hashes_roundtrip(self, actual_path):
        """Trailing hashes should be handled correctly."""
        input_file = INPUTS_DIR / "trailing-hashes.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=2)
        join_markdown(split_dir, output_file)

        input_file.read_text()
        result = output_file.read_text()

        # Headers should be preserved (trailing hashes may be normalized)
        assert "Header with Trailing Hash" in result
        assert "Another with Multiple" in result
        assert "Three Hashes" in result


class TestSingleHeader:
    """Test file with single header."""

    def test_single_header_split(self, actual_path):
        """Single header file should split correctly."""
        input_file = INPUTS_DIR / "single-header.md"
        output_dir = actual_path / "split"

        split_markdown(input_file, output_dir, level=1)

        # Should create directory with single file
        files = list(output_dir.rglob("*.md"))
        assert len(files) >= 1

    def test_single_header_roundtrip(self, actual_path):
        """Single header should round-trip."""
        input_file = INPUTS_DIR / "single-header.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=1)
        join_markdown(split_dir, output_file)

        input_file.read_text()
        result = output_file.read_text()

        assert "# Only Header" in result
        assert "Just one header" in result


class TestConsecutiveHeaders:
    """Test consecutive headers with no content between."""

    def test_consecutive_headers_roundtrip(self, actual_path):
        """Consecutive headers should be preserved."""
        input_file = INPUTS_DIR / "consecutive-headers.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=3)
        join_markdown(split_dir, output_file)

        input_file.read_text()
        result = output_file.read_text()

        # All headers should be preserved
        assert "## Immediate Sub" in result
        assert "### Another Immediate" in result
        assert "### Another Sub" in result


class TestComplexContent:
    """Test complex markdown content."""

    def test_tables_preserved(self, actual_path):
        """Tables should be preserved in round-trip."""
        input_file = INPUTS_DIR / "complex-content.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=2)
        join_markdown(split_dir, output_file)

        result = output_file.read_text()

        # Table should be preserved
        assert "| Header 1 | Header 2 |" in result
        assert "|----------|----------|" in result
        assert "| Cell 1   | Cell 2   |" in result

    def test_lists_preserved(self, actual_path):
        """Lists should be preserved in round-trip."""
        input_file = INPUTS_DIR / "complex-content.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=2)
        join_markdown(split_dir, output_file)

        result = output_file.read_text()

        # Lists should be preserved
        assert "- Item 1" in result
        assert "  - Nested 1" in result
        assert "1. Ordered item" in result

    def test_blockquotes_preserved(self, actual_path):
        """Blockquotes should be preserved in round-trip."""
        input_file = INPUTS_DIR / "complex-content.md"
        split_dir = actual_path / "split"
        output_file = actual_path / "output.md"

        split_markdown(input_file, split_dir, level=2)
        join_markdown(split_dir, output_file)

        result = output_file.read_text()

        # Blockquotes should be preserved
        assert "> A blockquote" in result


class TestAllRoundTrips:
    """Test round-trip for all fixtures."""

    @pytest.mark.parametrize(
        "input_file",
        [
            "code-blocks.md",
            "special-chars.md",
            "empty-sections.md",
            "deep-nesting.md",
            "consecutive-headers.md",
            "complex-content.md",
        ],
    )
    def test_roundtrip_preserves_content(self, actual_path, input_file):
        """Test that split -> join preserves content for all fixtures."""
        original_file = INPUTS_DIR / input_file
        split_dir = actual_path / "split"
        rejoined_file = actual_path / "rejoined.md"

        # Split at level 2 (standard)
        split_markdown(original_file, split_dir, level=2)

        # Join back
        join_markdown(split_dir, rejoined_file)

        original_content = original_file.read_text()
        rejoined_content = rejoined_file.read_text()

        # Normalize whitespace for comparison
        def normalize(text):
            lines = [line.rstrip() for line in text.strip().split("\n")]
            # Remove consecutive blank lines
            result = []
            prev_blank = False
            for line in lines:
                is_blank = not line
                if not (is_blank and prev_blank):
                    result.append(line)
                prev_blank = is_blank
            return "\n".join(result)

        assert normalize(rejoined_content) == normalize(original_content)

    def test_trailing_hashes_normalized(self, actual_path):
        """Trailing hashes in headers are normalized (ATX spec allows optional trailing #s)."""
        input_file = INPUTS_DIR / "trailing-hashes.md"
        split_dir = actual_path / "split"
        rejoined_file = actual_path / "rejoined.md"

        split_markdown(input_file, split_dir, level=2)
        join_markdown(split_dir, rejoined_file)

        result = rejoined_file.read_text()

        # Content should be preserved, but trailing hashes are normalized
        assert "Header with Trailing Hash" in result
        assert "Another with Multiple" in result
        assert "Three Hashes" in result
        assert "Mismatched Trailing" in result

    def test_single_header_roundtrip_content(self, actual_path):
        """Single header file preserves content."""
        input_file = INPUTS_DIR / "single-header.md"
        split_dir = actual_path / "split"
        rejoined_file = actual_path / "rejoined.md"

        split_markdown(input_file, split_dir, level=1)
        join_markdown(split_dir, rejoined_file)

        result = rejoined_file.read_text()

        # Content should be preserved
        assert "# Only Header" in result
        assert "Just one header with some content" in result
        assert "Nothing else to split here" in result


class TestErrorConditions:
    """Test error handling."""

    def test_no_headers_raises_error(self, actual_path):
        """File with no headers should raise ValueError."""
        no_headers_file = actual_path / "no-headers.md"
        no_headers_file.write_text("Just plain text, no headers at all.")

        with pytest.raises(ValueError, match="No headers found"):
            split_markdown(no_headers_file, actual_path / "output", level=2)

    def test_nonexistent_file_raises_error(self, actual_path):
        """Nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            split_markdown(actual_path / "nonexistent.md", actual_path / "output", level=2)

    def test_nonexistent_dir_for_join_raises_error(self, actual_path):
        """Nonexistent directory should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            join_markdown(actual_path / "nonexistent", actual_path / "output.md")
