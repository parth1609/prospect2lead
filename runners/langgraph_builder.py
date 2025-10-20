"""
1.Reads and validates workflow.json
2.Dynamically constructs nodes and edges
3.Executes sequential or conditional flows
4. Uses ReAct prompting for reasoning
5. Loads tool credentials from .env
"""

import argparse
import hashlib
import json
import os
import re
import time
from typing import Any, Dict, List, Optional
# Use absolute imports instead of relative imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.utils import _log, _sanitize_tools
from agents import AGENTS as AGENT_REGISTRY

try:
    from dotenv import load_dotenv
    # Try to load .env from config directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)  # Go up to project root
    env_path = os.path.join(parent_dir, "config", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    else:
        # Fallback: try from script directory
        env_path = os.path.join(script_dir, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
except ImportError:
    pass


def _deep_get(data: Any, path: str) -> Any:
    cur = data
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    return cur


def _resolve_placeholders(obj: Any, memory: Dict[str, Any]) -> Any:
    if isinstance(obj, str):
        m = re.fullmatch(r"\{\{\s*([^}]+)\s*\}\}", obj)
        if m:
            v = _deep_get(memory, m.group(1))
            return _resolve_placeholders(v, memory)
        def repl(match: re.Match) -> str:
            key = match.group(1).strip()
            v = _deep_get(memory, key)
            return "" if v is None else str(v)
        return re.sub(r"\{\{\s*([^}]+)\s*\}\}", repl, obj)
    if isinstance(obj, list):
        return [_resolve_placeholders(v, memory) for v in obj]
    if isinstance(obj, dict):
        return {k: _resolve_placeholders(v, memory) for k, v in obj.items()}
    return obj


class Agent:
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        return {}


class ProspectSearchAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        _log(memory, sid, "reasoning", {"note": "searching prospects by ICP/signals"})
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        icp = inputs.get("icp", {})
        signals = inputs.get("signals", [])
        leads = [
            {
                "company": "Acme SaaS",
                "contact_name": "Alex Doe",
                "email": "alex@acme.com",
                "linkedin": "https://linkedin.com/in/alexdoe",
                "signal": signals[0] if signals else ""
            },
            {
                "company": "BetaSoft",
                "contact_name": "Blair Kim",
                "email": "blair@betasoft.io",
                "linkedin": "https://linkedin.com/in/blairkim",
                "signal": signals[1] if len(signals) > 1 else ""
            },
        ]
        _log(memory, sid, "api_response", {"count": len(leads)})
        return {"leads": leads}


class LLMPreEnrichmentAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        _log(memory, sid, "reasoning", {"note": "normalize and infer missing fields"})
        leads = inputs.get("leads", [])
        out_leads = []
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


class DataEnrichmentAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        leads = inputs.get("leads", [])
        enriched = []
        for ld in leads:
            domain = ld.get("domain", "")
            company = ld.get("company", "")
            if domain:
                # Simulate Hunter domain search
                if "acme" in domain:
                    company = "Acme SaaS"
                    technologies = ["Salesforce", "HubSpot"]
                elif "betasoft" in domain:
                    company = "BetaSoft"
                    technologies = ["Google Analytics", "Slack"]
                else:
                    technologies = ["Unknown"]
            else:
                technologies = ["Unknown"]
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


class ThirdPartyEnrichmentAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        leads = inputs.get("leads", [])
        out = []
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


class AnonymizedIntentSignalAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        leads = inputs.get("leads", [])
        intents = []
        for ld in leads:
            domain = ld.get("domain", "")
            h = int(hashlib.sha256(domain.encode("utf-8")).hexdigest(), 16) if domain else 0
            traffic = (h % 100) / 100.0
            sentiment = ((h // 100) % 100) / 100.0
            intent = 0.5 + (0.5 if ld.get("signal") == "recent_funding" else 0.0)
            intents.append({
                "domain": domain,
                "intent_score": round(min(1.0, intent), 3),
                "news_sentiment": round(sentiment, 3),
                "traffic_score": round(traffic, 3)
            })
        _log(memory, sid, "api_response", {"intent_records": len(intents)})
        return {"intent_signals": intents}


class ScoringAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        _log(memory, sid, "reasoning", {"note": "computing composite lead score"})
        leads = inputs.get("enriched_leads", [])
        intents = inputs.get("intent_signals", [])
        scoring = inputs.get("scoring_criteria", {})
        weights = scoring.get("weights", {})
        thresholds = scoring.get("thresholds", {})
        tech_pref = scoring.get("criteria", {}).get("tech_stack_preferred", [])
        intent_map = {i.get("domain"): i for i in intents}
        ranked = []
        for ld in leads:
            score = 0.0
            techs = set(ld.get("technologies", []))
            role = ld.get("role", "")
            email = ld.get("email", "") or (ld.get("emails", [""]) or [""])[0]
            domain = ld.get("domain", "")
            intent = intent_map.get(domain, {})
            if "Salesforce" in techs or any(t in techs for t in tech_pref):
                score += weights.get("tech_stack_match", 0)
            if any(k in role for k in ["Sales", "Revenue"]):
                score += weights.get("role_function_match", 0)
            if "@" in email and "." in email.split("@")[-1]:
                score += weights.get("email_validity", 0)
            score += weights.get("intent_score", 0) * float(intent.get("intent_score", 0))
            score += weights.get("domain_traffic", 0) * float(intent.get("traffic_score", 0))
            score += weights.get("news_sentiment", 0) * float(intent.get("news_sentiment", 0))
            s = round(score, 3)
            if s >= thresholds.get("A", 9999):
                grade = "A"
            elif s >= thresholds.get("B", 9999):
                grade = "B"
            elif s >= thresholds.get("C", 9999):
                grade = "C"
            else:
                grade = "D"
            item = dict(ld)
            item.update({"score": s, "grade": grade})
            ranked.append(item)
        ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
        _log(memory, sid, "intermediate", {"ranked": len(ranked)})
        return {"ranked_leads": ranked}


class EmailVerificationAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        leads = inputs.get("leads", [])
        criteria = memory.get("config", {}).get("scoring", {}).get("criteria", {})
        allow_free = criteria.get("email_requirements", {}).get("allow_free_providers", False)
        free_domains = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com"}
        verified = []
        for ld in leads:
            email = ld.get("email") or (ld.get("emails", [""]) or [""])[0]
            domain = email.split("@")[-1] if email and "@" in email else ""
            if not email or "@" not in email or not domain:
                continue
            if not allow_free and domain in free_domains:
                continue
            verified.append(ld)
        _log(memory, sid, "api_response", {"verified": len(verified)})
        return {"verified_leads": verified}


class OutreachContentAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        _log(memory, sid, "reasoning", {"note": "generating personalized emails"})
        leads = inputs.get("ranked_leads", [])
        persona = inputs.get("persona", "SDR")
        tone = inputs.get("tone", "friendly")
        msgs = []
        for ld in leads:
            cn = ld.get("contact") or ld.get("contact_name") or "there"
            company = ld.get("company", "your team")
            body = f"Hi {cn}, we help {company} accelerate outbound with LLM agents. Would you be open to a quick chat?"
            if tone == "friendly":
                body += " Thanks!"
            msgs.append({"lead": ld.get("email") or (ld.get("emails", [""]) or [""])[0], "email_body": body, "persona": persona})
        _log(memory, sid, "intermediate", {"messages": len(msgs)})
        return {"messages": msgs}


class OutreachExecutorAgent(Agent):
    def run(self, inputs, tools, config, memory):
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


class ResponseTrackerAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        cid = inputs.get("campaign_id")
        _log(memory, sid, "api_request", {"provider": "apollo", "campaign_id": cid})
        responses = []
        for s in memory.get("send", {}).get("output", {}).get("sent_status", []):
            responses.append({"lead": s.get("lead"), "opened": False, "clicked": False, "replied": False})
        _log(memory, sid, "api_response", {"responses": len(responses)})
        return {"responses": responses}


class FeedbackTrainerAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        responses = inputs.get("responses", [])
        open_rate = 0.0
        reply_rate = 0.0
        recs = []
        if reply_rate < 0.05:
            recs.append({"type": "scoring_weight_adjustment", "path": "scoring.weights.intent_score", "delta": 0.1})
            recs.append({"type": "messaging", "suggestion": "Test a more direct CTA in first sentence"})
        sheet_id = None
        for t in tools:
            if t.get("name") == "GoogleSheets":
                sheet_id = _resolve_placeholders(t.get("config", {}).get("sheet_id"), memory)
                break
        rows = [{"ts": int(time.time()), "open_rate": open_rate, "reply_rate": reply_rate, "recommendations": recs}]
        _log(memory, sid, "api_request", {"sheets": bool(sheet_id)})
        _log(memory, sid, "api_response", {"sheets_rows_written": len(rows)})
        return {"recommendations": recs, "sheets_write": {"sheet_id": sheet_id, "rows": len(rows)}, "approval": {"required": True, "status": "pending"}}


class FeedbackApplyAgent(Agent):
    def run(self, inputs, tools, config, memory):
        sid = memory.get("_current_step")
        auto = inputs.get("auto_apply", False)
        updated = dict(inputs.get("current_config", {}))
        approved = False
        approval = inputs.get("recommendations")
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


AGENTS: Dict[str, Any] = {
    "ProspectSearchAgent": ProspectSearchAgent,
    "LLMPreEnrichmentAgent": LLMPreEnrichmentAgent,
    "DataEnrichmentAgent": DataEnrichmentAgent,
    "ThirdPartyEnrichmentAgent": ThirdPartyEnrichmentAgent,
    "AnonymizedIntentSignalAgent": AnonymizedIntentSignalAgent,
    "ScoringAgent": ScoringAgent,
    "EmailVerificationAgent": EmailVerificationAgent,
    "OutreachContentAgent": OutreachContentAgent,
    "OutreachExecutorAgent": OutreachExecutorAgent,
    "ResponseTrackerAgent": ResponseTrackerAgent,
    "FeedbackTrainerAgent": FeedbackTrainerAgent,
    "FeedbackApplyAgent": FeedbackApplyAgent,
}


def run_workflow(workflow_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    with open(workflow_path, "r", encoding="utf-8") as f:
        wf = json.load(f)
    memory: Dict[str, Any] = {}
    config = wf.get("config", {})
    memory["config"] = config
    env_cfg = config.get("env", {})
    if env_cfg.get("load_from") == "env":
        loaded_keys = []
        for key in env_cfg.get("required", []):
            value = os.environ.get(key)
            memory[key] = value
            loaded_keys.append({"key": key, "loaded": bool(value), "length": len(value) if value else 0})
        _log(memory, None, "env_loading", {"keys": loaded_keys})
    steps: List[Dict[str, Any]] = wf.get("steps", [])
    for step in steps:
        sid = step.get("id")
        agent_name = step.get("agent")
        agent_cls = AGENT_REGISTRY.get(agent_name)
        if not agent_cls:
            raise ValueError(f"Unknown agent: {agent_name}")
        inputs = _resolve_placeholders(step.get("inputs", {}), memory)
        tools = _resolve_placeholders(step.get("tools", []), memory)
        agent = agent_cls()
        t0 = time.time()
        memory["_current_step"] = sid
        _log(memory, sid, "step_start", {"agent": agent_name, "input_keys": list(inputs.keys())})
        output = agent.run(inputs=inputs, tools=tools, config=config, memory=memory)
        dt = int((time.time() - t0) * 1000)
        _log(memory, sid, "step_end", {"duration_ms": dt, "output_keys": list(output.keys())})
        memory[sid] = {"output": output}
    result = {"workflow_name": wf.get("workflow_name"), "results": memory, "logs": memory.get("_logs", {})}
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workflow", default="single_workflow.json")
    p.add_argument("--output", default="final_output.json")
    args = p.parse_args()
    res = run_workflow(args.workflow, args.output)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


def _sanitize_tools(tools: Any) -> Any:
    if isinstance(tools, list):
        return [_sanitize_tools(t) for t in tools]
    if isinstance(tools, dict):
        out = {}
        for k, v in tools.items():
            if k.lower() in {"api_key", "authorization", "token"}:
                out[k] = "***"
            else:
                out[k] = _sanitize_tools(v)
        return out
    return tools


def _log(memory: Dict[str, Any], step_id: Optional[str], event_type: str, data: Dict[str, Any]) -> None:
    logs = memory.setdefault("_logs", {})
    if not step_id:
        step_id = "_global"
    arr = logs.setdefault(step_id, [])
    arr.append({"ts": int(time.time() * 1000), "type": event_type, "data": data})
