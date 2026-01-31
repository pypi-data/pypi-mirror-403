from __future__ import annotations

from typing import List, Set

from .core import Edge, FinishNode, StartNode, Strategy


def as_mermaid_diagram(strategy: Strategy) -> str:
    """
    Generate a Mermaid state diagram similar to Koog's JVM MermaidDiagramGenerator.
    """
    title = strategy.name

    # Collect nodes reachable from strategy.start (excluding technical start/finish)
    nodes: Set[str] = set()
    lines: List[str] = []

    def visit(node) -> None:
        if isinstance(node, (StartNode, FinishNode)):
            return
        if node.name in nodes:
            return
        nodes.add(node.name)
        for e in node.edges:
            visit(e.to_node)

    # Start reachability
    for e in strategy.start.edges:
        visit(e.to_node)

    # Node declarations
    for name in sorted(nodes):
        lines.append(f'    state "{name}" as {name}')

    # Edges: start -> ...
    for e in strategy.start.edges:
        if isinstance(e.to_node, FinishNode):
            continue
        lines.append(f"    [*] --> {e.to_node.name}")

    # Edges among nodes
    def render_edge(src_name: str, edge: Edge) -> None:
        dst = edge.to_node
        label = f" : {edge.label}" if edge.label else ""
        if isinstance(dst, FinishNode):
            lines.append(f"    {src_name} --> [*]{label}")
        elif isinstance(dst, StartNode):
            # technical; skip
            return
        else:
            lines.append(f"    {src_name} --> {dst.name}{label}")

    # Walk nodes and edges
    def visit_edges(node) -> None:
        if isinstance(node, (StartNode, FinishNode)):
            return
        for e in node.edges:
            render_edge(node.name, e)
            visit_edges(e.to_node)

    for e in strategy.start.edges:
        visit_edges(e.to_node)

    header = ["```mermaid", "---", f"title: {title}", "---", "stateDiagram"]
    footer = ["```"]
    return "\n".join(header + lines + footer)


