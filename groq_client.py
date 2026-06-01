import json
import re

import requests

from config import GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL


def strip_json_fence(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def generate_documentation(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(
        GROQ_API_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )

    print("\nGROQ STATUS:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return None

    content = response.json()["choices"][0]["message"]["content"]
    return strip_json_fence(content)


def parse_documentation_response(raw_result):
    raw_result = strip_json_fence(raw_result)
    result = json.loads(raw_result)

    documentation_html = result["documentation_html"]
    diagrams = result.get("diagrams", [])

    return documentation_html, diagrams
