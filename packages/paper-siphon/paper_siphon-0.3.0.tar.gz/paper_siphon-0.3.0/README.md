# Paper Siphon

**Extract clean Markdown from academic PDFs** - like drinking through a straw.

Academic papers come with artifacts: awkward page breaks, mangled tables, or even line numbers.
Paper Siphon filters them out, leaving you with clean, readable Markdown.

```
paper-siphon paper.pdf
```

That's it. Your paper is now `paper.md`.

---

## Features

- **Smart whitespace** - Collapses excessive blank lines, normalizes spacing
- **Table preservation** - Keeps your data tables intact and formatted
- **Formula support** - Optional enrichment for mathematical expressions
- **Line number removal** - Automatically strips the margin numbers (when present)
- **VLM pipeline** - Use vision-language models for complex layouts
- **Apple Silicon acceleration** - MLX support for fast processing on M-series Macs

## Installation

```bash
# With uv (recommended)
uv pip install paper-siphon

# With pip
pip install paper-siphon
```

For Apple Silicon acceleration (optional):

```bash
uv pip install paper-siphon[mlx]
```

## Usage

### Quick start (no install)

```bash
uvx paper-siphon paper.pdf                # Run directly with uvx
```

### Basic

```bash
paper-siphon paper.pdf                    # Creates paper.md
paper-siphon paper.pdf -o notes.md        # Custom output path
```

### From URL (including arXiv)

```bash
paper-siphon https://arxiv.org/pdf/1706.03762.pdf
```

**Tip:** For arXiv papers, just change `/abs/` to `/pdf/` in the URL:
```
https://arxiv.org/abs/1706.03762  →  https://arxiv.org/pdf/1706.03762.pdf
```

(That's "Attention Is All You Need" - the Transformer paper)

### Advanced

```bash
paper-siphon --vlm paper.pdf              # Use VLM for complex layouts
paper-siphon --enrich-formula paper.pdf   # Enable formula enrichment
paper-siphon --no-mlx --vlm paper.pdf     # VLM without MLX acceleration
paper-siphon -v paper.pdf                 # Verbose logging
```

## How It Works

Paper Siphon uses [Docling](https://github.com/DS4SD/docling) for PDF parsing, then applies
post-processing to clean up common academic paper artifacts:

1. **PDF parsing** - Extracts structure, text, and tables
2. **Line number filtering** - Removes standalone 1-4 digit numbers (common in journal formats)
3. **Whitespace normalization** - Collapses multiple blank lines

## Options

| Flag | Description |
|------|-------------|
| `-o, --output` | Output file path (default: input with `.md` extension) |
| `--vlm` | Use VLM pipeline for complex layouts |
| `--mlx/--no-mlx` | Toggle MLX acceleration (Apple Silicon, default: on) |
| `--enrich-formula` | Enable formula enrichment (slow, CPU-bound) |
| `-v, --verbose` | Enable debug logging |

## Development

```bash
# Clone and install
git clone https://github.com/mrshu/paper-siphon.git
cd paper-siphon
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=paper_siphon
```

## License

MIT

---

*Stop wrestling with PDFs. Just siphon the good stuff.*
