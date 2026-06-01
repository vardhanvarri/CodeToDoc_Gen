# Deploy doc_gen on PythonAnywhere

## 1. Upload folder

Upload everything under `doc_gen/` to:

```text
/home/YOUR_USERNAME/doc_gen/
```

## 2. Install dependencies

```bash
cd ~/doc_gen
mkvirtualenv docgen --python=/usr/bin/python3.10
pip install -r requirements.txt
```

## 3. Create `.env`

```bash
cd ~/doc_gen
cp .env.example .env
nano .env
```

Fill in all keys (use the **full** Atlassian API token).

## 4. WSGI configuration (fix ImportError)

Your error happens when WSGI still says:

```python
from test import app as application   # WRONG after moving to doc_gen
```

Open **Web → WSGI configuration file** and **replace the whole file** with:

```python
import sys

sys.path.insert(0, "/home/vardhanvarri/doc_gen")

from app import application
```

Or copy from [`pythonanywhere_wsgi.py`](pythonanywhere_wsgi.py) in this folder.

**Do not** use `from test import app` — `doc_gen/app.py` defines `application` directly.

Select virtualenv `docgen` (or whichever has `flask`, `requests`, `python-dotenv` installed) and click **Reload**.

### Verify

- `https://vardhanvarri.pythonanywhere.com/` → `GitLab Webhook Server Running!`
- If ImportError persists: Bash → `ls /home/vardhanvarri/doc_gen/app.py` (folder must exist)

## 5. GitLab webhook URL

```text
https://YOUR_USERNAME.pythonanywhere.com/webhook/gitlab
```

Trigger: **Comments** only.

## 6. Output artifacts

Each `/make-doc` run writes:

```text
doc_gen/output/mr_{iid}_{timestamp}/
  final_prompt.txt
  commits.txt
  diffs.txt
  discussions.txt
  generated_doc.html
  diagrams.json
  raw_response.json
  diagram_validation_errors.txt   (only if validation warnings)
```

## 7. Module layout

| File | Role |
|------|------|
| `app.py` | Flask routes |
| `pipeline.py` | Orchestration |
| `config.py` | Env vars + JSON schema |
| `prompt_builder.py` | LLM prompt (synced with production rules) |
| `gitlab_client.py` | MR / commits / diffs / discussions |
| `groq_client.py` | Groq API + JSON parse |
| `confluence_client.py` | Confluence v2 publish |
| `diagram_utils.py` | Validate diagrams + HTML appendix |
