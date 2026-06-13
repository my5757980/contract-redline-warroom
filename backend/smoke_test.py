"""Backend smoke test via FastAPI TestClient (no live server needed)."""
import asyncio
import os
os.environ.setdefault("SIMULATION", "1")

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

# human gate seals the chain
dec = c.post("/api/decision", json={"review_id": rid, "action": "reject",
                                    "reviewer": "judge", "note": "uncapped liability"}).json()
print("sealed:", dec["sealed"], "verify:", dec["verify"]["valid"])

# tamper-evidence still holds via API
v = c.get(f"/api/verify/{rid}").json()
print("verify endpoint:", v["valid"], "entries:", v.get("entries"))

n_events = len(c.get(f"/api/reviews/{rid}").json()["events"])
print("streamed events:", n_events)
print("OK" if (pkt["exposure_score"] > 0 and dec["sealed"] and v["valid"]) else "FAIL")
