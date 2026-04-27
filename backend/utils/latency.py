import time
from dataclasses import dataclass, field


@dataclass
class LatencyProfiler:
    started_at: float = field(default_factory=time.perf_counter)
    stages: dict[str, float] = field(default_factory=dict)

    def mark(self, stage: str) -> None:
        now = time.perf_counter()
        self.stages[stage] = (now - self.started_at) * 1000

    def summary(self) -> dict[str, float]:
        out = {k: round(v, 2) for k, v in self.stages.items()}
        if self.stages:
            out["first_response_ms"] = max(out.values())
        return out
