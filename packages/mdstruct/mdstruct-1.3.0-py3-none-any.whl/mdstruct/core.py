"""Core functionality for splitting and joining markdown files."""

import re
from dataclasses import dataclass
from pathlib import Path

# Pre-compile regex patterns for performance
HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#*)?$")


@dataclass
class Header:
    """Represents a markdown ATX header."""

    level: int
    title: str
    line_num: int
    full_line: str


def slugify(text: str) -> str:
    """Convert header text to a filesystem-safe slug."""
    # Remove markdown formatting
    text = re.sub(r"[*_`]", "", text)
    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    # Lowercase for consistency
    return text.strip("-").lower()


def index_to_prefix(index: int, total_count: int) -> str:
    """
    Convert 0-based index to prefix based on total item count.

    Uses rescaling strategy:
    - ≤36 items: 1-char indexes (0-9, a-z)
    - 37-702 items: 2-char indexes (aa-zz, base-26)
    - 703+ items: 3-char indexes (aaa-zzz, base-26)

    This allows fractional insertion by users:
    - Between 0 and 1: insert 0m, 0z (any chars after index)
    - Between z and aa: insert z0, zm, zz
    - Between aa and ab: insert aam, aaz

    Examples with total_count=10:
    - index 0 → "0."
    - index 9 → "9."

    Examples with total_count=50:
    - index 0 → "aa."
    - index 25 → "az."
    - index 49 → "bx."
    """
    if total_count <= 36:
        # 1-char indexes: 0-9, a-z
        if index < 10:
            return str(index) + "."
        else:
            return chr(ord("a") + index - 10) + "."
    elif total_count <= 702:  # 26^2 + 26 + 10 = 702
        # 2-char indexes: aa-zz (base-26)
        result = ""
        temp = index
        for _ in range(2):
            result = chr(ord("a") + (temp % 26)) + result
            temp //= 26
        return result + "."
    else:
        # 3+ char indexes
        width = 3
        capacity = 26**3
        while capacity <= total_count:
            width += 1
            capacity = 26**width

        result = ""
        temp = index
        for _ in range(width):
            result = chr(ord("a") + (temp % 26)) + result
            temp //= 26
        return result + "."


def compute_code_block_lines(lines: list[str]) -> list[bool]:
    """
    Precompute which lines are inside code blocks.

    Returns a list of booleans where True means the line is inside a code block.
    """
    in_code_block = []
    in_code = False

    for line in lines:
        in_code_block.append(in_code)
        # Use lstrip() instead of strip() - only need to check line start
        line_stripped = line.lstrip()
        if line_stripped.startswith("```") or line_stripped.startswith("~~~"):
            in_code = not in_code

    return in_code_block


def parse_headers(lines: list[str], *, in_code_block: list[bool]) -> list[Header]:
    """
    Parse ATX headers from markdown content.

    Returns list of Header objects.
    Ignores headers inside code blocks.
    """
    headers = []
    for i, line in enumerate(lines):
        # Skip if inside code block
        if in_code_block[i]:
            continue

        # Pre-filter: skip lines that obviously aren't headers
        stripped = line.lstrip()
        if not stripped or stripped[0] != "#":
            continue

        match = HEADER_PATTERN.match(stripped)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append(Header(level=level, title=title, line_num=i, full_line=line))

    return headers


def bump_heading_levels(text: str, bump_by: int, in_code_block: list[bool] | None = None) -> str:
    """
    Adjust heading levels in markdown text.

    Args:
        text: Markdown content
        bump_by: Positive to increase level (H2->H1), negative to decrease (H1->H2)
        in_code_block: Optional pre-computed code block info. If None, will compute.

    Returns:
        Modified markdown with adjusted heading levels
    """
    if bump_by == 0:
        return text

    lines = text.split("\n")
    if in_code_block is None:
        in_code_block = compute_code_block_lines(lines)
    result = []

    for i, line in enumerate(lines):
        # Skip if inside code block
        if in_code_block[i]:
            result.append(line)
            continue

        # Pre-filter: skip lines that obviously aren't headers
        stripped = line.lstrip()
        if not stripped or stripped[0] != "#":
            result.append(line)
            continue

        match = HEADER_PATTERN.match(stripped)
        if match:
            current_level = len(match.group(1))
            title = match.group(2).strip()
            new_level = max(1, min(6, current_level - bump_by))
            result.append("#" * new_level + " " + title)
        else:
            result.append(line)

    return "\n".join(result)


def split_markdown(input_path: Path, output_dir: Path, level: int | None = None) -> None:
    """
    Split markdown file hierarchically by headers.

    Headings are bumped up in split files (H2 becomes H1, etc.) to make them standalone.

    Args:
        input_path: Path to input .md file
        output_dir: Directory to write split files
        level: Maximum heading level to split at (splits H1, then H2s, etc.)
               If None, automatically determines the best level:
               - Multiple H1s: split at level 1
               - Single H1: split at level 2
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    content = input_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Parse all headers
    in_code_block = compute_code_block_lines(lines)
    headers = parse_headers(lines, in_code_block=in_code_block)

    if not headers:
        raise ValueError("No headers found in markdown file")

    # Auto-detect best level if not specified
    if level is None:
        h1_count = sum(1 for h in headers if h.level == 1)
        if h1_count == 0:
            # No H1s, start from H2
            level = 2
        elif h1_count == 1:
            # Single H1, split on H2s
            level = 2
        else:
            # Multiple H1s, split on H1s
            level = 1

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Compute code block info once for entire file

    # Determine starting level based on content
    # If there are no H1s or just one H1, start splitting from H2
    # This avoids creating a single folder for the lone H1
    h1_count = sum(1 for h in headers if h.level == 1)
    if h1_count <= 1:
        # No H1s or single H1 - start from level 2 (avoids lone folder)
        _split_by_level(
            lines,
            headers,
            output_dir,
            target_level=2,
            max_level=level,
            bump_level=1,
            in_code_block=in_code_block,
        )
    else:
        # Split by hierarchical levels starting from H1
        _split_by_level(
            lines,
            headers,
            output_dir,
            target_level=1,
            max_level=level,
            bump_level=0,
            in_code_block=in_code_block,
        )


def _split_by_level(
    lines: list[str],
    headers: list[Header],
    parent_dir: Path,
    target_level: int,
    max_level: int,
    bump_level: int,
    in_code_block: list[bool],
    start_line: int = 0,
    end_line: int | None = None,
) -> None:
    """
    Recursively split content by header levels.

    Args:
        lines: Content lines
        headers: Parsed headers
        parent_dir: Output directory
        target_level: Current heading level to split at
        max_level: Maximum level to split to
        bump_level: How many levels to bump headings down (for standalone files)
        in_code_block: Pre-computed code block info for all lines
        start_line: Start of section
        end_line: End of section
    """
    if end_line is None:
        end_line = len(lines)

    # Filter headers at target level within range
    level_headers = [
        h for h in headers if h.level == target_level and start_line <= h.line_num < end_line
    ]

    if not level_headers:
        # No headers at this level - write all content to README.md
        content = "\n".join(lines[start_line:end_line]).strip()
        if content:
            if bump_level > 0:
                # Pass subset of code block info for this section
                section_code_blocks = in_code_block[start_line:end_line]
                content = bump_heading_levels(content, bump_level, section_code_blocks)
            readme_path = parent_dir / "README.md"
            readme_path.write_text(content + "\n", encoding="utf-8")
        return

    # Handle preamble content before first header at this level
    first_header_line = level_headers[0].line_num
    if first_header_line > start_line:
        preamble = "\n".join(lines[start_line:first_header_line]).strip()
        if preamble:
            # Bump headings in preamble
            if bump_level > 0:
                section_code_blocks = in_code_block[start_line:first_header_line]
                preamble = bump_heading_levels(preamble, bump_level, section_code_blocks)
            readme_path = parent_dir / "README.md"
            readme_path.write_text(preamble + "\n", encoding="utf-8")

    # Generate slugs and check if prefixes are needed
    slugs = [slugify(h.title) for h in level_headers]
    # Need prefixes if: (1) not in alphabetical order, or (2) there are duplicates
    has_duplicates = len(slugs) != len(set(slugs))
    needs_prefixes = slugs != sorted(slugs) or has_duplicates

    # Split each section at this level
    for i, header in enumerate(level_headers):
        # Determine end of this section
        if i + 1 < len(level_headers):
            section_end = level_headers[i + 1].line_num
        else:
            section_end = end_line

        # Create filename from header with optional alphanumeric prefix
        slug = slugs[i]
        if needs_prefixes:
            slug_with_prefix = index_to_prefix(i, len(level_headers)) + slug
        else:
            slug_with_prefix = slug

        # If we're at max level, write file with bumped headings
        if target_level >= max_level:
            # Extract section content including header
            section_content = "\n".join(lines[header.line_num : section_end]).strip()

            # Bump headings down (H2 becomes H1, etc.) for standalone files
            if bump_level > 0:
                section_code_blocks = in_code_block[header.line_num : section_end]
                section_content = bump_heading_levels(
                    section_content, bump_level, section_code_blocks
                )

            file_path = parent_dir / f"{slug_with_prefix}.md"
            file_path.write_text(section_content + "\n", encoding="utf-8")
        else:
            # Create subdirectory and recurse
            section_dir = parent_dir / slug_with_prefix
            section_dir.mkdir(parents=True, exist_ok=True)

            # Recursively split subsections
            # Start from header.line_num (include header) so it can be written to README
            _split_by_level(
                lines,
                headers,
                section_dir,
                target_level + 1,
                max_level,
                bump_level + 1,
                in_code_block,
                header.line_num,  # Include the header line
                section_end,
            )


def join_markdown(input_dir: Path, output_path: Path) -> None:
    """
    Join split markdown files back into a single file.

    Reverses the split operation, restoring original heading levels.

    Args:
        input_dir: Directory containing split markdown files
        output_path: Path to write combined .md file
    """
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    parts = []

    # Read README.md first if it exists (preamble content before any headers)
    readme_path = input_dir / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8").strip()
        # Preamble should not have headings bumped
        parts.append(content)

    # Recursively collect all markdown files
    _collect_markdown_files(input_dir, parts, depth=0)

    # Write combined content
    combined = "\n\n".join(parts)
    output_path.write_text(combined + "\n", encoding="utf-8")


def _collect_markdown_files(directory: Path, parts: list[str], depth: int) -> None:
    """
    Recursively collect markdown files in sorted order.

    Args:
        directory: Directory to scan
        parts: List to append content to
        depth: Current depth (0 = top level, 1 = first subdirectory, etc.)
    """
    # Get all items in directory, sorted by name (numeric prefixes ensure correct order)
    items = sorted(directory.iterdir(), key=lambda p: p.name)

    for item in items:
        if item.name == "README.md":
            continue  # Already handled at parent level

        if item.is_file() and item.suffix == ".md":
            # Read file content
            content = item.read_text(encoding="utf-8").strip()

            # Unbump headings to restore original structure
            # Files were bumped during split:
            # - depth 0: may be bumped by 1 if single/no H1 (split skips H1 folder)
            # - depth 1+: bumped by depth levels
            # Use max(1, depth) to handle both cases correctly
            unbump = max(1, depth)
            content = bump_heading_levels(content, -unbump)

            parts.append(content)

        elif item.is_dir():
            # Directory represents a header section
            # The header is stored in the first line of README.md
            subdir_readme = item / "README.md"

            if subdir_readme.exists():
                readme_content = subdir_readme.read_text(encoding="utf-8").strip()
                readme_lines = readme_content.split("\n")

                # First line should be the header (bumped)
                first_line = readme_lines[0] if readme_lines else ""
                header_match = HEADER_PATTERN.match(first_line.strip())

                if header_match:
                    # Extract header text and reconstruct at correct level
                    header_text = header_match.group(2).strip()
                    header_level = depth + 1
                    header = "#" * header_level + " " + header_text
                    parts.append(header)

                    # Add remaining README content (if any) after the header
                    if len(readme_lines) > 1:
                        remaining = "\n".join(readme_lines[1:]).strip()
                        if remaining:
                            # Unbump headings in remaining content
                            if depth > 0:
                                remaining = bump_heading_levels(remaining, -depth)
                            parts.append(remaining)
                else:
                    # No header in README, fall back to directory name
                    header_text = _slug_to_title(item.name)
                    header_level = depth + 1
                    header = "#" * header_level + " " + header_text
                    parts.append(header)

                    # Add all README content
                    if depth > 0:
                        readme_content = bump_heading_levels(readme_content, -depth)
                    parts.append(readme_content)
            else:
                # No README, reconstruct from directory name
                header_text = _slug_to_title(item.name)
                header_level = depth + 1
                header = "#" * header_level + " " + header_text
                parts.append(header)

            # Recurse into subdirectory
            _collect_markdown_files(item, parts, depth + 1)


def _slug_to_title(slug: str) -> str:
    """
    Convert a slug back to a title.

    Strips alphanumeric prefix if present (e.g., "0.foo", "a.bar", "00.baz" -> "Foo", "Bar", "Baz").
    Note: This is a best-effort conversion. The original casing is lost.
    """
    # Strip alphanumeric prefix (one or more digits/letters followed by dot)
    slug = re.sub(r"^[0-9a-z]+\.", "", slug)
    # Replace hyphens with spaces and title-case
    return slug.replace("-", " ").title()
