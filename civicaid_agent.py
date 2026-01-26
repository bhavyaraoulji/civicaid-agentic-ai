import os
import json
import warnings
from dotenv import load_dotenv

from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from opik.integrations.adk import OpikTracer

warnings.filterwarnings("ignore")
load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found. Put it in .env")

# If both GOOGLE_API_KEY and GEMINI_API_KEY exist, prefer GOOGLE_API_KEY.
if os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ.pop("GEMINI_API_KEY", None)

# --- OPIK TRACER (INSTRUMENTATION)
opik_tracer = OpikTracer(
    name="civicaid-agent-system",
    tags=["civicaid", "demo", "multi-agent", "civic", "veterans", "immigration", "housing"],
    metadata={"environment": "demo", "version": "0.1.0"},
    project_name="civicaid"
)

# --- TOOLS (MVP: TRUSTED STARTING POINTS)
def trusted_resource_stub(domain: str, location: str | None) -> str:
    """
    Returns a small set of trusted, official starting points.
    (In v2 you can replace with real retrieval/search.)
    """
    loc = location or "your city/state"
    if domain == "veteran":
        return (
            f"- VA (start here): https://www.va.gov/\n"
            f"- VA health care: https://www.va.gov/health-care/\n"
            f"- Find VA locations near {loc}: https://www.va.gov/find-locations/\n"
            f"- Veterans Crisis Line: https://www.veteranscrisisline.net/"
        )
    if domain == "immigration":
        return (
            f"- USCIS (official): https://www.uscis.gov/\n"
            f"- Find legal aid (directory): https://www.immigrationadvocates.org/nonprofit/legaldirectory/\n"
            f"- Avoid immigration scams (USCIS): https://www.uscis.gov/avoid-scams"
        )
    if domain == "housing":
        return (
            f"- Find local help (211): https://www.211.org/\n"
            f"- HUD housing counseling: https://www.hud.gov/findacounselor\n"
            f"- Emergency help near {loc}: https://www.211.org/"
        )
    return "- Start with your city/county official website + 211: https://www.211.org/"

# --- AGENT INSTRUCTIONS
INTAKE_INSTRUCTION = """
You are CivicAid Intake & Routing Agent.
Your job: classify the civic scenario and collect minimal missing info.

Return ONLY valid JSON with this schema:
{
  "domain": "veteran|immigration|housing|other",
  "need_more_info": true/false,
  "question": "string or null",
  "slots": {
    "location": "string or null",
    "urgency": "string or null",
    "veteran": true/false/null
  }
}

Rules:
- Ask ONLY ONE short question if info is missing.
- If user mentions self-harm, immediate danger, or crisis, set urgency="crisis".
- If location is missing, ask for city/state.
"""

NAVIGATOR_INSTRUCTION = """
You are CivicAid Navigator Agent.
You receive state keys: domain, location, urgency, veteran, user_message.
You MUST produce:
- steps (bullet list)
- checklist (bullet list)
- links (use the tool output as trusted starting points)
- safety note (no legal advice; verify official sources)

Return ONLY valid JSON:
{
  "summary": "string",
  "steps": ["..."],
  "checklist": ["..."],
  "links_markdown": "string",
  "safety_note": "string"
}

Rules:
- No legal advice. Use “general information” wording.
- For immigration: advise consulting qualified nonprofit/attorney for case-specific advice.
- If crisis: include safety-first guidance and relevant crisis resources.
"""

# --- CREATE ADK AGENTS (WITH OPIK CALLBACKS)
intake_agent = Agent(
    name="IntakeRouterAgent",
    model="gemini-2.0-flash-exp",
    instruction=INTAKE_INSTRUCTION,
    output_key="intake",
    before_agent_callback=opik_tracer.before_agent_callback,
    after_agent_callback=opik_tracer.after_agent_callback,
    before_model_callback=opik_tracer.before_model_callback,
    after_model_callback=opik_tracer.after_model_callback,
    before_tool_callback=opik_tracer.before_tool_callback,
    after_tool_callback=opik_tracer.after_tool_callback,
)

navigator_agent = Agent(
    name="NavigatorAgent",
    model="gemini-2.0-flash-exp",
    instruction=NAVIGATOR_INSTRUCTION,
    tools=[trusted_resource_stub],
    output_key="nav",
    before_agent_callback=opik_tracer.before_agent_callback,
    after_agent_callback=opik_tracer.after_agent_callback,
    before_model_callback=opik_tracer.before_model_callback,
    after_model_callback=opik_tracer.after_model_callback,
    before_tool_callback=opik_tracer.before_tool_callback,
    after_tool_callback=opik_tracer.after_tool_callback,
)

pipeline = SequentialAgent(
    name="CivicAidPipeline",
    sub_agents=[intake_agent, navigator_agent],
    description="Sequential civic workflow: intake -> navigation"
)

runner = InMemoryRunner(agent=pipeline)

async def run_civicaid(user_message: str, state: dict | None = None) -> dict:
    """
    Runs the ADK pipeline and returns:
    {
      "reply": "...",
      "state": {...}
    }
    """
    state = state or {}

    # Keep the state minimal but include the message for the navigator.
    initial_state = dict(state)
    initial_state["user_message"] = user_message

    result = await runner.run_async(
        messages=[types.Content(role="user", parts=[types.Part(text=user_message)])],
        state=initial_state
    )

    st = result.state or {}
    intake = st.get("intake")
    nav = st.get("nav")

    # Normalize JSON outputs
    if isinstance(intake, str):
        intake = json.loads(intake)

    if intake and intake.get("need_more_info"):
        # update state with slots and domain
        slots = intake.get("slots") or {}
        new_state = {**state, **{k: v for k, v in slots.items() if v is not None}, "domain": intake.get("domain")}
        return {
            "reply": intake.get("question") or "What city/state are you in?",
            "state": new_state
        }

    if isinstance(nav, str):
        nav = json.loads(nav)

    reply = (
        f"{nav.get('summary','')}\n\n"
        f"STEPS:\n- " + "\n- ".join(nav.get("steps", [])) + "\n\n"
        f"CHECKLIST:\n- " + "\n- ".join(nav.get("checklist", [])) + "\n\n"
        f"TRUSTED STARTING POINTS:\n{nav.get('links_markdown','')}\n\n"
        f"{nav.get('safety_note','')}"
    )

    # Flush traces so Opik UI updates quickly.
    try:
        opik_tracer.flush()
    except Exception:
        pass

    # Keep only core state keys
    keep_keys = ["domain", "location", "urgency", "veteran"]
    compact_state = {k: st.get(k) for k in keep_keys if st.get(k) is not None}
    return {"reply": reply.strip(), "state": compact_state}
