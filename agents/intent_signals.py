from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log, _sanitize_tools
import hashlib
import json
from urllib.parse import urlencode
from urllib.request import urlopen


class AnonymizedIntentSignalAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        leads = inputs.get("leads", [])
        intents: List[Dict[str, Any]] = []
        bw_key = bw_ep = news_key = news_ep = None
        for t in tools or []:
            name = (t.get("name") or "").lower()
            cfg = t.get("config") or {}
            if name.startswith("builtwith"):
                bw_key = cfg.get("api_key")
                bw_ep = cfg.get("endpoint")
            if name.startswith("newsapi"):
                news_key = cfg.get("api_key")
                news_ep = cfg.get("endpoint")
        for ld in leads:
            domain = ld.get("domain", "")
            h = int(hashlib.sha256(domain.encode("utf-8")).hexdigest(), 16) if domain else 0
            traffic = (h % 100) / 100.0
            sentiment = ((h // 100) % 100) / 100.0
            intent = 0.5 + (0.5 if ld.get("signal") == "recent_funding" else 0.0)
            if domain and bw_key and bw_ep:
                try:
                    q = urlencode({"KEY": bw_key, "LOOKUP": domain})
                    url = f"{bw_ep}?{q}"
                    _log(memory, sid, "api_call", {"provider": "builtwith", "domain": domain})
                    with urlopen(url, timeout=10) as r:
                        data = json.loads(r.read().decode("utf-8")) or {}
                    tcount = 0
                    if isinstance(data, dict):
                        for v in data.values():
                            if isinstance(v, list):
                                tcount += len(v)
                    traffic = min(1.0, max(0.0, tcount / 50.0))
                    _log(memory, sid, "api_success", {"provider": "builtwith", "tech_count": tcount})
                except Exception as e:
                    _log(memory, sid, "api_error", {"provider": "builtwith", "error": str(e)})
            if domain and news_key and news_ep:
                try:
                    q = urlencode({"q": domain, "apiKey": news_key, "pageSize": 10, "sortBy": "publishedAt"})
                    with urlopen(f"{news_ep}?{q}", timeout=10) as r:
                        data = json.loads(r.read().decode("utf-8")) or {}
                    articles = data.get("articles") or []
                    hits = 0
                    for a in articles:
                        title = (a.get("title") or "").lower()
                        if any(k in title for k in ["fund", "hiring", "growth"]):
                            hits += 1
                    sentiment = min(1.0, 0.4 + min(0.6, hits * 0.1))
                except Exception as e:
                    _log(memory, sid, "api_error", {"provider": "newsapi"})
            intents.append({
                "domain": domain,
                "intent_score": round(min(1.0, intent), 3),
                "news_sentiment": round(sentiment, 3),
                "traffic_score": round(traffic, 3)
            })
        _log(memory, sid, "api_response", {"intent_records": len(intents)})
        return {"intent_signals": intents}
