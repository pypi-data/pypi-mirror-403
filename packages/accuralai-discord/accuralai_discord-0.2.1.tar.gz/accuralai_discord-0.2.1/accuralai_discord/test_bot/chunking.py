"""Text chunking utilities for RAG."""

from __future__ import annotations

import re
from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    min_chunk_size: int = 100,
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Target size of each chunk (in characters)
        chunk_overlap: Number of characters to overlap between chunks
        min_chunk_size: Minimum size for a chunk (smaller chunks are merged)

    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If we're not at the end, try to break at sentence or line boundary
        if end < len(text):
            # Try to find sentence boundary (., !, ? followed by space)
            sentence_end = max(
                text.rfind(". ", start, end),
                text.rfind("! ", start, end),
                text.rfind("? ", start, end),
                text.rfind(".\n", start, end),
                text.rfind("!\n", start, end),
                text.rfind("?\n", start, end),
            )

            # If sentence boundary found and not too close to start, use it
            if sentence_end > start + min_chunk_size:
                end = sentence_end + 1
            else:
                # Fallback: try line break
                line_end = text.rfind("\n", start, end)
                if line_end > start + min_chunk_size:
                    end = line_end + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap
        start = end - chunk_overlap if end < len(text) else end

    # Merge very small chunks with previous ones
    merged_chunks: List[str] = []
    for chunk in chunks:
        if merged_chunks and len(chunk) < min_chunk_size and len(merged_chunks[-1]) < chunk_size * 1.5:
            merged_chunks[-1] += "\n\n" + chunk
        else:
            merged_chunks.append(chunk)

    return merged_chunks


def chunk_code(
    code: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[str]:
    """
    Split code into chunks, preserving structure when possible.

    Args:
        code: Code to chunk
        chunk_size: Target size of each chunk (in characters)
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List of code chunks
    """
    if not code or len(code) <= chunk_size:
        return [code] if code else []

    chunks: List[str] = []
    lines = code.split("\n")
    current_chunk: List[str] = []
    current_size = 0

    for line in lines:
        line_size = len(line) + 1  # +1 for newline

        if current_size + line_size > chunk_size and current_chunk:
            # Save current chunk
            chunks.append("\n".join(current_chunk))

            # Start new chunk with overlap
            overlap_lines = []
            overlap_size = 0
            for prev_line in reversed(current_chunk):
                if overlap_size + len(prev_line) + 1 <= chunk_overlap:
                    overlap_lines.insert(0, prev_line)
                    overlap_size += len(prev_line) + 1
                else:
                    break

            current_chunk = overlap_lines + [line]
            current_size = sum(len(l) + 1 for l in current_chunk)
        else:
            current_chunk.append(line)
            current_size += line_size

    # Add remaining chunk
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def chunk_markdown(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Split markdown text into chunks, preserving sections when possible.

    Args:
        text: Markdown text to chunk
        chunk_size: Target size of each chunk (in characters)
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List of markdown chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    # Split by headers (##, ###, etc.) but preserve headers in chunks
    sections: List[str] = []
    current_section: List[str] = []

    lines = text.split("\n")
    for line in lines:
        # Check if line is a header
        is_header = re.match(r"^#{1,6}\s+", line)

        if is_header and current_section:
            # Save current section
            sections.append("\n".join(current_section))
            current_section = [line]
        else:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    # If sections are still too large, chunk them further
    chunks: List[str] = []
    for section in sections:
        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            # Chunk large sections using regular text chunking
            section_chunks = chunk_text(section, chunk_size, chunk_overlap)
            chunks.extend(section_chunks)

    return chunks


def smart_chunk(
    text: str,
    file_type: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Intelligently chunk text based on file type.

    Args:
        text: Text to chunk
        file_type: Type of file (python, markdown, config, etc.)
        chunk_size: Target size of each chunk
        chunk_overlap: Overlap between chunks

    Returns:
        List of chunks
    """
    if file_type == "python":
        return chunk_code(text, chunk_size, chunk_overlap)
    elif file_type == "markdown":
        return chunk_markdown(text, chunk_size, chunk_overlap)
    else:
        return chunk_text(text, chunk_size, chunk_overlap)

