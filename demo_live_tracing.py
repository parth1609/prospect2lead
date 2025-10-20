#!/usr/bin/env python3
"""
Demo script to show live API tracing in action
"""
import time
import threading
from realtime_dashboard import tracer, start_dashboard_server, FLASK_AVAILABLE


def demo_api_calls():
    """Simulate a realistic workflow with live API traces"""
    
    print("🚀 Starting Live API Tracing Demo")
    print("=" * 50)
    
    # Start workflow
    tracer.start_workflow("OutboundLeadGeneration")
    time.sleep(1)
    
    # Step 1: Prospect Search
    print("\n📋 Step 1: Prospect Search")
    tracer.start_step("prospect_search", "ProspectSearchAgent")
    
    # Clay API call (will fail)
    print("   🌐 Calling Clay API...")
    call1 = tracer.start_api_call("clay", "https://api.clay.com/search")
    time.sleep(2)
    tracer.complete_api_call(call1, success=False, error_msg="HTTP 404: Not Found")
    
    # Apollo API call (will fail)
    print("   🌐 Calling Apollo API...")
    call2 = tracer.start_api_call("apollo", "https://api.apollo.io/v1/mixed_search")
    time.sleep(1.5)
    tracer.complete_api_call(call2, success=False, error_msg="HTTP 403: Forbidden")
    
    # Synthetic generation
    print("   🤖 Generating synthetic leads...")
    time.sleep(1)
    tracer.complete_step("prospect_search", success=True, output_data={"leads": 20})
    
    # Step 2: Data Enrichment
    print("\n📋 Step 2: Data Enrichment")
    tracer.start_step("enrichment", "DataEnrichmentAgent")
    
    # Multiple Hunter API calls
    domains = ["techflow.com", "datavault.io", "cloudsync.co", "scaleforce.ai", "growthengine.com"]
    for i, domain in enumerate(domains, 1):
        print(f"   🌐 Enriching domain {i}/{len(domains)}: {domain}")
        call_id = tracer.start_api_call("hunter", f"https://api.hunter.io/v2/domain-search?domain={domain}")
        time.sleep(1)
        tracer.complete_api_call(call_id, success=True, response_data={"company": f"Company {i}", "emails": 3})
    
    tracer.complete_step("enrichment", success=True, output_data={"enriched": 20})
    
    # Step 3: Intent Signals
    print("\n📋 Step 3: Intent Signals")
    tracer.start_step("intent_signals", "IntentSignalAgent")
    
    # BuiltWith API calls
    for i, domain in enumerate(domains, 1):
        print(f"   🌐 Checking tech stack {i}/{len(domains)}: {domain}")
        call_id = tracer.start_api_call("builtwith", f"https://api.builtwith.com/v21/api.json?LOOKUP={domain}")
        time.sleep(1.2)
        tracer.complete_api_call(call_id, success=True, response_data={"technologies": ["Salesforce", "HubSpot"]})
    
    tracer.complete_step("intent_signals", success=True)
    
    # Step 4: Email Verification
    print("\n📋 Step 4: Email Verification")
    tracer.start_step("email_verification", "EmailVerificationAgent")
    
    emails = ["john@techflow.com", "sarah@datavault.io", "mike@cloudsync.co"]
    for i, email in enumerate(emails, 1):
        print(f"   🌐 Verifying email {i}/{len(emails)}: {email}")
        call_id = tracer.start_api_call("hunter", f"https://api.hunter.io/v2/email-verifier?email={email}")
        time.sleep(2)
        tracer.complete_api_call(call_id, success=True, response_data={"result": "deliverable", "score": 95})
    
    tracer.complete_step("email_verification", success=True, output_data={"verified": 3})
    
    # Step 5: Send Emails
    print("\n📋 Step 5: Send Emails")
    tracer.start_step("send", "EmailSenderAgent")
    
    print("   📧 Sending emails via SendGrid...")
    call_id = tracer.start_api_call("sendgrid", "https://api.sendgrid.com/v3/mail/send")
    time.sleep(1.5)
    tracer.complete_api_call(call_id, success=True, response_data={"message_id": "sg_abc123", "sent": 3})
    
    tracer.complete_step("send", success=True, output_data={"sent": 3})
    
    # Step 6: Google Sheets Logging
    print("\n📋 Step 6: Logging to Sheets")
    tracer.start_step("feedback_trainer", "FeedbackAgent")
    
    print("   📊 Logging to Google Sheets...")
    call_id = tracer.start_api_call("google_sheets", "https://sheets.googleapis.com/v4/spreadsheets/xxx/values:append")
    time.sleep(1)
    tracer.complete_api_call(call_id, success=True, response_data={"updates": 1})
    
    tracer.complete_step("feedback_trainer", success=True)
    
    print("\n✅ Demo workflow completed!")
    print("📊 Check the dashboard to see all API traces")


def main():
    if not FLASK_AVAILABLE:
        print("❌ Flask not installed. Installing...")
        import subprocess
        import sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-socketio"])
            print("✅ Flask installed. Please restart the script.")
            return
        except:
            print("❌ Failed to install Flask. Please install manually:")
            print("   pip install flask flask-socketio")
            return
    
    print("🌐 Starting Real-time API Dashboard...")
    
    # Start dashboard server
    start_dashboard_server()
    time.sleep(3)
    
    print("\n🌐 Dashboard is now running at: http://localhost:5000")
    print("👀 Open your browser and watch the live API traces!")
    print("\n⏳ Starting demo in 3 seconds...")
    
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    # Run demo in separate thread so dashboard keeps running
    demo_thread = threading.Thread(target=demo_api_calls)
    demo_thread.start()
    
    print("\n🔄 Demo running! Watch your browser for live traces.")
    print("Press Ctrl+C to stop the dashboard")
    
    try:
        # Keep main thread alive for dashboard
        demo_thread.join()
        
        print("\n✨ Demo completed! Dashboard still running...")
        print("Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping dashboard...")


if __name__ == "__main__":
    main()
