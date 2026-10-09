from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import logging

from memory import ShortTermMemory


@dataclass
class AgentResult:
    success: bool
    data: Any = None
    error: str = ""
    agent_name: str = ""
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Contract that every agent in the system fulfils.

    Each agent receives shared short-term memory so it can read context
    left by upstream agents and write its own outputs for downstream ones.
    """

    def __init__(self, name: str, memory: ShortTermMemory):
        self.name = name
        self.memory = memory
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    def run(self, context: dict) -> AgentResult:
        """Execute this agent's core responsibility."""

    def _success(self, data: Any, **meta) -> AgentResult:
        return AgentResult(success=True, data=data, agent_name=self.name, metadata=meta)

    def _failure(self, error: str) -> AgentResult:
        self.logger.error("Agent %s failed: %s", self.name, error)
        return AgentResult(success=False, error=error, agent_name=self.name)

    def __repr__(self):
        return f"<Agent: {self.name}>"
