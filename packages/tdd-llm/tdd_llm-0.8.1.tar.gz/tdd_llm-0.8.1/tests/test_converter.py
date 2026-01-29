"""Tests for converter module."""


from tdd_llm.converter import extract_description, md_to_toml


class TestExtractDescription:
    """Tests for extract_description function."""

    def test_extract_from_content_after_title(self):
        """Test extracting description from first paragraph after title."""
        content = "# My Title\n\nSome content here."
        result = extract_description(content)
        assert result == "Some content here."

    def test_extract_without_title(self):
        """Test extracting from first line when no title."""
        content = "This is the first line.\n\nMore content."
        result = extract_description(content)
        assert result == "This is the first line."

    def test_skip_command_title(self):
        """Test skipping command-style titles."""
        content = "# /tdd:flow:1-analyze\n\nActual description here."
        result = extract_description(content)
        assert result == "Actual description here."

    def test_truncate_long_description(self):
        """Test that long descriptions are truncated."""
        long_text = "A" * 200
        content = f"# Title\n\n{long_text}"
        result = extract_description(content)
        assert len(result) <= 103  # 100 + "..."
        assert result.endswith("...")

    def test_empty_content(self):
        """Test empty content returns default."""
        result = extract_description("")
        assert result == "Command"  # Actual default

    def test_only_title_fallback(self):
        """Test content with only title falls back to title."""
        content = "# Just a Title"
        result = extract_description(content)
        assert result == "Just a Title"


class TestMdToToml:
    """Tests for md_to_toml function."""

    def test_basic_conversion(self):
        """Test basic markdown to TOML conversion."""
        md_content = "# My Command\n\nDo something useful."
        result = md_to_toml(md_content)

        # Description comes from content after title
        assert 'description = "Do something useful."' in result
        assert 'prompt = """' in result
        assert "# My Command" in result
        assert "Do something useful." in result
        assert result.endswith('"""')

    def test_preserves_content(self):
        """Test that full content is preserved in prompt."""
        md_content = """# Title

## Section 1

Some content.

## Section 2

More content.
"""
        result = md_to_toml(md_content)

        assert "## Section 1" in result
        assert "## Section 2" in result
        assert "Some content." in result
        assert "More content." in result

    def test_escapes_triple_quotes(self):
        """Test that triple quotes in content are handled."""
        md_content = '# Title\n\n```python\nprint("hello")\n```'
        result = md_to_toml(md_content)

        # Should still be valid TOML structure
        assert 'description = "' in result
        assert 'prompt = """' in result

    def test_command_style_title(self):
        """Test conversion with command-style title."""
        md_content = "# /tdd:flow:1-analyze\n\nAnalyze the task."
        result = md_to_toml(md_content)

        # Description should come from content, not command title
        assert 'description = "Analyze the task' in result

    def test_multiline_content(self):
        """Test that multiline content is preserved."""
        md_content = """# Title

Line 1
Line 2
Line 3
"""
        result = md_to_toml(md_content)

        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
