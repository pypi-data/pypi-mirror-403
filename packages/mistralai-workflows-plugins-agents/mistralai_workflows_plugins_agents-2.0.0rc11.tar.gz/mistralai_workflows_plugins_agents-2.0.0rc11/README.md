# Mistral Workflows - Agents Plugin

AI agent runtime and MCP (Model Context Protocol) support for Mistral Workflows.

## Overview

This plugin provides agent runtime helpers, session management, and MCP integration for building autonomous AI agents with Mistral Workflows.

## Features

- **Agent Runtime**: Build and run autonomous AI agents
- **Session Management**: Stateful agent sessions with context persistence
- **MCP Support**: Model Context Protocol integration for tool use
- **Tool Execution**: Built-in tool calling and execution framework

## Installation

```bash
pip install mistralai-workflows[agents]
```

Or install directly:

```bash
pip install mistralai-workflows-plugins-agents
```

## Quick Start

```python
import mistralai_workflows as workflows
import mistralai_workflows.plugins.agents as workflows_agents

@workflows.workflow.define(name="agent-workflow")
class AgentWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, prompt: str) -> str:
        agent = workflows_agents.Agent(
            model="mistral-medium-latest",
            description="Helpful assistant",
            instructions="Answer questions concisely.",
            name="my-agent",
        )

        outputs = await workflows_agents.Runner.run(agent=agent, inputs=prompt)

        return "".join(chunk.text for chunk in outputs if hasattr(chunk, "text"))
```

## Documentation

For full documentation, visit [docs-internal-frameworks.mistral.ai/workflows](https://docs-internal-frameworks.mistral.ai/workflows)

## Examples

Run examples with:

```bash
python -m mistralai_workflows.plugins.agents.examples.workflow_local_session_streaming
python -m mistralai_workflows.plugins.agents.examples.workflow_travel_agent_streaming
python -m mistralai_workflows.plugins.agents.examples.workflow_with_agent
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
