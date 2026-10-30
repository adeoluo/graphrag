"""Tests for the knowledge graph and extraction."""

from __future__ import annotations

import pytest

from graphrag.core import KnowledgeGraph, Relation
from graphrag.extraction import (
    build_graph,
    extract_entities,
    extract_relations,
)


# --------------------------------------------------------------------------- #
# Knowledge graph
# --------------------------------------------------------------------------- #
def test_add_relation_creates_entities() -> None:
    graph = KnowledgeGraph()
    graph.add_relation(Relation("Paris", "capital_of", "France"))
    assert graph.num_entities == 2
    assert graph.num_relations == 1
    assert "Paris" in graph.entities


def test_add_empty_entity_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        KnowledgeGraph().add_entity("")


def test_neighbors_both_directions() -> None:
    graph = KnowledgeGraph()
    graph.add_relation(Relation("Paris", "capital_of", "France"))
    assert len(graph.neighbors("Paris")) == 1
    assert len(graph.neighbors("France")) == 1


def test_neighbors_counts_self_loop_once() -> None:
    # Regression: a self-loop is stored in both the outgoing and incoming lists,
    # so it was returned twice.
    graph = KnowledgeGraph()
    graph.add_relation(Relation("A", "relates_to", "A"))
    assert len(graph.neighbors("A")) == 1
    graph.add_relation(Relation("A", "points_to", "B"))
    assert len(graph.neighbors("A")) == 2
    assert len(graph.neighbors("B")) == 1


def test_bfs_reaches_multi_hop() -> None:
    graph = KnowledgeGraph()
    graph.add_relation(Relation("Eiffel Tower", "located_in", "Paris"))
    graph.add_relation(Relation("Paris", "capital_of", "France"))
    reachable = graph.bfs(["Eiffel Tower"], max_hops=2)
    assert {"Eiffel Tower", "Paris", "France"} <= reachable


def test_bfs_respects_hop_limit() -> None:
    graph = KnowledgeGraph()
    graph.add_relation(Relation("A", "r", "B"))
    graph.add_relation(Relation("B", "r", "C"))
    one_hop = graph.bfs(["A"], max_hops=1)
    assert "B" in one_hop
    assert "C" not in one_hop


def test_bfs_validates() -> None:
    with pytest.raises(ValueError, match="max_hops"):
        KnowledgeGraph().bfs(["A"], max_hops=-1)


def test_subgraph_relations() -> None:
    graph = KnowledgeGraph()
    graph.add_relation(Relation("A", "r", "B"))
    graph.add_relation(Relation("B", "r", "C"))
    sub = graph.subgraph_relations({"A", "B"})
    assert len(sub) == 1
    assert sub[0].as_triple() == ("A", "r", "B")


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #
def test_extract_entities() -> None:
    entities = extract_entities("The Eiffel Tower is located in Paris, France.")
    assert "Eiffel Tower" in entities
    assert "Paris" in entities


def test_extract_relation_capital() -> None:
    relations = extract_relations("Paris is the capital of France.", document_id="d0")
    assert relations
    assert relations[0].relation == "capital_of"
    assert relations[0].document_id == "d0"


def test_extract_relation_located_in() -> None:
    relations = extract_relations("The Colosseum is located in Rome.")
    assert relations[0].relation == "located_in"


def test_extract_no_relation_without_pattern() -> None:
    assert extract_relations("Paris Rome Tokyo exist.") == []


def test_build_graph_from_documents() -> None:
    docs = [
        ("d0", "The Eiffel Tower is located in Paris."),
        ("d1", "Paris is the capital of France."),
    ]
    graph = build_graph(docs)
    assert graph.num_relations == 2
    reachable = graph.bfs(["Eiffel Tower"], max_hops=2)
    assert "France" in reachable
