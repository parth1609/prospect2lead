#!/usr/bin/env python3
"""
Real-time Dashboard for API call traces and workflow monitoring
"""
import json
import time
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-socketio")


class RealTimeTracer:
    """Real-time tracer for API calls and workflow steps"""
    
    def __init__(self):
        self.traces = []
        self.active_calls = {}
        self.workflow_status = "idle"
        self.step_progress = {}
        self.api_stats = {
            "total_calls": 0,
            "successful": 0,
            "failed": 0,
            "providers": {}
        }
        self.subscribers = []
        
    def start_workflow(self, workflow_name: str):
        """Mark workflow as started"""
        self.workflow_status = "running"
        self.step_progress = {}
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "workflow_start",
            "message": f"🚀 Starting workflow: {workflow_name}",
            "level": "info",
            "data": {"workflow_name": workflow_name}
        }
        self.add_trace(trace)
    
    def start_step(self, step_name: str, agent_name: str):
        """Mark step as started"""
        self.step_progress[step_name] = {"status": "running", "agent": agent_name, "start_time": time.time()}
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "step_start",
            "message": f"📋 Step: {step_name} ({agent_name})",
            "level": "info", 
            "data": {"step": step_name, "agent": agent_name}
        }
        self.add_trace(trace)
    
    def start_api_call(self, provider: str, endpoint: str, call_id: str = None):
        """Track API call start"""
        call_id = call_id or f"{provider}_{int(time.time()*1000)}"
        self.active_calls[call_id] = {
            "provider": provider,
            "endpoint": endpoint,
            "start_time": time.time(),
            "status": "calling"
        }
        self.api_stats["total_calls"] += 1
        
        if provider not in self.api_stats["providers"]:
            self.api_stats["providers"][provider] = {"calls": 0, "success": 0, "errors": 0}
        self.api_stats["providers"][provider]["calls"] += 1
        
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "api_call_start",
            "message": f"📡 API Call: {provider} -> {endpoint}",
            "level": "info",
            "data": {"provider": provider, "endpoint": endpoint, "call_id": call_id}
        }
        self.add_trace(trace)
        return call_id
    
    def complete_api_call(self, call_id: str, success: bool = True, response_data: Dict = None, error_msg: str = None):
        """Track API call completion"""
        if call_id not in self.active_calls:
            return
        
        call_info = self.active_calls[call_id]
        duration = time.time() - call_info["start_time"]
        provider = call_info["provider"]
        
        if success:
            self.api_stats["successful"] += 1
            self.api_stats["providers"][provider]["success"] += 1
            message = f"✅ API Success: {provider} ({duration:.2f}s)"
            level = "success"
        else:
            self.api_stats["failed"] += 1
            self.api_stats["providers"][provider]["errors"] += 1
            message = f"❌ API Error: {provider} - {error_msg} ({duration:.2f}s)"
            level = "error"
        
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "api_call_complete",
            "message": message,
            "level": level,
            "data": {
                "provider": provider,
                "success": success,
                "duration": duration,
                "response_data": response_data,
                "error": error_msg
            }
        }
        self.add_trace(trace)
        del self.active_calls[call_id]
    
    def complete_step(self, step_name: str, success: bool = True, output_data: Dict = None):
        """Mark step as completed"""
        if step_name in self.step_progress:
            duration = time.time() - self.step_progress[step_name]["start_time"]
            self.step_progress[step_name]["status"] = "completed" if success else "failed"
            self.step_progress[step_name]["duration"] = duration
        
        message = f"{'✅' if success else '❌'} Step Complete: {step_name}"
        trace = {
            "timestamp": datetime.now().isoformat(),
            "type": "step_complete",
            "message": message,
            "level": "success" if success else "error",
            "data": {"step": step_name, "success": success, "output_data": output_data}
        }
        self.add_trace(trace)
    
    def add_trace(self, trace: Dict[str, Any]):
        """Add trace and notify subscribers"""
        self.traces.append(trace)
        
        # Keep only last 1000 traces
        if len(self.traces) > 1000:
            self.traces = self.traces[-1000:]
        
        # Notify all subscribers
        for callback in self.subscribers:
            try:
                callback(trace)
            except:
                pass
        
        # Print to console
        print(f"[{trace['timestamp']}] {trace['message']}")
    
    def subscribe(self, callback):
        """Subscribe to trace updates"""
        self.subscribers.append(callback)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return {
            "workflow_status": self.workflow_status,
            "step_progress": self.step_progress,
            "active_calls": len(self.active_calls),
            "api_stats": self.api_stats,
            "recent_traces": self.traces[-50:],  # Last 50 traces
            "active_call_details": list(self.active_calls.values())
        }


# Global tracer instance
tracer = RealTimeTracer()


class DashboardServer:
    """Flask-based dashboard server"""
    
    def __init__(self, tracer: RealTimeTracer):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for dashboard. Install with: pip install flask flask-socketio")
        
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'workflow_tracer_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.tracer = tracer
        
        # Subscribe to tracer updates
        self.tracer.subscribe(self.broadcast_trace)
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify(self.tracer.get_dashboard_data())
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            # Send current dashboard data to new client
            emit('dashboard_update', self.tracer.get_dashboard_data())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
    
    def broadcast_trace(self, trace: Dict[str, Any]):
        """Broadcast trace to all connected clients"""
        self.socketio.emit('new_trace', trace)
        self.socketio.emit('dashboard_update', self.tracer.get_dashboard_data())
    
    def run(self, host='localhost', port=5000, debug=False):
        """Run the dashboard server"""
        print(f"🌐 Dashboard starting at http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)


def create_dashboard_html():
    """Create HTML template for dashboard"""
    
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workflow API Tracer Dashboard</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f5f5; 
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            background: #2c3e50; 
            color: white; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 20px; 
        }
        .stat-card { 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        .stat-number { 
            font-size: 2em; 
            font-weight: bold; 
            color: #3498db; 
        }
        .traces-container { 
            background: white; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            height: 500px; 
            overflow-y: auto; 
        }
        .trace-item { 
            padding: 10px 20px; 
            border-bottom: 1px solid #eee; 
            font-family: monospace; 
        }
        .trace-success { color: #27ae60; }
        .trace-error { color: #e74c3c; }
        .trace-info { color: #3498db; }
        .status-badge { 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-size: 0.8em; 
            font-weight: bold; 
        }
        .status-running { background: #f39c12; color: white; }
        .status-completed { background: #27ae60; color: white; }
        .status-failed { background: #e74c3c; color: white; }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: #3498db;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Workflow API Tracer Dashboard</h1>
            <p>Real-time monitoring of your lead generation workflow</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Workflow Status</h3>
                <div class="stat-number" id="workflow-status">Idle</div>
            </div>
            <div class="stat-card">
                <h3>Active API Calls</h3>
                <div class="stat-number" id="active-calls">0</div>
            </div>
            <div class="stat-card">
                <h3>Total API Calls</h3>
                <div class="stat-number" id="total-calls">0</div>
            </div>
            <div class="stat-card">
                <h3>Success Rate</h3>
                <div class="stat-number" id="success-rate">0%</div>
            </div>
        </div>
        
        <div class="stat-card" style="margin-bottom: 20px;">
            <h3>Step Progress</h3>
            <div id="step-progress"></div>
        </div>
        
        <div class="traces-container">
            <div style="padding: 20px; background: #34495e; color: white; font-weight: bold;">
                📡 Live API Traces
            </div>
            <div id="traces-list"></div>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to tracer dashboard');
        });
        
        socket.on('dashboard_update', function(data) {
            updateDashboard(data);
        });
        
        socket.on('new_trace', function(trace) {
            addTrace(trace);
        });
        
        function updateDashboard(data) {
            // Update status
            document.getElementById('workflow-status').textContent = data.workflow_status;
            document.getElementById('active-calls').textContent = data.active_calls;
            document.getElementById('total-calls').textContent = data.api_stats.total_calls;
            
            // Calculate success rate
            const total = data.api_stats.total_calls;
            const success = data.api_stats.successful;
            const rate = total > 0 ? Math.round((success / total) * 100) : 0;
            document.getElementById('success-rate').textContent = rate + '%';
            
            // Update step progress
            updateStepProgress(data.step_progress);
            
            // Update traces
            updateTraces(data.recent_traces);
        }
        
        function updateStepProgress(steps) {
            const container = document.getElementById('step-progress');
            container.innerHTML = '';
            
            for (const [stepName, stepData] of Object.entries(steps)) {
                const stepDiv = document.createElement('div');
                stepDiv.style.marginBottom = '10px';
                
                const statusBadge = getStatusBadge(stepData.status);
                const duration = stepData.duration ? ` (${stepData.duration.toFixed(2)}s)` : '';
                
                stepDiv.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>${stepName} - ${stepData.agent}</span>
                        <span>${statusBadge}${duration}</span>
                    </div>
                `;
                container.appendChild(stepDiv);
            }
        }
        
        function getStatusBadge(status) {
            const badges = {
                'running': '<span class="status-badge status-running">RUNNING</span>',
                'completed': '<span class="status-badge status-completed">COMPLETED</span>',
                'failed': '<span class="status-badge status-failed">FAILED</span>'
            };
            return badges[status] || '<span class="status-badge">UNKNOWN</span>';
        }
        
        function updateTraces(traces) {
            const container = document.getElementById('traces-list');
            container.innerHTML = '';
            
            traces.reverse().forEach(trace => {
                addTrace(trace);
            });
        }
        
        function addTrace(trace) {
            const container = document.getElementById('traces-list');
            const traceDiv = document.createElement('div');
            traceDiv.className = `trace-item trace-${trace.level}`;
            
            const timestamp = new Date(trace.timestamp).toLocaleTimeString();
            traceDiv.innerHTML = `
                <span style="color: #7f8c8d;">[${timestamp}]</span> ${trace.message}
            `;
            
            container.insertBefore(traceDiv, container.firstChild);
            
            // Keep only last 100 traces
            while (container.children.length > 100) {
                container.removeChild(container.lastChild);
            }
        }
    </script>
</body>
</html>
    '''
    
    # Create templates directory
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Write HTML template
    with open(os.path.join(templates_dir, "dashboard.html"), "w") as f:
        f.write(html_content)


def start_dashboard_server():
    """Start the dashboard server in a separate thread"""
    
    def run_server():
        try:
            create_dashboard_html()
            server = DashboardServer(tracer)
            server.run(host='localhost', port=5000, debug=False)
        except Exception as e:
            print(f"Dashboard server error: {e}")
    
    dashboard_thread = threading.Thread(target=run_server, daemon=True)
    dashboard_thread.start()
    time.sleep(2)  # Give server time to start
    print("🌐 Dashboard available at: http://localhost:5000")


if __name__ == "__main__":
    # Demo the tracer
    print("🚀 Starting Real-time API Tracer Demo")
    
    # Start dashboard server
    if FLASK_AVAILABLE:
        start_dashboard_server()
        time.sleep(3)
    
    # Simulate workflow execution
    tracer.start_workflow("OutboundLeadGeneration")
    time.sleep(1)
    
    tracer.start_step("prospect_search", "ProspectSearchAgent")
    time.sleep(0.5)
    
    # Simulate API calls
    call1 = tracer.start_api_call("clay", "https://api.clay.com/search")
    time.sleep(2)
    tracer.complete_api_call(call1, success=False, error_msg="HTTP 404: Not Found")
    
    call2 = tracer.start_api_call("apollo", "https://api.apollo.io/v1/mixed_search")
    time.sleep(1.5)
    tracer.complete_api_call(call2, success=False, error_msg="HTTP 403: Forbidden")
    
    tracer.complete_step("prospect_search", success=True, output_data={"leads": 20})
    
    tracer.start_step("enrichment", "DataEnrichmentAgent")
    time.sleep(0.5)
    
    # Simulate multiple Hunter API calls
    for i, domain in enumerate(["techflow.com", "datavault.io", "cloudsync.co"]):
        call_id = tracer.start_api_call("hunter", f"https://api.hunter.io/v2/domain-search?domain={domain}")
        time.sleep(1)
        tracer.complete_api_call(call_id, success=True, response_data={"company": f"Company {i+1}"})
    
    tracer.complete_step("enrichment", success=True)
    
    if FLASK_AVAILABLE:
        print("\n🌐 Dashboard running at: http://localhost:5000")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Stopping dashboard...")
    else:
        print("\n📊 Traces completed. Install Flask to see web dashboard:")
        print("pip install flask flask-socketio")
