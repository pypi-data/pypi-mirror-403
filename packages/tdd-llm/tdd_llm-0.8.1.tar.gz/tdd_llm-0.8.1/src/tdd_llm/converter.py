"""Convert Claude .md files to Gemini .toml format."""

import re
from pathlib import Path


def extract_description(content: str) -> str:
    """Extract description from markdown content.

    Takes the first non-empty line after the title, or the title itself
    if no description follows.

    Args:
        content: Markdown content.

    Returns:
        Description string for TOML.
    """
    lines = content.strip().split("\n")

    # Find title line (starts with #)
    title = ""
    description_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            # Extract title without # prefix
            title = re.sub(r"^#+\s*", "", stripped)
            description_start = i + 1
            break

    # Look for first non-empty line after title for description
    for i in range(description_start, len(lines)):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            # Use this as description (truncate if too long)
            desc = stripped[:100]
            if len(stripped) > 100:
                desc += "..."
            return desc

    # Fallback to title
    return title if title else "Command"


def md_to_toml(content: str) -> str:
    """Convert markdown content to Gemini TOML format.

    Args:
        content: Markdown content from Claude command file.

    Returns:
        TOML content for Gemini command file.
    """
    description = extract_description(content)

    # Escape any triple quotes in the content
    escaped_content = content.replace('"""', '\\"\\"\\"')

    # Build TOML
    toml_lines = [
        f'description = "{description}"',
        'prompt = """',
        escaped_content,
        '"""',
    ]

    return "\n".join(toml_lines)


def convert_file(source: Path, dest: Path) -> None:
    """Convert a single .md file to .toml.

    Args:
        source: Source .md file path.
        dest: Destination .toml file path.
    """
    content = source.read_text(encoding="utf-8")
    toml_content = md_to_toml(content)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(toml_content, encoding="utf-8")


def get_toml_path(md_path: Path) -> Path:
    """Get the corresponding .toml path for a .md file.

    Args:
        md_path: Path to .md file.

    Returns:
        Path with .toml extension.
    """
    return md_path.with_suffix(".toml")
