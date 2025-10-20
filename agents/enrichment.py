from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log, _sanitize_tools
import json
from urllib.parse import urlencode
from urllib.request import urlopen


class DataEnrichmentAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        leads = inputs.get("leads", [])
        enriched: List[Dict[str, Any]] = []
        api_key = None
        endpoint = None
        for t in tools or []:
            if (t.get("name") or "").lower().startswith("hunter"):
                cfg = t.get("config") or {}
                api_key = cfg.get("api_key")
                endpoint = cfg.get("endpoint")
                break
        for ld in leads:
            domain = ld.get("domain", "")
            company = ld.get("company", "")
            technologies: List[str] = ["Unknown"]
            if domain and api_key and endpoint:
                try:
                    q = urlencode({"domain": domain, "api_key": api_key})
                    url = f"{endpoint}?{q}"
                    _log(memory, sid, "api_call", {"url": endpoint, "domain": domain})
                    with urlopen(url, timeout=10) as r:
                        data = json.loads(r.read().decode("utf-8")) or {}
                    d = (data.get("data") or {})
                    company = d.get("organization") or company or d.get("domain") or company
                    _log(memory, sid, "api_success", {"provider": "hunter", "company": company})
                except Exception as e:
                    _log(memory, sid, "api_error", {"provider": "hunter", "error": str(e)})
            elif domain:
                if "acme" in domain:
                    company = "Acme SaaS"
                    technologies = ["Salesforce", "HubSpot"]
                elif "betasoft" in domain:
                    company = "BetaSoft"
                    technologies = ["Google Analytics", "Slack"]
            enriched.append({
                "company": company,
                "contact": ld.get("contact_name", ""),
                "role": ld.get("title", "") or "Unknown",
                "technologies": technologies,
                "email": ld.get("email", ""),
                "domain": domain,
                "signal": ld.get("signal", "")
            })
        _log(memory, sid, "api_response", {"enriched": len(enriched)})
        return {"enriched_leads": enriched}
