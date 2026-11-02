# Changelog

All notable changes to this project are documented here. The file is generated
from Conventional Commits by [git-cliff](https://git-cliff.org) when a release is cut
with `make cut-release`.

## Unreleased

### Features

- **core:** Add the knowledge graph and entity/relation extraction
- **retrieval:** Add entity linking and traversal-based retrieval
- **cli:** Add dataset, evaluation, and CLI with multi-hop traversal
- Add a deterministic graph-traversal micro-benchmark
- Add HTTP service, stress benchmark, and operations documentation
- Add production observability (metrics and readiness) and reword footer

### Bug fixes

- Deterministic entity linking and single-count self-loops (#17)

### Documentation

- Write README, architecture diagram, and responsible-AI cards
- Format README code block to satisfy ruff format check
- Use plain, factual wording (#16)
- Standard README structure and language framing (#1)
- Vertical layered architecture diagram
- Horizontal layered architecture diagram
- Compact horizontal architecture diagram
- Recorded demos of more commands, with their vhs tapes (#2)
- Recorded demos of the HTTP service and more commands (#3)

### Build and CI

- Run CodeQL on main and on a weekly schedule only

### Maintenance

- Scaffold graphrag from standards template
- Bump continuous integration action versions and dev dependencies
- **deps-dev:** Bump the python-dependencies group with 4 updates
- Remove Dependabot configuration
