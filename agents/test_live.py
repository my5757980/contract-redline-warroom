"""Validate live Band credentials.

Run AFTER you've created the 5 External Agents at band.ai/agents and pasted their
agent_id + api_key into agent_config.yaml:

    uv run python -m agents.test_live

For each agent it calls the real Band identity endpoint (band_get_agent_me) to
confirm the key is valid and the agent is reachable. Then it does a tiny live
round-trip: Coordinator creates a chat room and recruits the specialists.
"""
from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from agents.common.band_client import load_creds

load_dotenv()


async def main():
    creds = load_creds()
    if not creds:
        print("✗ No usable credentials in agent_config.yaml (still placeholders?).")
        print("  Fill agent_id + api_key for coordinator/legal/risk/finance/compliance.")
        return

    from band.client.rest import AsyncRestClient, ChatRoomRequest, ParticipantRequest
    base = os.getenv("THENVOI_REST_URL", "https://app.band.ai").rstrip("/")

    print(f"Base URL: {base}\nValidating {len(creds)} agent key(s)...\n")
    ok = {}
    for name, c in creds.items():
        cli = AsyncRestClient(api_key=c["api_key"], base_url=base)
        try:
            me = await cli.agent_api_identity.get_agent_me()
            who = getattr(getattr(me, "agent", me), "name", None) or c["agent_id"][:8]
            print(f"  ✓ {name:<11} reachable as '{who}'")
            ok[name] = cli
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {name:<11} FAILED: {type(e).__name__}: {str(e)[:120]}")

    if "Coordinator" not in ok:
        print("\nCoordinator key invalid — cannot run the live round-trip.")
        return

    print("\nLive round-trip: Coordinator creates a room + recruits specialists...")
    coord = ok["Coordinator"]
    try:
        room = await coord.agent_api_chats.create_agent_chat(chat=ChatRoomRequest())
        room_id = getattr(room, "id", None) or getattr(getattr(room, "chat", None), "id", "?")
        print(f"  ✓ room created: {room_id}")
        for name in ("Legal", "Risk", "Finance", "Compliance"):
            if name in creds:
                await coord.agent_api_participants.add_agent_chat_participant(
                    room_id, participant=ParticipantRequest(
                        participant_id=creds[name]["agent_id"], role="member"))
                print(f"  ✓ recruited {name}")
        print("\n🎉 LIVE BAND CONNECTION WORKS. Set SIMULATION=0 and run the backend.")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ round-trip failed: {type(e).__name__}: {str(e)[:160]}")


if __name__ == "__main__":
    asyncio.run(main())
