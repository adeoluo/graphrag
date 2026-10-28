"""Evaluating graph retrieval against a flat text-retrieval baseline.

GraphRAG's claim is that traversing explicit relations answers questions the connecting
facts of which are spread across passages. :func:`evaluate` measures answer accuracy for
the graph retriever and for a flat baseline that returns the top passage's leading entity,
split by single- vs multi-hop questions.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from graphrag.core.graph import KnowledgeGraph
from graphrag.extraction import extract_entities
from graphrag.retrieval import GraphRetriever

_TOKEN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True, slots=True)
class EvalReport:
    """Aggregated answer accuracy for a method."""

    method: str
    overall: float
    multi_hop: float
    single_hop: float
    num_questions: int

    def format(self) -> str:
        return (
            f"{self.method:<12} overall={self.overall:.2f}  "
            f"multi-hop={self.multi_hop:.2f}  single-hop={self.single_hop:.2f}  "
            f"(N={self.num_questions})"
        )


def _flat_answer(documents: Sequence[tuple[str, str]], question: str) -> str:
    """A flat baseline: return an entity from the best keyword-overlap passage."""
    query_terms = set(_TOKEN.findall(question.lower()))
    best_text = ""
    best_hits = -1
    for _doc_id, text in documents:
        hits = len(query_terms & set(_TOKEN.findall(text.lower())))
        if hits > best_hits:
            best_hits = hits
            best_text = text
    entities = extract_entities(best_text)
    # Return the entity not already named in the question, if any.
    for entity in entities:
        if not all(tok in query_terms for tok in _TOKEN.findall(entity.lower())):
            return entity
    return entities[0] if entities else ""


def evaluate(
    graph: KnowledgeGraph,
    documents: Sequence[tuple[str, str]],
    questions: Sequence[tuple[str, str, bool]],
    *,
    graph_retrieval: bool,
    max_hops: int = 3,
) -> EvalReport:
    """Evaluate answer accuracy for graph or flat retrieval."""
    retriever = GraphRetriever(graph, max_hops=max_hops) if graph_retrieval else None

    overall = 0
    multi_total = multi_hits = 0
    single_total = single_hits = 0
    for question, expected, multi_hop in questions:
        if retriever is not None:
            answer = retriever.retrieve(question).answer
        else:
            answer = _flat_answer(documents, question)
        hit = answer == expected
        overall += hit
        if multi_hop:
            multi_total += 1
            multi_hits += hit
        else:
            single_total += 1
            single_hits += hit

    n = len(questions)
    return EvalReport(
        method="graph" if graph_retrieval else "flat",
        overall=overall / n if n else 0.0,
        multi_hop=multi_hits / multi_total if multi_total else 0.0,
        single_hop=single_hits / single_total if single_total else 0.0,
        num_questions=n,
    )
