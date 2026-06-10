import requests
from requests.auth import HTTPBasicAuth

# Configuration values loaded from config.py
from config import (
    CONFLUENCE_API_TOKEN,
    CONFLUENCE_ATTACHMENT_UPLOAD,
    CONFLUENCE_BASE_URL,
    CONFLUENCE_EMAIL,
    CONFLUENCE_PAGE_ID,
)


def _auth():

    return HTTPBasicAuth(
        CONFLUENCE_EMAIL,
        CONFLUENCE_API_TOKEN
    )


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
    """
    Find an existing attachment by filename.

    Why:
        Confluence does not allow creating
        another attachment with the same filename.

    We first check whether the file already exists.
    """

    response = requests.get(
        f"{CONFLUENCE_BASE_URL}/pages/{page_id}/attachments",
        params={
            "filename": filename,
            "limit": 50
        },
        auth=_auth(),
        timeout=60,
    )

    if response.status_code != 200:
        return None

    for item in response.json().get("results", []):

        if item.get("title") == filename:
            return item.get("id")

    return None


def create_page_attachment(
    page_id,
    filename,
    file_bytes,
    content_type="image/png"
):
    """
    Upload a brand new attachment.

    Example:
        architecture.png

    Used when the file does not already exist.
    """

    url = (
        f"{CONFLUENCE_ATTACHMENT_UPLOAD}"
        f"/{page_id}/child/attachment"
    )

    response = requests.post(
        url,
        auth=_auth(),
        headers={
            "X-Atlassian-Token": "no-check"
        },
        files={
            "file": (
                filename,
                file_bytes,
                content_type
            )
        },
        data={
            "comment": "MR doc diagram (doc_gen)"
        },
        timeout=120,
    )

    print(
        f"  create attachment {filename}: "
        f"{response.status_code}"
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(response.text[:500])

    return response.json()


def update_page_attachment_data(
    page_id,
    attachment_id,
    filename,
    file_bytes,
    content_type="image/png"
):
    """
    Replace an existing attachment.

    Example:

        architecture.png v1
            ↓
        architecture.png v2

    Confluence creates a new version internally.
    """

    url = (
        f"{CONFLUENCE_ATTACHMENT_UPLOAD}"
        f"/{page_id}/child/attachment"
        f"/{attachment_id}/data"
    )

    response = requests.post(
        url,
        auth=_auth(),
        headers={
            "X-Atlassian-Token": "no-check"
        },
        files={
            "file": (
                filename,
                file_bytes,
                content_type
            )
        },
        data={
            "comment": "MR doc diagram updated",
            "minorEdit": "true",
        },
        timeout=120,
    )

    print(
        f"  update attachment {filename}: "
        f"{response.status_code}"
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(response.text[:500])

    return response.json()


def upsert_page_attachment(
    page_id,
    filename,
    file_bytes,
    content_type="image/png"
):
    """
    Create-or-update attachment.

    Logic:

        Exists?
            YES -> Update
            NO  -> Create

    This prevents duplicate filename errors.
    """

    attachment_id = find_page_attachment_id(
        page_id,
        filename
    )

    if attachment_id:

        return update_page_attachment_data(
            page_id,
            attachment_id,
            filename,
            file_bytes,
            content_type,
        )

    return create_page_attachment(
        page_id,
        filename,
        file_bytes,
        content_type,
    )


def upload_diagram_attachments(
    page_id,
    prepared_diagrams,
    output_dir
):
    """
    Render PlantUML diagrams to PNG.

    Save local copies for debugging.

    Upload all diagrams to Confluence.

    Returns:
        List of successfully uploaded diagrams.
    """

    from plantuml_client import fetch_png

    uploaded = []

    for diagram in prepared_diagrams:

        filename = diagram["attachment_filename"]

        print(
            f"\nDiagram: "
            f"{diagram['name']} → {filename}"
        )

        # Convert PlantUML source
        # into PNG bytes
        png_bytes = fetch_png(
            diagram["plantuml"]
        )

        # Save PlantUML source
        puml_path = (
            output_dir /
            filename.replace(".png", ".puml")
        )

        puml_path.write_text(
            diagram["plantuml"],
            encoding="utf-8"
        )

        # Save PNG locally
        png_path = output_dir / filename

        png_path.write_bytes(
            png_bytes
        )

        print(
            f"  saved "
            f"{puml_path.name}, "
            f"{png_path.name}"
        )

        # Upload image to Confluence
        upsert_page_attachment(
            page_id,
            filename,
            png_bytes,
        )

        uploaded.append(diagram)

    return uploaded


def publish_to_confluence(
    content,
    page_id=None,
    page=None
):

    page_id = page_id or CONFLUENCE_PAGE_ID

    if page is None:
        page = get_page(page_id)

    if page is None:
        return None

    # Confluence requires
    # version number to increase
    status = page.get(
        "status",
        "current"
    )

    version_number = (
        1
        if status == "draft"
        else page["version"]["number"] + 1
    )

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
            "message":
                "Automated update from GitLab Bot",
        },
    }

    response = requests.put(
        f"{CONFLUENCE_BASE_URL}/pages/{page_id}",
        json=payload,
        auth=_auth(),
        timeout=60,
    )

    print(
        "\nCONFLUENCE PUT page (v2):",
        response.status_code
    )

    if response.status_code not in (200, 202):
        print(response.text[:1000])
        return None

    print(
        "Confluence page updated successfully"
    )

    return response.json()