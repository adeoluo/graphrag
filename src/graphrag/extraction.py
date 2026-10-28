"""Extracting entities and relations from text to build the knowledge graph.

Real GraphRAG uses a language model to extract triples; to stay from-scratch and
deterministic, this module extracts them with transparent rules:

- **Entities** are capitalized noun phrases (sequences of capitalized words), the common
  surface form of named entities.
- **Relations** are detected from a small set of verb/preposition patterns ("is the
  capital of", "is located in", "is a") between two entities in the same sentence.

The point of the project is the graph construction and traversal, so a model-backed
extractor would drop in behind :func:`extract_relations` without changing the graph layer.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from graphrag.core.graph import KnowledgeGraph, Relation

_SENTENCE = re.compile(r"[^.!?]+[.!?]?")
_ENTITY = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+(?:of\s+)?[A-Z][a-zA-Z]+)*)\b")
_LEADING_ARTICLE = re.compile(r"^(?:The|A|An)\s+(?=[A-Z])")

# Ordered relation patterns; the first to match a sentence wins for a given entity pair.
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bis the capital of\b", re.IGNORECASE), "capital_of"),
    (re.compile(r"\bis located in\b|\blocated in\b|\bis in\b", re.IGNORECASE), "located_in"),
    (re.compile(r"\bis a country in\b|\bis a city in\b", re.IGNORECASE), "part_of"),
    (re.compile(r"\bis a\b|\bis an\b|\bwas a\b", re.IGNORECASE), "is_a"),
    (re.compile(r"\bborders\b|\bis adjacent to\b", re.IGNORECASE), "borders"),
    (re.compile(r"\bflows through\b|\bruns through\b", re.IGNORECASE), "flows_through"),
)


def extract_entities(text: str) -> list[str]:
    """Return capitalized noun-phrase entities in ``text``, in order of appearance.

    A leading article ("The", "A", "An") is stripped so sentence-initial phrases such as
    "The Eiffel Tower" normalize to "Eiffel Tower".
    """
    seen: list[str] = []
    for match in _ENTITY.findall(text):
        entity = _LEADING_ARTICLE.sub("", match.strip()).strip()
        if entity and entity not in seen:
            seen.append(entity)
    return seen


def extract_relations(text: str, *, document_id: str = "") -> list[Relation]:
    """Extract ``(source, relation, target)`` relations from ``text``.

    For each sentence, the first two distinct entities and the first matching relation
    pattern yield a relation. This is deliberately simple and inspectable.
    """
    relations: list[Relation] = []
    for sentence in _SENTENCE.findall(text):
        entities = extract_entities(sentence)
        if len(entities) < 2:
            continue
        label = _match_relation(sentence)
        if label is None:
            continue
        relations.append(
            Relation(
                source=entities[0],
                relation=label,
                target=entities[1],
                document_id=document_id,
            )
        )
    return relations


def _match_relation(sentence: str) -> str | None:
    for pattern, label in _PATTERNS:
        if pattern.search(sentence):
            return label
    return None


def build_graph(documents: Sequence[tuple[str, str]]) -> KnowledgeGraph:
    """Build a knowledge graph from ``(document_id, text)`` pairs."""
    graph = KnowledgeGraph()
    for document_id, text in documents:
        for relation in extract_relations(text, document_id=document_id):
            graph.add_relation(relation)
    return graph
