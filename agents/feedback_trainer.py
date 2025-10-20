from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log, _sanitize_tools
import time


class FeedbackTrainerAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        responses = inputs.get("responses", [])
        open_rate = 0.0
        reply_rate = 0.0
        recs: List[Dict[str, Any]] = []
        if reply_rate < 0.05:
            recs.append({"type": "scoring_weight_adjustment", "path": "scoring.weights.intent_score", "delta": 0.1})
            recs.append({"type": "messaging", "suggestion": "Test a more direct CTA in first sentence"})
        sheet_id = None
        for t in tools:
            if t.get("name") == "GoogleSheets":
                sheet_id = (t.get("config") or {}).get("sheet_id")
                break
        rows = [{"ts": int(time.time()), "open_rate": open_rate, "reply_rate": reply_rate, "recommendations": recs}]
        _log(memory, sid, "api_request", {"sheets": bool(sheet_id)})
        _log(memory, sid, "api_response", {"sheets_rows_written": len(rows)})
        return {"recommendations": recs, "sheets_write": {"sheet_id": sheet_id, "rows": len(rows)}, "approval": {"required": True, "status": "pending"}}
