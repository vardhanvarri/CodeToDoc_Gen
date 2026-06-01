from flask import Flask, request

from pipeline import run_doc_pipeline

app = Flask(__name__)


@app.route("/")
def home():
    return "GitLab Webhook Server Running!", 200


@app.route("/webhook/gitlab", methods=["POST"])
def gitlab_webhook():
    payload = request.get_json(silent=True) or {}

    print("\nFULL PAYLOAD:\n")
    print(payload)
    print("\n")

    if payload.get("object_kind") != "note":
        return "Ignored - Not a comment event", 200

    object_attributes = payload.get("object_attributes", {})
    if object_attributes.get("noteable_type") != "MergeRequest":
        return "Ignored - Not a Merge Request comment", 200

    comment_text = object_attributes.get("note", "")
    if "/make-doc" not in comment_text:
        return "Ignored - No /make-doc command found", 200

    print("\n" + "=" * 80)
    print("/make-doc COMMAND DETECTED")
    print("=" * 80 + "\n")

    project_id = payload["project"]["id"]
    mr_iid = payload["merge_request"]["iid"]

    print(f"Project ID : {project_id}")
    print(f"MR IID     : {mr_iid}\n")

    success, message = run_doc_pipeline(project_id, mr_iid)

    print("\n" + "=" * 80)
    print("END OF PIPELINE")
    print("=" * 80 + "\n")

    if not success:
        status_code = 400 if message == "Failed to fetch MR" else 500
        return message, status_code

    return message, 200


application = app

if __name__ == "__main__":
    app.run(debug=True, port=5000)
