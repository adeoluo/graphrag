# Threat Model - GraphRAG

## Assets

- Integrity of the extracted graph and the answers read off it.

## Trust boundaries

- **Documents and questions are untrusted text.** They are parsed and traversed, never
  executed; there is no path from text to execution.

## Threats and mitigations

| Threat | Vector | Impact | Mitigation |
|---|---|---|---|
| Non-terminating traversal | Cyclic relations | Hang | Breadth-first traversal with a visited set and a hop budget |
| Extraction errors | Prose that misleads the patterns | Wrong edges | Rule-based extraction is inspectable; relations record their source document |
| Graph poisoning | Malicious documents added | Skewed answers | Extraction and traversal are read-only; callers control the corpus |
| Supply-chain compromise | Malicious dependency | Code execution | Zero runtime dependencies; Dependabot and CodeQL in continuous integration |

## Residual risk

Rule-based extraction cannot capture relations phrased outside its patterns; such facts are
simply absent from the graph, a capability limit rather than a security control.
