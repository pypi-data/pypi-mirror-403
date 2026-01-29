"""Paper Siphon - Extract clean Markdown from academic PDFs."""

import logging
import platform
import sys
import tempfile
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

import click

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    TableStructureOptions,
    VlmPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

from paper_siphon.cleaning import clean_markdown

logger = logging.getLogger(__name__)

MLX_AVAILABLE = platform.system() == "Darwin" and platform.machine() == "arm64"


def is_url(source: str) -> bool:
    """Check if source is a URL."""
    parsed = urlparse(source)
    return parsed.scheme in ("http", "https")


def to_markdown_filename(filename: str) -> Path:
    """Convert a filename to .md output path.

    Handles arXiv-style IDs like '1706.03762' where the dot is not a file extension.
    """
    path = Path(filename)
    suffix = path.suffix

    # If suffix looks like a number (e.g., .03762), it's not a real extension
    if suffix and suffix[1:].isdigit():
        return Path(filename + ".md")

    return path.with_suffix(".md")


@contextmanager
def resolve_source(source: str):
    """Resolve source to a local file path, downloading if URL.

    Yields (path, filename) where filename is used for default output naming.
    """
    if is_url(source):
        parsed = urlparse(source)
        filename = Path(parsed.path).name or "paper.pdf"
        click.echo(f"Downloading {source}")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            urllib.request.urlretrieve(source, tmp_path)
            yield tmp_path, filename
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        path = Path(source)
        if not path.exists():
            raise click.ClickException(f"File not found: {source}")
        yield path, path.name


def create_standard_converter(enrich_formula: bool) -> DocumentConverter:
    """Create a converter using the standard PDF pipeline."""
    pipeline_options = PdfPipelineOptions(
        do_table_structure=True,
        table_structure_options=TableStructureOptions(mode=TableFormerMode.ACCURATE),
        do_formula_enrichment=enrich_formula,
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }
    )


def create_vlm_converter(use_mlx: bool, enrich_formula: bool) -> DocumentConverter:
    """Create a converter using the VLM pipeline.

    Args:
        use_mlx: Use MLX acceleration (Apple Silicon only).
        enrich_formula: Enable formula enrichment.

    Raises:
        ImportError: If MLX is requested but mlx-vlm is not installed.
        RuntimeError: If MLX is requested on non-Apple Silicon hardware.
    """
    from docling.datamodel import vlm_model_specs

    if use_mlx:
        if not MLX_AVAILABLE:
            raise RuntimeError("MLX requires Apple Silicon (arm64 macOS)")
        try:
            vlm_options = vlm_model_specs.GRANITEDOCLING_MLX
        except AttributeError:
            raise ImportError(
                "mlx-vlm not installed. Install with: uv pip install mlx-vlm"
            )
    else:
        vlm_options = vlm_model_specs.GRANITEDOCLING_TRANSFORMERS

    pipeline_options = VlmPipelineOptions(
        vlm_options=vlm_options,
        do_formula_enrichment=enrich_formula,
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline, pipeline_options=pipeline_options
            ),
        }
    )


@click.command()
@click.version_option(package_name="paper-siphon")
@click.argument("source", required=False)
@click.pass_context
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output file path. Defaults to input filename with .md extension.",
)
@click.option(
    "--vlm",
    is_flag=True,
    default=False,
    help="Use VLM pipeline (slower but better for complex layouts).",
)
@click.option(
    "--mlx/--no-mlx",
    default=True,
    help="Use MLX acceleration on Apple Silicon. Only applies with --vlm.",
)
@click.option(
    "--enrich-formula",
    is_flag=True,
    default=False,
    help="Enable formula enrichment (slow, runs on CPU).",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging.",
)
def main(
    ctx: click.Context,
    source: str | None,
    output: Path | None,
    vlm: bool,
    mlx: bool,
    enrich_formula: bool,
    verbose: bool,
) -> None:
    """Siphon clean Markdown from academic PDFs.

    SOURCE can be a local file path or a URL to a PDF.

    Extracts content from academic papers, automatically removing line numbers
    and cleaning up formatting artifacts.

    \b
    Examples:
        paper-siphon paper.pdf
        paper-siphon paper.pdf -o notes.md
        paper-siphon https://arxiv.org/pdf/1706.03762.pdf
        paper-siphon --vlm paper.pdf

    \b
    Tip: For arXiv papers, just change /abs/ to /pdf/ in the URL:
        https://arxiv.org/abs/1706.03762  ->  https://arxiv.org/pdf/1706.03762.pdf
    """
    if source is None:
        click.echo(ctx.get_help())
        return

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    with resolve_source(source) as (file_path, filename):
        if output is None:
            output = to_markdown_filename(filename)

        click.echo(f"Converting {source} -> {output}")

        try:
            if vlm:
                mode = "VLM + MLX" if mlx else "VLM + CPU"
                click.echo(f"Using {mode} pipeline")
                converter = create_vlm_converter(use_mlx=mlx, enrich_formula=enrich_formula)
            else:
                click.echo("Using standard pipeline (accurate table mode)")
                converter = create_standard_converter(enrich_formula=enrich_formula)

            result = converter.convert(file_path)
        except (ImportError, RuntimeError) as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            logger.exception("Conversion failed")
            click.echo(f"Error: Conversion failed - {e}", err=True)
            sys.exit(1)

        markdown = result.document.export_to_markdown()
        cleaned = clean_markdown(markdown)

        output.write_text(cleaned)
        click.echo(f"Done! Output saved to {output}")


if __name__ == "__main__":
    main()
