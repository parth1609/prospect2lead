from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log


class LLMPreEnrichmentAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        _log(memory, sid, "reasoning", {"note": "normalize and infer missing fields"})
        leads = inputs.get("leads", [])
        out_leads: List[Dict[str, Any]] = []
        for ld in leads:
            email = ld.get("email", "")
            domain = email.split("@")[1] if "@" in email else ""
            out_leads.append({
                "company": ld.get("company", ""),
                "domain": domain,
                "contact_name": ld.get("contact_name", ""),
                "title": ld.get("title", ""),
                "email": email,
                "signal": ld.get("signal", "")
            })
        clusters = [{"label": "default", "lead_ids": list(range(len(out_leads)))}]
        _log(memory, sid, "intermediate", {"normalized": len(out_leads)})
        return {"leads": out_leads, "clusters": clusters}
