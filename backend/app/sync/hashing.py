"""
hashing.py — Deterministic ID and content-hash utilities.
"""
import base64
import hashlib


def file_doc_id(file_path: str) -> str:
    """
    Stable doc-level ID derived from the file path.
    Uses base64url(sha256(path)) so the same path always maps to the same ID.
    """
    digest = hashlib.sha256(file_path.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def file_content_hash(file_path: str) -> str:
    """SHA-256 hex digest of file contents — used to detect modifications."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def make_chunk_id(doc_id: str, chunk_index: int) -> str:
    """Chunk-level primary key: <doc_id>:<chunk_index>."""
    return f"{doc_id}:{chunk_index}"
