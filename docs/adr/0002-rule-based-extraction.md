# ADR-0002: Rule-based entity and relation extraction

- **Status:** Accepted
- **Date:** 2026-01-01

## Context

Building the knowledge graph requires extracting entities and relations from text. This
could be model-backed or rule-based.

## Decision

Extract entities as capitalized noun phrases (leading articles stripped) and relations from
a small set of verb/preposition patterns between two entities in a sentence. Extraction is
deterministic and offline.

## Alternatives considered

- **Model-backed triple extraction.** More general on messy prose, but adds a dependency
  and nondeterminism, obscuring the graph construction and traversal that are the point.
- **Dependency parsing.** More accurate but heavy; overkill for a from-scratch reference.

## Consequences

- The graph is reproducible and the pipeline fully testable offline.
- A model-backed extractor can replace the rule-based one behind `extract_relations`.
- Extraction quality is limited on prose that does not match the patterns (documented).
