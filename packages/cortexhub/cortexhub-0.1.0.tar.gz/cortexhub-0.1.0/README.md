# CortexHub Python SDK

**Runtime Governance for AI Agents** - Policy enforcement, PII/secrets detection, complete audit trails with OpenTelemetry.

## Installation

```bash
# Core SDK
pip install cortexhub

# With framework support (choose one or more)
pip install cortexhub[langchain]      # LangChain/LangGraph
pip install cortexhub[crewai]         # CrewAI
pip install cortexhub[openai-agents]  # OpenAI Agents SDK
pip install cortexhub[llamaindex]     # LlamaIndex
pip install cortexhub[litellm]        # LiteLLM

# All frameworks (for development)
pip install cortexhub[all]
```

## Quick Start

```python
from cortexhub import init, Framework

# Initialize CortexHub FIRST, before importing your framework
cortex = init(
    agent_id="customer_support_agent",
    framework=Framework.LANGCHAIN,  # or CREWAI, OPENAI_AGENTS, etc.
)

# Now import and use your framework
from langchain_core.tools import tool

@tool
def process_refund(customer_id: str, amount: float) -> dict:
    """Process a customer refund."""
    return {"status": "processed", "amount": amount}

# All tool calls are now governed!
```

## Supported Frameworks

| Framework | Enum Value | Install |
|-----------|------------|---------|
| LangChain | `Framework.LANGCHAIN` | `pip install cortexhub[langchain]` |
| LangGraph | `Framework.LANGCHAIN` | `pip install cortexhub[langchain]` |
| CrewAI | `Framework.CREWAI` | `pip install cortexhub[crewai]` |
| OpenAI Agents | `Framework.OPENAI_AGENTS` | `pip install cortexhub[openai-agents]` |
| LlamaIndex | `Framework.LLAMAINDEX` | `pip install cortexhub[llamaindex]` |
| LiteLLM | `Framework.LITELLM` | `pip install cortexhub[litellm]` |

## Configuration

```bash
# Required: API key for telemetry
export CORTEXHUB_API_KEY=ch_live_...

# Optional: Backend URL (defaults to production)
export CORTEXHUB_API_URL=https://api.cortexhub.ai

# Optional: OpenAI key for LLM-based examples
export OPENAI_API_KEY=sk-...
```

## Features

- **Policy Enforcement** - Cedar-based policies, local evaluation
- **PII Detection** - Presidio-powered, 50+ entity types, configurable
- **Secrets Detection** - detect-secrets integration, 30+ secret types
- **Configurable Guardrails** - Select specific PII/secret types to redact
- **Custom Patterns** - Add company-specific regex patterns
- **OpenTelemetry** - Industry-standard observability
- **Framework Adapters** - Automatic interception for all major frameworks
- **Privacy Mode** - Metadata-only by default, safe for production

## Privacy Modes

```python
# Production (default) - only metadata sent
cortex = init(agent_id="...", framework=..., privacy=True)
# Sends: tool names, arg schemas, PII types detected
# Never: raw values, prompts, responses

# Development - full data for testing policies  
cortex = init(agent_id="...", framework=..., privacy=False)
# Also sends: raw args, results, prompts (for policy testing)
```

## Policy Enforcement

Policies are created in the CortexHub dashboard from detected risks. The SDK automatically fetches and enforces them:

```python
from cortexhub.errors import PolicyViolationError, ApprovalRequiredError

# Policies are fetched automatically during init()
# If policies exist, enforcement mode is enabled

try:
    agent.run("Process a $10,000 refund")
except PolicyViolationError as e:
    print(f"Blocked by policy: {e.policy_name}")
    print(f"Reason: {e.reasoning}")
except ApprovalRequiredError as e:
    print(f"\n⏸️  APPROVAL REQUIRED")
    print(f"   Approval ID: {e.approval_id}")
    print(f"   Tool: {e.tool_name}")
    print(f"   Reason: {e.reason}")
    print(f"   Expires: {e.expires_at}")
    print(f"\n   Decision endpoint: {e.decision_endpoint}")
    print(f"   Configure a webhook to receive approval.decisioned event")
```

## Guardrail Configuration

Guardrails detect PII and secrets in LLM prompts. Configure in the dashboard:

1. **Select types to redact**: Choose specific PII types (email, phone, etc.)
2. **Add custom patterns**: Regex for company-specific data (employee IDs, etc.)
3. **Choose action**: Redact, block, or monitor only

The SDK applies your configuration automatically:

```python
# With guardrail policy active:
# Input prompt: "Contact john@email.com about employee EMP-123456"
# After redaction: "Contact [REDACTED-EMAIL_ADDRESS] about employee [REDACTED-CUSTOM_EMPLOYEE_ID]"
# Only configured types are redacted
```

## Examples

```bash
cd python/examples

# LangChain customer support
python langchain_example.py

# LangGraph fraud investigation  
python langgraph_example.py

# CrewAI financial operations
python crewai_example.py

# OpenAI Agents research assistant
python openai_agents_example.py

# LiteLLM multi-provider
python litellm_example.py
```

## Important: Initialization Order

**Always initialize CortexHub FIRST**, before importing your framework:

```python
# ✅ CORRECT
from cortexhub import init, Framework
cortex = init(agent_id="my_agent", framework=Framework.LANGCHAIN)

from langchain_core.tools import tool  # Import AFTER init

# ❌ WRONG
from langchain_core.tools import tool  # Framework imported first
from cortexhub import init, Framework
cortex = init(...)  # Too late!
```

This ensures:
1. CortexHub sets up OpenTelemetry before frameworks that also use it
2. Framework decorators/classes are properly wrapped

## Architecture

```
Agent Decides → [CortexHub] → Agent Executes
                    │
              ┌─────┴─────┐
              │           │
         Policy      Guardrails
         Engine      (PII/Secrets)
              │           │
              └─────┬─────┘
                    │
              OpenTelemetry
               (to backend)
```

## Development

```bash
cd python

# Install with all frameworks
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

## Links

- [Documentation](https://docs.cortexhub.ai)
- [Dashboard](https://app.cortexhub.ai)
- [Issues](https://github.com/cortexhub/sdks/issues)

## License

MIT
