"""Agent infrastructure for orchestrating AI assistants."""

from hypergolic.agents.interrupts import prepare_interrupted_history
from hypergolic.agents.roles import AgentRole
from hypergolic.agents.trace import SubAgentTrace, ToolCallRecord

__all__ = [
    "AgentRole",
    "prepare_interrupted_history",
    "SubAgentTrace",
    "ToolCallRecord",
]
