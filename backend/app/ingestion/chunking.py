"""
chunking.py — Split page-level text into overlapping chunks.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return [c for c in splitter.split_text(text) if c.strip()]


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Args:
        pages: list of {"text": str, "page": int | None}
    Returns:
        list of {"chunk_text": str, "page": int | None}
    """
    result = []
    for page in pages:
        chunks = chunk_text(page["text"], chunk_size, chunk_overlap)
        for chunk in chunks:
            result.append({"chunk_text": chunk, "page": page.get("page")})
    return result
