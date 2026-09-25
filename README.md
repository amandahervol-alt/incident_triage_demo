# Incident‑Triage Assistant Demo

## Overview
A **2‑3 min video demo** of an **incident‑triage assistant** built with **FastAPI** and **Claude (Anthropic) function‑calling**. The service:

1. Accepts raw log files (or log snippets) via a POST endpoint.
2. Performs lightweight pattern detection (error keyword extraction, frequency counts).
3. Calls Claude with a structured **function definition** (`suggest_rca`) to generate a concise Root‑Cause Analysis (RCA) based on the extracted context.
4. Returns the suggested RCA as JSON.

The demo is intentionally lightweight so you can spin it up locally, record a short walkthrough (e.g., using OBS), and showcase:
- Real‑time log ingestion.
- Automatic extraction of salient patterns.
- LLM‑driven reasoning and actionable suggestions.

---
## Quick Start
```bash
# 1. Clone / copy the demo folder
git clone <repo‑url> incident_triage_demo  # or copy the folder manually
cd incident_triage_demo

# 2. Install dependencies (Python 3.11+ recommended)
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Set your Anthropic API key (Claude)
export ANTHROPIC_API_KEY=your_key_here  # Windows: set ANTHROPIC_API_KEY=your_key_here

# 4. Run the FastAPI server
uvicorn main:app --reload --port 8000
```
The service will be available at `http://localhost:8000`.

---
## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/triage` | Accepts a JSON payload with a `logs` field (string). Returns extracted patterns and Claude‑generated RCA. |
| `GET`  | `/health` | Simple health check. |

---
## Sample Request
```json
POST http://localhost:8000/triage
Content-Type: application/json

{
  "logs": "[2026-09-24 22:30:12] ERROR DB_CONN_TIMEOUT: connection to postgres timed out after 30s\n[2026-09-24 22:30:15] WARN CacheMiss: key=user:1234 not found\n[2026-09-24 22:30:20] ERROR DB_CONN_TIMEOUT: connection to postgres timed out after 30s"
}
```
---
## Expected Response
```json
{
  "patterns": ["DB_CONN_TIMEOUT", "CacheMiss"],
  "rca": "The repeated DB_CONN_TIMEOUT errors indicate a network latency or database overload issue. Check PostgreSQL connection pool size and underlying network stability. The cache miss is a secondary symptom caused by failed DB lookups."
}
```
---
## Video Script (2‑3 min)
1. **Intro (10 s)** – Briefly state the goal: "Show an AI‑driven incident‑triage assistant that ingests logs and suggests RCA."
2. **Run the Service (20 s)** – Launch `uvicorn`, show the terminal.
3. **Send a Sample Log (30 s)** – Use `curl` or VS Code REST client to POST the sample logs. Highlight the request body.
4. **Show Response (20 s)** – Explain the extracted patterns and the LLM‑generated RCA.
5. **Talk Claude Function Call (30 s)** – Open `main.py`, point to the `suggest_rca` function schema and the `client.messages.create` call. Emphasize how the function‑calling API enforces structured output.
6. **Wrap‑Up (10 s)** – Summarize benefits: fast triage, consistent RCA, easy integration into existing monitoring pipelines.

---
## Next Steps (optional)
- Hook the service into a real log shipper (e.g., Fluentd) for continuous monitoring.
- Extend the function schema to include `severity`, `service_name`, or `suggested_fix` fields.
- Deploy to Cloud Run or Azure Functions for production use.

---
## License
MIT – feel free to adapt and extend.
