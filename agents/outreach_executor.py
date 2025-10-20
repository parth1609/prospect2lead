from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log
import time


class OutreachExecutorAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        msgs = inputs.get("messages", [])
        provider = "apollo"
        for t in tools:
            if t.get("name", "").lower() == "sendgrid":
                provider = "sendgrid"
                break
        _log(memory, sid, "api_request", {"provider": provider})
        status = [{"lead": m.get("lead"), "status": "sent", "provider": provider} for m in msgs]
        campaign_id = f"cmp-{int(time.time())}"
        _log(memory, sid, "api_response", {"sent": len(status), "provider": provider})
        return {"sent_status": status, "campaign_id": campaign_id}
