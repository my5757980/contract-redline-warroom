"""Model router for the War Room agents.

Two partner gateways are first-class (both are OpenAI-compatible):

  * AI/ML API   — PRIMARY reasoning/orchestration gateway for every agent
                  (qualifies for "Best Use of AI/ML API").
  * Featherless — serverless OPEN-SOURCE inference, used for the Compliance
                  agent's clause-classification path
                  (qualifies for "Best Use of Featherless AI").

Every call records which provider answered, so the README / audit can prove
both partners were genuinely exercised. If a partner key is missing or the call
fails, a deterministic local stub keeps the demo alive and the result is marked
`degraded=True`.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import httpx

# provider-usage tally (partner-prize evidence)
USAGE: dict[str, int] = {"aimlapi": 0, "featherless": 0, "stub": 0}


@dataclass
class LLMResult:
    text: str
    provider: str
    degraded: bool = False
    raw: dict = field(default_factory=dict)


def _chat(base_url: str, api_key: str, model: str, system: str, user: str,
          provider: str, temperature: float = 0.2, timeout: float = 45.0) -> LLMResult:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    text = data["choices"][0]["message"]["content"]
    USAGE[provider] = USAGE.get(provider, 0) + 1
    return LLMResult(text=text, provider=provider, raw=data)


def reason(system: str, user: str, temperature: float = 0.2) -> LLMResult:
    """Primary path → AI/ML API. Used by Coordinator/Legal/Risk/Finance."""
    key = os.getenv("AIML_API_KEY", "")
    base = os.getenv("AIML_BASE_URL", "https://api.aimlapi.com/v1")
    model = os.getenv("AIML_MODEL", "gpt-4o")
    if key and not key.startswith("your-"):
        try:
            return _chat(base, key, model, system, user, provider="aimlapi", temperature=temperature)
        except Exception as e:  # noqa: BLE001
            return _stub(system, user, note=f"aimlapi error: {e}")
    return _stub(system, user, note="aimlapi key missing")


def classify(system: str, user: str, temperature: float = 0.0) -> LLMResult:
    """Specialist path → Featherless AI (open-source model). Used by Compliance."""
    key = os.getenv("FEATHERLESS_API_KEY", "")
    base = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
    model = os.getenv("FEATHERLESS_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct")
    if key and not key.startswith("your-"):
        try:
            return _chat(base, key, model, system, user, provider="featherless", temperature=temperature)
        except Exception as e:  # noqa: BLE001
            return _stub(system, user, note=f"featherless error: {e}")
    return _stub(system, user, note="featherless key missing")


# ── deterministic fallback so the workflow never hard-fails in judging ─────
def _stub(system: str, user: str, note: str = "") -> LLMResult:
    USAGE["stub"] = USAGE.get("stub", 0) + 1
    # Heuristic, schema-aware stub: returns plausible structured findings so the
    # multi-agent choreography is fully demoable offline. Replaced by real
    # partner output the moment keys are present.
    low = user.lower()
    sys_l = system.lower()
    payload: dict = {}
    # Dispatch on the agent's distinctive role phrase (robust to overlapping words
    # like "legal redlines" appearing inside the Risk prompt).
    if "legal counsel" in sys_l:
        payload = {
            "findings": [
                {"section": "8.2", "issue": "Liability is uncapped", "severity": "high",
                 "suggested": "Cap aggregate liability at 12 months of fees",
                 "citation": "Neither party's liability shall be limited..."},
                {"section": "3.1", "issue": "Auto-renewal with 90-day notice", "severity": "medium",
                 "suggested": "Reduce notice window to 30 days; add opt-out",
                 "citation": "This Agreement renews automatically for successive..."},
            ]
        }
    elif "risk officer" in sys_l:
        payload = {"severity": "high", "exposure_usd": 500000,
                   "rationale": "Uncapped liability + data-breach indemnity",
                   "citation": "Customer shall indemnify Provider for any breach..."}
    elif "finance controller" in sys_l:
        payload = {"annual_value_usd": 240000, "worst_case_usd": 740000,
                   "penalties": "5% late fee/mo", "citation": "Fees are $20,000 per month..."}
    elif "compliance officer" in sys_l:
        verdict = "FAIL" if ("data" in low or "gdpr" in low or "personal" in low) else "PASS"
        payload = {"verdict": verdict,
                   "required_addenda": ["GDPR DPA", "EU data-residency rider"] if verdict == "FAIL" else [],
                   "veto": verdict == "FAIL",
                   "citation": "Provider may process Customer personal data..."}
    else:
        payload = {"note": "coordinator stub", "ok": True}
    return LLMResult(text=json.dumps(payload), provider="stub", degraded=True,
                     raw={"note": note})


def usage_report() -> dict:
    total = sum(USAGE.values()) or 1
    return {k: {"calls": v, "pct": round(100 * v / total)} for k, v in USAGE.items()}


def extract_json(text: str) -> dict:
    """Best-effort JSON extraction from a model reply."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except Exception:  # noqa: BLE001
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except Exception:  # noqa: BLE001
                pass
    return {"_unparsed": text}
