"""Stress tests for edge cases."""

from mdstruct.core import join_markdown, split_markdown


class TestDuplicateHeaders:
    """Test handling of duplicate header names."""

    def test_duplicate_header_names(self, actual_path):
        """Sections with same header name should be handled."""
        content = """# Introduction

First intro.

## Setup

First setup.

# Introduction

Second intro.

## Setup

Second setup.
"""
        input_file = actual_path / "duplicates.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        split_markdown(input_file, output_dir, level=2)

        # Should create files with numeric prefixes to differentiate
        files = list(output_dir.rglob("*.md"))
        [f.name for f in files]

        # Should have multiple introduction directories
        intro_dirs = [d for d in output_dir.iterdir() if "introduction" in d.name.lower()]
        assert len(intro_dirs) == 2

    def test_duplicate_headers_roundtrip(self, actual_path):
        """Duplicate headers should round-trip correctly."""
        content = """# Same Name

First content.

# Same Name

Second content.

# Same Name

Third content.
"""
        input_file = actual_path / "same-names.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        output_file = actual_path / "rejoined.md"

        split_markdown(input_file, output_dir, level=1)
        join_markdown(output_dir, output_file)

        result = output_file.read_text()

        # All three sections should be preserved
        assert result.count("# Same Name") == 3
        assert "First content" in result
        assert "Second content" in result
        assert "Third content" in result


class TestWhitespace:
    """Test whitespace handling."""

    def test_preserves_indentation(self, actual_path):
        """Indentation in content should be preserved."""
        content = """# Code Example

Here's some indented content:

    def foo():
        return bar()

## Another Section

- List item
  - Nested item
    - Double nested
"""
        input_file = actual_path / "indented.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        output_file = actual_path / "rejoined.md"

        split_markdown(input_file, output_dir, level=2)
        join_markdown(output_dir, output_file)

        result = output_file.read_text()

        # Indentation should be preserved
        assert "    def foo():" in result
        assert "        return bar()" in result
        assert "  - Nested item" in result
        assert "    - Double nested" in result

    def test_handles_multiple_blank_lines(self, actual_path):
        """Multiple consecutive blank lines should be handled."""
        content = """# Header One


Content with multiple blank lines.



## Subheader


More content.


"""
        input_file = actual_path / "blanks.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        output_file = actual_path / "rejoined.md"

        split_markdown(input_file, output_dir, level=2)
        join_markdown(output_dir, output_file)

        # Should successfully round-trip
        assert output_file.exists()


class TestUnicode:
    """Test Unicode and internationalization."""

    def test_unicode_headers(self, actual_path):
        """Headers with Unicode characters should work."""
        content = """# 中文标题

Chinese content.

## 日本語のヘッダー

Japanese content.

# Заголовок на русском

Russian content.

## العربية

Arabic content.
"""
        input_file = actual_path / "unicode.md"
        input_file.write_text(content, encoding="utf-8")

        output_dir = actual_path / "split"
        output_file = actual_path / "rejoined.md"

        split_markdown(input_file, output_dir, level=2)
        join_markdown(output_dir, output_file)

        result = output_file.read_text(encoding="utf-8")

        # Unicode should be preserved
        assert "中文标题" in result
        assert "日本語のヘッダー" in result
        assert "Заголовок на русском" in result
        assert "العربية" in result

    def test_unicode_content(self, actual_path):
        """Content with various Unicode should be preserved."""
        content = """# Unicode Test

Math symbols: ∑, ∫, √, ∞

Arrows: →, ←, ↑, ↓, ⇒

Emoji: 😀, 🎉, 🚀, ✨

Special chars: ©, ®, ™, €, £, ¥
"""
        input_file = actual_path / "unicode-content.md"
        input_file.write_text(content, encoding="utf-8")

        output_dir = actual_path / "split"
        output_file = actual_path / "rejoined.md"

        split_markdown(input_file, output_dir, level=1)
        join_markdown(output_dir, output_file)

        result = output_file.read_text(encoding="utf-8")

        # All Unicode should be preserved
        assert "∑, ∫, √, ∞" in result
        assert "😀, 🎉, 🚀, ✨" in result
        assert "©, ®, ™, €, £, ¥" in result
