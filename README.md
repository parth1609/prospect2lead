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
```bash
python graph_runner.py --workflow single_workflow.json --visualize
```

**Option B: Sequential Runner (Simple)**
```bash
python langgraph_builder.py --workflow single_workflow.json
```

**Option C: Compare Both**
```bash
python compare_runners.py --workflow single_workflow.json
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

## 📁 File Structure

```
prospect2lead workflow/
├── single_workflow.json      # Workflow configuration
├── .env                      # API keys (create this)
├── graph_runner.py          # LangGraph implementation
├── langgraph_builder.py     # Sequential runner
├── compare_runners.py       # Performance comparison
├── setup_langgraph.py       # Setup and validation
├── agents/                  # Agent implementations
│   ├── __init__.py         # Agent registry
│   ├── base.py             # Base agent class
│   ├── utils.py            # Logging utilities
│   ├── prospect_search.py   # Clay/Apollo integration
│   ├── enrichment.py       # Hunter domain search
│   ├── intent_signals.py   # BuiltWith/NewsAPI
│   ├── scoring.py          # ICP scoring logic
│   ├── email_verification.py # Hunter email verify
│   ├── outreach_content.py # LLM messaging
│   ├── outreach_executor.py # SendGrid/Apollo send
│   ├── response_tracker.py # Response monitoring
│   ├── feedback_trainer.py # Performance analysis
│   └── feedback_apply.py   # Config optimization
└── requirements.txt        # Python dependencies
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
