import requests

from config import DIFF_PREVIEW_LIMIT, GITLAB_TOKEN, GITLAB_URL


def _headers():
    return {"PRIVATE-TOKEN": GITLAB_TOKEN}


def fetch_complete_mr_details(project_id, mr_iid):
    headers = _headers()

    mr_response = requests.get(
        f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}",
        headers=headers,
        timeout=60,
    )
    print("\nMR STATUS:", mr_response.status_code)
 ### check 
    if mr_response.status_code != 200:
        print("Failed to fetch MR")
        return None

    mr = mr_response.json()
    print("MR metadata fetched")

    commits_response = requests.get(
        f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}/commits",
        headers=headers,
        timeout=60,
    )
    commits = commits_response.json() if commits_response.status_code == 200 else []
    print(f"Commits fetched: {len(commits)}")

    changes_response = requests.get(
        f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}/changes",
        headers=headers,
        timeout=60,
    )
    print("\nCHANGES STATUS CODE:", changes_response.status_code)

    if changes_response.status_code != 200:
        changes = []
    else:
        changes_data = changes_response.json()
        changes = changes_data.get("changes", [])

    print(f"Files changed fetched: {len(changes)}")

    discussions_response = requests.get(
        f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}/discussions",
        headers=headers,
        timeout=60,
    )
    print("\nDISCUSSIONS STATUS:", discussions_response.status_code)

    ## data Minimization (Refractoring)
    discussions = []
    if discussions_response.status_code == 200:
        for discussion in discussions_response.json():
            for note in discussion.get("notes", []):
                discussions.append(
                    {
                        "author": note.get("author", {}).get("name", "Unknown"),
                        "comment": note.get("body", ""),
                    }
                )

    print(f"Discussions fetched: {len(discussions)}")

    ## data Minimization (Refractoring)
    files_changed = []
    for change in changes:
        files_changed.append(
            {
                "path": change["new_path"],
                "status": (
                    "NEW"
                    if change["new_file"]
                    else "DELETED"
                    if change["deleted_file"]
                    else "MODIFIED"
                ),
                "diff": change.get("diff", "")[:DIFF_PREVIEW_LIMIT],
            }
        )

    return {
        "title": mr["title"],
        "description": mr.get("description") or "",
        "author": mr["author"]["name"],
        "source_branch": mr["source_branch"],
        "target_branch": mr["target_branch"],
        "created_at": mr["created_at"],
        "updated_at": mr["updated_at"],
        "commits": commits,
        "files_changed": files_changed,
        "discussions": discussions,
    }
