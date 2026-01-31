# Mistral Workflows

Build reliable, production-grade AI workflows with Python.

## Overview

Mistral Workflows is a Python SDK for building AI-powered workflows with built-in reliability, observability, and scalability. It provides fault tolerance, durability, and exactly-once execution guarantees.

## Features

- **Simple Python API**: Define workflows using Python decorators
- **Built-in Reliability**: Automatic retries, timeouts, and error handling
- **Distributed Execution**: Scale workflows across multiple workers
- **LLM Integration**: Native support for Mistral AI and other LLM providers
- **Observability**: Distributed tracing, structured logging, and event streaming
- **Type Safety**: Full type hints and Pydantic validation

## Installation

```bash
pip install mistralai-workflows
```

## Quick Start

```python
from mistralai_workflows import workflow, activity

@activity
async def get_weather(city: str) -> str:
    # Your activity implementation
    return f"Weather in {city}: Sunny"

@workflow.define
class WeatherWorkflow:
    @workflow.run
    async def run(self, city: str) -> str:
        weather = await workflow.execute_activity(
            get_weather,
            city,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return weather
```

## Documentation

For full documentation, visit [docs.mistral.ai/workflows](https://docs.mistral.ai/workflows)

## Examples

The SDK includes comprehensive examples in the `mistralai_workflows/examples` directory. You can run all examples with a single command:

```bash
# Run all example workflows in a single worker
python -m mistralai_workflows.examples.all_workflows_worker
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
