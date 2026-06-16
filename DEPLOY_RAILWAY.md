# Deploy doc_gen on Railway

## 1. Create a Railway project

1. Push this repo to GitHub or GitLab.
2. In [Railway](https://railway.app), create a new project → **Deploy from GitHub/GitLab repo**.
3. Railway detects Python from `requirements.txt` and starts the app via the `Procfile`.

## 2. Set environment variables

In Railway → your service → **Variables**, add:

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | Optional (default: `llama-3.3-70b-versatile`) |
| `GITLAB_TOKEN` | GitLab personal access token |
| `GITLAB_URL` | Optional (default: `https://gitlab.com/api/v4`) |
| `CONFLUENCE_SITE` | Atlassian site URL |
| `CONFLUENCE_EMAIL` | Confluence user email |
| `CONFLUENCE_API_TOKEN` | Full Atlassian API token |
| `CONFLUENCE_PAGE_ID` | Target Confluence page ID |
| `PLANTUML_BASE_URL` | Optional PlantUML server URL |

Railway sets `PORT` automatically — do not override it.

## 3. Generate a public URL

Railway → service → **Settings** → **Networking** → **Generate Domain**.

### Verify

- `https://YOUR_APP.up.railway.app/` → `GitLab Webhook Server Running!`

## 4. GitLab webhook URL

```text
https://YOUR_APP.up.railway.app/webhook/gitlab
```

Trigger: **Comments** only.

## 5. Output artifacts

Each `/make-doc` run writes:

```text
output/mr_{iid}_{timestamp}/
  final_prompt.txt
  commits.txt
  diffs.txt
  discussions.txt
  generated_doc.html
  diagrams.json
  raw_response.json
  diagram_validation_errors.txt   (only if validation warnings)
```

Note: Railway ephemeral filesystem — artifacts are lost on redeploy. Confluence is the durable publish target.

## 6. Module layout

| File | Role |
|------|------|
| `app.py` | Flask routes (`application` WSGI entry) |
| `Procfile` | Gunicorn start command for Railway |
| `pipeline.py` | Orchestration |
| `config.py` | Env vars + JSON schema |
| `prompt_builder.py` | LLM prompt |
| `gitlab_client.py` | MR / commits / diffs / discussions |
| `groq_client.py` | Groq API + JSON parse |
| `confluence_client.py` | Confluence v2 publish |
| `diagram_utils.py` | Validate diagrams + HTML appendix |
