from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log, _sanitize_tools


class ThirdPartyEnrichmentAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        leads = inputs.get("leads", [])
        out: List[Dict[str, Any]] = []
        for ld in leads:
            emails = [ld.get("email", "")] if ld.get("email") else []
            out.append({
                "company": ld.get("company", ""),
                "contact": ld.get("contact", ""),
                "role": ld.get("role", ""),
                "technologies": ld.get("technologies", []),
                "emails": emails,
                "email": ld.get("email", ""),
                "domain": ld.get("domain", ""),
                "signal": ld.get("signal", "")
            })
        _log(memory, sid, "api_response", {"augmented": len(out)})
        return {"enriched_leads": out}
