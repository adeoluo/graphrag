"""Tests for the dependency-free HTTP graph service (pure handler layer)."""

from __future__ import annotations

from graphrag.service import GraphService, handle


def _service() -> GraphService:
    return GraphService.from_documents()


def test_health() -> None:
    status, payload = handle("GET", "/health", {}, _service())
    assert status == 200
    assert payload["status"] == "ok"
    assert payload["entities"] > 0
    assert payload["relations"] > 0


def test_ask_multi_hop() -> None:
    status, payload = handle(
        "POST", "/ask", {"query": "What country is the Eiffel Tower in"}, _service()
    )
    assert status == 200
    assert payload["answer"]
    assert isinstance(payload["path"], list)
    assert payload["linked_entities"]


def test_ask_rejects_missing_query() -> None:
    status, payload = handle("POST", "/ask", {}, _service())
    assert status == 400
    assert "query" in payload["error"]


def test_ask_rejects_overlong_query() -> None:
    status, _ = handle("POST", "/ask", {"query": "a" * 5000}, _service())
    assert status == 400


def test_unknown_route() -> None:
    status, payload = handle("GET", "/nope", {}, _service())
    assert status == 404
    assert "error" in payload


def test_ready_endpoint() -> None:
    status, payload = handle("GET", "/ready", {}, _service())
    assert status == 200
    assert payload["status"] == "ready"


def test_metrics_record_requests() -> None:
    service = _service()
    handle("POST", "/ask", {"query": "What country is the Eiffel Tower in"}, service)
    handle("POST", "/ask", {}, service)  # a 400
    text = service.metrics.render_prometheus()
    assert "service_requests_total" in text
    assert 'route="POST /ask"' in text
    assert service.metrics.total_requests == 2
    assert service.metrics.total_errors == 1
