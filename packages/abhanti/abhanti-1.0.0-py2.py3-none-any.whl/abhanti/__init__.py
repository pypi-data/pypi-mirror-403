"""
Abhanti - Universal AI Client
Works out of the box with FREE endpoint!

Usage:
    from abhanti import ai
    response = ai("What is Python?")
    print(response)

Homepage: https://github.com/yourusername/abhanti
"""

from .client import AIClient
from .exceptions import AbhantiError, ProviderError, ConfigError

__version__ = "1.0.0"
__author__ = "Abhishek"
__email__ = "abhishek@example.com"
__all__ = ["AIClient", "ai", "configure", "reset"]

# Global client instance
_default_client = None


def ai(prompt: str, **kwargs) -> str:
    """
    Ask AI a question - Works immediately with FREE endpoint!
    
    Args:
        prompt: Your question
        **kwargs: temperature, max_tokens, etc.
    
    Returns:
        AI response
    
    Examples:
        >>> from abhanti import ai
        >>> ai("What is 2+2?")
        '4'
    """
    global _default_client
    if _default_client is None:
        _default_client = AIClient()
    return _default_client.ask(prompt, **kwargs)


def configure(**kwargs):
    """
    Configure default client
    
    Examples:
        >>> from abhanti import configure, ai
        >>> configure(url="https://ollama.com/v1", api_key="your-key")
        >>> ai("Hello!")
    """
    global _default_client
    _default_client = AIClient(**kwargs)


def reset():
    """Reset to default configuration"""
    global _default_client
    _default_client = None
