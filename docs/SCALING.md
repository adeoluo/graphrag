# Scaling and Design Tradeoffs - GraphRAG

How the reference design grows, and the tradeoffs taken.

## Reference architecture (today)

A single process: an in-memory directed labeled multigraph, the traversal retriever, and
a standard-library HTTP service. Shared-nothing and stateless per request.

## Scaling path

| Stage | Bottleneck | Change |
|---|---|---|
| One process | CPU, global interpreter lock | One replica per core |
| One host | Host memory for the graph | Horizontal replicas behind a load balancer |
| Large graph | Graph memory per replica | Partition by entity namespace; route by partition |
| Deep traversals | Fan-out of breadth-first search | Cap hops; precompute popular paths |
| Messy prose | Rule-based extraction recall | Model-backed extractor behind the extraction interface |

Because replicas share nothing, throughput is approximately linear in replica count.

## Substantial tradeoffs

- **In-memory graph vs a graph database.** In memory gives sub-millisecond traversal and
  zero dependencies, bounded by graph size per replica and restart-to-update. A graph
  database lifts the size ceiling and adds durable writes, at the cost of a network hop,
  a dependency, and operational surface. The reference chooses latency and simplicity;
  the graph sits behind an interface for a later swap.
- **Rule-based extraction vs a model.** Rules are deterministic, free, and auditable but
  miss relations phrased outside their patterns. A model generalizes at the cost of
  latency, spend, and nondeterminism. Extraction is isolated behind `extract_relations`.
- **Breadth-first traversal vs weighted search.** Breadth-first is simple and bounded but
  treats all edges equally. Weighted or learned traversal would rank paths at the cost of
  tuning and a scoring model.
- **Threads vs processes.** Traversal is pure Python and GIL-bound, so processes, not
  threads, are the unit of scaling. The service is stateless to make that trivial.

## What would change under real load

Partition the graph, run process-per-core replicas, cache popular paths, and move
extraction behind a batched model service. The traversal retriever is unchanged; only
what sits behind its interfaces changes.
