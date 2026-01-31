from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

ToolPrompt = Dict[str, Any]
ToolCalls = List[Dict[str, Any]]


def _identity_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return list(tools or [])


@dataclass(frozen=True)
class ToolParser:
    name: str
    uses_chat_template_tools: bool
    build_tool_prompt: Callable[[List[Dict[str, Any]], Any, Any], Optional[ToolPrompt]]
    build_forced_prompt: Callable[[List[Dict[str, Any]], str], Optional[ToolPrompt]]
    parse_tool_calls: Callable[[str, Optional[List[Dict[str, Any]]]], Optional[ToolCalls]]
    format_tools_for_template: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]] = _identity_tools
