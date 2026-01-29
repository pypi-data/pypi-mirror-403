# 🚀 Abhanti - Universal AI Client

**Works out of the box with FREE endpoint!**
```python
from abhanti import ai

# Works immediately - no setup needed!
response = ai("What is Python?")
print(response)
```

## ✨ Features

- ✅ **Zero config** - works instantly
- ✅ **FREE by default** - uses llm7.io
- ✅ **Universal** - supports ollama.com, OpenAI, etc.
- ✅ **Smart API keys** - prompts when needed
- ✅ **Model discovery** - fetch available models
- ✅ **LangChain compatible**

## 📦 Installation
```bash
pip install abhanti
```

## 🚀 Quick Start

### Zero Config (FREE)
```python
from abhanti import ai

print(ai("What is 2+2?"))
print(ai("Explain AI"))
```

### Ollama.com (with API key)
```python
from abhanti import AIClient

# Get API key from: https://ollama.com/account
client = AIClient(
    url="https://ollama.com/v1",
    api_key="your-ollama-key"
)

# Get available models
models = client.get_available_models()
print([m['name'] for m in models])

# Use specific model
client.model = "gpt-oss:120b"
response = client.ask("Hello!")
```

### Environment Variables
```bash
export ABHANTI_URL="https://ollama.com/v1"
export ABHANTI_API_KEY="your-key"
export ABHANTI_MODEL="gpt-oss:120b"
```

## 🔥 Supported Providers

- **llm7.io** (FREE, default)
- **ollama.com** (requires API key)
- **OpenAI** (requires API key)
- **Groq** (requires API key)
- **Anthropic** (requires API key)

## 📖 Examples

See `examples/` folder for more examples.

## 📄 License

MIT License
