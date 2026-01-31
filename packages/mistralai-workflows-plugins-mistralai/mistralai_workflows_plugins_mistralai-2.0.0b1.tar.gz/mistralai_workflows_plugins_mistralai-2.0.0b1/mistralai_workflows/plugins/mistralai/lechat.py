from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatAssistantWorkingTask(BaseModel):
    model_config = ConfigDict(title="working")

    type: Literal["tool", "thinking"] | str = "tool"
    title: str
    content: str


class TextOutput(BaseModel):
    type: Literal["text"] = "text"
    text: str


class CanvasPayload(BaseModel):
    type: Literal[
        "text/markdown",
        "text/html",
        "image/svg+xml",
        "slides",
        "react",
        "code",
        "mermaid",
    ]
    title: str
    content: str
    language: str | None = None


class CanvasResource(BaseModel):
    uri: str
    mimeType: Literal["application/vnd.mistral.canvas"]
    canvas: CanvasPayload


class ResourceOutput(BaseModel):
    type: Literal["resource"] = "resource"
    resource: CanvasResource


class ChatAssistantWorkflowOutput(BaseModel):
    outputs: list[TextOutput | ResourceOutput] = Field(default_factory=list)


class ChatInput(BaseModel):
    """Input  for asking the user to chat."""

    model_config = ConfigDict(
        title="ChatInput",
    )
