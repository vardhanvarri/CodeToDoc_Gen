import html
import re

from plantuml_client import normalize_plantuml

VALID_DIAGRAM_TYPES = {"architecture", "workflow", "sequence", "dataflow", "component"}


def slugify_filename(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return (slug or "diagram")[:max_len]


def attachment_filename(mr_iid, diagram: dict, index: int) -> str:
    """Stable PNG name per MR + diagram (upsert on Confluence re-runs)."""
    name_slug = slugify_filename(str(diagram.get("name", f"diagram-{index}")))
    type_slug = slugify_filename(str(diagram.get("type", "diagram")), max_len=20)
    return f"mr-{mr_iid}-{type_slug}-{name_slug}.png"


def validate_diagrams(diagrams):
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

        for field in ("name", "type", "description", "plantuml"):
            if field not in diagram:
                errors.append(f"{prefix} missing '{field}'")

        diagram_type = diagram.get("type", "")
        if diagram_type and diagram_type not in VALID_DIAGRAM_TYPES:
            errors.append(f"{prefix} invalid type '{diagram_type}'")

        plantuml = diagram.get("plantuml", "")
        if not isinstance(plantuml, str) or len(plantuml.strip()) < 20:
            errors.append(f"{prefix} plantuml source too short")
        elif "@startuml" not in plantuml.lower() and "startuml" not in plantuml.lower():
            errors.append(f"{prefix} plantuml must contain @startuml")

    return errors


def prepare_diagrams(diagrams, mr_iid):
    """
    Normalize PlantUML and assign attachment filenames.
    Returns list of dicts with keys: name, type, description, plantuml, attachment_filename
    """
    prepared = []
    for index, diagram in enumerate(diagrams):
        plantuml = normalize_plantuml(diagram["plantuml"])
        prepared.append(
            {
                "name": diagram.get("name", f"Diagram {index + 1}"),
                "type": diagram.get("type", "architecture"),
                "description": diagram.get("description", ""),
                "plantuml": plantuml,
                "attachment_filename": attachment_filename(mr_iid, diagram, index),
            }
        )
    return prepared


def render_diagrams_html(prepared_diagrams):
    """Confluence storage HTML — embedded attachment images."""
    if not prepared_diagrams:
        return "<h2>Diagrams</h2><p>No diagrams generated for this merge request.</p>"

    parts = ["<h2>Diagrams</h2>"]
    parts.append(
        "<p>Diagrams below were generated as PlantUML, rendered to PNG, and attached to this page.</p>"
    )

    for diagram in prepared_diagrams:
        name = html.escape(diagram["name"])
        dtype = html.escape(diagram["type"])
        desc = html.escape(diagram.get("description", ""))
        filename = html.escape(diagram["attachment_filename"])

        parts.append(f"<h3>{name} ({dtype})</h3>")
        if desc:
            parts.append(f"<p>{desc}</p>")
        parts.append(
            f'<ac:image ac:align="center" ac:layout="center">'
            f'<ri:attachment ri:filename="{filename}" />'
            f"</ac:image>"
        )

    return "\n".join(parts)
