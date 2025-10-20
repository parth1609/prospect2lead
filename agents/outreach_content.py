from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log


class OutreachContentAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        _log(memory, sid, "reasoning", {"note": "generating personalized emails"})
        leads = inputs.get("ranked_leads", [])
        persona = inputs.get("persona", "SDR")
        tone = inputs.get("tone", "friendly")
        msgs: List[Dict[str, Any]] = []
        for ld in leads:
            cn = ld.get("contact") or ld.get("contact_name") or "there"
            company = ld.get("company", "your team")
            body = f"Hi {cn}, we help {company} accelerate outbound with LLM agents. Would you be open to a quick chat?"
            if tone == "friendly":
                body += " Thanks!"
            msgs.append({"lead": ld.get("email") or (ld.get("emails", [""]) or [""])[0], "email_body": body, "persona": persona})
        _log(memory, sid, "intermediate", {"messages": len(msgs)})
        return {"messages": msgs}
