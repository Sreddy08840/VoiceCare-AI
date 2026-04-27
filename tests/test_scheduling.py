from datetime import datetime, timedelta

from backend.memory.store import MemoryStore
from backend.scheduling.service import SchedulingService


def test_booking_conflict(tmp_path):
    store = MemoryStore(tmp_path / "t.db")
    svc = SchedulingService(store)
    t = (datetime.utcnow() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0).isoformat()
    first = svc.book("p1", "dr_meena", t, "check")
    second = svc.book("p2", "dr_meena", t, "check")
    assert first["ok"]
    assert not second["ok"]
    assert "already booked" in second["message"].lower()


def test_cancel(tmp_path):
    store = MemoryStore(tmp_path / "t2.db")
    svc = SchedulingService(store)
    t = (datetime.utcnow() + timedelta(days=1)).replace(minute=0, second=0, microsecond=0).isoformat()
    ap = svc.book("p1", "dr_rao", t, "check")
    out = svc.cancel("p1", ap["appointment_id"])
    assert out["ok"]
