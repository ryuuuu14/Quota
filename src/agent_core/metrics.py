import time
from dataclasses import dataclass, asdict
import json
import os

@dataclass
class AgentMetrics:
    agent_name: str
    pipeline_name: str
    duration_ms: float
    tokens_in: int
    tokens_out: int
    model_used: str
    cache_hit: bool

class MetricsCollector:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MetricsCollector, cls).__new__(cls, *args, **kwargs)
            cls._instance.metrics = []
        return cls._instance

    def log_call(self, agent_name: str, pipeline_name: str, duration_ms: float, tokens_in: int, tokens_out: int, model_used: str, cache_hit: bool = False):
        m = AgentMetrics(
            agent_name=agent_name,
            pipeline_name=pipeline_name,
            duration_ms=duration_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model_used=model_used,
            cache_hit=cache_hit
        )
        self.metrics.append(m)
        self.save_to_log(m)

    def save_to_log(self, m: AgentMetrics):
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "docs", "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "agent_metrics.jsonl")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(m), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def get_summary(self) -> dict:
        total_tokens_in = sum(m.tokens_in for m in self.metrics)
        total_tokens_out = sum(m.tokens_out for m in self.metrics)
        total_duration = sum(m.duration_ms for m in self.metrics)
        hits = sum(1 for m in self.metrics if m.cache_hit)
        total = len(self.metrics)
        hit_rate = (hits / total) if total > 0 else 0.0

        return {
            "total_calls": total,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_duration_ms": total_duration,
            "cache_hit_rate": hit_rate,
            "metrics_detail": [asdict(m) for m in self.metrics]
        }

    def clear(self):
        self.metrics.clear()
