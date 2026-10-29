"""Command-line interface for GraphRAG.

Subcommands:

- ``graph`` - build the knowledge graph from the bundled corpus and print its triples.
- ``ask`` - answer a question by traversing the graph, showing the relation path.
- ``evaluate`` - compare graph retrieval against a flat baseline on the bundled questions.

The CLI wires the bundled data, extraction, the graph retriever, and the evaluator
together; it holds no retrieval logic of its own.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from graphrag import __version__
from graphrag.data import documents, questions
from graphrag.evaluation import evaluate
from graphrag.extraction import build_graph
from graphrag.retrieval import GraphRetriever


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="graphrag",
        description="GraphRAG: knowledge-graph construction and traversal-based retrieval.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    graph_parser = subparsers.add_parser("graph", help="Print the knowledge graph triples.")
    graph_parser.set_defaults(handler=_handle_graph)

    ask_parser = subparsers.add_parser("ask", help="Answer a question over the graph.")
    ask_parser.add_argument("question", help="The question to answer.")
    ask_parser.set_defaults(handler=_handle_ask)

    eval_parser = subparsers.add_parser("evaluate", help="Compare graph and flat retrieval.")
    eval_parser.set_defaults(handler=_handle_evaluate)

    serve_parser = subparsers.add_parser("serve", help="Start the HTTP graph service.")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    serve_parser.add_argument("--port", type=int, default=8000, help="Bind port.")
    serve_parser.set_defaults(handler=_handle_serve)
    return parser


def _handle_graph(_: argparse.Namespace) -> int:
    graph = build_graph(documents())
    print(f"Knowledge graph: {graph.num_entities} entities, {graph.num_relations} relations\n")
    for relation in graph.relations():
        print(f"  ({relation.source}) -[{relation.relation}]-> ({relation.target})")
    return 0


def _handle_ask(args: argparse.Namespace) -> int:
    graph = build_graph(documents())
    answer = GraphRetriever(graph).retrieve(args.question)
    print(f"Question: {args.question}")
    print(f"Linked entities: {', '.join(answer.linked_entities) or 'none'}")
    if answer.path:
        print("Relation path:")
        for relation in answer.path:
            print(f"  ({relation.source}) -[{relation.relation}]-> ({relation.target})")
    print(f"\nAnswer: {answer.answer}  (confidence {answer.confidence:.2f})")
    return 0


def _handle_evaluate(_: argparse.Namespace) -> int:
    docs = documents()
    graph = build_graph(docs)
    labeled = questions()
    flat = evaluate(graph, docs, labeled, graph_retrieval=False)
    graph_report = evaluate(graph, docs, labeled, graph_retrieval=True)
    print("Answer accuracy:\n")
    print(flat.format())
    print(graph_report.format())
    gain = graph_report.multi_hop - flat.multi_hop
    print(f"\nMulti-hop gain from graph retrieval: {gain:+.2f}")
    return 0


def _handle_serve(args: argparse.Namespace) -> int:
    from graphrag.service import serve

    serve(host=args.host, port=args.port)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point; returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = args.handler
    exit_code: int = handler(args)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
