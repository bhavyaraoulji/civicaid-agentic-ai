import os
import re
from typing import Dict, Any, Tuple

from dotenv import load_dotenv

import opik
from google import genai
from google.genai import types


load_dotenv()

# =========
# ENV
# =========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

OPIK_PROJECT_NAME = os.getenv("OPIK_PROJECT_NAME", "civicaid")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

# =========
# Configure Opik safely (SDK versions differ)
# =========
# Opik supports configuring via env/config file; project name can be set for traces. :contentReference[oaicite:1]{index=1}
try:
    opik.configure(project_name=OPIK_PROJECT_NAME)
except TypeError:
    # Older/newer SDK: ignore kwargs mismatch; rely on ~/.opik.config + env.
    pass

# =========
# Gemini client (new SDK)
# =========
# New SDK import + client creation pattern. :contentReference[oaicite:2]{index=2}
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTIONS = """
You are CivicAid, a civic assistance helper.
Goals:
- Provide immediate next steps, a short checklist, and official starting links.
- Ask 1-3 clarifying questions only if needed.
- Prefer official sources (211, HUD, VA, USCIS, state/local gov).
- Be cautious: general info only, not legal advice.
Format:
1) QUICK SUMMARY (2-3 lines)
2) NEXT STEPS (bullets)
3) CHECKLIST (bullets)
4) OFFICIAL LINKS (bullets)
5) SAFETY NOTE (1 line)
"""


def route_domain(user_message: str) -> str:
    """
    Deterministic router (no LLM call — saves quota).
    """
    msg = user_message.lower()

    if any(k in msg for k in ["uscis", "i-485", "i-130", "i-765", "rfe", "i-94", "visa", "work permit", "ead", "green card"]):
        return "immigration"
    if any(k in msg for k in ["veteran", "va", "dd214", "disability", "gi bill", "vfw"]):
        return "veterans"
    if any(k in msg for k in ["eviction", "landlord", "notice", "court date", "rent", "housing", "shelter"]):
        return "housing"
    if any(k in msg for k in ["utility", "electric", "water", "gas", "shut off", "disconnection", "bill"]):
        return "utilities"
    if any(k in msg for k in ["snap", "food stamps", "pantry", "wic", "meal", "groceries"]):
        return "food"
    return "general"


def official_links_for(domain: str) -> list[str]:
    base = [
        "https://www.211.org/",
        "https://www.usa.gov/",
    ]
    domain_links = {
        "veterans": ["https://www.va.gov/"],
        "immigration": ["https://www.uscis.gov/"],
        "housing": ["https://www.hud.gov/"],
        "utilities": ["https://www.211.org/"],
        "food": ["https://www.fns.usda.gov/snap"],
        "general": [],
    }
    return base + domain_links.get(domain, [])


def _build_prompt(user_message: str, domain: str, state: Dict[str, Any]) -> str:
    loc = state.get("location", "")  # optional
    extra = ""
    if loc:
        extra = f"\nUser location context: {loc}\n"

    links = "\n".join(f"- {u}" for u in official_links_for(domain))

    return f"""{SYSTEM_INSTRUCTIONS}

Domain: {domain}
{extra}
User message: {user_message}

Include these OFFICIAL LINKS at minimum:
{links}
"""


@opik.track(name="civicaid.chat")
async def run_civicaid(user_message: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entrypoint called by FastAPI.
    Returns: { reply: str, state: dict }
    """
    domain = route_domain(user_message)
    prompt = _build_prompt(user_message, domain, state or {})

    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=600,
            ),
        )
        reply_text = (resp.text or "").strip()
        demo_fallback = False

    except Exception as e:
        # Quota/model errors: return a helpful fallback, but still trace the request.
        demo_fallback = True
        err = str(e)
        reply_text = (
            "QUICK SUMMARY\n"
            "CivicAid can help you map out safe next steps and what to gather. "
            f"(Demo fallback: Gemini unavailable — {err[:180]})\n\n"
            "NEXT STEPS\n"
            "- Confirm your city/state and any deadlines (notice date, shutoff date, hearing date).\n"
            "- Call 211 and ask for local emergency programs for your situation.\n"
            "- If a shutoff/eviction is within 72 hours, ask for “emergency assistance” / “crisis funds.”\n"
            "- Gather IDs + notices + case numbers before contacting agencies.\n"
            "- Track each call: date, agency, reference number, next action.\n\n"
            "CHECKLIST\n"
            "- Photo ID\n"
            "- Proof of address\n"
            "- Any notices (shutoff/eviction/USCIS)\n"
            "- Income proof (pay stubs/benefits letter)\n"
            "- Household info\n\n"
            "OFFICIAL LINKS\n"
            + "\n".join(f"- {u}" for u in official_links_for(domain))
            + "\n\nSAFETY NOTE\nGeneral info only, not legal advice.\n"
        )

    new_state = dict(state or {})
    new_state["domain"] = domain
    new_state["demo_fallback"] = demo_fallback

    return {"reply": reply_text, "state": new_state}
