"""Agent module for AI-powered summaries."""
from git_release_helper.agents.base import BaseAgent
from git_release_helper.agents.openai import OpenAIAgent

def get_ai_agent(config):
    """Get the appropriate AI agent based on the provider.
    
    Args:
        config: Dictionary containing AI agent configuration
    
    Returns:
        An instance of BaseAgent or None if provider is not supported
    """
    provider = config.get('provider', '').lower()

    if provider == 'openai':
        return OpenAIAgent(config.get('openai', {}))

    return None
