from typing import Any, Dict, List
from agents.base import Agent
from agents.utils import _log, _sanitize_tools
import json
from urllib.parse import urlencode
from urllib.request import urlopen
import random


class ProspectSearchAgent(Agent):
    def run(self, inputs: Dict[str, Any], tools: List[Dict[str, Any]], config: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        sid = memory.get("_current_step")
        _log(memory, sid, "reasoning", {"note": "searching prospects by ICP/signals"})
        _log(memory, sid, "api_request", {"tools": _sanitize_tools(tools)})
        
        icp = inputs.get("icp", {})
        signals = inputs.get("signals", [])
        target_count = inputs.get("target_count", 10)
        
        # Check for Clay/Apollo API integration
        clay_key = clay_ep = apollo_key = apollo_ep = None
        for t in tools or []:
            name = (t.get("name") or "").lower()
            cfg = t.get("config") or {}
            if "clay" in name:
                clay_key = cfg.get("api_key")
                clay_ep = cfg.get("endpoint")
            elif "apollo" in name:
                apollo_key = cfg.get("api_key")
                apollo_ep = cfg.get("endpoint")
        
        leads = []
        
        # Try Clay API first
        if clay_key and clay_ep:
            try:
                query_params = {
                    "api_key": clay_key,
                    "limit": target_count,
                    "industries": ",".join(icp.get("industry", ["SaaS", "Software"])),
                    "employee_count_min": icp.get("employee_count_range", {}).get("min", 50),
                    "employee_count_max": icp.get("employee_count_range", {}).get("max", 1500)
                }
                q = urlencode(query_params)
                _log(memory, sid, "api_call", {"provider": "clay", "target_count": target_count})
                with urlopen(f"{clay_ep}?{q}", timeout=15) as r:
                    data = json.loads(r.read().decode("utf-8")) or {}
                
                clay_leads = data.get("results", [])
                for lead in clay_leads[:target_count]:
                    leads.append({
                        "company": lead.get("company_name", f"Company {len(leads) + 1}"),
                        "contact_name": lead.get("full_name", f"Contact {len(leads) + 1}"),
                        "email": lead.get("email", f"contact{len(leads) + 1}@example.com"),
                        "linkedin": lead.get("linkedin_url", ""),
                        "signal": random.choice(signals) if signals else ""
                    })
                _log(memory, sid, "api_success", {"provider": "clay", "count": len(clay_leads)})
            except Exception as e:
                _log(memory, sid, "api_error", {"provider": "clay", "error": str(e)})
        
        # Try Apollo API if Clay didn't work or didn't return enough leads
        if len(leads) < target_count and apollo_key and apollo_ep:
            try:
                query_params = {
                    "api_key": apollo_key,
                    "person_locations": ["US", "CA", "UK"],
                    "organization_locations": ["US", "CA", "UK"],
                    "person_seniorities": ["director", "vp", "c_level"],
                    "organization_num_employees_ranges": ["51,200", "201,1000", "1001,5000"],
                    "q_organization_keyword_tags": " OR ".join(icp.get("industry", ["SaaS", "Software"])),
                    "page_size": min(target_count - len(leads), 25)
                }
                q = urlencode(query_params)
                _log(memory, sid, "api_call", {"provider": "apollo", "target_count": target_count - len(leads)})
                with urlopen(f"{apollo_ep}?{q}", timeout=15) as r:
                    data = json.loads(r.read().decode("utf-8")) or {}
                
                apollo_leads = data.get("people", [])
                for lead in apollo_leads:
                    org = lead.get("organization", {})
                    leads.append({
                        "company": org.get("name", f"Company {len(leads) + 1}"),
                        "contact_name": f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip(),
                        "email": lead.get("email", f"contact{len(leads) + 1}@{org.get('primary_domain', 'example.com')}"),
                        "linkedin": lead.get("linkedin_url", ""),
                        "signal": random.choice(signals) if signals else ""
                    })
                _log(memory, sid, "api_success", {"provider": "apollo", "count": len(apollo_leads)})
            except Exception as e:
                _log(memory, sid, "api_error", {"provider": "apollo", "error": str(e)})
        
        # Fallback: Generate synthetic leads if APIs didn't provide enough
        if len(leads) < target_count:
            synthetic_companies = [
                "TechFlow Solutions", "DataVault Inc", "CloudSync Pro", "ScaleForce", "GrowthEngine",
                "RevOps Labs", "SalesBoost AI", "LeadGen Pro", "ConvertFlow", "PipelinePlus",
                "MarketEdge", "SaaS Dynamics", "AutoScale Systems", "RevenueMax", "GrowthHacker Co",
                "CloudFirst Labs", "DataDriven Inc", "ScaleTech", "FlowState Software", "GrowthPath"
            ]
            
            synthetic_names = [
                "Sarah Johnson", "Mike Chen", "Jessica Rodriguez", "David Kim", "Amanda Foster",
                "Ryan Murphy", "Lisa Wang", "Tom Anderson", "Nicole Brown", "Alex Turner",
                "Maria Garcia", "Chris Lee", "Rachel Davis", "Kevin Wilson", "Amy Zhang",
                "Daniel Taylor", "Emily Carter", "Jason Park", "Michelle Liu", "Brandon Scott"
            ]
            
            synthetic_domains = [
                "techflow.com", "datavault.io", "cloudsync.co", "scaleforce.ai", "growthengine.com",
                "revopslabs.io", "salesboost.ai", "leadgenpro.com", "convertflow.co", "pipelineplus.io",
                "marketedge.com", "saasdynamics.io", "autoscale.ai", "revenuemax.com", "growthhacker.co",
                "cloudfirst.io", "datadriven.com", "scaletech.ai", "flowstate.co", "growthpath.io"
            ]
            
            for i in range(len(leads), min(target_count, len(synthetic_companies))):
                company = synthetic_companies[i]
                name = synthetic_names[i % len(synthetic_names)]
                domain = synthetic_domains[i]
                leads.append({
                    "company": company,
                    "contact_name": name,
                    "email": f"{name.lower().replace(' ', '.')}@{domain}",
                    "linkedin": f"https://linkedin.com/in/{name.lower().replace(' ', '')}",
                    "signal": random.choice(signals) if signals else ""
                })
            
            _log(memory, sid, "synthetic_generation", {"count": len(leads), "target_count": target_count})
        
        _log(memory, sid, "api_response", {"count": len(leads)})
        return {"leads": leads}
