#!/usr/bin/env python3
"""
Integrated workflow runner with storage, email, and full pipeline
"""
import json
import os
import argparse
from datetime import datetime

# Import our integrated components using absolute imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.storage_manager import StorageManager
from utils.email_delivery_manager import EmailDeliveryManager
from utils.google_sheets_logger import GoogleSheetsLogger
from runners.graph_runner import run_langgraph_workflow
from utils.simple_output_formatter import SimpleOutputFormatter


class IntegratedWorkflowRunner:
    """Complete workflow runner with all integrations"""

    def __init__(self):
        self.storage = StorageManager()
        self.email_manager = EmailDeliveryManager()
        self.sheets_logger = GoogleSheetsLogger()
        self.formatter = SimpleOutputFormatter()

    def run_complete_workflow(self, workflow_path: str, campaign_name: str = None, output_dir: str = "outputs") -> dict:
        """Run complete workflow with all integrations"""

        if not campaign_name:
            campaign_name = f"Campaign_{datetime.now().strftime('%Y%m%d_%H%M')}"

        print(f"🚀 Starting integrated workflow: {workflow_path}")
        print(f"📊 Campaign: {campaign_name}")

        # 1. Run the core workflow
        raw_output_path = os.path.join(output_dir, f"{campaign_name}_raw.json")
        print("\n1️⃣ Running LangGraph workflow...")
        raw_output = run_langgraph_workflow(workflow_path, raw_output_path)

        # 2. Format to simple JSON
        print("\n2️⃣ Converting to simple JSON format...")
        simple_output = self.formatter.format_leads(raw_output)
        simple_output_path = os.path.join(output_dir, f"{campaign_name}_simple.json")

        with open(simple_output_path, "w") as f:
            json.dump(simple_output, f, indent=2)

        # 3. Store in database
        print("\n3️⃣ Storing in database...")
        campaign_id = self.storage.store_leads(simple_output["leads"], campaign_name)

        # 4. Send emails to high-quality leads
        email_results = None
        high_quality_leads = [lead for lead in simple_output["leads"] if lead.get("grade") in ["A", "B"]]

        if high_quality_leads and len(high_quality_leads) > 0:
            print(f"\n4️⃣ Sending emails to {len(high_quality_leads)} high-quality leads...")
            email_results = self.email_manager.send_campaign(high_quality_leads)
        else:
            print("\n4️⃣ No high-quality leads found for email campaign")

        # 5. Log to Google Sheets
        print("\n5️⃣ Logging to Google Sheets...")
        campaign_data = {
            "campaign_name": campaign_name,
            "total_leads": simple_output["summary"]["total_leads"],
            "companies": simple_output["summary"]["companies"],
            "emails_sent": email_results.get("sent", 0) if email_results else 0,
            "grades": simple_output["summary"]["grades"],
            "avg_score": simple_output["summary"]["avg_score"]
        }
        self.sheets_logger.log_campaign_results(campaign_data)

        # 6. Generate summary
        summary = {
            "campaign": {
                "name": campaign_name,
                "timestamp": datetime.now().isoformat(),
                "workflow_file": workflow_path
            },
            "results": {
                "total_leads": simple_output["summary"]["total_leads"],
                "companies": simple_output["summary"]["companies"],
                "grade_distribution": simple_output["summary"]["grades"],
                "average_score": simple_output["summary"]["avg_score"]
            },
            "email_campaign": email_results or {"status": "not_executed"},
            "files": {
                "raw_output": raw_output_path,
                "simple_output": simple_output_path,
                "campaign_id": campaign_id
            },
            "api_usage": self.email_manager.get_delivery_stats()
        }

        # Save summary
        summary_path = os.path.join(output_dir, f"{campaign_name}_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        print("\n✅ Campaign completed!")
        print(f"📊 Leads generated: {simple_output['summary']['total_leads']}")
        print(f"🏢 Companies found: {simple_output['summary']['companies']}")
        print(f"📧 Emails sent: {email_results.get('sent', 0) if email_results else 0}")
        print(f"💾 Campaign ID: {campaign_id}")
        print(f"\n📁 Output files:")
        print(f"   Raw: {raw_output_path}")
        print(f"   Simple: {simple_output_path}")
        print(f"   Summary: {summary_path}")

        return summary


def main():
    parser = argparse.ArgumentParser(description="Run complete integrated workflow")
    parser.add_argument("--workflow", default="workflows/single_workflow.json", help="Workflow JSON file")
    parser.add_argument("--campaign", help="Campaign name")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")

    args = parser.parse_args()

    runner = IntegratedWorkflowRunner()
    result = runner.run_complete_workflow(args.workflow, args.campaign, args.output_dir)

    print("\n🎯 Next steps:")
    print("   - Check output files in outputs/ directory")
    print("   - Review campaign summary for metrics")
    print("   - Monitor Google Sheets for performance tracking")
    print("   - Check email delivery status in summary")


if __name__ == "__main__":
    main()
