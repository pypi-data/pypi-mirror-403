from typing import List

from pydantic import BaseModel, Field

import mistralai


class ContentChunk(BaseModel):
    type: str = "text"
    text: str


class ChatStreamState(BaseModel):
    contentChunks: List[ContentChunk] = Field(default_factory=list)


class ConversationStreamState(BaseModel):
    contentChunks: List[ContentChunk] = Field(default_factory=list)


class ConversationAppendRequest(mistralai.ConversationAppendRequest):
    conversation_id: str


class AgentUpdateRequest(mistralai.AgentUpdateRequest):
    agent_id: str
