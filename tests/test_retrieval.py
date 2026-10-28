"""Tests for entity linking and graph retrieval."""

from __future__ import annotations

import pytest

from graphrag import GraphRetriever, build_graph
from graphrag.core import KnowledgeGraph, Relation
from graphrag.retrieval import link_entities


def _graph() -> KnowledgeGraph:
    docs = [
        ("d0", "The Eiffel Tower is located in Paris."),
        ("d1", "Paris is the capital of France."),
        ("d2", "The Colosseum is located in Rome."),
        ("d3", "Rome is the capital of Italy."),
        ("d4", "Mount Fuji is located in Japan."),
    ]
    return build_graph(docs)


# --------------------------------------------------------------------------- #
# Entity linking
# --------------------------------------------------------------------------- #
def test_link_exact() -> None:
    linked = link_entities("Where is Paris", _graph())
    assert "Paris" in linked


def test_link_no_entity() -> None:
    assert link_entities("where is it located", _graph()) == []


# --------------------------------------------------------------------------- #
# Graph retrieval
# --------------------------------------------------------------------------- #
def test_retrieve_single_hop_capital() -> None:
    retriever = GraphRetriever(_graph())
    answer = retriever.retrieve("What is the capital of France")
    # Paris is the capital of France; following the capital_of edge from France yields Paris.
    assert answer.answer == "Paris"
    assert answer.linked_entities


def test_retrieve_location() -> None:
    retriever = GraphRetriever(_graph())
    answer = retriever.retrieve("Where is the Eiffel Tower located")
    assert answer.answer == "Paris"
    assert answer.confidence > 0.0


def test_retrieve_multi_hop_through_graph() -> None:
    # "Where is the Colosseum" -> located_in Rome (Rome is capital_of Italy exists too).
    retriever = GraphRetriever(_graph(), max_hops=3)
    answer = retriever.retrieve("Where is the Colosseum located")
    assert answer.answer == "Rome"


def test_retrieve_unknown_entity() -> None:
    retriever = GraphRetriever(_graph())
    answer = retriever.retrieve("Where is Atlantis")
    assert answer.confidence == 0.0


def test_retrieve_builds_subgraph() -> None:
    retriever = GraphRetriever(_graph())
    answer = retriever.retrieve("Where is the Eiffel Tower located")
    assert answer.subgraph_size >= 1


def test_retriever_validates() -> None:
    with pytest.raises(ValueError, match="max_hops"):
        GraphRetriever(_graph(), max_hops=0)


def test_relation_as_triple() -> None:
    assert Relation("A", "r", "B").as_triple() == ("A", "r", "B")
