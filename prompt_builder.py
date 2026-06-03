from pathlib import Path

from config import JSON_OUTPUT_SCHEMA, OUTPUT_DIR


def _write_debug_file(output_dir, filename, content):
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def build_llm_prompt(mr_details, output_dir=None):
    output_dir = output_dir or OUTPUT_DIR

    commit_section = "\n".join(
        f"""
Commit ID:
{commit['id'][:8]}

Commit Title:
{commit['title']}

Commit Message:
{commit['message']}

Author:
{commit['author_name']}
"""
        for commit in mr_details["commits"]
    )

    files_section = "\n".join(
        f"""
File Path:
{file['path']}

Status:
{file['status']}

Diff Preview:
{file['diff']}
"""
        for file in mr_details["files_changed"]
    )

    discussions_section = "\n".join(
        f"""
Author:
{discussion['author']}

Comment:
{discussion['comment']}
"""
        for discussion in mr_details["discussions"]
    )

    # _write_debug_file(output_dir, "commits.txt", commit_section)
    # _write_debug_file(output_dir, "diffs.txt", files_section)
    # _write_debug_file(output_dir, "discussions.txt", discussions_section)

    prompt = f"""
You are a senior software architect.

You must produce TWO outputs in one JSON object:
1) documentation_html — Confluence HTML prose (sections 1–12)
2) diagrams — PlantUML source for each diagram (rendered to PNG and embedded in Confluence)

Return ONLY valid JSON matching the schema below. No text before or after.

Schema:

{JSON_OUTPUT_SCHEMA}

Rules:
1. documentation_html must be valid Confluence storage HTML (h1, h2, p, ul, li, code only).
2. Do NOT use Markdown or Mermaid in documentation_html.
3. Return JSON only.

# MERGE REQUEST METADATA

Title:
{mr_details['title']}

Description:
{mr_details['description']}

Author:
{mr_details['author']}

Source Branch:
{mr_details['source_branch']}

Target Branch:
{mr_details['target_branch']}

Created At:
{mr_details['created_at']}

Updated At:
{mr_details['updated_at']}

# COMMIT DETAILS

{commit_section}

# FILES CHANGED + CODE DIFFS

{files_section}

# TEAM DISCUSSIONS

{discussions_section}

# REQUIRED OUTPUT SECTIONS (inside documentation_html)

1. Project Objective & Feature Description
2. Technical Changes Summary
3. Files / Components Impacted
4. Architectural Impact
5. Workflow Explanation
6. Decision Rationale
7. Risks / Concerns
8. High-Level Architecture Description
9. Low-Level Workflow Description
10. Sequence of Operations
11. Data Flow Explanation
12. Suggested Documentation Improvements

# DIAGRAM RULES (diagrams array — required, PlantUML)

- Include 1 to 3 diagrams only.
- Each diagram must have: "name", "type", "description", "plantuml".
- "plantuml" must be complete PlantUML source starting with @startuml and ending with @enduml.
- Use the best PlantUML diagram style for the type:
  - sequence: use actor/participant and arrows (->, -->)
  - architecture / component: use component, package, or rectangle nodes
  - workflow / dataflow: use activity or flowchart syntax where appropriate
- Use real module, file, service, and function names from the MR diffs and discussions.
- Do not invent components not evidenced in the MR context.
- Keep each diagram readable (roughly 5–12 elements); add a title line inside PlantUML.
- Optional: add "hide footbox" and "skinparam style strictuml" at the top for cleaner sequence diagrams.
- If context is insufficient for a diagram type, omit that diagram instead of guessing.

Example plantuml shape (adapt content to this MR):
@startuml
title Example
actor Dev
participant ServiceA
Dev -> ServiceA: action
@enduml

# DOCUMENTATION_HTML RULES

- Cover sections 1–12 as h1/h2 and paragraphs/lists.
- Sections 8–11 describe behavior in prose only; do NOT put PlantUML or diagram images inside documentation_html.
- Do NOT add a Diagrams section in documentation_html — diagrams are published separately as PNG attachments.
- If discussions are empty, state "No MR discussions" under Decision Rationale; do not invent decisions.
- If unsure about a claim, say "Not evident from the diff" instead of guessing.
- Focus on engineering understanding.
- Infer architectural relationships from changed files and diffs.
- Use discussions/comments to infer rationale and decision making.
- Be concise but technically detailed.
"""

   # _write_debug_file(output_dir, "final_prompt.txt", prompt)
    #print(f"Prompt written to {output_dir / 'final_prompt.txt'}")
    return prompt
