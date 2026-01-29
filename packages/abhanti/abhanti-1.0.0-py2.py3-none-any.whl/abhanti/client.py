"""
AIClient - Universal LLM client with smart defaults
"""

import os
import warnings
import requests
from typing import Optional, Dict, Any, List

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['NO_PROXY'] = '*'


class AIClient:
    """
    Universal AI Client - Works out of the box!
    
    Default: FREE https://api.llm7.io/v1 endpoint (no API key needed!)
    
    Features:
        - Works immediately with NO setup
        - Auto-detects provider from URL
        - Smart API key handling
        - Fetches available models for ollama.com
    
    Examples:
        # Zero config (uses FREE endpoint)
        >>> client = AIClient()
        >>> client.ask("What is Python?")
        
        # Ollama.com (requires API key)
        >>> client = AIClient(
        ...     url="https://ollama.com/v1",
        ...     api_key="your-ollama-key"
        ... )
        >>> models = client.get_available_models()
        >>> client.ask("Hello!")
    """
    
    # 🔥 CORRECT DEFAULTS - FREE & WORKING!
    DEFAULT_URL = "https://api.llm7.io/v1"
    DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"
    DEFAULT_API_KEY = "unused"
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_MAX_TOKENS = 2000
    DEFAULT_TIMEOUT = 120
    
    # Provider patterns
    PROVIDER_PATTERNS = {
        'llm7': ['llm7.io', 'api.llm7.io'],
        'ollama': ['ollama.com', 'api.ollama.com'],
        'openai': ['api.openai.com', 'openai.com/v1'],
        'groq': ['groq.com', 'api.groq.com'],
        'anthropic': ['anthropic.com', 'api.anthropic.com'],
    }
    
    # Providers that REQUIRE API keys
    REQUIRES_API_KEY = ['ollama', 'openai', 'groq', 'anthropic']
    
    def __init__(
        self,
        url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize AI Client
        
        Args:
            url: API endpoint (default: https://api.llm7.io/v1)
            model: Model name (default: gpt-4o-mini-2024-07-18)
            api_key: API key (default: unused for llm7)
            temperature: Sampling temperature (default: 0.1)
            max_tokens: Max response tokens (default: 2000)
            timeout: Request timeout (default: 120s)
        """
        
        # Load settings
        self.url = url or os.getenv("ABHANTI_URL") or self.DEFAULT_URL
        self.model = model or os.getenv("ABHANTI_MODEL") or self.DEFAULT_MODEL
        self.temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens is not None else self.DEFAULT_MAX_TOKENS
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        
        # Detect provider
        self.provider = self._detect_provider(self.url)
        
        # Smart API key handling
        self.api_key = self._get_api_key(api_key)
        
        # Initialize
        self._init_client()
        
        if os.getenv("ABHANTI_DEBUG") == "1":
            print(f"✅ Abhanti: {self.provider} | {self.model} | {self.url}")
    
    def _detect_provider(self, url: str) -> str:
        """Auto-detect provider"""
        url_lower = url.lower()
        for provider, patterns in self.PROVIDER_PATTERNS.items():
            if any(p in url_lower for p in patterns):
                return provider
        return 'openai'  # Default
    
    def _get_api_key(self, provided_key: Optional[str]) -> str:
        """
        Smart API key handling
        
        Priority:
        1. Provided key
        2. Environment variable ABHANTI_API_KEY
        3. Provider-specific env var
        4. Default based on provider
        """
        
        # 1. Provided key
        if provided_key:
            return provided_key
        
        # 2. ABHANTI_API_KEY
        if os.getenv("ABHANTI_API_KEY"):
            return os.getenv("ABHANTI_API_KEY")
        
        # 3. Provider-specific env vars
        provider_env_vars = {
            'openai': 'OPENAI_API_KEY',
            'groq': 'GROQ_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'ollama': 'OLLAMA_API_KEY',
        }
        
        if self.provider in provider_env_vars:
            env_var = provider_env_vars[self.provider]
            if os.getenv(env_var):
                return os.getenv(env_var)
        
        # 4. Default based on provider
        if self.provider in self.REQUIRES_API_KEY:
            if self.provider == 'ollama':
                print(f"\n⚠️  Ollama.com requires API key!")
                print(f"   Get yours from: https://ollama.com/account")
                print(f"   Then set: AIClient(api_key='your-key')")
                print()
            return "PLEASE_SET_YOUR_API_KEY"
        
        # llm7 doesn't need API key
        return "unused"
    
    def _init_client(self):
        """Initialize OpenAI-compatible client"""
        try:
            from openai import OpenAI
            import httpx
            
            # HTTP client with SSL bypass
            http_client = httpx.Client(
                verify=False,
                timeout=self.timeout,
                transport=httpx.HTTPTransport(retries=3, verify=False)
            )
            
            self.client = OpenAI(
                base_url=self.url,
                api_key=self.api_key,
                http_client=http_client,
                max_retries=3,
                timeout=self.timeout,
            )
        except ImportError:
            raise ImportError(
                "Install dependencies:\n"
                "  pip install openai httpx"
            )
    
    def ask(self, prompt: str, **kwargs) -> str:
        """
        Ask a question
        
        Args:
            prompt: Your question
            **kwargs: Override settings
        
        Returns:
            AI response
        
        Examples:
            >>> client = AIClient()
            >>> client.ask("What is 2+2?")
            '4'
        """
        temp = kwargs.get('temperature', self.temperature)
        max_tok = kwargs.get('max_tokens', self.max_tokens)
        
        # Check API key
        if self.api_key == "PLEASE_SET_YOUR_API_KEY":
            raise ValueError(
                f"\n❌ API key required for {self.provider}!\n"
                f"Set it via:\n"
                f"  1. Code: AIClient(api_key='your-key')\n"
                f"  2. Environment: export ABHANTI_API_KEY='your-key'\n"
            )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=max_tok,
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error = str(e).lower()
            
            if "connection" in error or "connect" in error:
                raise ConnectionError(
                    f"❌ Cannot connect to {self.url}\n"
                    f"💡 Check your internet connection\n"
                )
            elif "timeout" in error:
                raise TimeoutError(
                    f"⏰ Timeout after {self.timeout}s\n"
                    f"💡 Try: AIClient(timeout=180)\n"
                )
            elif "401" in error or "unauthorized" in error:
                raise PermissionError(
                    f"🔐 Invalid API key for {self.provider}\n"
                    f"💡 Check your API key\n"
                )
            elif "404" in error or "not found" in error:
                raise ValueError(
                    f"❌ Model '{self.model}' not found\n"
                    f"💡 Use: client.get_available_models()\n"
                )
            else:
                raise Exception(f"❌ Error: {str(e)}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get available models for current provider
        
        Returns:
            List of available models
        
        Examples:
            >>> client = AIClient(url="https://ollama.com/v1", api_key="your-key")
            >>> models = client.get_available_models()
            >>> print([m['name'] for m in models])
        """
        
        if self.provider == 'ollama':
            # Fetch from ollama.com/api/tags
            try:
                response = requests.get(
                    "https://ollama.com/api/tags",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get('models', [])
                    
                    # Format models
                    return [
                        {
                            'name': m['name'],
                            'model': m['model'],
                            'size': m.get('size', 0),
                            'modified_at': m.get('modified_at', ''),
                        }
                        for m in models
                    ]
                else:
                    print(f"⚠️  Failed to fetch models: HTTP {response.status_code}")
                    return []
                    
            except Exception as e:
                print(f"⚠️  Failed to fetch models: {e}")
                return []
        
        elif self.provider == 'llm7':
            # llm7 supported models (known list)
            return [
                {'name': 'gpt-4o-mini-2024-07-18', 'size': 0},
                {'name': 'gpt-4o', 'size': 0},
                {'name': 'gpt-4-turbo', 'size': 0},
            ]
        
        elif self.provider == 'openai':
            # OpenAI models (use API)
            try:
                models = self.client.models.list()
                return [{'name': m.id, 'size': 0} for m in models.data]
            except:
                return [
                    {'name': 'gpt-4', 'size': 0},
                    {'name': 'gpt-3.5-turbo', 'size': 0},
                ]
        
        else:
            return []
    
    @classmethod
    def from_config(cls, config_path: str):
        """Load from YAML config"""
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return cls(**config)
    
    def test(self) -> bool:
        """Test connection"""
        try:
            response = self.ask("Say OK")
            return "ok" in response.lower()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def info(self) -> Dict[str, Any]:
        """Get config info"""
        return {
            "provider": self.provider,
            "model": self.model,
            "url": self.url,
            "api_key_set": self.api_key not in ["unused", "PLEASE_SET_YOUR_API_KEY"],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """Allow direct calling"""
        return self.ask(prompt, **kwargs)
    
    def __repr__(self):
        return f"AIClient({self.provider}:{self.model})"


# LangChain support
try:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import AIMessage, HumanMessage
    from typing import List
    
    class LangChainAIClient(BaseChatModel):
        """LangChain wrapper"""
        
        def __init__(self, **kwargs):
            super().__init__()
            self.client = AIClient(**kwargs)
        
        @property
        def _llm_type(self) -> str:
            return f"abhanti_{self.client.provider}"
        
        def _generate(self, messages: List, stop=None, **kwargs):
            prompt = "\n".join([m.content for m in messages])
            response = self.client.ask(prompt, **kwargs)
            return AIMessage(content=response)
        
        def ask(self, prompt: str) -> str:
            return self.client.ask(prompt)

except ImportError:
    pass
