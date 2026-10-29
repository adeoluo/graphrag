"""A production-style stress benchmark for the graph service.

Drives the full service handler under sustained, concurrent load over a large
synthetic graph and reports throughput and the p50, p95, and p99 latency tail.
Deterministic and offline; run with:

    uv run python benchmarks/stress.py
"""

from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor

from graphrag.service import GraphService


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
        landmark, city, country = (
            _name("Landmark", index),
            _name("City", index),
            _name("Country", index),
        )
        documents.append((f"d{index}a", f"{landmark} is located in {city}."))
        documents.append((f"d{index}b", f"{city} is the capital of {country}."))
    return documents


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(fraction * len(ordered)))]


def main() -> None:
    service = GraphService.from_documents(_synthetic_documents(1000))
    requests = [
        {"query": f"What country is {_name('Landmark', index)} in"} for index in range(2000)
    ]
    from graphrag.service import handle

    def one(body: dict[str, str]) -> float:
        start = time.perf_counter()
        handle("POST", "/ask", body, service)
        return (time.perf_counter() - start) * 1000

    print(f"Graph: {service.graph.num_entities} entities, {service.graph.num_relations} relations")
    for workers in (1, 4, 8):
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            latencies = list(pool.map(one, requests))
        wall = time.perf_counter() - start
        print(
            f"workers={workers:<2}  "
            f"throughput={len(requests) / wall:>7.0f} req/s  "
            f"p50={statistics.median(latencies):>6.2f} ms  "
            f"p95={_percentile(latencies, 0.95):>6.2f} ms  "
            f"p99={_percentile(latencies, 0.99):>6.2f} ms"
        )


if __name__ == "__main__":
    main()
