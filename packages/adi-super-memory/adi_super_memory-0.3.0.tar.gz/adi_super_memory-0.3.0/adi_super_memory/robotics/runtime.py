from dataclasses import dataclass
@dataclass(frozen=True)
class RealTimePolicy:
    max_plan_latency_ms: int = 50
    max_action_latency_ms: int = 20
    fail_closed: bool = True
