"""GraphRAG - knowledge-graph construction and traversal-based retrieval.

Public API: the knowledge graph and extraction. Retrieval and answer composition live in
their own modules.
"""

from __future__ import annotations

from graphrag.core import KnowledgeGraph, Relation
from graphrag.extraction import build_graph, extract_entities, extract_relations
from graphrag.retrieval import GraphAnswer, GraphRetriever, link_entities

__version__ = "0.1.0"

__all__ = [
    "GraphAnswer",
    "GraphRetriever",
    "KnowledgeGraph",
    "Relation",
    "__version__",
    "build_graph",
    "extract_entities",
    "extract_relations",
    "link_entities",
]
