from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log


class ScoringAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        _log(memory, sid, "reasoning", {"note": "computing composite lead score"})
        leads = inputs.get("enriched_leads", [])
        intents = inputs.get("intent_signals", [])
        scoring = inputs.get("scoring_criteria", {})
        weights = scoring.get("weights", {})
        thresholds = scoring.get("thresholds", {})
        tech_pref = scoring.get("criteria", {}).get("tech_stack_preferred", [])
        intent_map = {i.get("domain"): i for i in intents}
        ranked: List[Dict[str, Any]] = []
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
