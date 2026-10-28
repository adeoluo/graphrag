# Data Card - GraphRAG

The project bundles one small, synthetic corpus and a labeled question set; there is no
training data and nothing is downloaded.

## bundled corpus (`src/graphrag/data.py`)

- **Provenance:** hand-authored for this project. Ten short passages, each stating a single
  relation (landmark located_in city, city capital_of country, country part_of continent),
  so extraction links them into chains.
- **Labeled questions:** six questions, two of them genuinely multi-hop (the answer is not
  in any single passage and is reachable only by traversing relations).
- **Licensing:** authored by this repository; MIT.
- **Known gaps:** tiny, English, general-knowledge; a demonstration set, not a benchmark.

## Ethical considerations

The corpus is synthetic and contains no personal, sensitive, or copyrighted content.
