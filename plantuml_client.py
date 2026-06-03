import re
import zlib

import requests

from config import PLANTUML_BASE_URL

PLANTUML_ENCODE_URL = f"{PLANTUML_BASE_URL}/png"

#PlantUML uses its own encoding scheme so we need to change the current UML syntax to encoded code.

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
    #sometimes the code can be large so we need to reduce the size and [2:-4] is compressed code part
    compressed = zlib.compress(source.encode("utf-8"), 9)[2:-4]
    return encode64(compressed)

## Remove unnecessary prefix and suffix
def normalize_plantuml(source: str) -> str:
    """Ensure valid PlantUML block from LLM output."""
    text = source.strip()
    ## some times grok returns in format ```json``` so we need to remove them 
    text = re.sub(r"^```(?:plantuml)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    if "@startuml" not in text.lower():
        text = f"@startuml\n{text}"
    if "@enduml" not in text.lower():
        text = f"{text}\n@enduml"
    return text

def fetch_png(plantuml_source: str) -> bytes:

    normalized = normalize_plantuml(plantuml_source)

    encoded = plantuml_encode(normalized)

    url = f"{PLANTUML_ENCODE_URL}/{encoded}"

    print("\nPLANTUML URL:")
    print(url)

    response = requests.get(url, timeout=90)

    print("\nSTATUS:")
    print(response.status_code)

    print("\nCONTENT TYPE:")
    print(response.headers.get("Content-Type"))

    print("\nFIRST 50 BYTES:")
    print(response.content[:50])

    print("\nFIRST 500 CHARS:")
    try:
        print(response.text[:500])
    except Exception:
        print("Cannot decode response text")

    if not response.content.startswith(b"\x89PNG"):
        raise RuntimeError(
            "PlantUML did not return valid PNG data"
        )

    return response.content