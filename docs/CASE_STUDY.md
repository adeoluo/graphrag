# End-to-End Case Study - A Multi-Hop Graph Query

How one compound question is answered by traversing explicit relations rather than
matching a passage.

## Scenario

> "What country is the Eiffel Tower in?"

No passage states this. The corpus says the Eiffel Tower is in Paris, and that Paris is
the capital of France. The answer exists only by **chaining relations**.

## Trace

```bash
curl -s -X POST localhost:8000/ask -d '{"query": "What country is the Eiffel Tower in"}'
```

```json
{
  "answer": "France",
  "path": [["eiffel tower", "located_in", "paris"], ["paris", "capital_of", "france"]],
  "linked_entities": ["eiffel tower"],
  "confidence": 0.8
}
```

The service links "Eiffel Tower" to a graph entity, follows `located_in` then
`capital_of` to the terminal country, and returns the connecting path as a citation.

## Why the baseline fails here

A flat keyword retriever scores passages once and returns an entity from the best match.
On the labeled multi-hop set it scores **0.00**: the answer entity never co-occurs with
the question's entity in one passage. Graph traversal scores **1.00**, a **+1.00** gain.

## What an operator sees

- **Latency.** A short bounded walk over an adjacency index; p50 about 0.5 ms.
- **Auditability.** The `path` array is the explicit evidence chain for the answer.
- **Cost.** Bounded by the hop budget, independent of corpus size.

## Takeaway

The retrieval primitive is a graph walk. Representing facts as explicit edges is what
turns an unanswerable multi-hop question into a cited, auditable answer.
