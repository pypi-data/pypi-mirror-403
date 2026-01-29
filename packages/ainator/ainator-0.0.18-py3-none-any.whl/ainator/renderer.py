import sys

from pygments import highlight
from pygments.lexers import MarkdownLexer
from pygments.formatters import Terminal256Formatter


class StreamingMarkdownPrinter:
    """
    Accumulates content (usually from an LLM stream),
    prints rendered Markdown line-by-line as soon as complete lines arrive.

    Uses real Pygments highlighting with Terminal256Formatter for nice CLI colors.
    Handles open code blocks intelligently during streaming.
    Supports separate reasoning output stream.
    """

    def __init__(
        self,
        output_file=sys.stderr,
        reasoning_file=sys.stderr,
        print_reasoning: bool = True,
        pygments_style: str = "monokai",           # popular dark theme
    ):
        self.output_file = output_file
        self.reasoning_file = reasoning_file
        self.print_reasoning = print_reasoning

        # Pygments setup
        self.formatter = Terminal256Formatter(
            style=pygments_style,
            linenos=False,
        )
        self.md_lexer = MarkdownLexer()

        # State
        self.full_content = ""
        self.full_reasoning = ""
        self.printed_lines = 0
        self.reasoning_header_shown = False
        self.code_open = False

    def add_content(self, text: str) -> None:
        """Add a chunk of main content (usually delta.content)"""
        if not text:
            return

        self.full_content += text

        # Early exit if no complete line yet
        if not text.endswith("\n") and "\n" not in text:
            return

        self._render_new_lines()

    def add_reasoning(self, text: str) -> None:
        """Add reasoning delta — printed immediately in dim gray"""
        if not self.print_reasoning or not text:
            return

        if not self.reasoning_header_shown:
            print("\n\033[1;33mREASONING\033[0m", file=self.reasoning_file, flush=True)
            self.reasoning_header_shown = True

        print(f"\033[90m{text}\033[0m", end="", flush=True, file=self.reasoning_file)

        self.full_reasoning += text

    def flush(self) -> None:
        """Print any remaining content when stream is done"""
        self._render_new_lines(final=True)

        if self.reasoning_header_shown:
            print(file=self.reasoning_file, flush=True)
            self.reasoning_header_shown = False

    def get_content(self) -> str:
        return self.full_content

    def get_reasoning(self) -> str:
        return self.full_reasoning

    def _render_new_lines(self, final: bool = False) -> None:
        lines = self.full_content.splitlines()
        new_lines = lines[self.printed_lines:]

        # Update code block state based on newly arrived complete lines
        for line in new_lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                # Ignore ```diff or other variants if you want, but usually just toggle
                self.code_open = not self.code_open

        # Decide what to highlight
        content_to_highlight = self.full_content
        added_temp_fence = False

        # Always temporarily close open code block for correct highlighting
        if self.code_open:
            if not content_to_highlight.endswith("\n"):
                content_to_highlight += "\n"
            content_to_highlight += "```"
            added_temp_fence = True

        # Highlight the (possibly temporarily closed) content
        highlighted = highlight(content_to_highlight, self.md_lexer, self.formatter)
        highlighted_lines = highlighted.splitlines()

        # Remove the artificial closing fence line if we added it
        if added_temp_fence and highlighted_lines:
            # Usually the last line contains the temporary ```
            if "```" in highlighted_lines[-1]:
                highlighted_lines = highlighted_lines[:-1]

        # Print only newly highlighted lines
        to_print = highlighted_lines[self.printed_lines:]
        if to_print:
            print("\n".join(to_print), flush=True, file=self.output_file)

        self.printed_lines = len(highlighted_lines)

        # Clean separation after reasoning once real content appears
        if self.reasoning_header_shown and to_print:
            print(file=self.reasoning_file, flush=True)
            self.reasoning_header_shown = False


# ────────────────────────────────────────────────
#   Example usage
# ────────────────────────────────────────────────

if __name__ == "__main__":
    printer = StreamingMarkdownPrinter(
        output_file=sys.stdout,          # or sys.stderr
        print_reasoning=True,
        pygments_style="monokai",        # try "dracula", "gruvbox-dark", "native", etc.
    )

    # Simulate streaming chunks
    simulation = [
        ("reasoning", "I need to solve this step by step...\n"),
        ("reasoning", "First, consider the constraints.\n\n"),
        ("content", "Here's a markdown example:\n"),
        ("content", "## Title\n\n"),
        ("content", "Some **bold** and *italic* text.\n\n"),
        ("content", "```python\n"),
        ("content", "def greet(name):\n"),
        ("content", "    return f'Hello, {name}!'\n"),
        ("content", "# still open...\n"),
        ("content", "print(greet('world'))\n"),
        ("content", "```\n"),
        ("content", "Final answer: **done**\n"),
    ]

    for kind, chunk in simulation:
        if kind == "reasoning":
            printer.add_reasoning(chunk)
        else:
            printer.add_content(chunk)

    printer.flush()

    print("\nCollected content:")
    print(repr(printer.get_content()))
