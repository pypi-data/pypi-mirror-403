"""
Entity extraction and content chunking for RLM-Graph.

Provides utilities for processing text content:
- EntityExtractor: Identifies named entities and code elements
- ContentChunker: Splits content into hierarchical chunks
"""

from __future__ import annotations

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extracts entities from text content.

    Identifies:
    - Capitalized terms (potential proper nouns)
    - Code elements (function names, classes, variables)
    - Markdown links and references
    - Frequent keywords
    """

    # Common words to ignore
    STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "this",
        "that", "these", "those", "then", "than", "when", "where", "which",
        "who", "what", "how", "why", "all", "any", "both", "each", "few",
        "more", "most", "other", "some", "such", "no", "not", "only", "same",
        "so", "than", "too", "very", "just", "also", "now", "here", "there",
        "user", "assistant", "tool", "result", "error", "success",
    }

    # Code-related patterns
    CODE_PATTERNS = [
        r"\b([A-Z][a-zA-Z0-9]*(?:Error|Exception|Handler|Manager|Service|Controller|Factory|Builder))\b",  # Classes
        r"\b(def\s+)?([a-z_][a-z0-9_]*)\s*\(",  # Functions
        r"\b([A-Z_][A-Z0-9_]{2,})\b",  # Constants
        r"`([^`]+)`",  # Inline code
        r"(?:class|interface|type|struct)\s+([A-Z][a-zA-Z0-9]*)",  # Type definitions
    ]

    def __init__(self) -> None:
        self._compiled_patterns = [re.compile(p) for p in self.CODE_PATTERNS]

    def extract(self, text: str) -> list[tuple[str, str]]:
        """
        Extract entities from text.

        Returns:
            List of (entity_name, entity_type) tuples
        """
        entities: dict[str, str] = {}

        # Extract capitalized terms (potential proper nouns)
        capitalized = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
        for term in capitalized:
            if term.lower() not in self.STOPWORDS and len(term) > 2:
                entities[term] = "proper_noun"

        # Extract code elements
        for pattern in self._compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Take the last non-empty group
                    term = next((m for m in reversed(match) if m), None)
                else:
                    term = match

                if term and term.lower() not in self.STOPWORDS and len(term) > 1:
                    entities[term] = "code_element"

        # Extract markdown links
        links = re.findall(r"\[([^\]]+)\]\([^)]+\)", text)
        for link_text in links:
            if link_text.lower() not in self.STOPWORDS:
                entities[link_text] = "reference"

        # Extract file paths
        paths = re.findall(r"(?:^|\s)([./]?(?:[a-zA-Z0-9_-]+/)+[a-zA-Z0-9_.-]+)", text)
        for path in paths:
            entities[path] = "file_path"

        return list(entities.items())

    def extract_keywords(self, text: str, top_n: int = 10) -> list[str]:
        """Extract top keywords based on frequency."""
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        word_counts: dict[str, int] = {}

        for word in words:
            if word not in self.STOPWORDS:
                word_counts[word] = word_counts.get(word, 0) + 1

        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]


class ContentChunker:
    """
    Splits content into hierarchical chunks.

    Creates sections based on natural breaks and chunks
    suitable for retrieval.
    """

    def __init__(
        self,
        section_min_chars: int = 500,
        chunk_target_chars: int = 300,
        chunk_overlap: int = 50,
    ) -> None:
        self.section_min_chars = section_min_chars
        self.chunk_target_chars = chunk_target_chars
        self.chunk_overlap = chunk_overlap

    def split_into_sections(self, content: str) -> list[tuple[str, str]]:
        """
        Split content into sections.

        Returns:
            List of (section_title, section_content) tuples
        """
        sections: list[tuple[str, str]] = []

        # Try to split by markdown headers
        header_pattern = r"(?:^|\n)(#{1,3})\s+(.+?)(?:\n|$)"
        matches = list(re.finditer(header_pattern, content))

        if matches:
            for i, match in enumerate(matches):
                title = match.group(2).strip()
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                section_content = content[start:end].strip()

                if section_content:
                    sections.append((title, section_content))
        else:
            # Fall back to paragraph-based splitting
            paragraphs = content.split("\n\n")
            current_section = []
            current_length = 0

            for para in paragraphs:
                current_section.append(para)
                current_length += len(para)

                if current_length >= self.section_min_chars:
                    section_text = "\n\n".join(current_section)
                    # Generate title from first line
                    first_line = section_text.split("\n")[0][:50]
                    sections.append((first_line, section_text))
                    current_section = []
                    current_length = 0

            if current_section:
                section_text = "\n\n".join(current_section)
                first_line = section_text.split("\n")[0][:50]
                sections.append((first_line, section_text))

        return sections

    def split_into_chunks(self, content: str) -> list[str]:
        """
        Split content into overlapping chunks.

        Returns:
            List of chunk texts
        """
        if len(content) <= self.chunk_target_chars:
            return [content]

        chunks: list[str] = []
        sentences = re.split(r"(?<=[.!?])\s+", content)
        current_chunk: list[str] = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_length + sentence_len > self.chunk_target_chars and current_chunk:
                chunks.append(" ".join(current_chunk))

                # Keep overlap
                overlap_chunk: list[str] = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) <= self.chunk_overlap:
                        overlap_chunk.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break

                current_chunk = overlap_chunk
                current_length = overlap_len

            current_chunk.append(sentence)
            current_length += sentence_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
