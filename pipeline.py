import json
from datetime import datetime, timezone

from confluence_client import publish_to_confluence
from diagram_utils import render_diagrams_html, validate_diagrams
from gitlab_client import fetch_complete_mr_details
from groq_client import generate_documentation, parse_documentation_response
from prompt_builder import build_llm_prompt


def _output_dir_for_mr(mr_iid):
    from config import OUTPUT_DIR

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = OUTPUT_DIR / f"mr_{mr_iid}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_doc_pipeline(project_id, mr_iid):
    mr_details = fetch_complete_mr_details(project_id, mr_iid)
    if mr_details is None:
        return False, "Failed to fetch MR"

    output_dir = _output_dir_for_mr(mr_iid)

    print("\n" + "=" * 80)
    print("FINAL LLM PROMPT")
    print("=" * 80 + "\n")

    final_prompt = build_llm_prompt(mr_details, output_dir=output_dir)

    raw_result = generate_documentation(final_prompt)
    if raw_result is None:
        return False, "Groq generation failed"

    try:
        documentation_html, diagrams = parse_documentation_response(raw_result)
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"Failed to parse Groq JSON: {exc}")
        print(raw_result[:500])
        return False, "Invalid Groq JSON response"

    diagram_errors = validate_diagrams(diagrams)
    if diagram_errors:
        print("Diagram validation warnings:")
        for err in diagram_errors:
            print(f"  - {err}")
        (output_dir / "diagram_validation_errors.txt").write_text(
            "\n".join(diagram_errors),
            encoding="utf-8",
        )

    documentation_html += render_diagrams_html(diagrams)

    (output_dir / "generated_doc.html").write_text(documentation_html, encoding="utf-8")
    (output_dir / "diagrams.json").write_text(
        json.dumps(diagrams, indent=2),
        encoding="utf-8",
    )
    (output_dir / "raw_response.json").write_text(raw_result, encoding="utf-8")

    print("Documentation generated")
    print("Diagrams saved")

    confluence_result = publish_to_confluence(documentation_html)
    if confluence_result is None:
        return False, "Confluence publish failed"

    print("Published to Confluence")
    print("\n" + "=" * 80)
    print("END OF PIPELINE")
    print("=" * 80 + "\n")

    return True, "OK"
