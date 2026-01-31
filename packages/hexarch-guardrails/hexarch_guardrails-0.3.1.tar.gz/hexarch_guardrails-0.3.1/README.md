# Hexarch Guardrails Python SDK

Lightweight policy-driven API protection for students, solo developers, and hackathons.

## Installation

```bash
pip install hexarch-guardrails
```

## Quick Start

### 1. Create a policy file (`hexarch.yaml`)

```yaml
policies:
  - id: "api_budget"
    description: "Protect against overspending"
    rules:
      - resource: "openai"
        monthly_budget: 10
        action: "warn_at_80%"

  - id: "rate_limit"
    description: "Prevent API abuse"
    rules:
      - resource: "*"
        requests_per_minute: 100
        action: "block"

  - id: "safe_delete"
    description: "Require confirmation for destructive ops"
    rules:
      - operation: "delete"
        action: "require_confirmation"
```

### 2. Use in your code

```python
from hexarch_guardrails import Guardian

# Initialize (auto-discovers hexarch.yaml)
guardian = Guardian()

# Protect API calls
@guardian.check("api_budget")
def call_openai(prompt):
    import openai
    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

# Use it
response = call_openai("Hello AI!")
```

## Features

- ✅ **Zero-config** - Auto-discovers `hexarch.yaml`
- ✅ **Decorator-based** - Drop in `@guardian.check(policy_id)`
- ✅ **Policy-driven** - YAML-based rules, no code changes
- ✅ **Local-first** - Works offline or with local OPA
- ✅ **Pluggable** - Works with any API/SDK

## Examples

### Budget Protection (OpenAI)

```python
@guardian.check("api_budget")
def expensive_operation():
    # This call is protected by budget limits
    return openai.ChatCompletion.create(model="gpt-4", ...)
```

### Rate Limiting

```python
@guardian.check("rate_limit")
def send_discord_message(msg):
    return client.send(msg)
```

### Safe File Operations

```python
@guardian.check("safe_delete")
def delete_file(path):
    os.remove(path)
```

## Documentation

- [Policy Authoring Guide](./docs/POLICY_GUIDE.md)
- [API Reference](./docs/API_REFERENCE.md)
- [Examples](./examples/)

## Admin CLI (v0.3.0+)

Hexarch includes a command-line interface for managing policies and monitoring decisions:

### Installation

```bash
# Install with CLI extras
pip install hexarch-guardrails[cli]
```

### Quick Start

```bash
# List all policies
hexarch-ctl policy list

# Export a policy
hexarch-ctl policy export ai_governance --format rego

# Validate policy syntax
hexarch-ctl policy validate ./policy.rego

# Compare policy versions
hexarch-ctl policy diff ai_governance
```

### Available Commands

**Policy Management**:
- `hexarch-ctl policy list` - List all OPA policies
- `hexarch-ctl policy export` - Export policy to file or stdout
- `hexarch-ctl policy validate` - Validate OPA policy syntax
- `hexarch-ctl policy diff` - Compare policy versions

**Upcoming** (Phase 3-4):
- Decision querying and analysis
- Metrics and performance monitoring
- Configuration management

For detailed CLI documentation, see [POLICY_COMMANDS_GUIDE.md](./POLICY_COMMANDS_GUIDE.md)

## License

MIT © Noir Stack LLC

See LICENSE for full details.
