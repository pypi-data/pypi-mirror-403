from __future__ import annotations

import structlog
from mistralai_workflows.core.activity import activity
from mistralai_workflows.core.dependencies.dependency_injector import Depends

import mistralai
from mistralai_workflows.plugins.mistralai.models import AgentUpdateRequest, ConversationAppendRequest
from mistralai_workflows.plugins.mistralai.utils import (
    _get_agent_llm_rate_limit,
    get_mistral_client,
    handle_chat_stream,
    handle_conversation_stream,
)

logger = structlog.get_logger(__name__)


@activity(rate_limit=_get_agent_llm_rate_limit())
async def mistralai_create_agent(
    params: mistralai.AgentCreationRequest,
    mistral_client: mistralai.Mistral = Depends(get_mistral_client),
) -> mistralai.Agent:
    agent = mistral_client.beta.agents.create(**params.model_dump(by_alias=True))
    return agent


@activity(rate_limit=_get_agent_llm_rate_limit())
async def mistralai_start_conversation(
    params: mistralai.ConversationRequest,
    mistral_client: mistralai.Mistral = Depends(get_mistral_client),
) -> mistralai.ConversationResponse:
    return await mistral_client.beta.conversations.start_async(**params.model_dump(by_alias=True))


@activity(rate_limit=_get_agent_llm_rate_limit())
async def mistralai_append_conversation(
    params: ConversationAppendRequest,
    mistral_client: mistralai.Mistral = Depends(get_mistral_client),
) -> mistralai.ConversationResponse:
    return await mistral_client.beta.conversations.append_async(**params.model_dump(by_alias=True))


@activity(rate_limit=_get_agent_llm_rate_limit())
async def mistralai_update_agent(
    params: AgentUpdateRequest,
    mistral_client: mistralai.Mistral = Depends(get_mistral_client),
) -> mistralai.Agent:
    return await mistral_client.beta.agents.update_async(**params.model_dump(by_alias=True))


@activity(rate_limit=_get_agent_llm_rate_limit())
async def mistralai_chat_complete(
    params: mistralai.ChatCompletionRequest,
    mistral_client: mistralai.Mistral = Depends(get_mistral_client),
) -> mistralai.ChatCompletionResponse:
    return await mistral_client.chat.complete_async(**params.model_dump())


@activity(rate_limit=_get_agent_llm_rate_limit())
async def mistralai_chat_stream(
    params: mistralai.ChatCompletionRequest,
    mistral_client: mistralai.Mistral = Depends(get_mistral_client),
) -> mistralai.AssistantMessage:
    payload = params.model_copy(update={"stream": True})
    stream = await mistral_client.chat.stream_async(**payload.model_dump(by_alias=True, exclude_none=True))
    return await handle_chat_stream(stream=stream)


@activity(rate_limit=_get_agent_llm_rate_limit())
async def mistralai_start_conversation_stream(
    params: mistralai.ConversationRequest, mistral_client: mistralai.Mistral = Depends(get_mistral_client)
) -> mistralai.ConversationResponse:
    payload = params.model_copy(update={"stream": True})

    stream = await mistral_client.beta.conversations.start_stream_async(
        **payload.model_dump(by_alias=True, exclude_none=True)
    )

    return await handle_conversation_stream(stream=stream)


@activity(rate_limit=_get_agent_llm_rate_limit())
async def mistralai_append_conversation_stream(
    params: ConversationAppendRequest, mistral_client: mistralai.Mistral = Depends(get_mistral_client)
) -> mistralai.ConversationResponse:
    payload = params.model_copy(update={"stream": True})

    stream = await mistral_client.beta.conversations.append_stream_async(
        **payload.model_dump(by_alias=True, exclude_none=True)
    )

    return await handle_conversation_stream(stream=stream)
