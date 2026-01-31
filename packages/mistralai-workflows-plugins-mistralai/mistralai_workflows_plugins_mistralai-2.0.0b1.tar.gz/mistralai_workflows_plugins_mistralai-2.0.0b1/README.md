# Mistral Workflows - Mistral AI Plugin

Native Mistral AI integration for Mistral Workflows.

## Overview

This plugin provides Mistral AI-specific activities and models for building AI workflows with the Mistral AI API.

## Features

- **Mistral AI Activities**: Pre-built activities for chat completions, embeddings, and more
- **Streaming Support**: Native streaming for chat responses
- **Model Definitions**: Type-safe model configurations

## Installation

```bash
pip install mistralai-workflows[mistralai]
```

Or install directly:

```bash
pip install mistralai-workflows-plugins-mistralai
```

## Quick Start

```python
import mistralai_workflows as workflows
import mistralai_workflows.plugins.mistralai as workflows_mistralai


@workflows.workflow.define(name="chat-workflow")
class ChatWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, prompt: str) -> str:
        response = await workflows_mistralai.mistralai_chat_stream(
            workflows_mistralai.ChatCompletionRequest(
                model="mistral-medium-latest",
                messages=[workflows_mistralai.UserMessage(content=prompt)],
            )
        )
        return response.content
```

## Documentation

For full documentation, visit [docs-internal-frameworks.mistral.ai/workflows](https://docs-internal-frameworks.mistral.ai/workflows)

## Examples

Run examples with:

```bash
python -m mistralai_workflows.plugins.mistralai.examples.workflow_multi_turn_chat
python -m mistralai_workflows.plugins.mistralai.examples.workflow_insurance_claims
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
