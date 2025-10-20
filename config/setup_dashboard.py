#!/usr/bin/env python3
"""
Setup script for dashboard dependencies (Flask + SocketIO)
"""
import subprocess
import sys
import os


def install_dashboard_requirements():
    """Install Flask and SocketIO for the real-time dashboard"""
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "flask>=2.0.0",
            "flask-socketio>=5.0.0",
            "eventlet>=0.30.0"
        ])
        print("✅ Successfully installed dashboard dependencies")
        print("   - Flask: Web framework for dashboard")
        print("   - Flask-SocketIO: Real-time communication")
        print("   - Eventlet: Async networking")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dashboard dependencies: {e}")
        return False


def test_dashboard_imports():
    """Test that dashboard dependencies can be imported"""
    try:
        import flask
        import flask_socketio
        import eventlet
        print("✅ Dashboard dependencies import successfully")
        return True
    except ImportError as e:
        print(f"❌ Dashboard dependency import failed: {e}")
        return False


def check_existing_files():
    """Check that required files exist for dashboard functionality"""
    required_files = [
        "dashboard/realtime_dashboard.py",
        "dashboard/demo_live_tracing.py",
        "dashboard/templates/dashboard.html"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"⚠️  Missing dashboard files: {', '.join(missing_files)}")
        print("   This may limit dashboard functionality")
        return False
    else:
        print("✅ All dashboard files found")
        return True


def main():
    print("🌐 Setting up Real-time API Dashboard")
    print("=" * 50)
    
    print("\n1️⃣ Installing dashboard dependencies...")
    deps_ok = install_dashboard_requirements()
    
    print("\n2️⃣ Testing imports...")
    import_ok = test_dashboard_imports()
    
    print("\n3️⃣ Checking dashboard files...")
    files_ok = check_existing_files()
    
    print("\n" + "=" * 50)
    if deps_ok and import_ok:
        print("✅ Dashboard setup complete!")
        print("\n🚀 You can now run:")
        print("   python dashboard/demo_live_tracing.py  # Demo with live traces")
        print("   python runners/traced_graph_runner.py --workflow workflows/single_workflow.json  # Workflow with traces")
        print("\n🌐 Dashboard will be available at: http://localhost:5000")
        
        if not files_ok:
            print("\n⚠️  Note: Some dashboard files are missing. Dashboard may have limited functionality.")
    else:
        print("❌ Dashboard setup incomplete.")
        print("\n🔧 To install manually:")
        print("   pip install flask flask-socketio eventlet")
    
    return deps_ok and import_ok


if __name__ == "__main__":
    main()
