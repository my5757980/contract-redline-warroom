"""Backend smoke test via FastAPI TestClient (no live server needed)."""
import asyncio
import os
os.environ.setdefault("SIMULATION", "1")
TOKEN = "smoke-test-reviewer-token-0123456789"
os.environ.setdefault("WARROOM_REVIEWERS", f"judge:{TOKEN}")

from fastapi.testclient import TestClient
from backend.main import app

c = TestClient(app)

print("health:", c.get("/api/health").json()["ok"])

r = c.post("/api/reviews", json={"use_sample": True}).json()
rid = r["review_id"]
print("started:", rid, "clauses:", len(r["clauses"]))

# the review runs as a background task; poll until the final packet appears
import time
for _ in range(50):
    got = c.get(f"/api/reviews/{rid}").json()
    if got.get("result"):
        break
    time.sleep(0.1)

pkt = got["result"]["packet"]
print("exposure:", pkt["exposure_score"], "rec:", pkt["recommendation"])

# the human gate refuses anyone without a reviewer token...
anon = c.post("/api/decision", json={"review_id": rid, "action": "approve"})
print("unauthenticated decision:", anon.status_code)

# ...and seals the chain for an authenticated reviewer
dec = c.post("/api/decision", json={"review_id": rid, "action": "reject", "note": "uncapped liability"},
             headers={"Authorization": f"Bearer {TOKEN}"}).json()
print("sealed:", dec["sealed"], "verify:", dec["verify"]["valid"])

# tamper-evidence still holds via API
v = c.get(f"/api/verify/{rid}").json()
print("verify endpoint:", v["valid"], "entries:", v.get("entries"))

n_events = len(c.get(f"/api/reviews/{rid}").json()["events"])
print("streamed events:", n_events)
print("OK" if (pkt["exposure_score"] > 0 and anon.status_code == 401 and dec["sealed"] and v["valid"])
      else "FAIL")
