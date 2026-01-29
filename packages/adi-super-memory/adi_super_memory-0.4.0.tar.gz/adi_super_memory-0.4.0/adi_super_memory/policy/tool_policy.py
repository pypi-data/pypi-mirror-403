from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    action: str
    args: Dict[str, str] = field(default_factory=dict)
    risk: str = "low"

@dataclass
class ToolPolicy:
    allowed_tools_by_scope: Dict[str, Set[str]] = field(default_factory=dict)
    denied_tools: Set[str] = field(default_factory=set)
    require_human_approval_risk: Set[str] = field(default_factory=lambda: {"high"})

    def is_allowed(self, scopes: List[str], call: ToolCall) -> bool:
        if call.tool_name in self.denied_tools:
            return False
        if not self.allowed_tools_by_scope:
            return True
        for s in scopes:
            allowed = self.allowed_tools_by_scope.get(s, set())
            if call.tool_name in allowed or "*" in allowed:
                return True
        return False

    def needs_human_approval(self, call: ToolCall) -> bool:
        return call.risk in self.require_human_approval_risk
