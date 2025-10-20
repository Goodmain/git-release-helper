"""Base class for AI agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAgent(ABC):
    """Base class that all agent implementations must inherit from."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the agent with configuration.

        Args:
            config: Dictionary containing agent configuration
        """
        self.config = config

    @abstractmethod
    def generate_summary(self, commit_messages: list) -> Optional[str]:
        """Generate a summary based on commit messages.

        Args:
            commit_messages: List of commit messages to summarize

        Returns:
            A summary string or None if generation fails
        """
