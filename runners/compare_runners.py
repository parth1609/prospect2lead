import json
import time
import argparse
from typing import Dict, Any

from langgraph_builder import run_workflow as run_sequential
from graph_runner import run_langgraph_workflow


def compare_outputs(sequential_result: Dict[str, Any], langgraph_result: Dict[str, Any]) -> None:
    print("📊 Comparing Sequential vs LangGraph Results\n")
    
    print("="*60)
    print("EXECUTION METADATA")
    print("="*60)
    
    seq_steps = len(sequential_result.get("results", {}).get("_logs", {}).keys())
    lg_steps = len(langgraph_result.get("results", {}))
    
    print(f"Sequential Runner: {seq_steps} steps executed")
    print(f"LangGraph Runner:  {lg_steps} steps executed")
    
    if "execution_metadata" in langgraph_result:
        metadata = langgraph_result["execution_metadata"]
        print(f"Graph Structure:")
        print(f"  Nodes: {metadata.get('graph_structure', {}).get('nodes', [])}")
        print(f"  Edges: {len(metadata.get('graph_structure', {}).get('edges', []))}")
    
    print("\n" + "="*60)
    print("STEP OUTPUTS COMPARISON")
    print("="*60)
    
    seq_results = sequential_result.get("results", {})
    lg_results = langgraph_result.get("results", {})
    
    common_steps = set(seq_results.keys()) & set(lg_results.keys())
    common_steps = {s for s in common_steps if not s.startswith("_")}
    
    for step in sorted(common_steps):
        print(f"\n🔹 {step}:")
        
        seq_output = seq_results.get(step, {}).get("output", {})
        lg_output = lg_results.get(step, {}).get("output", {})
        
        if seq_output == lg_output:
            print("  ✅ Outputs identical")
        else:
            print("  ⚠️  Outputs differ")
            
            seq_keys = set(seq_output.keys()) if isinstance(seq_output, dict) else set()
            lg_keys = set(lg_output.keys()) if isinstance(lg_output, dict) else set()
            
            if seq_keys != lg_keys:
                print(f"    Key differences: {seq_keys.symmetric_difference(lg_keys)}")
            
            # Check specific differences for key fields
            if isinstance(seq_output, dict) and isinstance(lg_output, dict):
                for key in seq_keys & lg_keys:
                    if seq_output.get(key) != lg_output.get(key):
                        if isinstance(seq_output.get(key), list) and isinstance(lg_output.get(key), list):
                            print(f"    {key}: lengths {len(seq_output[key])} vs {len(lg_output[key])}")
                        else:
                            print(f"    {key}: values differ")
    
    print("\n" + "="*60)
    print("LOGGING COMPARISON")
    print("="*60)
    
    seq_logs = sequential_result.get("logs", {})
    lg_logs = langgraph_result.get("logs", {})
    
    seq_log_count = sum(len(logs) for logs in seq_logs.values())
    lg_log_count = sum(len(logs) for logs in lg_logs.values())
    
    print(f"Sequential logs: {seq_log_count} entries across {len(seq_logs)} steps")
    print(f"LangGraph logs:  {lg_log_count} entries across {len(lg_logs)} steps")
    
    # Check for API calls
    seq_api_calls = sum(1 for logs in seq_logs.values() for log in logs if log.get("type") == "api_call")
    lg_api_calls = sum(1 for logs in lg_logs.values() for log in logs if log.get("type") == "api_call")
    
    print(f"API calls - Sequential: {seq_api_calls}, LangGraph: {lg_api_calls}")


def main():
    parser = argparse.ArgumentParser(description="Compare Sequential vs LangGraph workflow execution")
    parser.add_argument("--workflow", default="single_workflow.json", help="Workflow JSON file")
    
    args = parser.parse_args()
    
    print("🚀 Running Workflow Comparison\n")
    
    print("1️⃣ Running Sequential Runner...")
    start_time = time.time()
    sequential_result = run_sequential(args.workflow, "sequential_output.json")
    sequential_time = time.time() - start_time
    print(f"   ⏱️  Completed in {sequential_time:.2f}s")
    
    print("\n2️⃣ Running LangGraph Runner...")
    start_time = time.time()
    langgraph_result = run_langgraph_workflow(args.workflow, "langgraph_output.json")
    langgraph_time = time.time() - start_time
    print(f"   ⏱️  Completed in {langgraph_time:.2f}s")
    
    print(f"\n⚡ Performance: LangGraph was {sequential_time/langgraph_time:.1f}x the speed of Sequential")
    
    print("\n3️⃣ Analyzing Results...")
    compare_outputs(sequential_result, langgraph_result)
    
    print("\n✅ Comparison complete!")
    print("📁 Output files: sequential_output.json, langgraph_output.json")


if __name__ == "__main__":
    main()
