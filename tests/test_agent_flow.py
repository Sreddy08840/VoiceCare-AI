from datetime import datetime, timedelta

from backend.agents.orchestrator import AgentOrchestrator
from backend.memory.store import MemoryStore
from backend.scheduling.service import SchedulingService


def test_book_confirm_flow(tmp_path):
    store = MemoryStore(tmp_path / "a.db")
    sched = SchedulingService(store)
    agent = AgentOrchestrator(store, sched)

    slot = (datetime.utcnow() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0).isoformat()
    ask = agent.handle_turn("s1", "p1", f"Book with Dr Meena at {slot}", "en")
    assert "confirm" in ask["text"].lower()
    done = agent.handle_turn("s1", "p1", "yes", "en")
    assert "booked" in done["text"].lower()
