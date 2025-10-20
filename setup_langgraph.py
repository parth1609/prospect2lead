import subprocess
import sys
import os


def install_requirements():
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "python-dotenv>=1.0.0",
            "langgraph>=0.2.0", 
            "langchain-core>=0.3.0"
        ])
        print("✅ Successfully installed LangGraph dependencies")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_env_file():
    env_path = ".env"
    if not os.path.exists(env_path):
        print("❌ .env file not found")
        return False
    
    required_keys = [
        "GROQ_API_KEY", "CLAY_API_KEY", "APOLLO_API_KEY", "PDL_API_KEY",
        "HUNTER_API_KEY", "SHEET_ID", "BUILTWITH_API_KEY", "NEWS_API_KEY", "SENDGRID_API_KEY"
    ]
    
    missing_keys = []
    with open(env_path, 'r') as f:
        content = f.read()
        for key in required_keys:
            if f"{key}=" not in content or f'{key}=""' in content or f"{key}=..." in content:
                missing_keys.append(key)
    
    if missing_keys:
        print(f"⚠️  Missing or empty API keys in .env: {', '.join(missing_keys)}")
        return False
    else:
        print("✅ All required API keys found in .env")
        return True


def test_workflow_json():
    workflow_path = "single_workflow.json"
    if not os.path.exists(workflow_path):
        print("❌ single_workflow.json not found")
        return False
    
    try:
        import json
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        if "steps" not in workflow:
            print("❌ Invalid workflow.json: missing 'steps'")
            return False
        
        steps = workflow["steps"]
        print(f"✅ Workflow has {len(steps)} steps:")
        for step in steps:
            print(f"   - {step.get('id')}: {step.get('agent')}")
        
        return True
    except Exception as e:
        print(f"❌ Invalid workflow.json: {e}")
        return False


def main():
    print("🚀 Setting up LangGraph Prospect-to-Lead Workflow\n")
    
    print("1️⃣ Installing dependencies...")
    deps_ok = install_requirements()
    
    print("\n2️⃣ Checking .env configuration...")
    env_ok = check_env_file()
    
    print("\n3️⃣ Validating workflow.json...")
    workflow_ok = test_workflow_json()
    
    print("\n" + "="*50)
    if deps_ok and workflow_ok:
        print("✅ Setup complete! Ready to run LangGraph workflow")
        print("\nNext steps:")
        print("  Run with simple runner:")
        print("    python langgraph_builder.py --workflow single_workflow.json")
        print("  Run with LangGraph:")
        print("    python graph_runner.py --workflow single_workflow.json --visualize")
        
        if not env_ok:
            print("\n⚠️  Note: Some API keys are missing. The workflow will use simulated data.")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
    
    return deps_ok and workflow_ok


if __name__ == "__main__":
    main()
