"""A bundled corpus and labeled questions for GraphRAG evaluation.

The passages each state a single relation ("X is located in Y", "Y is the capital of Z"),
so the knowledge graph links them into chains. The questions include multi-hop cases whose
answer is not in any single passage but is reachable by traversing relations - exactly
where graph retrieval beats flat retrieval.
"""

from __future__ import annotations

_DOCUMENTS: tuple[tuple[str, str], ...] = (
    ("d0", "The Eiffel Tower is located in Paris."),
    ("d1", "Paris is the capital of France."),
    ("d2", "France is a country in Europe."),
    ("d3", "The Colosseum is located in Rome."),
    ("d4", "Rome is the capital of Italy."),
    ("d5", "Italy is a country in Europe."),
    ("d6", "The Statue of Liberty is located in New York."),
    ("d7", "New York is a city in the United States."),
    ("d8", "Mount Fuji is located in Tokyo prefecture."),
    ("d9", "Tokyo is the capital of Japan."),
)

# (question, expected_answer_entity, multi_hop)
_QUESTIONS: tuple[tuple[str, str, bool], ...] = (
    ("What is the capital of France", "Paris", False),
    ("Where is the Eiffel Tower located", "Paris", False),
    ("What country is the Eiffel Tower in", "France", True),
    ("What is the capital of Italy", "Rome", False),
    ("Where is the Colosseum located", "Rome", False),
    ("What country is the Colosseum in", "Italy", True),
)


def documents() -> list[tuple[str, str]]:
    """Return the bundled ``(document_id, text)`` pairs."""
    return list(_DOCUMENTS)


def questions() -> list[tuple[str, str, bool]]:
    """Return labeled ``(question, expected_answer, multi_hop)`` triples."""
    return list(_QUESTIONS)
