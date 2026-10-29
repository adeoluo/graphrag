"""A dependency-free HTTP service exposing graph retrieval.

The service separates a pure handler from the socket binding so it is fully
testable without a network. The graph is built once at startup from the bundled
corpus and then serves stateless requests.

Endpoints
---------
``GET  /health``   liveness, entity count, and relation count.
``POST /ask``      body ``{"query": str}``; returns the answer, the relation
                   path, the linked entities, and a confidence.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from graphrag.core import KnowledgeGraph
from graphrag.data import documents as bundled_documents
from graphrag.extraction import build_graph
from graphrag.retrieval import GraphRetriever

JsonObject = dict[str, Any]
_MAX_QUERY_CHARS = 2000


@dataclass(frozen=True)
class GraphService:
    """Holds the knowledge graph and answers retrieval requests."""

    graph: KnowledgeGraph

    @classmethod
    def from_documents(cls, documents: list[tuple[str, str]] | None = None) -> GraphService:
        pairs = documents if documents is not None else bundled_documents()
        return cls(graph=build_graph(pairs))

    def ask(self, query: str) -> JsonObject:
        answer = GraphRetriever(self.graph).retrieve(query)
        return {
            "query": query,
            "answer": answer.answer,
            "path": [relation.as_triple() for relation in answer.path],
            "linked_entities": list(answer.linked_entities),
            "subgraph_size": answer.subgraph_size,
            "confidence": round(answer.confidence, 4),
        }


def _validate_ask(body: Mapping[str, Any]) -> str:
    query = body.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("'query' must be a non-empty string")
    if len(query) > _MAX_QUERY_CHARS:
        raise ValueError(f"'query' exceeds {_MAX_QUERY_CHARS} characters")
    return query


def handle(
    method: str, path: str, body: Mapping[str, Any], service: GraphService
) -> tuple[int, JsonObject]:
    """Pure request handler: route a request to a status code and payload."""

    if method == "GET" and path == "/health":
        return 200, {
            "status": "ok",
            "entities": service.graph.num_entities,
            "relations": service.graph.num_relations,
        }
    if method == "POST" and path == "/ask":
        try:
            query = _validate_ask(body)
        except ValueError as error:
            return 400, {"error": str(error)}
        return 200, service.ask(query)
    return 404, {"error": f"no route for {method} {path}"}


class _Handler(BaseHTTPRequestHandler):  # pragma: no cover - exercised over sockets
    service: GraphService

    def _respond(self, status: int, payload: JsonObject) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        status, payload = handle("GET", self.path, {}, self.service)
        self._respond(status, payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._respond(400, {"error": "request body is not valid JSON"})
            return
        status, payload = handle("POST", self.path, body, self.service)
        self._respond(status, payload)

    def log_message(self, *_: Any) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Start the HTTP service (blocking)."""

    handler = type("_BoundHandler", (_Handler,), {"service": GraphService.from_documents()})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"graphrag service listening on http://{host}:{port}")
    server.serve_forever()
