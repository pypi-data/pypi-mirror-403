"""Paper Siphon - Markdown cleaning utilities."""

import re

# Pattern to match standalone line numbers (1-4 digits, common in academic papers)
LINE_NUMBER_PATTERN = re.compile(r"^\d{1,4}$")


def clean_markdown(text: str) -> str:
    """Clean up markdown output from PDF conversion.

    - Removes standalone line numbers (common in academic paper PDFs)
    - Collapses multiple blank lines into one

    Args:
        text: Raw markdown text from PDF conversion.

    Returns:
        Cleaned markdown with line numbers removed and whitespace normalized.
    """
    lines = text.split("\n")
    cleaned_lines = [
        line for line in lines if not LINE_NUMBER_PATTERN.match(line.strip())
    ]
    text = "\n".join(cleaned_lines)

    # Collapse 3+ newlines into 2 (one blank line)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
