"""A large-workload scale benchmark for graph construction and traversal.

Where ``benchmark.py`` builds one graph and times traversal, this script asks how
the core operation scales: it builds knowledge graphs from progressively larger
synthetic corpora of relation chains, then answers a fixed set of genuinely
multi-hop questions against each. It reports the graph size, wall-clock time,
traversal throughput, peak memory (via the stdlib ``tracemalloc``), and multi-hop
answer accuracy so cost and quality are visible side by side.

Each synthetic chain is three sentences -- ``Landmark is located in City``,
``City is the capital of Country``, ``Country is a country in Europe`` -- so that
answering "what country is Landmark in" requires chaining ``located_in`` then
``capital_of`` edges to the terminal country, which no single passage states.

The data is synthetic and the graph/traversal is from-scratch pure Python: it is
not meant to be competitive on wall-clock with compiled graph databases. The
point is to show how this implementation scales, honestly.

Run with:

    uv run python benchmarks/scale.py
"""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass

from graphrag import GraphRetriever, build_graph

_CHAIN_COUNTS: tuple[int, ...] = (250, 500, 1000, 2000)
_NUM_QUERIES = 200


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
        documents.append((f"d{index}c", f"{country} is a country in Europe."))
    return documents


def _labeled_queries(num_chains: int) -> list[tuple[str, str]]:
    count = min(num_chains, _NUM_QUERIES)
    return [
        (f"What country is {_name('Landmark', i)} in", _name("Country", i)) for i in range(count)
    ]


@dataclass(frozen=True, slots=True)
class ScaleResult:
    """One row of the scale table."""

    chains: int
    entities: int
    seconds: float
    queries_per_sec: float
    peak_mib: float
    accuracy: float


def measure(num_chains: int) -> ScaleResult:
    """Build a graph of ``num_chains`` chains and answer the multi-hop query set."""
    documents = _synthetic_documents(num_chains)
    queries = _labeled_queries(num_chains)

    tracemalloc.start()
    build_start = time.perf_counter()
    graph = build_graph(documents)
    build_elapsed = time.perf_counter() - build_start

    retriever = GraphRetriever(graph)
    query_start = time.perf_counter()
    hits = sum(retriever.retrieve(query).answer == expected for query, expected in queries)
    query_elapsed = time.perf_counter() - query_start

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return ScaleResult(
        chains=num_chains,
        entities=graph.num_entities,
        seconds=build_elapsed + query_elapsed,
        queries_per_sec=len(queries) / query_elapsed if query_elapsed else 0.0,
        peak_mib=peak / (1024 * 1024),
        accuracy=hits / len(queries) if queries else 0.0,
    )


def main() -> None:
    print("Synthetic corpus; from-scratch pure-Python graph + traversal (not a graph database).")
    print(f"Fixed query set: up to {_NUM_QUERIES} multi-hop 'what country is X in' questions.\n")
    header = (
        f"{'chains':>8}{'entities':>10}{'seconds':>10}"
        f"{'queries/sec':>14}{'peak MiB':>11}{'accuracy':>11}"
    )
    print(header)
    print("-" * len(header))
    for num_chains in _CHAIN_COUNTS:
        result = measure(num_chains)
        print(
            f"{result.chains:>8}{result.entities:>10}{result.seconds:>10.3f}"
            f"{result.queries_per_sec:>14.0f}{result.peak_mib:>11.1f}{result.accuracy:>11.2f}"
        )


if __name__ == "__main__":
    main()
