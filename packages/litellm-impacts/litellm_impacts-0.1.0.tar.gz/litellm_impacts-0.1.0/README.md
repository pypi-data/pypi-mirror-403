# litellm-impacts

Environmental impact metrics callback for [LiteLLM](https://github.com/BerriAI/litellm). Calculates and exposes carbon footprint metrics (energy consumption, CO2 emissions, resource depletion) for LLM API calls using the [EcoLogits](https://github.com/genai-impact/ecologits) library.

## Installation

```bash
pip install litellm-impacts
```

Or with uv:

```bash
uv add litellm-impacts
```

## Usage

### With LiteLLM Proxy (config.yaml)

```yaml
litellm_settings:
  callbacks: custom_callbacks.impacts_callback

model_list:
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
```

Create `custom_callbacks.py` in the same directory:

```python
from litellm_impacts import ImpactsCallback

impacts_callback = ImpactsCallback()
```

### With LiteLLM Python SDK

```python
import litellm
from litellm_impacts import ImpactsCallback

litellm.callbacks = [ImpactsCallback()]

response = litellm.completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Configuration Options

```python
from litellm_impacts import ImpactsCallback

callback = ImpactsCallback(
    prefix="litellm",        # Metric name prefix (default: "litellm")
    server_port=8000,        # Prometheus HTTP server port (default: 8000)
    start_server=True,       # Start built-in HTTP server (default: True)
    labels=["model", "key_alias"],  # Metric labels (default)
)
```

Set `start_server=False` if you're already running a Prometheus HTTP server or want to use a different metrics exposition method.

## Metrics

The callback exposes the following Prometheus metrics (all with min/max variants):

| Metric | Description |
|--------|-------------|
| `{prefix}_energy_kwh_min/max` | Energy consumption in kWh |
| `{prefix}_gwp_kgco2eq_min/max` | Global warming potential in kg CO2 equivalent |
| `{prefix}_adpe_kgsbeq_min/max` | Abiotic depletion potential in kg Sb equivalent |
| `{prefix}_pe_mj_min/max` | Primary energy in megajoules |

Labels:
- `model`: The LLM model name
- `key_alias`: The LiteLLM API key alias (if using proxy)

## Supported Providers

Models are automatically matched to EcoLogits providers:

- OpenAI (gpt-*, o1, o3, o4, chatgpt-*)
- Anthropic (claude-*)
- Google (gemini-*)
- Mistral AI (mistral-*, codestral-*, pixtral-*)
- Cohere (command-*)

Models can also be specified with explicit provider prefixes (e.g., `openai/gpt-4`, `anthropic/claude-3-sonnet`).

## License

MIT
