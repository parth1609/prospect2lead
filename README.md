# LangGraph Autonomous Prospect-to-Lead Workflow

An end-to-end LangGraph Agent System that autonomously discovers, enriches, scores, and contacts B2B prospects, with behavior refinement through a FeedbackTrainer mechanism.

## 🏗️ Architecture

The system uses a single `workflow.json` as input to dynamically build and execute a LangGraph where each node represents a specialized sub-agent:

- **ProspectSearchAgent** - Clay & Apollo API integration for lead discovery
- **LLMPreEnrichmentAgent** - LLM-powered data normalization and clustering  
- **DataEnrichmentAgent** - Hunter.io domain search for company info
- **ThirdPartyEnrichmentAgent** - People Data Labs augmentation
- **AnonymizedIntentSignalAgent** - BuiltWith & NewsAPI for intent signals
- **ScoringAgent** - Configurable ICP scoring with weighted criteria
- **EmailVerificationAgent** - Hunter.io email deliverability verification
- **OutreachContentAgent** - LLM-generated personalized messaging
- **OutreachExecutorAgent** - SendGrid/Apollo email delivery
- **ResponseTrackerAgent** - Apollo response monitoring
- **FeedbackTrainerAgent** - Google Sheets performance analysis
- **FeedbackApplyAgent** - Automated config optimization

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
python setup_langgraph.py

# Or manually:
pip install python-dotenv langgraph langchain-core
```

### 2. Configure API Keys

Copy your API keys to `.env`:
```env
GROQ_API_KEY=your_groq_key
HUNTER_API_KEY=your_hunter_key
BUILTWITH_API_KEY=your_builtwith_key
NEWS_API_KEY=your_newsapi_key
# ... other keys
```

### 3. Run the Workflow

**Option A: LangGraph Runner (Recommended)**
```powershell
python runners/graph_runner.py --workflow workflows/single_workflow.json --output outputs/multi_leads_output.json --visualize
```

**Option B: Sequential Runner (Simple)**
```powershell
print("  Run with simple runner:")
print("    python runners/langgraph_builder.py --workflow workflows/single_workflow.json")
print("  Run with LangGraph:")
print("    python runners/graph_runner.py --workflow workflows/single_workflow.json --visualize")
```

**Option C: Compare Both**
```powershell
python runners/compare_runners.py --workflow workflows/single_workflow.json
```

## 📊 Key Features

### Dynamic LangGraph Construction
- **JSON-Driven**: Entire workflow defined in `single_workflow.json`
- **Node Mapping**: Each step becomes a LangGraph node with the specified agent
- **Edge Creation**: Sequential flow with placeholder resolution between steps
- **State Management**: Typed state with step outputs and logging

### Real API Integration
- **Conditional Calling**: APIs called when keys are available, simulation fallback
- **Error Handling**: Graceful degradation with detailed error logging
- **Rate Limiting**: 10s timeouts with exception handling
- **Debug Logging**: `api_call`, `api_success`, `api_error` events

### Intelligent Scoring
- **Configurable Weights**: 14 scoring dimensions (tech stack, role, intent, etc.)
- **Grade Thresholds**: A/B/C/D classification with customizable cutoffs
- **Intent Integration**: Real-time signals from BuiltWith and NewsAPI
- **Email Quality**: Hunter.io deliverability filtering

### Feedback Loop
- **Performance Analysis**: Open/click/reply rate tracking
- **Auto-Optimization**: Scoring weight adjustments based on results
- **Human Approval**: Optional manual review before config changes
- **Google Sheets**: Campaign data logging for analysis

## 📁 Project Structure

```
prospect2lead workflow/
├── workflows/                    # Workflow configuration files
│   ├── single_workflow.json     # Main workflow (100 leads)
│   └── workflow_50_leads.json   # Alternative workflow (50 leads)
├── runners/                     # Workflow execution scripts
│   ├── graph_runner.py          # LangGraph implementation
│   ├── langgraph_builder.py     # Sequential runner
│   ├── compare_runners.py       # Performance comparison
│   └── traced_graph_runner.py   # Runner with live tracing
├── utils/                       # Utility and helper scripts
│   ├── simple_output_formatter.py # JSON formatter
│   └── storage_manager.py       # Database/storage management
├── dashboard/                   # Real-time dashboard
│   ├── realtime_dashboard.py    # Flask dashboard server
│   ├── demo_live_tracing.py     # Demo with live traces
│   └── templates/               # HTML templates
├── config/                      # Configuration and setup
│   ├── setup_langgraph.py       # Environment setup
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # API keys (create this)
├── agents/                      # Agent implementations
│   ├── __init__.py             # Agent registry
│   ├── base.py                 # Base agent class
│   ├── utils.py                # Logging utilities
│   ├── prospect_search.py       # Clay/Apollo integration
│   ├── enrichment.py           # Hunter domain search
│   ├── intent_signals.py       # BuiltWith/NewsAPI
│   ├── scoring.py              # ICP scoring logic
│   ├── email_verification.py   # Hunter email verify
│   ├── outreach_content.py     # LLM messaging
│   ├── outreach_executor.py    # SendGrid/Apollo send
│   ├── response_tracker.py     # Response monitoring
│   ├── feedback_trainer.py     # Performance analysis
│   └── feedback_apply.py       # Config optimization
├── outputs/                     # Generated output files
│   └── langgraph_output_graph.mmd # Graph visualization
└── docs/                       # Documentation
    └── README.md               # This file
```

## 🔧 Configuration

### Workflow JSON Structure
```json
{
  "config": {
    "env": { "load_from": "env", "required": ["GROQ_API_KEY", ...] },
    "models": { "llm": { "provider": "groq", "model": "llama-3.1-70b-versatile" } },
    "scoring": { "weights": {...}, "thresholds": {...}, "criteria": {...} },
    "feature_flags": { "auto_apply_feedback": false }
  },
  "steps": [
    {
      "id": "prospect_search",
      "agent": "ProspectSearchAgent",
      "inputs": { "icp": {...}, "signals": [...] },
      "tools": [{ "name": "ClayAPI", "config": {...} }],
      "output_schema": { "leads": [...] }
    }
  ]
}
```

### Placeholder Resolution
- `{{prospect_search.output.leads}}` - Reference previous step outputs
- `{{config.scoring.weights}}` - Access configuration values  
- `{{HUNTER_API_KEY}}` - Environment variable substitution

## 📈 Output Analysis

Both runners produce detailed JSON output with:
- **Step Results**: Structured data from each agent
- **Execution Logs**: Timestamped events (reasoning, API calls, errors)
- **Performance Metrics**: Duration, success rates, API usage
- **Graph Metadata**: Node/edge structure (LangGraph only)

### Key Log Events
- `env_loading` - API key status
- `step_start/step_end` - Execution timing
- `api_call/api_success/api_error` - API interaction details
- `reasoning` - Agent decision logic
- `intermediate` - Processing status

## 🔍 Troubleshooting

### API Keys Not Loading
```bash
# Check .env file exists and has correct format
python setup_langgraph.py

# Verify environment loading
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.environ.get('HUNTER_API_KEY'))"
```

### No API Calls Made
- Check logs for `api_call` events
- Verify API keys are non-empty strings
- Look for `api_error` logs indicating failures
- Confirm endpoint URLs in workflow JSON

### LangGraph Import Errors
```bash
# Install LangGraph dependencies
pip install langgraph langchain-core

# Or use setup script
python setup_langgraph.py
```

## 🤝 Contributing

The system is designed for extensibility:
1. **Add New Agents**: Create in `agents/` and register in `__init__.py`
2. **Modify Workflow**: Edit `single_workflow.json` structure
3. **Custom Tools**: Add API integrations to agent implementations
4. **Enhanced Logic**: Update scoring algorithms or approval flows

## 📝 License

This implementation is for educational and development purposes.

---

## ✅ Step-by-Step Run Guide (Windows)

All files and outputs live in this folder: `c:\Users\parth\OneDrive\Desktop\one\prospect2lead workflow\`.

### 0) Prerequisites

```text
- Windows 10/11 (PowerShell)
- Python 3.10+ (64-bit) available on PATH
- Internet access for API calls
- .env file in this folder with required keys:
  GROQ_API_KEY, CLAY_API_KEY, APOLLO_API_KEY, PDL_API_KEY, HUNTER_API_KEY,
  SHEET_ID (optional), BUILTWITH_API_KEY, NEWS_API_KEY, SENDGRID_API_KEY
```

Optional (for Google Sheets logging): a Service Account JSON and a sheet shared with that service account email.

### 1) Environment Setup (one-time)

From `c:\Users\parth\OneDrive\Desktop\one\prospect2lead workflow\`:

```powershell
# (Optional) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Core dependencies and validation
python config/setup_langgraph.py

# Dashboard dependencies (real-time tracing)
python config/setup_dashboard.py
```

If you prefer manual installs: `pip install -r config/requirements.txt` and `pip install flask flask-socketio eventlet`.

### 2) Run the Lead Generation Workflow (raw output + graph)

Generates raw workflow output and a graph visualization.

```powershell
python runners/graph_runner.py --workflow workflows/single_workflow.json --output outputs/multi_leads_output.json --visualize
```

Outputs written to this folder:
- `outputs/multi_leads_output.json` – full workflow results and logs
- `outputs/langgraph_output_graph.mmd` – graph visualization (Mermaid)

Tip: Adjust how many leads to target by editing `workflows/single_workflow.json` at `steps[].inputs.target_count` (default currently set to 100).

### 3) Convert to Simple JSON (CRM-ready, 50+ leads)

Converts the raw output to a minimal, clean format for easy consumption.

```powershell
python utils/simple_output_formatter.py
```

Outputs:
- `outputs/simple_leads_output.json` – compact leads format (id, company, contact_name, email, domain, role, signal, score, grade)

Note: By default the formatter reads `outputs/multi_leads_output.json`. Ensure step 2 used that output filename.

### 4) End-to-End Run with Storage, Email, Sheets, and Summary (optional)

Runs the full integrated pipeline and produces a complete summary.

```powershell
python runners/integrated_runner.py --workflow workflows/single_workflow.json --campaign "MyCampaign"
```

Outputs:
- `outputs/MyCampaign_raw.json` – raw workflow output
- `outputs/MyCampaign_simple.json` – simple leads JSON
- `outputs/MyCampaign_summary.json` – campaign metrics, next steps, API usage
- `outputs/workflow_memory.db` – SQLite DB (leads, campaigns, email logs)
- `outputs/api_usage.json` – free-tier usage tracking
- `outputs/sheets_fallback_logs.json` – local log if Google Sheets creds not provided

Email delivery (SendGrid/Apollo) sends only if API keys are present and free-tier usage allows.

### 5) Real-Time API Tracing Dashboard (optional)

See live API call traces, step progress, and success rates while the workflow runs.

```powershell
# Start the dashboard and run the workflow with tracing
python runners/traced_graph_runner.py --workflow workflows/single_workflow.json

# OR demo live tracing only
python dashboard/demo_live_tracing.py
```

Dashboard URL: `http://localhost:5000`

You’ll see:
- Workflow status and step progress
- Active/total API calls and success rate
- Live trace feed (api_call_start, api_call_complete, errors)

### 6) Larger Batches (optional)

Example workflow preconfigured for 50 leads:

```powershell
python runners/graph_runner.py --workflow workflows/workflow_50_leads.json --output outputs/leads_50_raw.json
```

Then convert to simple format if desired:

```powershell
python utils/simple_output_formatter.py
```

### 7) Where to Find Outputs (summary)

All outputs are created in `c:\Users\parth\OneDrive\Desktop\one\prospect2lead workflow\outputs\`:
- Raw outputs: `multi_leads_output.json`, `*_raw.json`
- Simple outputs: `simple_leads_output.json`, `*_simple.json`
- Summaries: `*_summary.json`
- Visualization: `langgraph_output_graph.mmd`
- Storage/Logs: `workflow_memory.db`, `api_usage.json`, `sheets_fallback_logs.json`

### 8) Troubleshooting Quick Checks

- **No live traces on dashboard**: Ensure `python config/setup_dashboard.py` ran and visit `http://localhost:5000`. Use `runners/traced_graph_runner.py` to execute with tracing.
- **No leads in simple JSON**: Confirm step 2 wrote `outputs/multi_leads_output.json` before running the formatter.
- **API calls failing**: Verify `config/.env` keys and network; check `api_error` events in the output JSON.
