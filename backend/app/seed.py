import json
from pathlib import Path

from backend.memory.store import MemoryStore


def seed() -> None:
    store = MemoryStore()
    patients = json.loads(Path("data/sample_patients.json").read_text())
    for p in patients:
        store.upsert_patient(p["id"], p["name"], p["language_preference"])
    print(f"Seeded {len(patients)} patients")


if __name__ == "__main__":
    seed()
