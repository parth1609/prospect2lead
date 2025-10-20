#!/usr/bin/env python3
"""
Diagnostic script to test imports and setup
"""
import sys
import os

def test_imports():
    print("🔍 Testing imports...")

    # Add current directory to path
    sys.path.insert(0, '.')

    # Test 1: Basic agents import
    try:
        from agents import AGENTS
        print("✅ Agents import successful")
        print(f"   Available agents: {len(AGENTS)}")
    except Exception as e:
        print(f"❌ Agents import failed: {e}")
        return False

    # Test 2: Utils import
    try:
        from agents.utils import _log
        print("✅ Utils import successful")
    except Exception as e:
        print(f"❌ Utils import failed: {e}")
        return False

    # Test 3: Runner imports
    try:
        from runners.graph_runner import WorkflowState
        print("✅ Graph runner import successful")
    except Exception as e:
        print(f"❌ Graph runner import failed: {e}")
        return False

    # Test 4: File paths
    print("\n📁 Checking file paths...")
    files_to_check = [
        "workflows/single_workflow.json",
        "config/.env",
        "agents/__init__.py",
        "runners/__init__.py"
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")

    # Test 5: Environment loading
    print("\n🔐 Testing environment...")
    try:
        from dotenv import load_dotenv
        env_path = "config/.env"
        if os.path.exists(env_path):
            load_dotenv(env_path)
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                print("✅ Environment loaded (API key found)")
            else:
                print("⚠️ Environment loaded but no GROQ_API_KEY found")
        else:
            print("❌ config/.env file not found")
    except ImportError:
        print("⚠️ python-dotenv not installed")

    print("\n🎯 All tests completed!")
    return True

if __name__ == "__main__":
    test_imports()
