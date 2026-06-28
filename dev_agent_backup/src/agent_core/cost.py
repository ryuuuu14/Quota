import os
import json
from datetime import datetime


class CostController:
    def __init__(self, budget_pct: float = 0.50):
        self.budget_pct = budget_pct
        self.log_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "docs",
            "logs",
        )
        self.budget_file = os.path.join(self.log_dir, "daily_budget.json")

        # Standard free-tier daily request limits (conservative estimates)
        self.limits = {
            "gemini-2.5-flash": 1500,
            "gemini-2.5-pro": 50,
            "gemini-2.0-flash": 1500,
            "openai-gpt-4o": 500,  # Fallback
        }

    def _load_data(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        default_data = {"date": today, "calls": {model: 0 for model in self.limits}}
        if not os.path.exists(self.budget_file):
            return default_data
        try:
            with open(self.budget_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") == today:
                    return data
                return default_data
        except Exception:
            return default_data

    def _save_data(self, data: dict):
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            with open(self.budget_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record_call(self, model: str):
        data = self._load_data()
        data["calls"][model] = data["calls"].get(model, 0) + 1
        self._save_data(data)

    def over_budget(self, model: str) -> bool:
        data = self._load_data()
        limit = self.limits.get(model, 1000)
        allowed = limit * self.budget_pct
        current = data["calls"].get(model, 0)
        return current >= allowed

    def select_model(self, complexity: str) -> str:
        # Check if planning can use gemini-2.5-pro
        if complexity == "planning":
            if not self.over_budget("gemini-2.5-pro"):
                return "gemini-2.5-pro"
            # Fallback to flash if pro is over budget
            return "gemini-2.5-flash"

        # Default routing
        if not self.over_budget("gemini-2.5-flash"):
            return "gemini-2.5-flash"
        return "gemini-2.0-flash"

    def can_proceed(self, model: str) -> bool:
        data = self._load_data()
        limit = self.limits.get(model, 1000)
        allowed = limit * self.budget_pct
        return data["calls"].get(model, 0) < allowed
