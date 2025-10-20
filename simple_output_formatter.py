#!/usr/bin/env python3
"""
Simple JSON output formatter for leads
Creates clean, minimal JSON format suitable for CRM import
"""
import json
import os
from typing import Dict, Any, List


class SimpleOutputFormatter:
    def __init__(self):
        self.simple_format = {
            "leads": [],
            "summary": {},
            "timestamp": "",
            "config": {}
        }
    
    def format_leads(self, workflow_output: Dict[str, Any]) -> Dict[str, Any]:
        """Convert complex workflow output to simple leads format"""
        
        # Extract leads from various steps
        all_leads = []
        
        # Get leads from prospect search
        if "prospect_search" in workflow_output.get("results", {}):
            search_leads = workflow_output["results"]["prospect_search"].get("output", {}).get("leads", [])
            all_leads.extend(search_leads)
        
        # Get enriched leads if available
        if "enrichment" in workflow_output.get("results", {}):
            enriched_leads = workflow_output["results"]["enrichment"].get("output", {}).get("enriched_leads", [])
            if enriched_leads:
                all_leads = enriched_leads
        
        # Get scored leads if available
        if "scoring" in workflow_output.get("results", {}):
            scored_leads = workflow_output["results"]["scoring"].get("output", {}).get("ranked_leads", [])
            if scored_leads:
                all_leads = scored_leads
        
        # Format leads in simple structure
        simple_leads = []
        for i, lead in enumerate(all_leads, 1):
            simple_lead = {
                "id": i,
                "company": lead.get("company", "Unknown Company"),
                "contact_name": lead.get("contact_name") or lead.get("contact", "Unknown Contact"),
                "email": lead.get("email", ""),
                "domain": self.extract_domain(lead.get("email", "")),
                "role": lead.get("role") or lead.get("title", "Unknown"),
                "linkedin": lead.get("linkedin", ""),
                "signal": lead.get("signal", ""),
                "score": round(lead.get("score", 0), 2) if lead.get("score") else 0,
                "grade": lead.get("grade", ""),
                "technologies": lead.get("technologies", []),
                "status": "active"
            }
            simple_leads.append(simple_lead)
        
        # Create summary
        summary = {
            "total_leads": len(simple_leads),
            "companies": len(set(lead["company"] for lead in simple_leads)),
            "signals": len(set(lead["signal"] for lead in simple_leads if lead["signal"])),
            "grades": {
                "A": len([l for l in simple_leads if l["grade"] == "A"]),
                "B": len([l for l in simple_leads if l["grade"] == "B"]),
                "C": len([l for l in simple_leads if l["grade"] == "C"]),
                "D": len([l for l in simple_leads if l["grade"] == "D"])
            },
            "avg_score": round(sum(l["score"] for l in simple_leads) / len(simple_leads), 2) if simple_leads else 0
        }
        
        # Get workflow config
        config = {
            "workflow_name": workflow_output.get("workflow_name", "Lead Generation"),
            "target_count": workflow_output.get("results", {}).get("config", {}).get("scoring", {}).get("criteria", {}).get("target_count", len(simple_leads)),
            "icp": workflow_output.get("results", {}).get("config", {}).get("scoring", {}).get("criteria", {})
        }
        
        return {
            "leads": simple_leads,
            "summary": summary,
            "timestamp": self.get_timestamp(),
            "config": config
        }
    
    def extract_domain(self, email: str) -> str:
        """Extract domain from email address"""
        if "@" in email:
            return email.split("@")[-1]
        return ""
    
    def get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_simple_format(self, workflow_output: Dict[str, Any], output_path: str):
        """Save workflow output in simple JSON format"""
        simple_output = self.format_leads(workflow_output)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(simple_output, f, indent=2, ensure_ascii=False)
        
        return simple_output


def convert_to_simple_format(input_file: str, output_file: str) -> Dict[str, Any]:
    """Convert existing workflow output to simple format"""
    
    with open(input_file, "r", encoding="utf-8") as f:
        workflow_output = json.load(f)
    
    formatter = SimpleOutputFormatter()
    simple_output = formatter.format_leads(workflow_output)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(simple_output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted to simple format: {output_file}")
    print(f"📊 Total leads: {simple_output['summary']['total_leads']}")
    print(f"🏢 Companies: {simple_output['summary']['companies']}")
    
    return simple_output


if __name__ == "__main__":
    # Convert existing output to simple format
    if os.path.exists("langgraph_output.json"):
        convert_to_simple_format("langgraph_output.json", "simple_leads_output.json")
    else:
        print("No langgraph_output.json found. Run the workflow first.")
