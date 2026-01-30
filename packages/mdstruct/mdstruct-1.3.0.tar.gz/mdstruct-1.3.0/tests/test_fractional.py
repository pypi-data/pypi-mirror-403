"""Tests for fractional indexing and manual insertion."""

from pathlib import Path

from mdstruct.core import index_to_prefix, split_markdown

FIXTURES_DIR = Path(__file__).parent / "fixtures"
INPUTS_DIR = FIXTURES_DIR / "inputs"


class TestDensePrefixing:
    """Test dense sequential prefix generation."""

    def test_first_ten_items(self):
        """First 10 items should be 0-9."""
        total = 10
        positions = [index_to_prefix(i, total) for i in range(total)]
        assert positions == ["0.", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."]

        # Verify lexicographic sorting
        assert sorted(positions) == positions

    def test_items_up_to_36(self):
        """Up to 36 items should use 1-char: 0-9, a-z."""
        total = 36
        positions = [index_to_prefix(i, total) for i in range(total)]

        # First 10 should be digits
        assert positions[:10] == [str(i) + "." for i in range(10)]

        # Next 26 should be letters
        assert positions[10:36] == [chr(ord("a") + i - 10) + "." for i in range(10, 36)]

        # Verify lexicographic sorting
        assert sorted(positions) == positions

    def test_items_beyond_36_use_two_chars(self):
        """37-702 items should use 2-char indexes: aa-zz."""
        total = 50
        positions = [index_to_prefix(i, total) for i in range(total)]

        # All should be 2 chars + dot
        for pos in positions:
            assert len(pos) == 3, f"{pos} should be 3 chars (2 letters + dot)"

        # Should maintain order
        assert sorted(positions) == positions

        # Check specific values
        assert index_to_prefix(0, total) == "aa."
        assert index_to_prefix(25, total) == "az."

    def test_rescaling_thresholds(self):
        """Test that rescaling happens at correct thresholds."""
        # ≤36 items: 1-char
        assert len(index_to_prefix(0, 36).replace(".", "")) == 1

        # 37-702 items: 2-char
        assert len(index_to_prefix(0, 37).replace(".", "")) == 2
        assert len(index_to_prefix(0, 702).replace(".", "")) == 2

        # 703+ items: 3-char
        assert len(index_to_prefix(0, 703).replace(".", "")) == 3


class TestManualInsertion:
    """Test that manual insertion works between dense positions."""

    def test_insertion_between_0_and_1(self):
        """Users can insert between 0 and 1 using 00-0z."""
        # Initial dense positions
        positions = ["0.", "1.", "2."]

        # Manual insertions between 0 and 1
        insertions = [
            "00.",  # 0 < 00 < 01 < ... < 0z < 1
            "05.",
            "0m.",
            "0z.",
        ]

        all_positions = positions + insertions
        sorted_positions = sorted(all_positions)

        # Verify all insertions are between 0 and 1
        idx_0 = sorted_positions.index("0.")
        idx_1 = sorted_positions.index("1.")

        for ins in insertions:
            idx = sorted_positions.index(ins)
            assert idx_0 < idx < idx_1, f"{ins} should be between 0 and 1"

    def test_insertion_between_9_and_a(self):
        """Users can insert between 9 and a using 90-9z."""
        positions = ["9.", "a.", "b."]

        # Insert between 9 and a
        insertions = ["90.", "95.", "9m.", "9z."]

        all_positions = positions + insertions
        sorted_positions = sorted(all_positions)

        idx_9 = sorted_positions.index("9.")
        idx_a = sorted_positions.index("a.")

        for ins in insertions:
            idx = sorted_positions.index(ins)
            assert idx_9 < idx < idx_a, f"{ins} should be between 9 and a"

    def test_deep_fractional_insertion(self):
        """For very tight spaces, can use 3+ characters."""
        # Between 00 and 01
        positions = ["0.", "00.", "000.", "001.", "00m.", "01.", "1."]

        # Should sort correctly
        assert sorted(positions) == positions

        # Verify order
        assert positions.index("0.") == 0
        assert positions.index("00.") == 1
        assert positions.index("000.") == 2
        assert positions.index("001.") == 3
        assert positions.index("00m.") == 4
        assert positions.index("01.") == 5
        assert positions.index("1.") == 6

    def test_real_world_scenario(self, actual_path):
        """Test a real workflow: split, manual insert, verify order."""
        # Create a test file with 3 non-alphabetical H1s with H2 subsections
        content = """# Zebra

First section.

## Subsection Z

Content Z.

# Apple

Second section.

## Subsection A

Content A.

# Banana

Third section.

## Subsection B

Content B.
"""
        input_file = actual_path / "test.md"
        input_file.write_text(content)

        output_dir = actual_path / "split"
        split_markdown(input_file, output_dir, level=2)

        # Should have dense sequential positions for directories (H1s)
        dirs = sorted([d.name for d in output_dir.iterdir() if d.is_dir()])

        # Verify we got dense positions: 0, 1, 2
        assert len(dirs) == 3
        assert dirs[0].startswith("0.")  # First item (zebra)
        assert dirs[1].startswith("1.")  # Second item (apple)
        assert dirs[2].startswith("2.")  # Third item (banana)

        # Simulate manual insertion: create a new directory between 0 and 1
        # Between 0 and 1, we can use 00, 01, 02, ..., 0z
        new_dir = output_dir / "0m.manually-inserted"
        new_dir.mkdir()
        readme = new_dir / "README.md"
        readme.write_text("# Manually Inserted\n\nThis was added later.\n")

        # Verify filesystem sorting includes the manual insertion correctly
        all_dirs = sorted([d.name for d in output_dir.iterdir() if d.is_dir()])
        assert all_dirs == ["0.zebra", "0m.manually-inserted", "1.apple", "2.banana"]

        # Position of manual insertion is correct
        assert all_dirs.index("0m.manually-inserted") == 1
        assert all_dirs.index("0.zebra") == 0
        assert all_dirs.index("1.apple") == 2


class TestEdgeCases:
    """Test edge cases for dense positioning."""

    def test_positions_are_stable(self):
        """Same index with same total always produces same position."""
        total = 50
        positions1 = [index_to_prefix(i, total) for i in range(total)]
        positions2 = [index_to_prefix(i, total) for i in range(total)]
        assert positions1 == positions2

    def test_single_char_range(self):
        """Up to 36 items use single characters: 0-9, a-z."""
        total = 36
        positions = [index_to_prefix(i, total) for i in range(total)]

        # All should be single char + dot
        for pos in positions:
            assert len(pos) == 2, f"{pos} should be 2 chars (char + dot)"

        # Should use 0-9 and a-z
        all_chars = set("".join(positions).replace(".", ""))
        assert all_chars == set("0123456789abcdefghijklmnopqrstuvwxyz")

    def test_two_char_range(self):
        """37-702 items use 2 chars: aa-zz."""
        total = 100
        positions = [index_to_prefix(i, total) for i in range(total)]

        # All should be 2 chars + dot
        for pos in positions:
            assert len(pos) == 3, f"{pos} should be 3 chars (2 letters + dot)"

        # First should be aa
        assert positions[0] == "aa."
