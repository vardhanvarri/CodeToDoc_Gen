import html


VALID_DIAGRAM_TYPES = {"architecture", "workflow", "sequence", "dataflow"}


def validate_diagrams(diagrams):
    """Return a list of validation error strings (empty if OK)."""
    errors = []

    if not isinstance(diagrams, list):
        return ["diagrams must be a list"]

    if not diagrams:
        errors.append("diagrams array is empty")
        return errors

    if len(diagrams) > 3:
        errors.append(f"too many diagrams ({len(diagrams)}); expected at most 3")

    for index, diagram in enumerate(diagrams):
        prefix = f"diagrams[{index}]"
        if not isinstance(diagram, dict):
            errors.append(f"{prefix} must be an object")
            continue

        for field in ("name", "type", "description", "nodes", "edges"):
            if field not in diagram:
                errors.append(f"{prefix} missing '{field}'")

        diagram_type = diagram.get("type", "")
        if diagram_type not in VALID_DIAGRAM_TYPES:
            errors.append(f"{prefix} invalid type '{diagram_type}'")

        nodes = diagram.get("nodes", [])
        edges = diagram.get("edges", [])

        if not isinstance(nodes, list) or len(nodes) < 2:
            errors.append(f"{prefix} must have at least 2 nodes")

        if not isinstance(edges, list) or len(edges) < 1:
            errors.append(f"{prefix} must have at least 1 edge")

        node_ids = set()
        for node_index, node in enumerate(nodes if isinstance(nodes, list) else []):
            node_prefix = f"{prefix}.nodes[{node_index}]"
            if not isinstance(node, dict):
                errors.append(f"{node_prefix} must be an object")
                continue
            node_id = node.get("id")
            if not node_id:
                errors.append(f"{node_prefix} missing id")
                continue
            if node_id in node_ids:
                errors.append(f"{prefix} duplicate node id '{node_id}'")
            node_ids.add(node_id)

        for edge_index, edge in enumerate(edges if isinstance(edges, list) else []):
            edge_prefix = f"{prefix}.edges[{edge_index}]"
            if not isinstance(edge, dict):
                errors.append(f"{edge_prefix} must be an object")
                continue
            source = edge.get("source")
            target = edge.get("target")
            if source not in node_ids:
                errors.append(f"{edge_prefix} source '{source}' not in nodes")
            if target not in node_ids:
                errors.append(f"{edge_prefix} target '{target}' not in nodes")

    return errors


def render_diagrams_html(diagrams):
    """Appendix HTML for Confluence — readable diagram specs from JSON."""
    if not diagrams:
        return (
            '<h2>Diagram specifications</h2>'
            "<p>No diagrams were generated for this merge request.</p>"
        )

    parts = ['<h2>Diagram specifications</h2>']

    for diagram in diagrams:
        name = html.escape(str(diagram.get("name", "Unnamed")))
        dtype = html.escape(str(diagram.get("type", "")))
        desc = html.escape(str(diagram.get("description", "")))
        parts.append(f"<h3>{name} ({dtype})</h3>")
        if desc:
            parts.append(f"<p>{desc}</p>")

        parts.append("<h4>Nodes</h4><ul>")
        for node in diagram.get("nodes", []):
            node_id = html.escape(str(node.get("id", "")))
            label = html.escape(str(node.get("label", "")))
            kind = node.get("kind")
            kind_text = f" [{html.escape(str(kind))}]" if kind else ""
            parts.append(f"<li><code>{node_id}</code> — {label}{kind_text}</li>")
        parts.append("</ul>")

        parts.append("<h4>Edges</h4><ul>")
        for edge in diagram.get("edges", []):
            source = html.escape(str(edge.get("source", "")))
            target = html.escape(str(edge.get("target", "")))
            label = html.escape(str(edge.get("label", "")))
            kind = edge.get("kind")
            kind_text = f" ({html.escape(str(kind))})" if kind else ""
            parts.append(
                f"<li><code>{source}</code> → <code>{target}</code>: {label}{kind_text}</li>"
            )
        parts.append("</ul>")

    return "\n".join(parts)
