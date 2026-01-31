from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .base import ToolParser, ToolPrompt, ToolCalls


def _build_tool_prompt(tools: List[Dict[str, Any]], tool_choice: Any, parallel: Any) -> Optional[ToolPrompt]:
    names = ", ".join(t.get("function", {}).get("name") for t in tools if t.get("type") == "function")
    choice_txt = "auto" if tool_choice in (None, "auto") else json.dumps(tool_choice)
    parallel_txt = "true" if (parallel is None or parallel) else "false"
    specs = []
    for t in tools:
        if t.get("type") != "function":
            continue
        fn = t.get("function") or {}
        specs.append(
            {
                "name": fn.get("name"),
                "description": fn.get("description") or "",
                "parameters": fn.get("parameters") or {},
            }
        )
    instruction = (
        "You can call external tools to help answer. "
        f"Available function tools: {names}. "
        f"tool_choice={choice_txt}, parallel_tool_calls={parallel_txt}.\n"
        "When you decide to call tool(s), reply with ONLY a JSON object on a single line of the form:\n"
        '{"tool_calls":[{"id":"call_1","type":"function","function":{"name":"<name>","arguments":{...}}}]}'
        " (no extra commentary). Arguments must be valid JSON. If no tool is needed, reply normally.\n"
        "Tool specs (name, description, parameters JSON Schema):\n" + json.dumps(specs, ensure_ascii=False)
    )
    return {"role": "user", "content": instruction, "_ephemeral": True}


def _build_forced_prompt(tools: List[Dict[str, Any]], forced_name: str) -> Optional[ToolPrompt]:
    spec = None
    for t in tools or []:
        fn = t.get("function") or {}
        if t.get("type") == "function" and fn.get("name") == forced_name:
            spec = t
            break
    schema = (spec.get("function", {}).get("parameters") if spec else {}) or {}
    example = "{}"
    try:
        req = (schema or {}).get("required") or []
        props = (schema or {}).get("properties") or {}
        ex = {k: ("string" if (props.get(k, {}).get("type") == "string") else 0) for k in req}
        example = json.dumps(ex) if ex else "{}"
    except Exception:
        pass
    instruction = (
        f"You MUST call the function '{forced_name}'.\n"
        "Reply with ONLY the JSON arguments object for that function on a single line, no code fences, no commentary.\n"
        f"Example: {example}\n"
        "JSON Schema for arguments: " + json.dumps(schema, ensure_ascii=False)
    )
    return {"role": "user", "content": instruction, "_ephemeral": True}


def _parse_tool_calls(text: str, tools: Optional[List[Dict[str, Any]]] = None) -> Optional[ToolCalls]:
    s = text.strip()
    m = re.search(r"```json\\s*(\\{[\\s\\S]*?\\})\\s*```", s, re.IGNORECASE)
    if m:
        s = m.group(1)
    if "{" in s and not s.lstrip().startswith("{"):
        s = s[s.find("{") :]
    try:
        obj = json.loads(s)
    except Exception:
        return None
    calls = None
    if isinstance(obj, dict):
        if "tool_calls" in obj and isinstance(obj["tool_calls"], list):
            calls = obj["tool_calls"]
        elif "function_call" in obj and isinstance(obj["function_call"], dict):
            fc = obj["function_call"]
            calls = [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": fc.get("name", ""), "arguments": fc.get("arguments", {})},
                }
            ]
    if not calls:
        return None
    normd = []
    for i, c in enumerate(calls):
        fn = c.get("function", {})
        args = fn.get("arguments", {})
        if not isinstance(args, str):
            try:
                args = json.dumps(args, ensure_ascii=False)
            except Exception:
                args = str(args)
        cid = c.get("id") or f"call_{i+1}"
        normd.append({"id": cid, "type": "function", "function": {"name": fn.get("name", ""), "arguments": args}})
    return normd


PARSER = ToolParser(
    name="openai-json",
    uses_chat_template_tools=False,
    build_tool_prompt=_build_tool_prompt,
    build_forced_prompt=_build_forced_prompt,
    parse_tool_calls=_parse_tool_calls,
)
