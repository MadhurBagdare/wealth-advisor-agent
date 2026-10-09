from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import logging


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)


class BaseTool(ABC):
    """Abstract interface that all tools must implement.

    Agents interact with external systems exclusively through tools,
    keeping the agent logic decoupled from I/O specifics.
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"tool.{name}")

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Run the tool with given parameters and return a structured result."""

    def validate_params(self, **kwargs) -> bool:
        """Optional pre-execution validation. Override for custom checks."""
        return True

    def __repr__(self):
        return f"<Tool: {self.name}>"
