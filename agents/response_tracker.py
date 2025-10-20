from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log


class ResponseTrackerAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        cid = inputs.get("campaign_id")
        _log(memory, sid, "api_request", {"provider": "apollo", "campaign_id": cid})
        responses: List[Dict[str, Any]] = []
        for s in memory.get("send", {}).get("output", {}).get("sent_status", []):
            responses.append({"lead": s.get("lead"), "opened": False, "clicked": False, "replied": False})
        _log(memory, sid, "api_response", {"responses": len(responses)})
        return {"responses": responses}
