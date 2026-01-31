from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .base import ToolParser, ToolPrompt, ToolCalls


def _normalize_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for t in tools or []:
        if "function" in t:
            fn = t.get("function") or {}
            out.append(
                {
                    "name": fn.get("name"),
                    "description": fn.get("description") or "",
                    "parameters": fn.get("parameters") or {},
                }
            )
        else:
            out.append(t)
    return out


def _format_tools_for_template(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for t in tools or []:
        if "function" in t:
            tool = dict(t)
            if tool.get("type") != "function":
                tool["type"] = "function"
            out.append(tool)
        else:
            out.append({"type": "function", "function": t})
    return out


def _tools_block(specs: List[Dict[str, Any]]) -> str:
    inner = []
    for spec in specs:
        inner.append(f"<tool>{json.dumps(spec, ensure_ascii=False)}</tool>")
    return "<tools>\n" + "\n".join(inner) + "\n</tools>"


def _build_tool_prompt(tools: List[Dict[str, Any]], tool_choice: Any, parallel: Any) -> Optional[ToolPrompt]:
    specs = _normalize_tools(tools)
    tools_section = _tools_block(specs)
    instruction = (
        "You may call one or more tools to assist with the user query. "
        "Here are the tools available in JSONSchema format:\n"
        f"{tools_section}\n"
        "When making tool calls, use XML format to invoke tools and pass parameters:\n"
        "<minimax:tool_call>\n"
        "  <invoke name=\"tool-name-1\">\n"
        "    <parameter name=\"param-key-1\">param-value-1</parameter>\n"
        "  </invoke>\n"
        "</minimax:tool_call>\n"
        "Return ONLY the tool call XML when invoking tools."
    )
    return {"role": "system", "content": instruction, "_ephemeral": True}


def _build_forced_prompt(tools: List[Dict[str, Any]], forced_name: str) -> Optional[ToolPrompt]:
    specs = _normalize_tools(tools)
    tools_section = _tools_block(specs)
    instruction = (
        f"You MUST call the function '{forced_name}'.\n"
        "Use XML format to invoke tools and pass parameters:\n"
        "<minimax:tool_call>\n"
        f"  <invoke name=\"{forced_name}\">\n"
        "    <parameter name=\"param-key\">param-value</parameter>\n"
        "  </invoke>\n"
        "</minimax:tool_call>\n"
        f"Available tools:\n{tools_section}"
    )
    return {"role": "system", "content": instruction, "_ephemeral": True}


def _extract_name(name_str: str) -> str:
    name_str = name_str.strip()
    if (name_str.startswith('"') and name_str.endswith('"')) or (name_str.startswith("'") and name_str.endswith("'")):
        return name_str[1:-1]
    return name_str


def _convert_param_value(value: str, param_type: str) -> Any:
    if value.lower() == "null":
        return None
    ptype = (param_type or "string").lower()
    if ptype in ("string", "str", "text"):
        return value
    if ptype in ("integer", "int"):
        try:
            return int(value)
        except Exception:
            return value
    if ptype in ("number", "float"):
        try:
            val = float(value)
            return val if val != int(val) else int(val)
        except Exception:
            return value
    if ptype in ("boolean", "bool"):
        return value.lower() in ("true", "1")
    if ptype in ("object", "array"):
        try:
            return json.loads(value)
        except Exception:
            return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _param_type_lookup(tools: Optional[List[Dict[str, Any]]], fn_name: str) -> Dict[str, str]:
    if not tools:
        return {}
    for t in tools:
        name = t.get("name") or t.get("function", {}).get("name")
        if name != fn_name:
            continue
        params = t.get("parameters") or t.get("function", {}).get("parameters") or {}
        props = params.get("properties") or {}
        out: Dict[str, str] = {}
        for key, meta in props.items():
            if isinstance(meta, dict) and "type" in meta:
                out[key] = str(meta["type"])
        return out
    return {}


def _parse_tool_calls(text: str, tools: Optional[List[Dict[str, Any]]] = None) -> Optional[ToolCalls]:
    if "<minimax:tool_call>" not in text:
        return None
    tool_calls: ToolCalls = []
    try:
        tool_call_regex = re.compile(r"<minimax:tool_call>(.*?)</minimax:tool_call>", re.DOTALL)
        invoke_regex = re.compile(r"<invoke name=(.*?)</invoke>", re.DOTALL)
        parameter_regex = re.compile(r"<parameter name=(.*?)</parameter>", re.DOTALL)
        for tool_block in tool_call_regex.findall(text):
            for invoke_match in invoke_regex.findall(tool_block):
                name_match = re.search(r"^([^>]+)", invoke_match)
                if not name_match:
                    continue
                fn_name = _extract_name(name_match.group(1))
                param_types = _param_type_lookup(tools, fn_name)
                param_dict: Dict[str, Any] = {}
                for match in parameter_regex.findall(invoke_match):
                    param_match = re.search(r"^([^>]+)>(.*)", match, re.DOTALL)
                    if not param_match:
                        continue
                    param_name = _extract_name(param_match.group(1))
                    param_value = param_match.group(2).strip()
                    if param_value.startswith("\n"):
                        param_value = param_value[1:]
                    if param_value.endswith("\n"):
                        param_value = param_value[:-1]
                    param_type = param_types.get(param_name, "string")
                    param_dict[param_name] = _convert_param_value(param_value, param_type)
                args = json.dumps(param_dict, ensure_ascii=False)
                tool_calls.append(
                    {
                        "id": f"call_{len(tool_calls) + 1}",
                        "type": "function",
                        "function": {"name": fn_name, "arguments": args},
                    }
                )
    except Exception:
        return None
    return tool_calls or None


PARSER = ToolParser(
    name="minimax-m2",
    uses_chat_template_tools=True,
    build_tool_prompt=_build_tool_prompt,
    build_forced_prompt=_build_forced_prompt,
    parse_tool_calls=_parse_tool_calls,
    format_tools_for_template=_format_tools_for_template,
)
