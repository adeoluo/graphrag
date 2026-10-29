# Operations Guide - GraphRAG

The operational contract of the graph retrieval service.

## Running the service

```bash
uv run python -m graphrag serve --host 0.0.0.0 --port 8000
```

A standard-library HTTP server with **zero runtime dependencies**. The knowledge graph
is built once at startup and then serves stateless requests.

## Endpoints

| Method | Path | Body | Success |
|---|---|---|---|
| GET | `/health` | none | `{"status": "ok", "entities": N, "relations": M}` |
| POST | `/ask` | `{"query"}` | answer, relation path, linked entities, confidence |

Errors return JSON `{"error": ...}` with a 4xx status; malformed JSON yields `400`,
unknown routes `404`.

## Service level objectives

Measured by `benchmarks/stress.py` over a 3000 entity graph on a developer laptop:

| Objective | Target | Observed (single worker) |
|---|---|---|
| Read latency p50 | < 2 ms | about 0.5 ms |
| Read latency p99 | < 2 ms at concurrency 1 | about 0.8 ms |
| Throughput | > 1000 queries/second/core | about 1800 queries/second |

Illustrative targets for the reference implementation, not a production guarantee.

## Operational constraints

- **Traversal is CPU bound and holds the global interpreter lock.** Throughput is flat
  across threads and the p99 tail grows with concurrency (measured: about 0.8 ms at one
  worker to tens of milliseconds at eight). Scale with **processes**, not threads.
- **The graph is in memory and immutable after startup.** Memory grows with the number
  of entities and relations; updates require a restart or a blue/green swap.
- **Queries are bounded** to 2000 characters, so a single request cannot exhaust CPU.
- **No persistence, no authentication.** Front the service with a gateway for transport
  security, authentication, and rate limiting.

## Failure modes and responses

| Symptom | Likely cause | Response |
|---|---|---|
| Rising p99 under load | Concurrency above one worker per core | Add replicas; cap per-replica concurrency |
| Empty answer | No entity in the query linked to the graph | Expected; the response states it |
| Memory growth at startup | Large graph | Shard the graph by entity namespace |

## Capacity planning

Throughput is approximately linear in shared-nothing replicas. For `R` queries per
second, provision about `ceil(R / 1800)` single-core replicas plus tail headroom.
