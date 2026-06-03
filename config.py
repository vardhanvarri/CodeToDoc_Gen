import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com/api/v4")

CONFLUENCE_SITE = os.getenv("CONFLUENCE_SITE", "https://sprinklr.atlassian.net")
CONFLUENCE_BASE_URL = os.getenv(
    "CONFLUENCE_BASE_URL", f"{CONFLUENCE_SITE}/wiki/api/v2"
)
CONFLUENCE_ATTACHMENT_UPLOAD = os.getenv(
    "CONFLUENCE_ATTACHMENT_UPLOAD",
    f"{CONFLUENCE_SITE}/wiki/rest/api/content",
)
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")
CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID", "6217925321")

PLANTUML_BASE_URL = os.getenv("PLANTUML_BASE_URL", "https://www.plantuml.com/plantuml")

DIFF_PREVIEW_LIMIT = int(os.getenv("DIFF_PREVIEW_LIMIT", "2000"))

# Plain string — not inside an f-string (avoids brace escaping issues)
JSON_OUTPUT_SCHEMA = """
{
  "documentation_html": "string",
  "diagrams": [
    {
      "name": "string",
      "type": "architecture | workflow | sequence | dataflow | component",
      "description": "string",
      "plantuml": "string (full PlantUML source between @startuml and @enduml)"
    }
  ]
}
"""
