# FlowAgent

[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange)](https://github.com/xiaoyu-work/flowagent)

**State-driven AI agent framework for task automation with human-in-the-loop.**

Build agents that collect information, validate input, and execute tasks with optional approval.

## Perfect For

- **Booking & Reservations** - Restaurants, flights, hotels, appointments
- **Request & Approval** - Leave requests, expense reports, access requests
- **Form Wizards** - Multi-step data collection with validation
- **Business Workflows** - Order processing, customer service, IT ticketing

## Installation

```bash
pip install flowagent              # Core
pip install flowagent[openai]      # + OpenAI
pip install flowagent[anthropic]   # + Claude
pip install flowagent[all]         # All providers
```

## Quick Example

```python
import asyncio
from flowagent import flowagent, StandardAgent, InputField, AgentStatus
from flowagent import Orchestrator, OpenAIClient

@flowagent(triggers=["book", "reservation"])
class BookingAgent(StandardAgent):
    guests = InputField("How many guests?")
    date = InputField("What date?")

    async def on_running(self, msg):
        return self.make_result(
            status=AgentStatus.COMPLETED,
            raw_message=f"Booked for {self.guests} on {self.date}!"
        )

async def main():
    llm = OpenAIClient(api_key="sk-xxx", model="gpt-4o-mini")
    orchestrator = Orchestrator(llm_client=llm)
    await orchestrator.initialize()

    result = await orchestrator.handle_message("user_1", "I want to book a table")
    print(result.raw_message)  # "How many guests?"

    result = await orchestrator.handle_message("user_1", "4")
    print(result.raw_message)  # "What date?"

    result = await orchestrator.handle_message("user_1", "Friday")
    print(result.raw_message)  # "Booked for 4 on Friday!"

asyncio.run(main())
```

## Key Features

- **State Machine** - `INITIALIZING → WAITING_FOR_INPUT → RUNNING → COMPLETED`
- **Field Collection** - Declarative `InputField` with validation
- **Approval Workflow** - Human confirmation before sensitive actions
- **Multi-LLM** - OpenAI, Claude, Azure, Gemini, Ollama, DashScope
- **Orchestrator** - Route messages to the right agent
- **Checkpoint** - Save & restore state, time-travel debugging
- **Multi-tenant** - Built-in isolation for SaaS

## Documentation

- [**Getting Started**](docs/getting-started.md) - Build your first agent
- [**Full Documentation**](docs/index.md) - Complete guide
- [**Examples**](examples/) - Sample code

**Guides:** [Agents](docs/agents.md) | [Tools](docs/tools.md) | [LLM Providers](docs/llm-providers.md) | [Orchestrator](docs/orchestrator.md) | [Workflow](docs/workflow.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)
