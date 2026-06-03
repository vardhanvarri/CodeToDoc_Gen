import re
import zlib

import requests

from config import PLANTUML_BASE_URL

PLANTUML_ENCODE_URL = f"{PLANTUML_BASE_URL}/png"


def encode6bit(b: int) -> str:
    if b < 10:
        return chr(48 + b)
    b -= 10
    if b < 26:
        return chr(65 + b)
    b -= 26
    if b < 26:
        return chr(97 + b)
    b -= 26
    if b == 0:
        return "-"
    if b == 1:
        return "_"
    return "?"


def encode64(data: bytes) -> str:
    result = []
    for i in range(0, len(data), 3):
        b1 = data[i]
        b2 = data[i + 1] if i + 1 < len(data) else 0
        b3 = data[i + 2] if i + 2 < len(data) else 0
        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F
        result.extend([encode6bit(c1), encode6bit(c2), encode6bit(c3), encode6bit(c4)])
    return "".join(result)


def plantuml_encode(source: str) -> str:
    compressed = zlib.compress(source.encode("utf-8"), 9)[2:-4]
    return encode64(compressed)


def normalize_plantuml(source: str) -> str:
    """Ensure valid PlantUML block from LLM output."""
    text = source.strip()
    text = re.sub(r"^```(?:plantuml)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    if "@startuml" not in text.lower():
        text = f"@startuml\n{text}"
    if "@enduml" not in text.lower():
        text = f"{text}\n@enduml"
    return text


def fetch_png(plantuml_source: str) -> bytes:
    """Render PlantUML source to PNG via public plantuml.com API."""
    normalized = normalize_plantuml(plantuml_source)
    encoded = plantuml_encode(normalized)
    url = f"{PLANTUML_ENCODE_URL}/{encoded}"

    response = requests.get(url, timeout=90)
    print(f"  PlantUML render: {response.status_code} (url len {len(url)})")

    if response.status_code != 200:
        raise RuntimeError(f"PlantUML API failed: {response.text[:200]}")

    if not response.content.startswith(b"\x89PNG"):
        raise RuntimeError("PlantUML did not return valid PNG data")

    return response.content
