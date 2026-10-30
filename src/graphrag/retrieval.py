"""Graph retrieval: linking a query to entities and traversing for an answer.

GraphRAG answers a question by (1) linking the question's mentions to entities in the
graph, (2) traversing outward to gather a connected subgraph of relations, and (3) reading
the answer off that subgraph. This answers multi-hop questions a flat retriever cannot,
because the connecting relations are explicit edges rather than words that must co-occur in
one passage.

- :func:`link_entities` - match capitalized mentions in the query to graph entities.
- :class:`GraphRetriever` - traverse from the linked entities and return the subgraph plus
  a path-based answer for relation-style questions ("capital of", "located in").
"""

from __future__ import annotations

from dataclasses import dataclass, field

from graphrag.core.graph import KnowledgeGraph, Relation
from graphrag.extraction import extract_entities

# Map question phrasings to the relation label that answers them.
_QUESTION_RELATION: tuple[tuple[str, str], ...] = (
    ("capital of", "capital_of"),
    ("located in", "located_in"),
    ("where is", "located_in"),
    ("what country", "located_in"),
    ("which country", "located_in"),
    ("part of", "part_of"),
    ("borders", "borders"),
)


def link_entities(query: str, graph: KnowledgeGraph) -> list[str]:
    """Return graph entities mentioned in ``query`` (exact, then containment match)."""
    mentions = extract_entities(query)
    linked: list[str] = []
    for mention in mentions:
        if mention in graph.entities and mention not in linked:
            linked.append(mention)
            continue
        # Fall back to a containment match (mention is part of an entity name or
        # vice versa). Iterate in sorted order so the choice is deterministic;
        # iterating the entity set directly depends on the hash seed.
        for entity in sorted(graph.entities):
            if (mention in entity or entity in mention) and entity not in linked:
                linked.append(entity)
                break
    return linked


@dataclass(frozen=True, slots=True)
class GraphAnswer:
    """An answer read off a traversed subgraph."""

    answer: str
    path: tuple[Relation, ...]
    linked_entities: tuple[str, ...]
    subgraph_size: int
    confidence: float = field(default=0.0)


class GraphRetriever:
    """Answers questions by linking entities and traversing the knowledge graph."""

    def __init__(self, graph: KnowledgeGraph, *, max_hops: int = 3) -> None:
        if max_hops < 1:
            raise ValueError("max_hops must be at least 1")
        self._graph = graph
        self._max_hops = max_hops

    def retrieve(self, query: str) -> GraphAnswer:
        """Return a graph-based answer to ``query``."""
        linked = link_entities(query, self._graph)
        if not linked:
            return GraphAnswer("I could not find an entity in the question.", (), (), 0)

        reachable = self._graph.bfs(linked, max_hops=self._max_hops)
        subgraph = self._graph.subgraph_relations(reachable)

        # Compound multi-hop: "what country is X in" follows location/capital chains to the
        # terminal country, which no single passage states.
        if self._asks_for_country(query):
            path, answer_entity = self._country_path(linked[0])
            if path:
                return GraphAnswer(
                    answer=answer_entity,
                    path=tuple(path),
                    linked_entities=tuple(linked),
                    subgraph_size=len(subgraph),
                    confidence=0.8,
                )

        target_relation = self._target_relation(query)
        path, answer_entity = self._find_path(linked[0], target_relation)
        if path:
            confidence = 1.0 if len(path) == 1 else 0.8
            return GraphAnswer(
                answer=answer_entity,
                path=tuple(path),
                linked_entities=tuple(linked),
                subgraph_size=len(subgraph),
                confidence=confidence,
            )
        return GraphAnswer(
            answer="No path to an answer was found.",
            path=(),
            linked_entities=tuple(linked),
            subgraph_size=len(subgraph),
            confidence=0.0,
        )

    @staticmethod
    def _asks_for_country(query: str) -> bool:
        lowered = query.lower()
        return "country" in lowered and "capital of" not in lowered

    def _country_path(self, start: str) -> tuple[list[Relation], str]:
        """Follow located_in and capital_of edges to the terminal country entity.

        A country is an entity that is the source of a ``part_of`` relation (for example
        "France is a country in Europe"). Chaining located_in then capital_of from a
        landmark reaches it - a genuine multi-hop answer.
        """
        from collections import deque

        countries = {
            relation.source
            for relation in self._graph.relations()
            if relation.relation == "part_of"
        }
        queue: deque[tuple[str, list[Relation]]] = deque([(start, [])])
        visited = {start}
        while queue:
            entity, path = queue.popleft()
            if entity in countries and path:
                return path, entity
            if len(path) >= self._max_hops:
                continue
            for relation in self._graph.neighbors(entity):
                if relation.relation not in {"located_in", "capital_of"}:
                    continue
                nxt = relation.target if relation.source == entity else relation.source
                if nxt in visited:
                    continue
                visited.add(nxt)
                queue.append((nxt, [*path, relation]))
        return [], ""

    @staticmethod
    def _target_relation(query: str) -> str | None:
        lowered = query.lower()
        for phrase, label in _QUESTION_RELATION:
            if phrase in lowered:
                return label
        return None

    def _find_path(self, start: str, target_relation: str | None) -> tuple[list[Relation], str]:
        """Find a relation path from ``start`` and return it with the answer entity.

        The answer is the endpoint reached by following edges of the target relation
        (in either direction), which handles both "where is X located" (X -> place) and
        "capital of Y" (capital -> Y, so from Y we reach the capital).
        """
        if target_relation is None:
            neighbors = self._graph.neighbors(start)
            if not neighbors:
                return [], ""
            relation = neighbors[0]
            other = relation.target if relation.source == start else relation.source
            return [relation], other

        from collections import deque

        queue: deque[tuple[str, list[Relation]]] = deque([(start, [])])
        visited = {start}
        while queue:
            entity, path = queue.popleft()
            if len(path) >= self._max_hops:
                continue
            for relation in self._graph.neighbors(entity):
                if relation.relation != target_relation:
                    continue
                other = relation.target if relation.source == entity else relation.source
                if other in visited:
                    continue
                new_path = [*path, relation]
                return new_path, other  # first matching-relation edge yields the answer
        return [], ""
