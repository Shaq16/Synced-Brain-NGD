"""
parsers.py — Parse .md and .pdf files into page-level text dicts.
"""
from pathlib import Path


def parse_markdown(file_path: str) -> list[dict]:
    """Read a markdown file and return a single-page dict."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return []
    return [{"text": text, "page": None}]


def parse_pdf(file_path: str) -> list[dict]:
    """Extract per-page text from a PDF using pdfplumber."""
    import pdfplumber

    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append({"text": text, "page": i + 1})
    return pages


def parse_file(file_path: str) -> list[dict]:
    """
    Dispatch to the correct parser based on file extension.

    Returns:
        list of {"text": str, "page": int | None}
    Raises:
        ValueError for unsupported extensions.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".md":
        return parse_markdown(file_path)
    elif ext == ".pdf":
        return parse_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext!r}")
