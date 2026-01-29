"""ToothFairyAI Python SDK.

Official Python SDK for the ToothFairyAI API.

Example:
    >>> from toothfairyai import ToothFairyClient
    >>> client = ToothFairyClient(
    ...     api_key="your-api-key",
    ...     workspace_id="your-workspace-id"
    ... )
    >>> # Non-streaming
    >>> response = client.chat.send_to_agent("Hello", "agent-id")
    >>> print(response.agent_response)

    >>> # Streaming (like OpenAI)
    >>> stream = client.streaming.send_to_agent("Hello", "agent-id")
    >>> for event in stream:
    ...     print(event.text, end="", flush=True)
"""

from .client import ToothFairyClient
from .errors import (
    ApiError,
    FileSizeError,
    JsonDecodeError,
    MissingApiKeyError,
    MissingWorkspaceIdError,
    NetworkError,
    StreamError,
    ToothFairyError,
    ValidationError,
)
from .streaming import StreamEvent, StreamResponse
from .types import (
    Agent,
    AgentFunction,
    AgentMessage,
    AgentMode,
    AgentRequest,
    AgentResponse,
    Attachments,
    Authorisation,
    Benchmark,
    Channel,
    ChartingSettings,
    Chat,
    ChatCreateData,
    Connection,
    DictionaryEntry,
    Document,
    DocumentCreateData,
    DocumentType,
    DocumentUpdateData,
    Embedding,
    EmbeddingsSettings,
    Entity,
    EntityCreateOptions,
    EntityType,
    EntityUpdateData,
    FileDownloadOptions,
    FileDownloadResult,
    FileUploadOptions,
    FileUploadResult,
    Folder,
    FolderCreateOptions,
    FolderTreeNode,
    FolderUpdateData,
    Hook,
    ListResponse,
    Member,
    Message,
    MessageCreateData,
    MessageRole,
    MonthCostsResponse,
    Prompt,
    PromptCreateData,
    PromptUpdateData,
    RequestLog,
    ScheduledJob,
    Secret,
    Site,
    ToothFairyClientConfig,
)

__version__ = "0.5.2"
__all__ = [
    # Client
    "ToothFairyClient",
    # Errors
    "ToothFairyError",
    "ApiError",
    "NetworkError",
    "ValidationError",
    "StreamError",
    "JsonDecodeError",
    "FileSizeError",
    "MissingApiKeyError",
    "MissingWorkspaceIdError",
    # Types - Config
    "ToothFairyClientConfig",
    # Types - Agent
    "Agent",
    "AgentMode",
    "AgentFunction",
    # Types - Chat
    "Chat",
    "ChatCreateData",
    "Message",
    "MessageCreateData",
    "MessageRole",
    "AgentMessage",
    "AgentRequest",
    "AgentResponse",
    "Attachments",
    # Types - Document
    "Document",
    "DocumentCreateData",
    "DocumentUpdateData",
    "DocumentType",
    "FileUploadOptions",
    "FileUploadResult",
    "FileDownloadOptions",
    "FileDownloadResult",
    # Types - Entity
    "Entity",
    "EntityType",
    "EntityCreateOptions",
    "EntityUpdateData",
    # Types - Folder
    "Folder",
    "FolderCreateOptions",
    "FolderUpdateData",
    "FolderTreeNode",
    # Types - Prompt
    "Prompt",
    "PromptCreateData",
    "PromptUpdateData",
    # Types - Workspace
    "Member",
    "Authorisation",
    "Channel",
    "Connection",
    # Types - Advanced
    "Benchmark",
    "Hook",
    "ScheduledJob",
    "Site",
    # Types - Utilities
    "Secret",
    "DictionaryEntry",
    "Embedding",
    "EmbeddingsSettings",
    "ChartingSettings",
    "MonthCostsResponse",
    "RequestLog",
    # Types - Streaming
    "StreamResponse",
    "StreamEvent",
    # Types - Response
    "ListResponse",
]
