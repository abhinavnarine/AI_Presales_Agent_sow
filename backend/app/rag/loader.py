"""Load the markdown knowledge base and split it into retrievable chunks.

Chunking strategy: RecursiveCharacterTextSplitter with markdown-aware separators.
We split on headings first, then paragraphs, then sentences. Each chunk keeps its
source filename and the nearest preceding section heading in metadata, which makes
retrieved context traceable back to a human-readable source in the UI.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import config


def _nearest_heading(text: str, upto: int) -> str:
    headings = [m for m in re.finditer(r"^#{1,6}\s+(.*)$", text[:upto], re.MULTILINE)]
    return headings[-1].group(1).strip() if headings else ""


def load_and_chunk() -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
        keep_separator=True,
    )

    docs: List[Document] = []
    md_files = sorted(Path(config.KNOWLEDGE_BASE_DIR).glob("*.md"))
    if not md_files:
        raise FileNotFoundError(
            f"No knowledge base files found in {config.KNOWLEDGE_BASE_DIR}"
        )

    for path in md_files:
        raw = path.read_text(encoding="utf-8")
        for chunk in splitter.split_text(raw):
            start = raw.find(chunk[:40]) if len(chunk) >= 40 else raw.find(chunk)
            heading = _nearest_heading(raw, start if start >= 0 else len(raw))
            docs.append(
                Document(
                    page_content=chunk.strip(),
                    metadata={
                        "source": path.name,
                        "section": heading or path.stem,
                    },
                )
            )
    return docs
