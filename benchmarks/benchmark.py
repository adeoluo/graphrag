"""A micro-benchmark for knowledge-graph construction and traversal.

Builds a graph from a synthetic corpus of single-relation sentences and
measures graph-build time, graph size, and query throughput for traversal
retrieval. Deterministic and offline; run with:

    uv run python benchmarks/benchmark.py
"""

from __future__ import annotations

import time

from graphrag import GraphRetriever, build_graph


def _name(prefix: str, index: int) -> str:
    letters = ""
    value = index + 1
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        letters = chr(ord("a") + remainder) + letters
    return prefix + letters.capitalize()


def _synthetic_documents(num_chains: int) -> list[tuple[str, str]]:
    documents: list[tuple[str, str]] = []
    for index in range(num_chains):
        landmark = _name("Landmark", index)
        city = _name("City", index)
        country = _name("Country", index)
        documents.append((f"d{index}a", f"{landmark} is located in {city}."))
        documents.append((f"d{index}b", f"{city} is the capital of {country}."))
    return documents


def main() -> None:
    documents = _synthetic_documents(500)

    start = time.perf_counter()
    graph = build_graph(documents)
    build_ms = (time.perf_counter() - start) * 1000

    retriever = GraphRetriever(graph)
    queries = [f"What country is {_name('Landmark', index)} in" for index in range(500)]

    start = time.perf_counter()
    for query in queries:
        retriever.retrieve(query)
    elapsed = time.perf_counter() - start

    print(f"Documents: {len(documents)} | Queries: {len(queries)}")
    print(f"Graph build: {build_ms:.1f} ms")
    print(f"Graph size: {graph.num_entities} entities, {graph.num_relations} relations")
    print(f"Traversal throughput: {len(queries) / elapsed:.0f} queries/sec")


if __name__ == "__main__":
    main()
