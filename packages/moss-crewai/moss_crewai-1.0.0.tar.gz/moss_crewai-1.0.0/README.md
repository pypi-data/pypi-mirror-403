# moss-crewai

MOSS signing integration for CrewAI. **Unsigned output is broken output.**

[![PyPI](https://img.shields.io/pypi/v/moss-crewai)](https://pypi.org/project/moss-crewai/)

## Installation

```bash
pip install moss-crewai
```

## Quick Start: Explicit Signing (Recommended)

Sign task outputs, crew results, and agent outputs:

```python
from crewai import Crew, Agent, Task
from moss_crewai import sign_task_output, sign_crew_result, sign_agent_output

# Run your crew
crew = Crew(agents=[...], tasks=[...])
result = crew.kickoff()

# Sign the crew result
signed = sign_crew_result(result, agent_id="research-crew")
print(f"Signed: {signed.signature[:20]}...")

# Sign individual task outputs
for task_output in result.tasks_output:
    signed = sign_task_output(task_output, agent_id="research-crew", task="research")
```

## Enterprise Mode

Set `MOSS_API_KEY` for automatic policy evaluation:

```python
import os
os.environ["MOSS_API_KEY"] = "your-api-key"

from moss_crewai import sign_crew_result, enterprise_enabled

print(f"Enterprise: {enterprise_enabled()}")  # True

result = sign_crew_result(
    crew_output,
    agent_id="finance-crew",
    context={"user_id": "u123", "department": "finance"}
)

if result.blocked:
    print(f"Blocked by policy: {result.policy.reason}")
```

## Verification

```python
from moss_crewai import verify_envelope

verify_result = verify_envelope(result.envelope)
if verify_result.valid:
    print(f"Signed by: {verify_result.subject}")
```

## All Functions

| Function | Description |
|----------|-------------|
| `sign_task_output()` | Sign a task's output |
| `sign_task_output_async()` | Async version |
| `sign_agent_output()` | Sign an agent's output |
| `sign_agent_output_async()` | Async version |
| `sign_crew_result()` | Sign full crew kickoff result |
| `sign_crew_result_async()` | Async version |
| `verify_envelope()` | Verify a signed envelope |

## Legacy API

The old auto-signing API is still available:

```python
from moss_crewai import enable_moss, moss_wrap

enable_moss("moss:myteam:crewai")  # Global auto-signing
agent = moss_wrap(agent, "moss:team:researcher")  # Per-agent signing
```

## Enterprise Features

| Feature | Free | Enterprise |
|---------|------|------------|
| Local signing | ✓ | ✓ |
| Offline verification | ✓ | ✓ |
| Policy evaluation | - | ✓ |
| Evidence retention | - | ✓ |
| Audit exports | - | ✓ |

## Links

- [moss-sdk](https://pypi.org/project/moss-sdk/) - Core MOSS SDK
- [mosscomputing.com](https://mosscomputing.com) - Project site

## License

This package is licensed under the [Business Source License 1.1](LICENSE).

- Free for evaluation, testing, and development
- Free for non-production use
- Production use requires a [MOSS subscription](https://mosscomputing.com/pricing)
- Converts to Apache 2.0 on January 25, 2030
