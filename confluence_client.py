import requests
from requests.auth import HTTPBasicAuth

from config import (
    CONFLUENCE_API_TOKEN,
    CONFLUENCE_BASE_URL,
    CONFLUENCE_EMAIL,
    CONFLUENCE_PAGE_ID,
)


def _auth():
    return HTTPBasicAuth(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)


def publish_to_confluence(content, page_id=None):
    page_id = page_id or CONFLUENCE_PAGE_ID

    page_response = requests.get(
        f"{CONFLUENCE_BASE_URL}/pages/{page_id}",
        auth=_auth(),
        timeout=60,
    )

    print("\nCONFLUENCE GET STATUS:", page_response.status_code)

    if page_response.status_code != 200:
        print(page_response.text[:500])
        return None

    page = page_response.json()
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

    update_response = requests.put(
        f"{CONFLUENCE_BASE_URL}/pages/{page_id}",
        json=payload,
        auth=_auth(),
        timeout=60,
    )

    print("\nCONFLUENCE UPDATE STATUS:", update_response.status_code)
    print("\nCONFLUENCE UPDATE RESPONSE:", update_response.text[:1000])

    if update_response.status_code not in (200, 202):
        return None

    print("Confluence page updated successfully")
    return update_response.json()
