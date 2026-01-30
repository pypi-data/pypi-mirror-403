"""Tests for smart default detection."""

from mdstruct.core import split_markdown


class TestSmartDefaultLevel:
    """Test automatic level detection."""

    def test_multiple_h1s_defaults_to_level_1(self, actual_path):
        """Multiple H1s should default to splitting at level 1."""
        content = """# First Section

Content here.

# Second Section

More content.

# Third Section

Even more content.
"""
        input_file = actual_path / "multi-h1.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        # Don't specify level - let it auto-detect
        split_markdown(input_file, output_dir)

        # Should split at H1 level (level=1), creating 3 files
        files = [f for f in output_dir.iterdir() if f.is_file() and f.suffix == ".md"]
        assert len(files) == 3
        assert any("first" in f.name for f in files)
        assert any("second" in f.name for f in files)
        assert any("third" in f.name for f in files)

    def test_single_h1_defaults_to_level_2(self, actual_path):
        """Single H1 should default to splitting at level 2."""
        content = """# Main Document

Introduction paragraph.

## Section A

Content A.

## Section B

Content B.

## Section C

Content C.
"""
        input_file = actual_path / "single-h1.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        # Don't specify level - let it auto-detect
        split_markdown(input_file, output_dir)

        # Should split at H2 level (level=2), but skip creating folder for single H1
        # README.md contains the H1 + intro, and H2s become files directly in output_dir
        assert output_dir.is_dir()

        # Should NOT have a main-document directory (single H1 optimization)
        main_dir = output_dir / "main-document"
        assert not main_dir.exists()

        # Should have README.md with the H1 content
        readme = output_dir / "README.md"
        assert readme.exists()
        readme_content = readme.read_text()
        assert "# Main Document" in readme_content
        assert "Introduction paragraph" in readme_content

        # Should have 3 H2 files directly in output_dir
        h2_files = [
            f
            for f in output_dir.iterdir()
            if f.is_file() and f.suffix == ".md" and f.name != "README.md"
        ]
        assert len(h2_files) == 3

    def test_no_h1s_defaults_to_level_2(self, actual_path):
        """No H1s should default to splitting at level 2."""
        content = """## First Section

Content here.

## Second Section

More content.

### Subsection

Nested content.
"""
        input_file = actual_path / "no-h1.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        # Don't specify level - let it auto-detect
        split_markdown(input_file, output_dir)

        # Should split at H2 level (level=2)
        files = [f for f in output_dir.iterdir() if f.is_file() and f.suffix == ".md"]
        assert len(files) == 2

    def test_explicit_level_overrides_auto_detection(self, actual_path):
        """Explicitly specified level should override auto-detection."""
        content = """# First Section

Content here.

# Second Section

More content.
"""
        input_file = actual_path / "multi-h1.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        # Explicitly set level=2 even though auto-detect would choose 1
        split_markdown(input_file, output_dir, level=2)

        # Should create 2 directories (not files)
        dirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(dirs) == 2
