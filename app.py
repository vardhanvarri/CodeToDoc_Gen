import threading
import os
from flask import Flask, request
import os
from pipeline import run_doc_pipeline
import threading

app = Flask(__name__)


def _run_pipeline_background(project_id, mr_iid):
    try:
        success, message = run_doc_pipeline(project_id, mr_iid)
        print(f"Background pipeline done: success={success} message={message}")
    except Exception as exc:
        print(f"Background pipeline error: {exc}")


@app.route("/")
def home():
    return "GitLab Webhook Server Running!", 200

# Trigger function
@app.route("/webhook/gitlab", methods=["POST"])
def gitlab_webhook():
    payload = request.get_json(silent=True) or {}

    print("\nFULL PAYLOAD:\n")
    print(payload)
    print("\n")
 # necessary check when webhooks are triggered not only for comments. ------- note == comments
    if payload.get("object_kind") != "note":
        return "Ignored - Not a comment event", 200
# request has obeject attr (like authorid , mr_id...)
    object_attributes = payload.get("object_attributes", {})
# we dont need comments on commit/issues/ etc
    if object_attributes.get("noteable_type") != "MergeRequest":
        return "Ignored - Not a Merge Request comment", 200

    comment_text = object_attributes.get("note", "")
#### ------- check "/make-doc" --------------
    if "/make-doc" not in comment_text:
        return "Ignored - No /make-doc command found", 200

    print("\n" + "=" * 80)
    print("/make-doc COMMAND DETECTED")
    print("=" * 80 + "\n")

    project_id = payload["project"]["id"]
    mr_iid = payload["merge_request"]["iid"]

    print(f"Project ID : {project_id}")
    print(f"MR IID     : {mr_iid}\n")

    # GitLab webhook timeout is ~10s; pipeline (Groq + PlantUML + Confluence) takes longer.
    # Return 200 immediately so GitLab does not log Net::ReadTimeout.
    threading.Thread(
        target=_run_pipeline_background,
        args=(project_id, mr_iid),
        daemon=True,
    ).start()

    return "Accepted - documentation generation started", 200


application = app

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
