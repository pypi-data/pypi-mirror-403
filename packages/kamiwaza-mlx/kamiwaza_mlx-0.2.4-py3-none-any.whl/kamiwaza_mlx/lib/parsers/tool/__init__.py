from __future__ import annotations

from typing import Dict, List, Optional

from .base import ToolParser
from .openai_json import PARSER as OPENAI_JSON
from .minimax_m2 import PARSER as MINIMAX_M2

_REGISTRY: Dict[str, ToolParser] = {
    "openai-json": OPENAI_JSON,
    "openai_json": OPENAI_JSON,
    "minimax-m2": MINIMAX_M2,
    "minimax_m2": MINIMAX_M2,
}


def get_tool_parser(name: str) -> Optional[ToolParser]:
    return _REGISTRY.get(name)


def list_tool_parsers() -> List[str]:
    return sorted(set(_REGISTRY.keys()))
