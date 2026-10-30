"""The knowledge graph: entities as nodes, relations as labeled edges.

A :class:`KnowledgeGraph` stores entities (nodes) and relations (directed, labeled edges)
and supports the traversal operations GraphRAG needs: neighbor lookup, breadth-first
exploration from a seed set, and extraction of the subgraph connecting a few entities.
Each edge remembers the id of the source document it came from, so retrieval can cite its
provenance.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Relation:
    """A directed, labeled edge between two entities."""

    source: str
    relation: str
    target: str
    document_id: str = ""

    def as_triple(self) -> tuple[str, str, str]:
        return (self.source, self.relation, self.target)


class KnowledgeGraph:
    """A directed multigraph of entities and labeled relations."""

    def __init__(self) -> None:
        self._entities: set[str] = set()
        self._out: dict[str, list[Relation]] = {}
        self._in: dict[str, list[Relation]] = {}

    def add_entity(self, name: str) -> None:
        """Add an entity node (idempotent)."""
        if not name:
            raise ValueError("entity name must be non-empty")
        self._entities.add(name)
        self._out.setdefault(name, [])
        self._in.setdefault(name, [])

    def add_relation(self, relation: Relation) -> None:
        """Add a relation, creating its endpoint entities if needed."""
        self.add_entity(relation.source)
        self.add_entity(relation.target)
        self._out[relation.source].append(relation)
        self._in[relation.target].append(relation)

    @property
    def entities(self) -> set[str]:
        return set(self._entities)

    @property
    def num_entities(self) -> int:
        return len(self._entities)

    @property
    def num_relations(self) -> int:
        return sum(len(edges) for edges in self._out.values())

    def relations(self) -> Iterator[Relation]:
        """Yield every relation in the graph."""
        for edges in self._out.values():
            yield from edges

    def neighbors(self, entity: str) -> list[Relation]:
        """Return relations incident to ``entity`` in either direction.

        A self-loop (source equal to target) is stored in both the outgoing and
        incoming lists, so it is counted once here by excluding self-loops from
        the incoming contribution rather than returning it twice.
        """
        outgoing = self._out.get(entity, [])
        incoming = [relation for relation in self._in.get(entity, []) if relation.source != entity]
        return outgoing + incoming

    def bfs(self, seeds: Iterable[str], *, max_hops: int = 2) -> set[str]:
        """Return all entities reachable from ``seeds`` within ``max_hops`` hops."""
        if max_hops < 0:
            raise ValueError("max_hops must be non-negative")
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        for seed in seeds:
            if seed in self._entities:
                visited.add(seed)
                queue.append((seed, 0))
        while queue:
            entity, depth = queue.popleft()
            if depth >= max_hops:
                continue
            for relation in self.neighbors(entity):
                for endpoint in (relation.source, relation.target):
                    if endpoint not in visited:
                        visited.add(endpoint)
                        queue.append((endpoint, depth + 1))
        return visited

    def subgraph_relations(self, entities: set[str]) -> list[Relation]:
        """Return relations whose endpoints are both within ``entities``."""
        return [
            relation
            for relation in self.relations()
            if relation.source in entities and relation.target in entities
        ]
