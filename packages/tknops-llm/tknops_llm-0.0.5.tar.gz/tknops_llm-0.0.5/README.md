# tknOps LLM Analytics SDK

The Python SDK for **tknOps**, an AI cost and usage analytics platform.

## Features

- **Automatic Usage Tracking**: Capture token usage and cost.
- **Privacy-First**: Prompt and response content are **NOT** stored by default.
- **Cost Calculation**: Built-in pricing registry for common models (OpenAI, Anthropic).
- **Environment Tagging**: Tag events as `prod`, `dev`, or `staging`.
- **Framework Support**: Automatic extraction for OpenAI and LangChain response objects.

## Installation

```bash
pip install tknops-llm
```

## Usage

### Initialization

```python
from tknops_llm.client import AIAnalytics

client = AIAnalytics(
    api_key="your_api_key_here", # Get your API Key from the tknOps Dashboard
    environment="prod", # Optional: "prod", "dev", "staging". Default: "prod"
    collect_content=False # Optional: Set to True to collect prompt/response text. Default: False
)
```

### 1. Automatic Tracking (OpenAI / LangChain)

Use `track_response` to automatically extract metrics and **calculate costs** from response objects.

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", ...)
response = llm.invoke("Hello world!")

# Automatically extracts tokens and calculates cost based on model name
client.track_response(
    response=response,
    response_type="langchain", # "openai" or "langchain"
    user_id="user-123",        # Optional: Internal user ID
    feature="summarization",   # Optional: Feature name
    team="marketing",          # Optional: Team or Dept name
    agent="assistant_v1",      # Optional: Specific agent ID
    tags=["bot", "v2-test"]    # Optional: Custom tags for filtering
)
```

### 2. Manual Tracking

If you are using a custom model or provider, you can track events manually.

```python
client.track(
    model="llama-3-8b",
    provider="together-ai",
    input_tokens=150,
    output_tokens=50,
    user_id="user-123",        # Optional: Internal user ID
    feature="adhoc-query",     # Optional: Feature name
    team="data-science",       # Optional: Team name
    agent="research-bot",      # Optional: Agent ID
    cost_usd=0.0002,           # Optional: Calculated by you
    latency_ms=450,            # Optional: Latency in ms
    tags=["custom-model"]      # Optional: Custom tags
)
```

### 3. Content Collection (Privacy)

By default, the SDK **does not** send the prompt or response text to the server. To enable content debugging:

```python
# Initialize with collection enabled
client = AIAnalytics(..., collect_content=True)

# OR pass it explicitly in manual track (only if initialized with True)
client.track(..., prompt_text="My prompt", response_text="My response")
```

### Tracking Parameters

The following parameters can be passed to tracking methods (`track_response`, `track`):

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `user_id` | `str` | **Optional.** The unique ID of the end-user in your system. Used for per-user cost analysis. |
| `feature` | `str` | **Optional.** The name of the feature or module where the AI is used (e.g., "summarization", "chat"). |
| `team` | `str` | **Optional.** The team or department responsible for this usage (e.g., "marketing", "customer-success"). |
| `agent` | `str` | **Optional.** The specific agent or bot identifier (e.g., "assistant_v1", "billing_bot"). |
| `environment`| `str` | **Optional.** The deployment stage. Defaults to `prod`. Common values: `stage`, `prod`, `dev`. |
| `tags` | `List[str]` | **Optional.** A list of custom strings for granular filtering and grouping. |

## Configuration

| Parameter | Description | Default |
| :--- | :--- | :--- |
| `api_key` | Your Project API Key (obtained from tknOps dashboard) | **Required** |
| `environment` | Default environment tag for all events | `"prod"` |
| `collect_content`| If `True`, sends prompt/response text to the server for debugging. | `False` |
