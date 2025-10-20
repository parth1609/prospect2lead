from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log


class FeedbackApplyAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        auto = inputs.get("auto_apply", False)
        updated = dict(inputs.get("current_config", {}))
        approved = False
        if isinstance(inputs.get("approval"), dict):
            approved = inputs.get("approval", {}).get("status") == "approved"
        if auto or approved:
            for r in inputs.get("recommendations", []):
                if r.get("type") == "scoring_weight_adjustment" and r.get("path") and isinstance(r.get("delta"), (int, float)):
                    path = r["path"].split(".")
                    cur = updated
                    for k in path[:-1]:
                        cur = cur.setdefault(k, {})
                    cur[path[-1]] = float(cur.get(path[-1], 0)) + float(r["delta"])
            memory["config"] = updated
            _log(memory, sid, "intermediate", {"applied": True})
            return {"updated_config": updated, "applied": True}
        _log(memory, sid, "intermediate", {"applied": False})
        return {"updated_config": updated, "applied": False}
