#!/usr/bin/env python3
"""
Graph runner with integrated real-time tracing
"""
import json
import time
import threading
from datetime import datetime

# Use absolute imports instead of relative imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from runners.graph_runner import run_langgraph_workflow
from dashboard.realtime_dashboard import tracer, start_dashboard_server, FLASK_AVAILABLE


class TracedWorkflowRunner:
    """Workflow runner that sends traces to the dashboard"""
    
    def __init__(self):
        self.tracer = tracer
        
    def run_workflow_with_tracing(self, workflow_path: str, output_path: str = None):
        """Run workflow with real-time tracing"""
        
        print("🚀 Starting traced workflow execution...")
        
        # Start dashboard if Flask is available
        if FLASK_AVAILABLE:
            start_dashboard_server()
            print("🌐 Dashboard available at: http://localhost:5000")
            time.sleep(3)  # Give dashboard time to load
        
        # Load workflow config to get step names
        with open(workflow_path, 'r') as f:
            workflow_config = json.load(f)
        
        workflow_name = workflow_config.get('workflow_name', 'Unknown Workflow')
        steps = workflow_config.get('steps', [])
        
        # Start workflow tracing
        self.tracer.start_workflow(workflow_name)
        
        # Simulate step execution with tracing
        self.simulate_workflow_steps(steps)
        
        # Run actual workflow (this will have its own logging)
        print("\n📊 Running actual workflow...")
        result = run_langgraph_workflow(workflow_path, output_path)
        
        print(f"\n✅ Workflow completed!")
        return result
    
    def simulate_workflow_steps(self, steps):
        """Simulate workflow steps with realistic API call tracing"""
        
        for step in steps:
            step_id = step.get('id', 'unknown_step')
            agent_name = step.get('agent', 'UnknownAgent')
            tools = step.get('tools', [])
            
            print(f"\n🔄 Executing step: {step_id}")
            self.tracer.start_step(step_id, agent_name)
            
            # Simulate API calls based on step type
            self.simulate_step_api_calls(step_id, tools)
            
            # Complete step
            time.sleep(0.5)
            self.tracer.complete_step(step_id, success=True)
    
    def simulate_step_api_calls(self, step_id: str, tools: list):
        """Simulate API calls for different step types"""
        
        if step_id == "prospect_search":
            # Clay API call
            call_id = self.tracer.start_api_call("clay", "https://api.clay.com/search")
            time.sleep(1.5)
            self.tracer.complete_api_call(call_id, success=False, error_msg="HTTP 404: Not Found")
            
            # Apollo API call
            call_id = self.tracer.start_api_call("apollo", "https://api.apollo.io/v1/mixed_search")
            time.sleep(2.0)
            self.tracer.complete_api_call(call_id, success=False, error_msg="HTTP 403: Forbidden")
            
            # Synthetic generation
            time.sleep(1.0)
            self.tracer.add_trace({
                "timestamp": datetime.now().isoformat(),
                "type": "synthetic_generation",
                "message": "🤖 Generating synthetic leads (APIs unavailable)",
                "level": "info",
                "data": {"count": 20, "target_count": 100}
            })
        
        elif step_id == "enrichment":
            # Hunter API calls for each domain
            domains = [
                "techflow.com", "datavault.io", "cloudsync.co", "scaleforce.ai", 
                "growthengine.com", "revopslabs.io", "salesboost.ai", "leadgenpro.com",
                "convertflow.co", "pipelineplus.io"
            ]
            
            for domain in domains:
                call_id = self.tracer.start_api_call("hunter", f"https://api.hunter.io/v2/domain-search?domain={domain}")
                time.sleep(0.8)
                self.tracer.complete_api_call(call_id, success=True, response_data={"domain": domain})
        
        elif step_id == "intent_signals":
            # BuiltWith API calls
            domains = [
                "techflow.com", "datavault.io", "cloudsync.co", "scaleforce.ai",
                "growthengine.com", "revopslabs.io", "salesboost.ai"
            ]
            
            for domain in domains:
                call_id = self.tracer.start_api_call("builtwith", f"https://api.builtwith.com/v21/api.json?KEY=xxx&LOOKUP={domain}")
                time.sleep(1.2)
                self.tracer.complete_api_call(call_id, success=True, response_data={"tech_count": 1})
        
        elif step_id == "email_verification":
            # Hunter email verification
            emails = [
                "tom.anderson@leadgenpro.com", "maria.garcia@marketedge.com", 
                "kevin.wilson@revenuemax.com", "daniel.taylor@cloudfirst.io"
            ]
            
            for email in emails:
                call_id = self.tracer.start_api_call("hunter", f"https://api.hunter.io/v2/email-verifier?email={email}")
                time.sleep(2.5)
                self.tracer.complete_api_call(call_id, success=True, response_data={"result": "deliverable"})
        
        elif step_id == "send":
            # SendGrid API calls
            call_id = self.tracer.start_api_call("sendgrid", "https://api.sendgrid.com/v3/mail/send")
            time.sleep(1.0)
            self.tracer.complete_api_call(call_id, success=True, response_data={"message_id": "sg_123"})
        
        elif step_id == "feedback_trainer":
            # Google Sheets API
            call_id = self.tracer.start_api_call("google_sheets", "https://sheets.googleapis.com/v4/spreadsheets/xxx/values:append")
            time.sleep(0.8)
            self.tracer.complete_api_call(call_id, success=True, response_data={"updates": 1})


def main():
    """Main function to run traced workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run workflow with real-time API tracing")
    parser.add_argument("--workflow", default="single_workflow.json", help="Workflow JSON file")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--dashboard-only", action="store_true", help="Start dashboard only (no workflow)")
    
    args = parser.parse_args()
    
    if args.dashboard_only:
        if FLASK_AVAILABLE:
            print("🌐 Starting dashboard server...")
            start_dashboard_server()
            print("🌐 Dashboard available at: http://localhost:5000")
            print("Press Ctrl+C to stop")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Stopping dashboard...")
        else:
            print("❌ Flask not available. Install with: pip install flask flask-socketio")
        return
    
    runner = TracedWorkflowRunner()
    
    try:
        result = runner.run_workflow_with_tracing(args.workflow, args.output)
        
        if FLASK_AVAILABLE:
            print("\n🌐 Dashboard still running at: http://localhost:5000")
            print("Press Ctrl+C to stop")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Stopping dashboard...")
        
        return result
    
    except KeyboardInterrupt:
        print("\n⏹️ Workflow interrupted by user")
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        tracer.add_trace({
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "message": f"❌ Workflow failed: {str(e)}",
            "level": "error",
            "data": {"error": str(e)}
        })


if __name__ == "__main__":
    main()
