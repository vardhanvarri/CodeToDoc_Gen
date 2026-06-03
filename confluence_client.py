import requests
from requests.auth import HTTPBasicAuth

from config import (
    CONFLUENCE_API_TOKEN,
    CONFLUENCE_ATTACHMENT_UPLOAD,
    CONFLUENCE_BASE_URL,
    CONFLUENCE_EMAIL,
    CONFLUENCE_PAGE_ID,
)


def _auth():
    return HTTPBasicAuth(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)


def get_page(page_id=None):
    page_id = page_id or CONFLUENCE_PAGE_ID
    response = requests.get(
        f"{CONFLUENCE_BASE_URL}/pages/{page_id}",
        auth=_auth(),
        timeout=60,
    )
    print("\nCONFLUENCE GET page (v2):", response.status_code)
    if response.status_code != 200:
        print(response.text[:500])
        return None
    return response.json()


def find_page_attachment_id(page_id, filename):
    response = requests.get(
        f"{CONFLUENCE_BASE_URL}/pages/{page_id}/attachments",
        params={"filename": filename, "limit": 50},
        auth=_auth(),
        timeout=60,
    )
    if response.status_code != 200:
        return None
    for item in response.json().get("results", []):
        if item.get("title") == filename:
            return item.get("id")
    return None


def create_page_attachment(page_id, filename, file_bytes, content_type="image/png"):
    url = f"{CONFLUENCE_ATTACHMENT_UPLOAD}/{page_id}/child/attachment"
    response = requests.post(
        url,
        auth=_auth(),
        headers={"X-Atlassian-Token": "no-check"},
        files={"file": (filename, file_bytes, content_type)},
        data={"comment": "MR doc diagram (doc_gen)"},
        timeout=120,
    )
    print(f"  create attachment {filename}: {response.status_code}")
    if response.status_code not in (200, 201):
        raise RuntimeError(response.text[:500])
    return response.json()


def update_page_attachment_data(page_id, attachment_id, filename, file_bytes, content_type="image/png"):
    url = f"{CONFLUENCE_ATTACHMENT_UPLOAD}/{page_id}/child/attachment/{attachment_id}/data"
    response = requests.post(
        url,
        auth=_auth(),
        headers={"X-Atlassian-Token": "no-check"},
        files={"file": (filename, file_bytes, content_type)},
        data={"comment": "MR doc diagram updated", "minorEdit": "true"},
        timeout=120,
    )
    print(f"  update attachment {filename}: {response.status_code}")
    if response.status_code not in (200, 201):
        raise RuntimeError(response.text[:500])
    return response.json()


def upsert_page_attachment(page_id, filename, file_bytes, content_type="image/png"):
    """
    Create or replace attachment by filename.
    Avoids 400 duplicate when the same PNG name already exists on the page.
    """
    attachment_id = find_page_attachment_id(page_id, filename)
    if attachment_id:
        return update_page_attachment_data(
            page_id, attachment_id, filename, file_bytes, content_type
        )
    return create_page_attachment(page_id, filename, file_bytes, content_type)


def upload_diagram_attachments(page_id, prepared_diagrams, output_dir):
    """Render PlantUML → PNG and upsert each attachment on the Confluence page."""
    from plantuml_client import fetch_png

    uploaded = []
    for diagram in prepared_diagrams:
        filename = diagram["attachment_filename"]
        print(f"\nDiagram: {diagram['name']} → {filename}")

        png_bytes = fetch_png(diagram["plantuml"])

        puml_path = output_dir / filename.replace(".png", ".puml")
        puml_path.write_text(diagram["plantuml"], encoding="utf-8")
        png_path = output_dir / filename
        png_path.write_bytes(png_bytes)
        print(f"  saved {puml_path.name}, {png_path.name}")

        upsert_page_attachment(page_id, filename, png_bytes)
        uploaded.append(diagram)

    return uploaded


def publish_to_confluence(content, page_id=None, page=None):
    page_id = page_id or CONFLUENCE_PAGE_ID

    if page is None:
        page = get_page(page_id)
    if page is None:
        return None

    status = page.get("status", "current")
    version_number = 1 if status == "draft" else page["version"]["number"] + 1

    payload = {
        "id": page_id,
        "status": "current",
        "title": page["title"],
        "body": {
            "representation": "storage",
            "value": content,
        },
        "version": {
            "number": version_number,
            "message": "Automated update from GitLab Bot",
        },
    }

    response = requests.put(
        f"{CONFLUENCE_BASE_URL}/pages/{page_id}",
        json=payload,
        auth=_auth(),
        timeout=60,
    )

    print("\nCONFLUENCE PUT page (v2):", response.status_code)
    if response.status_code not in (200, 202):
        print(response.text[:1000])
        return None

    print("Confluence page updated successfully")
    return response.json()
