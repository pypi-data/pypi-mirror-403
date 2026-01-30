"""Tests for core split/join functionality."""

from pathlib import Path

import pytest

from mdstruct.core import join_markdown, slugify, split_markdown

FIXTURES_DIR = Path(__file__).parent / "fixtures"
INPUTS_DIR = FIXTURES_DIR / "inputs"


class TestSlugify:
    """Test slug generation from header text."""

    def test_basic_slugify(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self):
        assert slugify("Hello, World!") == "hello-world"

    def test_markdown_formatting(self):
        assert slugify("**Bold** and *italic*") == "bold-and-italic"

    def test_multiple_spaces(self):
        assert slugify("Multiple   Spaces") == "multiple-spaces"

    def test_trailing_hyphens(self):
        assert slugify("-Leading and Trailing-") == "leading-and-trailing"


class TestSplitMarkdown:
    """Test markdown splitting functionality."""

    def test_split_simple_level2(self, actual_path):
        """Test splitting simple.md at level 2."""
        input_file = INPUTS_DIR / "simple.md"
        output_dir = actual_path / "simple"

        split_markdown(input_file, output_dir, level=2)

        # Check directory structure - no prefixes needed (alphabetical)
        assert (output_dir / "first-section").is_dir()
        assert (output_dir / "second-section").is_dir()
        assert (output_dir / "first-section" / "subsection-a.md").exists()
        assert (output_dir / "first-section" / "subsection-b.md").exists()
        assert (output_dir / "second-section" / "another-subsection.md").exists()

    def test_split_with_preamble(self, actual_path):
        """Test splitting file with preamble content."""
        input_file = INPUTS_DIR / "with-preamble.md"
        output_dir = actual_path / "with-preamble"

        split_markdown(input_file, output_dir, level=2)

        # Check that preamble is in README.md
        readme = output_dir / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "This is preamble content" in content

    def test_split_with_frontmatter(self, actual_path):
        """Test splitting file with YAML frontmatter."""
        input_file = INPUTS_DIR / "with-frontmatter.md"
        output_dir = actual_path / "with-frontmatter"

        split_markdown(input_file, output_dir, level=2)

        # Check that frontmatter is preserved in top-level README.md
        readme = output_dir / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert "---" in content
        assert "title: Example Document" in content
        assert "author: Test Author" in content

        # Verify sections were still split correctly
        assert (output_dir / "first-section").is_dir()
        assert (output_dir / "second-section").is_dir()

    def test_split_nested_level3(self, actual_path):
        """Test splitting nested.md at level 3."""
        input_file = INPUTS_DIR / "nested.md"
        output_dir = actual_path / "nested"

        split_markdown(input_file, output_dir, level=3)

        # Verify deep nesting exists (with dense sequential prefixes where needed)
        # H1s need prefixes (not alphabetical): 2 items → 0, 1
        # H2s under main-topic need prefixes (not alphabetical): 2 items → 0, 1
        # H3s under overview don't need prefixes (alphabetical: "detail-1", "detail-2")
        assert (output_dir / "0.main-topic" / "0.overview").is_dir()
        assert (output_dir / "0.main-topic" / "0.overview" / "detail-1.md").exists()
        assert (output_dir / "0.main-topic" / "0.overview" / "detail-2.md").exists()

    def test_split_nonexistent_file(self, actual_path):
        """Test splitting nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            split_markdown(actual_path / "nonexistent.md", actual_path / "output", level=2)

    def test_split_no_headers(self, actual_path):
        """Test splitting file with no headers raises error."""
        no_headers_file = actual_path / "no-headers.md"
        no_headers_file.write_text("Just plain text, no headers.")

        with pytest.raises(ValueError, match="No headers found"):
            split_markdown(no_headers_file, actual_path / "output", level=2)


class TestJoinMarkdown:
    """Test markdown joining functionality."""

    def test_join_simple(self, actual_path):
        """Test joining split files back together."""
        # First split
        input_file = INPUTS_DIR / "simple.md"
        split_dir = actual_path / "simple-split"
        split_markdown(input_file, split_dir, level=2)

        # Then join
        output_file = actual_path / "simple-rejoined.md"
        join_markdown(split_dir, output_file)

        # Verify result (content should be equivalent, but may have formatting differences)
        assert output_file.exists()
        output_content = output_file.read_text()

        # Check that major sections are present
        assert "# First Section" in output_content
        assert "## Subsection A" in output_content
        assert "# Second Section" in output_content

    def test_join_nonexistent_dir(self, actual_path):
        """Test joining nonexistent directory raises error."""
        with pytest.raises(FileNotFoundError):
            join_markdown(actual_path / "nonexistent", actual_path / "output.md")

    def test_join_preserves_hierarchy(self, actual_path):
        """Test that joining preserves header hierarchy."""
        # Split nested file
        input_file = INPUTS_DIR / "nested.md"
        split_dir = actual_path / "nested-split"
        split_markdown(input_file, split_dir, level=3)

        # Join back
        output_file = actual_path / "nested-rejoined.md"
        join_markdown(split_dir, output_file)

        # Verify hierarchy
        content = output_file.read_text()
        lines = content.split("\n")

        # Check that headers appear in correct order
        h1_indices = [i for i, line in enumerate(lines) if line.startswith("# ")]
        h2_indices = [i for i, line in enumerate(lines) if line.startswith("## ")]
        h3_indices = [i for i, line in enumerate(lines) if line.startswith("### ")]

        # There should be headers at each level
        assert len(h1_indices) > 0
        assert len(h2_indices) > 0
        assert len(h3_indices) > 0


class TestRoundTrip:
    """Test split -> join round-trip behavior."""

    @pytest.mark.parametrize(
        "input_file",
        [
            "simple.md",
            "nested.md",
            "with-preamble.md",
            "with-frontmatter.md",
        ],
    )
    def test_roundtrip_preserves_content(self, actual_path, input_file):
        """Test that split -> join preserves all content."""
        original_file = INPUTS_DIR / input_file
        original_content = original_file.read_text()

        # Split
        split_dir = actual_path / "split"
        split_markdown(original_file, split_dir, level=2)

        # Join
        rejoined_file = actual_path / "rejoined.md"
        join_markdown(split_dir, rejoined_file)

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
