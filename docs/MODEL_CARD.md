# System Card - GraphRAG

## Overview

- **What it is:** a GraphRAG system - entity/relation extraction, knowledge-graph
  construction, and traversal-based retrieval with cited relation paths.
- **What it is not:** a generator. It extracts and traverses; it does not call a language
  model to write answers.
- **Version:** 0.1.0.

## Intended use

- **Primary use cases:** learning and demonstrating knowledge-graph RAG and multi-hop
  retrieval; a from-scratch reference for extraction and graph traversal.
- **Primary users:** engineers and researchers building retrieval systems.

## Out-of-scope / prohibited use

- Not tuned for production-scale graphs; the graph is in-memory.
- The bundled corpus is a demonstration, not a benchmark.

## Performance

See the README results. Graph traversal answers multi-hop questions (1.00) the flat
baseline cannot (0.00), with no single-hop regression.

## Risks and limitations

- Rule-based extraction misses relations that do not match the patterns.
- The relation vocabulary is small and illustrative.

## Safety mitigations

- Deterministic, offline, reproducible; bounded traversal guarantees termination.

## Environmental / cost footprint

Negligible; all in-memory with no model calls.
