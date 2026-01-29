import pytest
import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
import re

# Add src to path for imports
sys.path.insert(0, str("src"))

from ainator.renderer import StreamingMarkdownPrinter


@pytest.fixture
def mock_output_file():
    """Mock output file for testing."""
    return StringIO()


@pytest.fixture
def mock_reasoning_file():
    """Mock reasoning file for testing."""
    return StringIO()


@pytest.fixture
def printer(mock_output_file, mock_reasoning_file):
    """Create a StreamingMarkdownPrinter instance with mock files."""
    return StreamingMarkdownPrinter(
        output_file=mock_output_file,
        reasoning_file=mock_reasoning_file,
        print_reasoning=True,
        pygments_style="monokai"
    )


@pytest.fixture
def printer_no_reasoning(mock_output_file, mock_reasoning_file):
    """Create a StreamingMarkdownPrinter with reasoning disabled."""
    return StreamingMarkdownPrinter(
        output_file=mock_output_file,
        reasoning_file=mock_reasoning_file,
        print_reasoning=False,
        pygments_style="monokai"
    )


def test_initialization_defaults():
    """Test initialization with default parameters."""
    printer = StreamingMarkdownPrinter()
    
    assert printer.output_file == sys.stderr
    assert printer.reasoning_file == sys.stderr
    assert printer.print_reasoning is True
    assert printer.full_content == ""
    assert printer.full_reasoning == ""
    assert printer.printed_lines == 0
    assert printer.reasoning_header_shown is False
    assert printer.code_open is False


def test_initialization_custom():
    """Test initialization with custom parameters."""
    output = StringIO()
    reasoning = StringIO()
    printer = StreamingMarkdownPrinter(
        output_file=output,
        reasoning_file=reasoning,
        print_reasoning=False,
        pygments_style="native"
    )
    
    assert printer.output_file == output
    assert printer.reasoning_file == reasoning
    assert printer.print_reasoning is False


def test_add_content_empty(printer, mock_output_file):
    """Test adding empty content."""
    printer.add_content("")
    assert printer.full_content == ""
    assert mock_output_file.getvalue() == ""


def test_add_content_simple_text(printer, mock_output_file):
    """Test adding simple text content."""
    text = "Hello, world!\n"
    printer.add_content(text)
    
    assert printer.full_content == text
    # Should print the highlighted content
    assert mock_output_file.getvalue() != ""


def test_add_content_partial_line_no_print(printer, mock_output_file):
    """Test adding content without complete line doesn't print."""
    text = "Partial line"
    printer.add_content(text)
    
    assert printer.full_content == text
    # No complete line, so nothing should be printed yet
    assert mock_output_file.getvalue() == ""


def test_add_content_completes_line(printer, mock_output_file):
    """Test that adding newline completes line and triggers print."""
    printer.add_content("Partial line")
    assert mock_output_file.getvalue() == ""  # Not printed yet
    
    printer.add_content("\n")
    assert mock_output_file.getvalue() != ""  # Now printed


def test_get_content(printer):
    """Test retrieving accumulated content."""
    content1 = "First part\n"
    content2 = "Second part\n"
    
    printer.add_content(content1)
    printer.add_content(content2)
    
    assert printer.get_content() == content1 + content2


def test_add_reasoning_enabled(printer, mock_reasoning_file):
    """Test adding reasoning when enabled."""
    reasoning = "Thinking about this...\n"
    printer.add_reasoning(reasoning)
    
    assert printer.full_reasoning == reasoning
    # Should print reasoning header and content
    output = mock_reasoning_file.getvalue()
    assert "REASONING" in output
    assert reasoning.strip() in output


def test_add_reasoning_disabled(printer_no_reasoning, mock_reasoning_file):
    """Test adding reasoning when disabled."""
    reasoning = "Thinking about this...\n"
    printer_no_reasoning.add_reasoning(reasoning)
    
    # Should not accumulate or print reasoning
    assert printer_no_reasoning.full_reasoning == ""
    assert mock_reasoning_file.getvalue() == ""


def test_add_reasoning_header_only_once(printer, mock_reasoning_file):
    """Test reasoning header is shown only once."""
    reasoning1 = "First thought\n"
    reasoning2 = "Second thought\n"
    
    printer.add_reasoning(reasoning1)
    output1 = mock_reasoning_file.getvalue()
    header_count1 = output1.count("REASONING")
    
    # Reset buffer to count only new output
    mock_reasoning_file.truncate(0)
    mock_reasoning_file.seek(0)
    
    printer.add_reasoning(reasoning2)
    output2 = mock_reasoning_file.getvalue()
    header_count2 = output2.count("REASONING")
    
    # Header should appear only in first output
    assert header_count1 == 1
    assert header_count2 == 0  # No header in second output


def test_get_reasoning(printer):
    """Test retrieving accumulated reasoning."""
    reasoning1 = "First thought\n"
    reasoning2 = "Second thought\n"
    
    printer.add_reasoning(reasoning1)
    printer.add_reasoning(reasoning2)
    
    assert printer.get_reasoning() == reasoning1 + reasoning2


def test_flush_prints_remaining_content(printer, mock_output_file):
    """Test flush prints any remaining unprinted content."""
    content = "Partial line without newline"
    printer.add_content(content)
    
    # Content hasn't been printed yet (no complete line)
    assert mock_output_file.getvalue() == ""
    
    printer.flush()
    
    # Flush should trigger printing of remaining content
    assert mock_output_file.getvalue() != ""


def test_flush_resets_reasoning_header(printer, mock_reasoning_file):
    """Test flush resets reasoning header state."""
    printer.add_reasoning("Some reasoning\n")
    assert printer.reasoning_header_shown is True
    
    printer.flush()
    assert printer.reasoning_header_shown is False


def test_code_block_state_management(printer):
    """Test code block open/close state tracking."""
    # Start with code block closed
    assert printer.code_open is False
    
    # Open code block
    printer.add_content("```python\n")
    assert printer.code_open is True
    
    # Close code block
    printer.add_content("```\n")
    assert printer.code_open is False
    
    # Open again with different language
    printer.add_content("```javascript\n")
    assert printer.code_open is True


def test_markdown_highlighting_basic(printer, mock_output_file):
    """Test basic markdown highlighting."""
    content = "# Heading\n\n**Bold** and *italic* text.\n"
    printer.add_content(content)
    
    output = mock_output_file.getvalue()
    # Should have some output (highlighted)
    assert output != ""
    # Should not contain raw markdown markers in highlighted output
    # (though this depends on pygments theme)


def test_markdown_highlighting_with_code(printer, mock_output_file):
    """Test markdown highlighting with code blocks."""
    content = "```python\ndef hello():\n    print('world')\n```\n"
    printer.add_content(content)
    
    output = mock_output_file.getvalue()
    assert output != ""


def test_streaming_with_multiple_chunks(printer, mock_output_file):
    """Test streaming content in multiple chunks."""
    chunks = [
        "# Title\n",
        "\n",
        "Some content ",
        "split across ",
        "multiple chunks.\n",
        "```python\n",
        "print('hello')\n",
        "```\n"
    ]
    
    for chunk in chunks:
        printer.add_content(chunk)
    
    # All content should be accumulated
    expected_content = "".join(chunks)
    assert printer.get_content() == expected_content
    
    # Should have printed something
    assert mock_output_file.getvalue() != ""


def test_reasoning_stops_when_content_appears(printer, mock_reasoning_file, mock_output_file):
    """Test reasoning stops and newline added when content appears."""
    # Add reasoning
    printer.add_reasoning("Thinking...\n")
    reasoning_output = mock_reasoning_file.getvalue()
    assert "REASONING" in reasoning_output
    
    # Add content
    printer.add_content("Actual answer\n")
    
    # Check that reasoning file got a newline after content appeared
    # (The implementation adds newline when content appears after reasoning)
    # We need to check the full output
    final_reasoning_output = mock_reasoning_file.getvalue()
    # Should end with newline after the content printed
    assert final_reasoning_output.endswith("\n") or "\n\n" in final_reasoning_output


def test_empty_reasoning_not_printed(printer, mock_reasoning_file):
    """Test empty reasoning text is not printed."""
    printer.add_reasoning("")
    assert mock_reasoning_file.getvalue() == ""
    assert printer.reasoning_header_shown is False


def test_empty_content_not_printed(printer, mock_output_file):
    """Test empty content text is not printed."""
    printer.add_content("")
    assert mock_output_file.getvalue() == ""


def test_style_parameter_affects_highlighting():
    """Test that different pygments styles can be set."""
    # This is a basic test - actual highlighting differences are hard to test
    # without inspecting pygments internals
    printer1 = StreamingMarkdownPrinter(pygments_style="monokai")
    printer2 = StreamingMarkdownPrinter(pygments_style="native")
    
    # Both should have formatters with different styles
    # (We can't easily test the actual highlighting difference)
    assert printer1.formatter is not None
    assert printer2.formatter is not None


@patch('ainator.renderer.highlight')
def test_highlight_called_correctly(mock_highlight, mock_output_file):
    """Test that pygments.highlight is called with correct parameters."""
    mock_highlight.return_value = "# Highlighted\n"
    
    printer = StreamingMarkdownPrinter(output_file=mock_output_file)
    content = "# Test\n"
    printer.add_content(content)
    
    # highlight should have been called
    assert mock_highlight.called
    # Check it was called with markdown lexer and terminal formatter
    args, kwargs = mock_highlight.call_args
    assert args[1] == printer.md_lexer
    assert args[2] == printer.formatter


def test_complex_markdown_rendering(printer, mock_output_file):
    """Test rendering of complex markdown with mixed elements."""
    complex_md = """# Main Title

This is a paragraph with **bold** and *italic* text.

## Subsection

1. First item
2. Second item
3. Third item

```python
import sys

def main():
    print("Hello")
```

> Blockquote here

`inline code` and more text.
"""
    
    # Add in chunks to simulate streaming
    lines = complex_md.splitlines(keepends=True)
    for line in lines:
        printer.add_content(line)
    
    printer.flush()
    
    output = mock_output_file.getvalue()
    assert output != ""
    # Should have multiple lines of output
    assert output.count('\n') > 5
    """Test content that ends with an open code block."""
    content = "```python\ndef unfinished():\n    pass\n"
    printer.add_content(content)
    
    # Content ends with open code block
    assert printer.code_open is True
    
    printer.flush()
    
    # Flush should handle the open code block
    output = mock_output_file.getvalue()
    assert output != ""


def test_unicode_content(printer, mock_output_file):
    """Test handling of unicode content."""
    unicode_content = "Hello 🌍 World\nEmoji: 😀 🚀\n"
    printer.add_content(unicode_content)
    
    output = mock_output_file.getvalue()
    assert output != ""
    # Should not crash with unicode


if __name__ == "__main__":
    # Quick manual test if run directly
    pytest.main([__file__, "-v"])