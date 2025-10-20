from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log, _sanitize_tools
import json
from urllib.parse import urlencode
from urllib.request import urlopen


class EmailVerificationAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        leads = inputs.get("leads", [])
        criteria = memory.get("config", {}).get("scoring", {}).get("criteria", {})
        allow_free = criteria.get("email_requirements", {}).get("allow_free_providers", False)
        free_domains = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com"}
        verified: List[Dict[str, Any]] = []
        api_key = None
        endpoint = None
        for t in tools or []:
            if (t.get("name") or "").lower().startswith("hunter"):
                cfg = t.get("config") or {}
                api_key = cfg.get("api_key")
                endpoint = cfg.get("endpoint")
                break
        for ld in leads:
            email = ld.get("email") or (ld.get("emails", [""]) or [""])[0]
            domain = email.split("@")[-1] if email and "@" in email else ""
            if not email or "@" not in email or not domain:
                continue
            if api_key and endpoint:
                try:
                    q = urlencode({"email": email, "api_key": api_key})
                    with urlopen(f"{endpoint}?{q}", timeout=10) as r:
                        data = json.loads(r.read().decode("utf-8")) or {}
                    d = (data.get("data") or {})
                    webmail = bool(d.get("webmail"))
                    result = (d.get("result") or "").lower()
                    if not allow_free and webmail:
                        continue
                    if result == "undeliverable":
                        continue
                    verified.append(ld)
                    continue
                except Exception:
                    pass
            if not allow_free and domain in free_domains:
                continue
            verified.append(ld)
        _log(memory, sid, "api_response", {"verified": len(verified)})
        return {"verified_leads": verified}
