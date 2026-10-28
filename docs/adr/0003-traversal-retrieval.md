# ADR-0003: Traversal-based retrieval instead of similarity

- **Status:** Accepted
- **Date:** 2026-01-01

## Context

The system must answer questions whose supporting facts are spread across documents. Vector
or keyword retrieval scores whole passages by similarity and cannot connect facts that
never co-occur in one passage.

## Decision

Answer by linking the question to graph entities and traversing explicit relation edges:
follow a target relation for direct questions, or chain location and capital edges for
compound "what country" questions, returning the connecting path as a citation.

## Alternatives considered

- **Flat passage retrieval.** Simple, but structurally cannot answer multi-hop questions
  (demonstrated: 0.00 on the multi-hop set).
- **Retrieve passages then re-read.** Still bounded by what co-occurs in a passage.

## Consequences

- Multi-hop questions resolve by following edges (1.00 on the multi-hop set).
- Answers come with an explicit, auditable relation path.
- Coverage depends on the extracted relations; missing edges mean missing answers.
