"""Performance and benchmark tests."""

import random
import string
import time

import pytest

from mdstruct.core import join_markdown, split_markdown


class TestBasicPerformance:
    """Basic performance tests for common scenarios."""

    def test_many_sections(self, actual_path):
        """Handle file with many sections."""
        # Create file with 100 H1 sections
        content_parts = []
        for i in range(100):
            content_parts.append(f"# Section {i}\n\nContent for section {i}.\n")

        input_file = actual_path / "large.md"
        input_file.write_text("\n".join(content_parts))

        output_dir = actual_path / "split"
        split_markdown(input_file, output_dir, level=1)

        # Should create 100 files (H1s at level 1 become files)
        files = [f for f in output_dir.iterdir() if f.is_file() and f.suffix == ".md"]
        assert len(files) == 100

        # Round-trip should work
        output_file = actual_path / "rejoined.md"
        join_markdown(output_dir, output_file)

        result = output_file.read_text()
        for i in range(100):
            assert f"# Section {i}" in result

    def test_deeply_nested_structure(self, actual_path):
        """Handle deeply nested hierarchical structure."""
        # Create H1 with 10 H2s each with 5 H3s
        content_parts = []
        for i in range(10):
            content_parts.append(f"# Top {i}\n\nTop level {i}.\n")
            for j in range(5):
                content_parts.append(f"## Mid {i}.{j}\n\nMid level.\n")
                for k in range(3):
                    content_parts.append(f"### Deep {i}.{j}.{k}\n\nDeep content.\n")

        input_file = actual_path / "nested.md"
        input_file.write_text("\n".join(content_parts))

        output_dir = actual_path / "split"
        split_markdown(input_file, output_dir, level=3)

        # Should have deeply nested structure
        deep_files = list(output_dir.rglob("*/*/*.md"))
        assert len(deep_files) > 0

        # Round-trip should work
        output_file = actual_path / "rejoined.md"
        join_markdown(output_dir, output_file)

        result = output_file.read_text()
        assert "# Top 0" in result
        assert "### Deep 9.4.2" in result

    def test_long_content_sections(self, actual_path):
        """Handle sections with very long content."""
        # Create sections with lots of content
        content_parts = []
        for i in range(10):
            content_parts.append(f"# Section {i}\n\n")
            # Add 100 lines of content per section
            for j in range(100):
                content_parts.append(f"Line {j} of content in section {i}.\n")

        input_file = actual_path / "long-content.md"
        input_file.write_text("\n".join(content_parts))

        output_dir = actual_path / "split"
        split_markdown(input_file, output_dir, level=1)

        # Round-trip should preserve all content
        output_file = actual_path / "rejoined.md"
        join_markdown(output_dir, output_file)

        original = input_file.read_text()
        result = output_file.read_text()

        # Count lines to verify nothing was lost
        assert (
            len(result.split("\n")) >= len(original.split("\n")) - 20
        )  # Allow some blank line variance


def generate_random_heading(level: int, used_titles: set) -> str:
    """Generate a random unique heading."""
    while True:
        # Generate random words
        num_words = random.randint(2, 5)
        words = []
        for _ in range(num_words):
            word_length = random.randint(3, 10)
            word = "".join(random.choices(string.ascii_lowercase, k=word_length))
            words.append(word.capitalize())

        title = " ".join(words)
        if title not in used_titles:
            used_titles.add(title)
            return "#" * level + " " + title


@pytest.mark.slow
class TestPerformance:
    """Performance benchmarks for large files."""

    def test_large_file_30k_headings(self, actual_path):
        """
        Performance test: Generate ~200MB file with 33,330 random headings and split it.

        This test is marked as slow and can be skipped with: pytest -m "not slow"
        """
        print("\n=== Generating large test file ===")

        # Target metrics
        # To reach ~200MB, we need significant content per heading
        # With 33,330 headings, that's ~6KB per section on average
        lines_per_section = 350  # Each line ~17 bytes = ~6KB per section

        content_parts = []
        used_titles = set()

        # Generate hierarchical structure
        # Structure: H1 (30) -> H2 (10 each) -> H3 (10 each) -> H4 (10 each) = 33,330 headers
        h1_count = 30
        h2_per_h1 = 10
        h3_per_h2 = 10
        h4_per_h3 = 10

        total_expected = h1_count * (1 + h2_per_h1 * (1 + h3_per_h2 * (1 + h4_per_h3)))
        print(f"Expected headers: {total_expected}")

        start_gen = time.time()

        for i in range(h1_count):
            if i % 10 == 0:
                print(f"  Generating H1 {i}/{h1_count}...")

            content_parts.append(generate_random_heading(1, used_titles))
            content_parts.append("\n")

            for _ in range(lines_per_section):
                content_parts.append(f"Content line {random.randint(1000, 9999)}\n")

            for _j in range(h2_per_h1):
                content_parts.append(generate_random_heading(2, used_titles))
                content_parts.append("\n")

                for _ in range(lines_per_section):
                    content_parts.append(
                        f"H2 content {random.randint(1000, 9999)} more text here.\n"
                    )

                for _k in range(h3_per_h2):
                    content_parts.append(generate_random_heading(3, used_titles))
                    content_parts.append("\n")

                    for _ in range(lines_per_section):
                        content_parts.append(
                            f"H3 content {random.randint(1000, 9999)} even more text.\n"
                        )

                    for _l in range(h4_per_h3):
                        content_parts.append(generate_random_heading(4, used_titles))
                        content_parts.append("\n")

                        for _ in range(lines_per_section):
                            content_parts.append(f"H4 content {random.randint(1000, 9999)}\n")

        content = "".join(content_parts)
        gen_time = time.time() - start_gen

        file_size_mb = len(content) / (1024 * 1024)
        print(f"Generated {file_size_mb:.1f} MB in {gen_time:.2f}s")
        print(f"Total unique titles: {len(used_titles)}")

        # Write to file
        input_file = actual_path / "large-perf.md"
        print(f"Writing to {input_file}...")
        start_write = time.time()
        input_file.write_text(content)
        write_time = time.time() - start_write
        print(f"Write completed in {write_time:.2f}s")

        # Split the file
        output_dir = actual_path / "split"
        print(f"\n=== Splitting to {output_dir} ===")
        start_split = time.time()
        split_markdown(input_file, output_dir, level=4)
        split_time = time.time() - start_split
        print(f"Split completed in {split_time:.2f}s")

        # Count output files
        all_files = list(output_dir.rglob("*.md"))
        print(f"Created {len(all_files)} files")

        # Join back
        output_file = actual_path / "rejoined.md"
        print(f"\n=== Joining back to {output_file} ===")
        start_join = time.time()
        join_markdown(output_dir, output_file)
        join_time = time.time() - start_join
        print(f"Join completed in {join_time:.2f}s")

        rejoined_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"Rejoined file size: {rejoined_size_mb:.1f} MB")

        # Summary
        print("\n=== Performance Summary ===")
        print(f"File size: {file_size_mb:.1f} MB")
        print(f"Headers: {len(used_titles)}")
        print(f"Generation time: {gen_time:.2f}s")
        print(f"Write time: {write_time:.2f}s")
        print(f"Split time: {split_time:.2f}s ({file_size_mb / split_time:.1f} MB/s)")
        print(f"Join time: {join_time:.2f}s ({rejoined_size_mb / join_time:.1f} MB/s)")
        print(f"Total time: {gen_time + write_time + split_time + join_time:.2f}s")

        # Assertions
        assert file_size_mb >= 190, f"File should be ~200MB, got {file_size_mb:.1f}MB"
        assert len(used_titles) >= 33_000, f"Should have 33,330 headers, got {len(used_titles)}"
        assert len(all_files) > 0, "Should create split files"
        assert output_file.exists(), "Should create rejoined file"

        # Performance expectations (adjust based on your system)
        # These are generous limits - on modern hardware should be much faster
        assert split_time < 60, f"Split should complete in <60s, took {split_time:.2f}s"
        assert join_time < 60, f"Join should complete in <60s, took {join_time:.2f}s"

    def test_medium_file_1000_headings(self, actual_path):
        """
        Faster performance test with 1000 headings (~30MB).

        This is a quicker version for regular test runs.
        """
        print("\n=== Medium file test: 1000 headings ===")

        # Generate 1000 headings in a reasonable structure
        # 10 H1s, 10 H2s each, 10 H3s each = 1,110 headers
        content_parts = []
        used_titles = set()

        for _i in range(10):
            content_parts.append(generate_random_heading(1, used_titles))
            content_parts.append("\nH1 content here.\n\n")

            for _j in range(10):
                content_parts.append(generate_random_heading(2, used_titles))
                content_parts.append("\nH2 content here.\n\n")

                for _k in range(10):
                    content_parts.append(generate_random_heading(3, used_titles))
                    content_parts.append("\nH3 content here.\n\n")

        input_file = actual_path / "medium.md"
        input_file.write_text("".join(content_parts))

        file_size_mb = input_file.stat().st_size / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB, Headers: {len(used_titles)}")

        # Split
        output_dir = actual_path / "split"
        start_split = time.time()
        split_markdown(input_file, output_dir, level=3)
        split_time = time.time() - start_split

        # Join
        output_file = actual_path / "rejoined.md"
        start_join = time.time()
        join_markdown(output_dir, output_file)
        join_time = time.time() - start_join

        print(f"Split: {split_time:.3f}s, Join: {join_time:.3f}s")

        # Should be fast
        assert split_time < 5, f"Split should be <5s for medium file, took {split_time:.3f}s"
        assert join_time < 5, f"Join should be <5s for medium file, took {join_time:.3f}s"
        assert len(used_titles) >= 1000
