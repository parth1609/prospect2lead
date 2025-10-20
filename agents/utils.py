from typing import Any, Dict, Optional
import time


def _sanitize_tools(tools: Any) -> Any:
    if isinstance(tools, list):
        return [_sanitize_tools(t) for t in tools]
    if isinstance(tools, dict):
        out = {}
        for k, v in tools.items():
            if isinstance(k, str) and k.lower() in {"api_key", "authorization", "token"}:
                out[k] = "***"
            else:
                out[k] = _sanitize_tools(v)
        return out
    return tools


def _log(memory: Dict[str, Any], step_id: Optional[str], event_type: str, data: Dict[str, Any]) -> None:
    logs = memory.setdefault("_logs", {})
    if not step_id:
        step_id = "_global"
    arr = logs.setdefault(step_id, [])
    arr.append({"ts": int(time.time() * 1000), "type": event_type, "data": data})
