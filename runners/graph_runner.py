import argparse
import json
import os
import time
from typing import Any, Dict, List, Optional, TypedDict

try:
    from dotenv import load_dotenv
    # Try to load .env from config directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)  # Go up to project root
    env_path = os.path.join(parent_dir, "config", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    else:
        # Fallback: try from script directory
        env_path = os.path.join(script_dir, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
except ImportError:
    pass

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# Use absolute imports instead of relative imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents import AGENTS as AGENT_REGISTRY
from agents.utils import _log, _sanitize_tools


class WorkflowState(TypedDict):
    config: Dict[str, Any]
    memory: Dict[str, Any]
    logs: Dict[str, List[Dict[str, Any]]]
    current_step: Optional[str]
    
    # Step outputs
    prospect_search_output: Optional[Dict[str, Any]]
    pre_enrichment_output: Optional[Dict[str, Any]]
    enrichment_output: Optional[Dict[str, Any]]
    third_party_enrichment_output: Optional[Dict[str, Any]]
    intent_signals_output: Optional[Dict[str, Any]]
    scoring_output: Optional[Dict[str, Any]]
    email_verification_output: Optional[Dict[str, Any]]
    outreach_content_output: Optional[Dict[str, Any]]
    send_output: Optional[Dict[str, Any]]
    response_tracking_output: Optional[Dict[str, Any]]
    feedback_trainer_output: Optional[Dict[str, Any]]
    feedback_apply_output: Optional[Dict[str, Any]]


def _deep_get(data: Any, path: str) -> Any:
    cur = data
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    return cur


def _resolve_placeholders(obj: Any, state: WorkflowState) -> Any:
    if isinstance(obj, str):
        m = __import__("re").fullmatch(r"\{\{\s*([^}]+)\s*\}\}", obj)
        if m:
            path = m.group(1)
            if path.startswith("config."):
                v = _deep_get(state["config"], path[7:])
            elif "." in path and path.split(".")[0] in state["memory"]:
                v = _deep_get(state["memory"], path)
            elif path in state["memory"]:
                v = state["memory"][path]
            elif "output" in path:
                step_name = path.split(".")[0]
                output_key = f"{step_name}_output"
                if output_key in state and state[output_key]:
                    remaining_path = ".".join(path.split(".")[1:])
                    v = _deep_get(state[output_key], remaining_path)
                else:
                    v = None
            else:
                v = None
            return _resolve_placeholders(v, state) if v is not None else None
        
        def repl(match):
            key = match.group(1).strip()
            if key.startswith("config."):
                v = _deep_get(state["config"], key[7:])
            elif key in state["memory"]:
                v = state["memory"][key]
            elif "output" in key:
                step_name = key.split(".")[0]
                output_key = f"{step_name}_output"
                if output_key in state and state[output_key]:
                    remaining_path = ".".join(key.split(".")[1:])
                    v = _deep_get(state[output_key], remaining_path)
                else:
                    v = None
            else:
                v = None
            return "" if v is None else str(v)
        
        return __import__("re").sub(r"\{\{\s*([^}]+)\s*\}\}", repl, obj)
    
    if isinstance(obj, list):
        return [_resolve_placeholders(v, state) for v in obj]
    if isinstance(obj, dict):
        return {k: _resolve_placeholders(v, state) for k, v in obj.items()}
    return obj


def create_agent_node(step_config: Dict[str, Any]):
    def agent_node(state: WorkflowState) -> WorkflowState:
        step_id = step_config.get("id")
        agent_name = step_config.get("agent")
        agent_cls = AGENT_REGISTRY.get(agent_name)
        
        if not agent_cls:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        state["current_step"] = step_id
        
        inputs = _resolve_placeholders(step_config.get("inputs", {}), state)
        tools = _resolve_placeholders(step_config.get("tools", []), state)
        
        t0 = time.time()
        _log(state["memory"], step_id, "step_start", {"agent": agent_name, "input_keys": list(inputs.keys())})
        
        agent = agent_cls()
        output = agent.run(inputs=inputs, tools=tools, config=state["config"], memory=state["memory"])
        
        dt = int((time.time() - t0) * 1000)
        _log(state["memory"], step_id, "step_end", {"duration_ms": dt, "output_keys": list(output.keys())})
        
        # Store output in state
        output_key = f"{step_id}_output"
        state[output_key] = output
        
        # Also store in memory for backwards compatibility
        state["memory"][step_id] = {"output": output}
        
        # Copy logs from memory to state
        state["logs"] = state["memory"].get("_logs", {})
        
        return state
    
    return agent_node


def build_graph_from_workflow(workflow_config: Dict[str, Any]) -> StateGraph:
    graph = StateGraph(WorkflowState)
    
    steps = workflow_config.get("steps", [])
    
    # Add nodes for each step
    for step in steps:
        step_id = step.get("id")
        node_func = create_agent_node(step)
        graph.add_node(step_id, node_func)
    
    # Add edges sequentially (can be enhanced for conditional flows)
    if steps:
        graph.add_edge(START, steps[0]["id"])
        
        for i in range(len(steps) - 1):
            current_step = steps[i]["id"]
            next_step = steps[i + 1]["id"]
            graph.add_edge(current_step, next_step)
        
        graph.add_edge(steps[-1]["id"], END)
    
    return graph


def run_langgraph_workflow(workflow_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_config = json.load(f)
    
    # Initialize state
    config = workflow_config.get("config", {})
    memory: Dict[str, Any] = {"config": config, "_logs": {}}
    
    # Load environment variables
    env_cfg = config.get("env", {})
    if env_cfg.get("load_from") == "env":
        loaded_keys = []
        for key in env_cfg.get("required", []):
            value = os.environ.get(key)
            memory[key] = value
            loaded_keys.append({"key": key, "loaded": bool(value), "length": len(value) if value else 0})
        _log(memory, None, "env_loading", {"keys": loaded_keys})
    
    initial_state: WorkflowState = {
        "config": config,
        "memory": memory,
        "logs": {},
        "current_step": None,
        "prospect_search_output": None,
        "pre_enrichment_output": None,
        "enrichment_output": None,
        "third_party_enrichment_output": None,
        "intent_signals_output": None,
        "scoring_output": None,
        "email_verification_output": None,
        "outreach_content_output": None,
        "send_output": None,
        "response_tracking_output": None,
        "feedback_trainer_output": None,
        "feedback_apply_output": None,
    }
    
    # Build and compile the graph
    graph = build_graph_from_workflow(workflow_config)
    app = graph.compile()
    
    # Execute the graph
    final_state = app.invoke(initial_state)
    
    # Prepare result
    result = {
        "workflow_name": workflow_config.get("workflow_name"),
        "config": final_state["config"],
        "results": {
            step["id"]: {"output": final_state.get(f"{step['id']}_output")}
            for step in workflow_config.get("steps", [])
            if final_state.get(f"{step['id']}_output") is not None
        },
        "logs": final_state["logs"],
        "execution_metadata": {
            "graph_structure": {
                "nodes": [step["id"] for step in workflow_config.get("steps", [])],
                "edges": [(workflow_config["steps"][i]["id"], workflow_config["steps"][i+1]["id"]) 
                         for i in range(len(workflow_config.get("steps", [])) - 1)]
            },
            "agent_mapping": {
                step["id"]: step["agent"] 
                for step in workflow_config.get("steps", [])
            }
        }
    }
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Run LangGraph-based prospect-to-lead workflow")
    parser.add_argument("--workflow", default="single_workflow.json", help="Path to workflow JSON file")
    parser.add_argument("--output", default="langgraph_output.json", help="Path to output JSON file")
    parser.add_argument("--visualize", action="store_true", help="Generate graph visualization")
    
    args = parser.parse_args()
    
    result = run_langgraph_workflow(args.workflow, args.output)
    
    if args.visualize:
        try:
            with open(args.workflow, "r") as f:
                workflow_config = json.load(f)
            graph = build_graph_from_workflow(workflow_config)
            app = graph.compile()
            
            # Generate mermaid diagram
            mermaid_path = args.output.replace(".json", "_graph.mmd")
            with open(mermaid_path, "w") as f:
                f.write("graph TD\n")
                f.write("    START([START])\n")
                for step in workflow_config.get("steps", []):
                    step_id = step["id"]
                    agent_name = step["agent"]
                    f.write(f"    {step_id}[{agent_name}]\n")
                f.write("    END([END])\n")
                f.write(f"    START --> {workflow_config['steps'][0]['id']}\n")
                for i in range(len(workflow_config.get("steps", [])) - 1):
                    current = workflow_config["steps"][i]["id"]
                    next_step = workflow_config["steps"][i+1]["id"]
                    f.write(f"    {current} --> {next_step}\n")
                f.write(f"    {workflow_config['steps'][-1]['id']} --> END\n")
            
            print(f"Graph visualization saved to: {mermaid_path}")
            
        except Exception as e:
            print(f"Visualization failed: {e}")
    
    print(f"Workflow completed. Results saved to: {args.output}")
    print(f"Total steps executed: {len(result.get('results', {}))}")
    
    return result


if __name__ == "__main__":
    main()
