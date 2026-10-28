# Evaluation Report - GraphRAG

> Reproduce with `python -m graphrag evaluate`. Deterministic and offline.

## Setup

- **Corpus:** 10 single-relation passages that extraction links into landmark -> city ->
  country -> continent chains.
- **Questions:** 6 labeled questions, 2 of them multi-hop (the answer is reachable only by
  traversing more than one relation).
- **Metric:** answer accuracy, split by single- vs multi-hop.
- **Methods:** graph traversal vs a flat keyword baseline that returns an entity from the
  best-overlap passage.

## Results

| Method | overall | multi-hop | single-hop |
|---|---:|---:|---:|
| flat baseline | 0.67 | 0.00 | 1.00 |
| graph | 1.00 | 1.00 | 1.00 |

## Interpretation

The flat baseline answers single-hop questions perfectly but fails every multi-hop question
(0.00): the answer entity never appears in the same passage as the question's entity. Graph
traversal chains the connecting relations and answers all of them (1.00), a +1.00 multi-hop
gain with no single-hop regression. This is the central claim of GraphRAG, measured directly.

## Reproducibility

Everything is offline and deterministic; the numbers regenerate exactly.
