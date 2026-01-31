"""Agent role definitions."""

from enum import Enum, auto


class AgentRole(Enum):
    """Defines the role an agent plays in the system."""

    OPERATOR = auto()  # Main agent that interacts with the user
    CODE_REVIEWER = auto()  # Sub-agent for code review tasks
