"""Tests for the bundled data, evaluation, and CLI."""

from __future__ import annotations

import pytest

from graphrag.cli import main
from graphrag.data import documents, questions
from graphrag.evaluation import evaluate
from graphrag.extraction import build_graph


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def test_has_multi_hop_questions() -> None:
    assert any(multi for _, _, multi in questions())


def test_documents_build_a_connected_graph() -> None:
    graph = build_graph(documents())
    assert graph.num_relations >= 8
    reachable = graph.bfs(["Eiffel Tower"], max_hops=3)
    assert "France" in reachable


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def test_graph_beats_flat_on_multi_hop() -> None:
    docs = documents()
    graph = build_graph(docs)
    labeled = questions()
    flat = evaluate(graph, docs, labeled, graph_retrieval=False)
    graph_report = evaluate(graph, docs, labeled, graph_retrieval=True)
    assert graph_report.multi_hop > flat.multi_hop
    assert graph_report.multi_hop == 1.0
    assert flat.multi_hop == 0.0


def test_evaluation_reports_fields() -> None:
    docs = documents()
    report = evaluate(build_graph(docs), docs, questions(), graph_retrieval=True)
    assert report.num_questions == len(questions())
    assert "graph" in report.format()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def test_cli_graph(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["graph"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "entities" in output
    assert "capital_of" in output


def test_cli_ask_single_hop(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["ask", "Where is the Eiffel Tower located"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Answer: Paris" in output


def test_cli_ask_multi_hop(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["ask", "What country is the Eiffel Tower in"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Answer: France" in output


def test_cli_evaluate(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["evaluate"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "flat" in output
    assert "graph" in output
    assert "Multi-hop gain" in output


def test_cli_requires_command() -> None:
    with pytest.raises(SystemExit):
        main([])
