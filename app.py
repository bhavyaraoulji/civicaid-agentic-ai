from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional

from civicaid_agent import run_civicaid

app = FastAPI(title="CivicAid Agentic AI")

# -------------------------
# CHAT REQUEST SCHEMA
# -------------------------
class ChatPayload(BaseModel):
    message: str
    state: Dict[str, Any] = {}

# -------------------------
# EVAL REQUEST SCHEMA
# -------------------------
class EvalPayload(BaseModel):
    input: str
    expected_domain: Optional[str] = None
    state: Dict[str, Any] = {}

# -------------------------
# HEALTH CHECK
# -------------------------
@app.get("/")
def health():
    return {"ok": True, "message": "CivicAid running locally"}

# -------------------------
# MAIN CHAT ENDPOINT
# -------------------------
@app.post("/chat")
async def chat(payload: ChatPayload):
    return await run_civicaid(payload.message, payload.state)

# -------------------------
# EVAL ENDPOINT (FOR DATASET ROWS)
# -------------------------
@app.post("/eval")
async def eval_one(payload: EvalPayload):
    # Put expected domain into state for tracking
    state = dict(payload.state or {})
    if payload.expected_domain:
        state["expected_domain"] = payload.expected_domain

    return await run_civicaid(payload.input, state)
