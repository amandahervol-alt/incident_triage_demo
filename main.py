import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic, AIMessage, ToolResult

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY not set in environment")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

app = FastAPI()

class LogRequest(BaseModel):
    logs: str

# Define the function schema that Claude will call
function_schema = {
    "name": "suggest_rca",
    "description": "Generate a concise Root‑Cause Analysis (RCA) based on extracted log patterns.",
    "parameters": {
        "type": "object",
        "properties": {
            "patterns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of distinct error or warning patterns detected in the logs."
            },
            "rca": {
                "type": "string",
                "description": "Brief, actionable root‑cause analysis using the patterns."
            }
        },
        "required": ["patterns", "rca"]
    }
}

def extract_patterns(log_text: str) -> list[str]:
    """Very lightweight pattern extraction.
    For demo purposes we simply pull uppercase words that look like error codes.
    """
    import re
    # Find tokens like DB_CONN_TIMEOUT, CACHE_MISS, etc.
    matches = re.findall(r"[A-Z_]{2,}", log_text)
    # Return unique list preserving order
    seen = set()
    uniq = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            uniq.append(m)
    return uniq

@app.post("/triage")
async def triage(request: LogRequest):
    # 1. Extract patterns
    patterns = extract_patterns(request.logs)
    if not patterns:
        raise HTTPException(status_code=400, detail="No recognizable patterns found in logs.")

    # 2. Build the prompt for Claude, ask it to call the function
    user_message = AIMessage(
        content=f"Given the following log patterns: {patterns}, provide a concise RCA."
    )

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        temperature=0,
        system="You are an expert incident‑triage assistant. Use the provided function to return a structured RCA.",
        messages=[user_message],
        tools=[function_schema]
    )

    # Claude should respond with a tool call; we extract the arguments
    if response.content[0].type != "tool_use":
        # fallback – if for some reason no tool call, just return plain text
        return {"patterns": patterns, "rca": response.content[0].text}

    tool_call = response.content[0]
    args = tool_call.input
    # The function schema guarantees both fields exist
    return {"patterns": args["patterns"], "rca": args["rca"]}

@app.get("/health")
async def health():
    return {"status": "ok"}
