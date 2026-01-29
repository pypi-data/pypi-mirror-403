"""Type definitions for the ToothFairyAI SDK."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, TypedDict, Union

# Type aliases.
EntityType = Literal["intent", "ner", "topic"]
DocumentType = Literal["readComprehensionUrl", "readComprehensionPdf", "readComprehensionFile"]
MessageRole = Literal["user", "assistant", "system"]
AgentMode = Literal["retriever", "coder", "chatter", "planner", "computer", "voice", "accuracy"]


# Configuration types
@dataclass
class ToothFairyClientConfig:
    """Configuration for the ToothFairyClient."""

    api_key: str
    workspace_id: str
    base_url: str = "https://api.toothfairyai.com"
    ai_url: str = "https://ai.toothfairyai.com"
    ai_stream_url: str = "https://ais.toothfairyai.com"
    timeout: int = 120  # seconds


# Chat types
@dataclass
class ChannelSettings:
    """Channel settings for a chat."""

    channel: Optional[str] = None
    provider: Optional[str] = None


@dataclass
class Chat:
    """Represents a chat conversation."""

    id: str
    name: str = ""
    primary_role: str = ""
    external_participant_id: str = ""
    channel_settings: Optional[ChannelSettings] = None
    customer_id: str = ""
    customer_info: Dict[str, Any] = field(default_factory=dict)
    is_ai_replying: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chat":
        """Create a Chat instance from a dictionary."""
        channel_settings = None
        if data.get("channelSettings"):
            channel_settings = ChannelSettings(
                channel=data["channelSettings"].get("channel"),
                provider=data["channelSettings"].get("provider"),
            )
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            primary_role=data.get("primaryRole", ""),
            external_participant_id=data.get("externalParticipantId", ""),
            channel_settings=channel_settings,
            customer_id=data.get("customerId", ""),
            customer_info=data.get("customerInfo", {}),
            is_ai_replying=data.get("isAIReplying", False),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


@dataclass
class ChatCreateData:
    """Data for creating a chat."""

    name: str = ""
    customer_id: str = ""
    customer_info: Dict[str, Any] = field(default_factory=dict)
    primary_role: str = "user"
    external_participant_id: str = ""
    channel_settings: Optional[Dict[str, str]] = None


@dataclass
class Message:
    """Represents a chat message."""

    id: str
    chat_id: str
    text: str
    role: MessageRole
    user_id: str = ""
    images: List[str] = field(default_factory=list)
    audios: List[str] = field(default_factory=list)
    videos: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create a Message instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            chat_id=data.get("chatID", ""),
            text=data.get("text", ""),
            role=data.get("role", "user"),
            user_id=data.get("userID", ""),
            images=data.get("images", []),
            audios=data.get("audios", []),
            videos=data.get("videos", []),
            files=data.get("files", []),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


@dataclass
class MessageCreateData:
    """Data for creating a message."""

    chat_id: str
    text: str
    role: MessageRole = "user"
    user_id: str = ""
    images: List[str] = field(default_factory=list)
    audios: List[str] = field(default_factory=list)
    videos: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)


class Attachments(TypedDict, total=False):
    """Attachments for agent messages."""

    images: List[str]
    audios: List[str]
    videos: List[str]
    files: List[str]


@dataclass
class AgentMessage:
    """Message to send to an agent."""

    role: MessageRole
    content: str


@dataclass
class AgentRequest:
    """Request to send to an agent."""

    messages: List[AgentMessage]
    agentid: str
    chatid: Optional[str] = None
    raw_stream: bool = False
    phone_number: Optional[str] = None
    customer_id: Optional[str] = None
    provider_id: Optional[str] = None
    customer_info: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    """Response from an agent."""

    chat_id: str
    message_id: str
    agent_response: Any

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponse":
        """Create an AgentResponse instance from a dictionary."""
        return cls(
            chat_id=data.get("chatId", ""),
            message_id=data.get("messageId", ""),
            agent_response=data.get("agentResponse"),
        )


# Document types
@dataclass
class Document:
    """Represents a document."""

    id: str
    workspace_id: str = ""
    user_id: str = ""
    doc_type: DocumentType = "readComprehensionFile"
    title: str = ""
    topics: List[str] = field(default_factory=list)
    folder_id: str = ""
    external_path: str = ""
    source: str = ""
    status: str = ""
    scope: Optional[str] = None
    rawtext: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create a Document instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceid", ""),
            user_id=data.get("userid", ""),
            doc_type=data.get("type", "readComprehensionFile"),
            title=data.get("title", ""),
            topics=data.get("topics", []),
            folder_id=data.get("folderid", ""),
            external_path=data.get("external_path", ""),
            source=data.get("source", ""),
            status=data.get("status", ""),
            scope=data.get("scope"),
            rawtext=data.get("rawtext"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


@dataclass
class DocumentCreateData:
    """Data for creating a document."""

    user_id: str
    title: str
    doc_type: DocumentType = "readComprehensionFile"
    topics: List[str] = field(default_factory=list)
    folder_id: str = "mrcRoot"
    external_path: str = ""
    source: str = ""
    status: str = "published"
    scope: Optional[str] = None


@dataclass
class DocumentUpdateData:
    """Data for updating a document."""

    title: Optional[str] = None
    topics: Optional[List[str]] = None
    folder_id: Optional[str] = None
    status: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class FileUploadOptions:
    """Options for file upload."""

    folder_id: str = "mrcRoot"
    on_progress: Optional[Callable[[int, int, int], None]] = None


@dataclass
class Base64FileUploadOptions:
    """Options for base64 file upload."""

    filename: str
    content_type: str
    folder_id: str = "mrcRoot"
    on_progress: Optional[Callable[[int, int, int], None]] = None


@dataclass
class FileUploadResult:
    """Result of a file upload."""

    success: bool
    original_filename: str
    sanitized_filename: str
    filename: str
    import_type: str
    content_type: str
    size: int
    size_in_mb: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileUploadResult":
        """Create a FileUploadResult instance from a dictionary."""
        return cls(
            success=data.get("success", False),
            original_filename=data.get("originalFilename", ""),
            sanitized_filename=data.get("sanitizedFilename", ""),
            filename=data.get("filename", ""),
            import_type=data.get("importType", ""),
            content_type=data.get("contentType", ""),
            size=data.get("size", 0),
            size_in_mb=data.get("sizeInMB", 0.0),
        )


@dataclass
class FileDownloadOptions:
    """Options for file download."""

    context: str = "documents"
    on_progress: Optional[Callable[[int, int, int], None]] = None


@dataclass
class FileDownloadResult:
    """Result of a file download."""

    success: bool
    filename: str
    output_path: str
    size: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileDownloadResult":
        """Create a FileDownloadResult instance from a dictionary."""
        return cls(
            success=data.get("success", False),
            filename=data.get("filename", ""),
            output_path=data.get("outputPath", ""),
            size=data.get("size", 0),
        )


# Entity types
@dataclass
class Entity:
    """Represents an entity (topic, intent, or NER)."""

    id: str
    workspace_id: str = ""
    created_by: str = ""
    label: str = ""
    entity_type: EntityType = "topic"
    description: Optional[str] = None
    emoji: Optional[str] = None
    parent_entity: Optional[str] = None
    background_color: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Create an Entity instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceid", ""),
            created_by=data.get("createdBy", ""),
            label=data.get("label", ""),
            entity_type=data.get("type", "topic"),
            description=data.get("description"),
            emoji=data.get("emoji"),
            parent_entity=data.get("parentEntity"),
            background_color=data.get("backgroundColor"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


@dataclass
class EntityCreateOptions:
    """Options for creating an entity."""

    description: Optional[str] = None
    emoji: Optional[str] = None
    parent_entity: Optional[str] = None
    background_color: Optional[str] = None


@dataclass
class EntityUpdateData:
    """Data for updating an entity."""

    label: Optional[str] = None
    description: Optional[str] = None
    emoji: Optional[str] = None
    parent_entity: Optional[str] = None
    background_color: Optional[str] = None


# Folder types
@dataclass
class Folder:
    """Represents a folder."""

    id: str
    workspace_id: str = ""
    created_by: str = ""
    name: str = ""
    description: Optional[str] = None
    emoji: Optional[str] = None
    status: Optional[str] = None
    parent: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Folder":
        """Create a Folder instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceID", ""),
            created_by=data.get("createdBy", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            emoji=data.get("emoji"),
            status=data.get("status"),
            parent=data.get("parent"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


@dataclass
class FolderCreateOptions:
    """Options for creating a folder."""

    description: Optional[str] = None
    emoji: Optional[str] = None
    status: str = "active"
    parent: Optional[str] = None


@dataclass
class FolderUpdateData:
    """Data for updating a folder."""

    name: Optional[str] = None
    description: Optional[str] = None
    emoji: Optional[str] = None
    status: Optional[str] = None
    parent: Optional[str] = None


@dataclass
class FolderTreeNode:
    """A folder in a tree structure."""

    id: str
    workspace_id: str
    created_by: str
    name: str
    description: Optional[str]
    emoji: Optional[str]
    status: Optional[str]
    parent: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    children: List["FolderTreeNode"] = field(default_factory=list)

    @classmethod
    def from_folder(
        cls, folder: Folder, children: Optional[List["FolderTreeNode"]] = None
    ) -> "FolderTreeNode":
        """Create a FolderTreeNode from a Folder."""
        return cls(
            id=folder.id,
            workspace_id=folder.workspace_id,
            created_by=folder.created_by,
            name=folder.name,
            description=folder.description,
            emoji=folder.emoji,
            status=folder.status,
            parent=folder.parent,
            created_at=folder.created_at,
            updated_at=folder.updated_at,
            children=children or [],
        )


# Prompt types
@dataclass
class Prompt:
    """Represents a prompt template."""

    id: str
    workspace_id: str = ""
    created_by: str = ""
    prompt_type: str = ""
    label: str = ""
    prompt_length: int = 0
    interpolation_string: str = ""
    scope: Optional[str] = None
    style: Optional[str] = None
    domain: Optional[str] = None
    prompt_placeholder: Optional[str] = None
    available_to_agents: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Prompt":
        """Create a Prompt instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceID", ""),
            created_by=data.get("createdBy", ""),
            prompt_type=data.get("type", ""),
            label=data.get("label", ""),
            prompt_length=data.get("promptLength", 0),
            interpolation_string=data.get("interpolationString", ""),
            scope=data.get("scope"),
            style=data.get("style"),
            domain=data.get("domain"),
            prompt_placeholder=data.get("promptPlaceholder"),
            available_to_agents=data.get("availableToAgents", []),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


@dataclass
class PromptCreateData:
    """Data for creating a prompt."""

    label: str
    prompt_type: str
    interpolation_string: str
    scope: Optional[str] = None
    style: Optional[str] = None
    domain: Optional[str] = None
    prompt_placeholder: Optional[str] = None
    available_to_agents: List[str] = field(default_factory=list)


@dataclass
class PromptUpdateData:
    """Data for updating a prompt."""

    label: Optional[str] = None
    prompt_type: Optional[str] = None
    interpolation_string: Optional[str] = None
    scope: Optional[str] = None
    style: Optional[str] = None
    domain: Optional[str] = None
    prompt_placeholder: Optional[str] = None
    available_to_agents: Optional[List[str]] = None


# Response types
@dataclass
class ListResponse:
    """Generic list response."""

    items: List[Any]
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


# Streaming types
class StreamingOptions(TypedDict, total=False):
    """Options for streaming requests."""

    chat_id: str
    phone_number: str
    customer_id: str
    provider_id: str
    customer_info: Dict[str, Any]
    attachments: Attachments
    show_progress: bool
    raw_stream: bool


@dataclass
class StreamEventData:
    """Data from a stream event."""

    text: str = ""
    message_type: str = ""
    message_id: str = ""
    chat_id: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamEventData":
        """Create a StreamEventData instance from a dictionary."""
        return cls(
            text=data.get("text", ""),
            message_type=data.get("type", ""),
            message_id=data.get("message_id", ""),
            chat_id=data.get("chatId", ""),
        )


@dataclass
class StreamStatusEvent:
    """Status event from a stream."""

    status: str
    processing_status: Optional[str] = None
    metadata_parsed: Optional[Dict[str, Any]] = None


@dataclass
class StreamingResult:
    """Result of a streaming request."""

    chat_id: str
    message_id: str


# Content type mapping
CONTENT_TYPE_MAP: Dict[str, str] = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".json": "application/json",
    ".xml": "application/xml",
    ".html": "text/html",
    ".htm": "text/html",
    ".md": "text/markdown",
    ".rtf": "application/rtf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".zip": "application/zip",
    ".rar": "application/vnd.rar",
    ".7z": "application/x-7z-compressed",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".py": "text/x-python",
    ".js": "application/javascript",
    ".ts": "application/typescript",
    ".java": "text/x-java-source",
    ".c": "text/x-c",
    ".cpp": "text/x-c++",
    ".h": "text/x-c",
    ".hpp": "text/x-c++",
    ".cs": "text/x-csharp",
    ".go": "text/x-go",
    ".rs": "text/x-rust",
    ".rb": "text/x-ruby",
    ".php": "text/x-php",
    ".swift": "text/x-swift",
    ".kt": "text/x-kotlin",
    ".scala": "text/x-scala",
}


def get_content_type(filename: str) -> str:
    """Get content type from filename extension."""
    import os

    ext = os.path.splitext(filename)[1].lower()
    return CONTENT_TYPE_MAP.get(ext, "application/octet-stream")


# Max file size constant
MAX_FILE_SIZE_MB = 15
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# Agent types
@dataclass
class Agent:
    """Represents an AI agent."""

    id: str
    workspace_id: str = ""
    type: str = ""
    label: str = ""
    description: Optional[str] = None
    interpolation_string: Optional[str] = None
    emoji: Optional[str] = None
    color: Optional[str] = None
    is_default: bool = False
    has_memory: bool = True
    has_images: bool = False
    prompt_top_keywords: int = 5
    key_words_for_knowledge_base: bool = True
    has_topics_context: bool = True
    has_functions: bool = False
    advanced_language_detection: bool = False
    allowed_topics: List[str] = field(default_factory=list)
    default_answer: Optional[str] = None
    stop_sequence: Optional[str] = None
    examples: List[Dict[str, str]] = field(default_factory=list)
    enhancement_passage: Optional[str] = None
    inhibition_passage: Optional[str] = None
    pertinence_passage: Optional[str] = None
    goals: Optional[str] = None
    qa_url: Optional[str] = None
    top_k: int = 10
    mode: AgentMode = "accuracy"
    charting: bool = False
    summarisation: bool = True
    compressor: bool = False
    doc_top_k: int = 5
    max_history: int = 10
    max_tokens: int = 1000
    topic_enhancer: bool = False
    max_topics: int = 3
    blender: bool = False
    temperature: float = 0.7
    version: int = 1
    subject: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    agent_functions: List[str] = field(default_factory=list)
    is_global: bool = False
    plain_text_output: bool = False
    chain_of_thoughts: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Create an Agent instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceid", ""),
            type=data.get("type", ""),
            label=data.get("label", ""),
            description=data.get("description"),
            interpolation_string=data.get("interpolationString"),
            emoji=data.get("emoji"),
            color=data.get("color"),
            is_default=data.get("isDefault", False),
            has_memory=data.get("hasMemory", True),
            has_images=data.get("hasImages", False),
            prompt_top_keywords=data.get("promptTopKeywords", 5),
            key_words_for_knowledge_base=data.get("keyWordsForKnowledgeBase", True),
            has_topics_context=data.get("hasTopicsContext", True),
            has_functions=data.get("hasFunctions", False),
            advanced_language_detection=data.get("advancedLanguageDetection", False),
            allowed_topics=data.get("allowedTopics", []),
            default_answer=data.get("defaultAnswer"),
            stop_sequence=data.get("stopSequence"),
            examples=data.get("examples", []),
            enhancement_passage=data.get("enhancementPassage"),
            inhibition_passage=data.get("inhibitionPassage"),
            pertinence_passage=data.get("pertinencePassage"),
            goals=data.get("goals"),
            qa_url=data.get("qaUrl"),
            top_k=data.get("topK", 10),
            mode=data.get("mode", "accuracy"),
            charting=data.get("charting", False),
            summarisation=data.get("summarisation", True),
            compressor=data.get("compressor", False),
            doc_top_k=data.get("docTopK", 5),
            max_history=data.get("maxHistory", 10),
            max_tokens=data.get("maxTokens", 1000),
            topic_enhancer=data.get("topicEnhancer", False),
            max_topics=data.get("maxTopics", 3),
            blender=data.get("blender", False),
            temperature=data.get("temperature", 0.7),
            version=data.get("version", 1),
            subject=data.get("subject"),
            created_by=data.get("createdBy"),
            updated_by=data.get("updatedBy"),
            agent_functions=data.get("agentFunctions", []),
            is_global=data.get("isGlobal", False),
            plain_text_output=data.get("plainTextOutput", False),
            chain_of_thoughts=data.get("chainOfThoughts", False),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


# Agent Function types
@dataclass
class AgentFunction:
    """Represents an agent function."""

    id: str
    name: str
    url: str
    workspace_id: str = ""
    model: Optional[str] = None
    request_type: str = "GET"
    authorisation_type: str = "none"
    authorisation_key: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    headers: List[Dict[str, str]] = field(default_factory=list)
    static_args: List[Dict[str, str]] = field(default_factory=list)
    custom_execution_code: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentFunction":
        """Create an AgentFunction instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            url=data.get("url", ""),
            workspace_id=data.get("workspaceid", ""),
            model=data.get("model"),
            request_type=data.get("requestType", "GET"),
            authorisation_type=data.get("authorisationType", "none"),
            authorisation_key=data.get("authorisationKey"),
            description=data.get("description"),
            parameters=data.get("parameters", []),
            headers=data.get("headers", []),
            static_args=data.get("staticArgs", []),
            custom_execution_code=data.get("customExecutionCode"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


# Authorisation types
@dataclass
class Authorisation:
    """Represents an authorisation configuration."""

    id: str
    name: str
    type: str
    workspace_id: str = ""
    token_secret: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[str] = None
    grant_type: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorization_base_url: Optional[str] = None
    static_args: Optional[str] = None
    token_base_url: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Authorisation":
        """Create an Authorisation instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type", ""),
            workspace_id=data.get("workspaceid", ""),
            token_secret=data.get("tokenSecret"),
            description=data.get("description"),
            scope=data.get("scope"),
            grant_type=data.get("grantType"),
            client_id=data.get("clientId"),
            client_secret=data.get("clientSecret"),
            authorization_base_url=data.get("authorizationBaseUrl"),
            static_args=data.get("staticArgs"),
            token_base_url=data.get("tokenBaseUrl"),
            created_by=data.get("createdBy"),
            updated_by=data.get("updatedBy"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


# Channel types
@dataclass
class Channel:
    """Represents a communication channel."""

    id: str
    name: str
    channel: str
    provider: str
    workspace_id: str = ""
    description: Optional[str] = None
    senderid: Optional[str] = None
    is_active: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Channel":
        """Create a Channel instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            channel=data.get("channel", ""),
            provider=data.get("provider", ""),
            workspace_id=data.get("workspaceid", ""),
            description=data.get("description"),
            senderid=data.get("senderid"),
            is_active=data.get("isActive", True),
        )


# Connection types
@dataclass
class Connection:
    """Represents a database/API connection."""

    id: str
    name: str
    type: str
    host: str
    port: str
    workspace_id: str = ""
    description: Optional[str] = None
    username: Optional[str] = None
    password_secret: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    ssl: bool = False
    ssh: bool = False
    ssh_host: Optional[str] = None
    ssh_port: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password_secret: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Connection":
        """Create a Connection instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type", ""),
            host=data.get("host", ""),
            port=data.get("port", ""),
            workspace_id=data.get("workspaceid", ""),
            description=data.get("description"),
            username=data.get("username"),
            password_secret=data.get("passwordSecret"),
            database=data.get("database"),
            schema=data.get("schema"),
            ssl=data.get("ssl", False),
            ssh=data.get("ssh", False),
            ssh_host=data.get("sshHost"),
            ssh_port=data.get("sshPort"),
            ssh_username=data.get("sshUsername"),
            ssh_password_secret=data.get("sshPasswordSecret"),
            created_by=data.get("createdBy"),
            updated_by=data.get("updatedBy"),
        )


# Member types
@dataclass
class Member:
    """Represents a workspace member."""

    id: str
    user_id: str
    workspace_id: str = ""
    role: str = "member"
    status: str = "active"
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Member":
        """Create a Member instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            user_id=data.get("userID", ""),
            workspace_id=data.get("workspaceid", ""),
            role=data.get("role", "member"),
            status=data.get("status", "active"),
            created_by=data.get("createdBy"),
            updated_by=data.get("updatedBy"),
        )


# Site types
@dataclass
class Site:
    """Represents a website for crawling."""

    id: str
    name: str
    url: str
    workspace_id: str = ""
    description: Optional[str] = None
    topics: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    last_validation_date: Optional[str] = None
    validation_token: Optional[str] = None
    allowed_paths: List[str] = field(default_factory=list)
    completion_percentage: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Site":
        """Create a Site instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            url=data.get("url", ""),
            workspace_id=data.get("workspaceid", ""),
            description=data.get("description"),
            topics=data.get("topics", {}),
            status=data.get("status", "active"),
            last_validation_date=data.get("lastValidationDate"),
            validation_token=data.get("validationToken"),
            allowed_paths=data.get("allowedPaths", []),
            completion_percentage=data.get("completion_percentage", 0.0),
        )


# Benchmark types
@dataclass
class Benchmark:
    """Represents a benchmark for testing agent performance."""

    id: str
    name: str
    workspace_id: str = ""
    description: Optional[str] = None
    questions: List[Dict[str, str]] = field(default_factory=list)
    files: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Benchmark":
        """Create a Benchmark instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workspace_id=data.get("workspaceid", ""),
            description=data.get("description"),
            questions=data.get("questions", []),
            files=data.get("files", []),
        )


# Hook types
@dataclass
class Hook:
    """Represents a custom code execution hook."""

    id: str
    name: str
    workspace_id: str = ""
    description: Optional[str] = None
    function_name: Optional[str] = None
    custom_execution_code: Optional[str] = None
    custom_execution_instructions: Optional[str] = None
    available_libraries: Optional[str] = None
    allow_external_api: bool = False
    hardcoded_script: bool = False
    is_template: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hook":
        """Create a Hook instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workspace_id=data.get("workspaceid", ""),
            description=data.get("description"),
            function_name=data.get("functionName"),
            custom_execution_code=data.get("customExecutionCode"),
            custom_execution_instructions=data.get("customExecutionInstructions"),
            available_libraries=data.get("availableLibraries"),
            allow_external_api=data.get("allowExternalAPI", False),
            hardcoded_script=data.get("hardcodedScript", False),
            is_template=data.get("isTemplate", False),
        )


# Scheduled Job types
@dataclass
class ScheduledJob:
    """Represents a scheduled job (cron job)."""

    id: str
    name: str
    workspace_id: str = ""
    description: Optional[str] = None
    agent_id: Optional[str] = None
    custom_prompt_id: Optional[str] = None
    forced_prompt: Optional[str] = None
    schedule: Dict[str, Any] = field(default_factory=dict)
    timezone: Optional[str] = None
    is_active: bool = True
    status: str = "ACTIVE"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledJob":
        """Create a ScheduledJob instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workspace_id=data.get("workspaceid", ""),
            description=data.get("description"),
            agent_id=data.get("agentID"),
            custom_prompt_id=data.get("customPromptID"),
            forced_prompt=data.get("forcedPrompt"),
            schedule=data.get("schedule", {}),
            timezone=data.get("timezone"),
            is_active=data.get("isActive", True),
            status=data.get("status", "ACTIVE"),
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
        )


# Secret types
@dataclass
class Secret:
    """Represents a secret."""

    id: str
    name: str
    workspace_id: str = ""
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Secret":
        """Create a Secret instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            workspace_id=data.get("workspaceid", ""),
            description=data.get("description"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


# Dictionary types
@dataclass
class DictionaryEntry:
    """Represents a dictionary entry for translations."""

    id: str
    owner: str
    source_language: str
    target_language: str
    source_text: str
    target_text: str
    workspace_id: str = ""
    pos: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DictionaryEntry":
        """Create a DictionaryEntry instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            owner=data.get("owner", ""),
            source_language=data.get("sourceLanguage", ""),
            target_language=data.get("targetLanguage", ""),
            source_text=data.get("sourceText", ""),
            target_text=data.get("targetText", ""),
            workspace_id=data.get("workspaceid", ""),
            pos=data.get("pos"),
            description=data.get("description"),
            created_by=data.get("createdBy"),
            updated_by=data.get("updatedBy"),
        )


# Embeddings types
@dataclass
class Embedding:
    """Represents a document embedding."""

    id: str
    chunk_id: str
    title: Optional[str] = None
    external_path: Optional[str] = None
    type: Optional[str] = None
    raw_text: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Embedding":
        """Create an Embedding instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            chunk_id=data.get("chunk_id", ""),
            title=data.get("title"),
            external_path=data.get("external_path"),
            type=data.get("type"),
            raw_text=data.get("raw_text"),
        )


# Charting Settings types
@dataclass
class ChartingSettings:
    """Represents workspace charting settings."""

    id: str
    workspace_id: str = ""
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    tertiary_color: Optional[str] = None
    primary_text_color: Optional[str] = None
    primary_border_color: Optional[str] = None
    line_color: Optional[str] = None
    plot_primary_color: Optional[str] = None
    plot_secondary_color: Optional[str] = None
    plot_tertiary_color: Optional[str] = None
    xy_background_color: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChartingSettings":
        """Create a ChartingSettings instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceid", ""),
            primary_color=data.get("primaryColor"),
            secondary_color=data.get("secondaryColor"),
            tertiary_color=data.get("tertiaryColor"),
            primary_text_color=data.get("primaryTextColor"),
            primary_border_color=data.get("primaryBorderColor"),
            line_color=data.get("lineColor"),
            plot_primary_color=data.get("plotPrimaryColor"),
            plot_secondary_color=data.get("plotSecondaryColor"),
            plot_tertiary_color=data.get("plotTertiaryColor"),
            xy_background_color=data.get("xyBackgroundColor"),
        )


# Embeddings Settings types
@dataclass
class EmbeddingsSettings:
    """Represents workspace embeddings settings."""

    id: str
    workspace_id: str = ""
    max_chunk_words: int = 500
    max_overlap_sentences: int = 2
    chunking_strategy: str = "keywords"
    image_extraction_strategy: str = "safe"
    min_image_width: int = 100
    min_image_height: int = 100
    aspect_ratio_min: float = 0.1
    aspect_ratio_max: float = 1.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddingsSettings":
        """Create an EmbeddingsSettings instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceid", ""),
            max_chunk_words=data.get("maxChunkWords", 500),
            max_overlap_sentences=data.get("maxOverlapSentences", 2),
            chunking_strategy=data.get("chunkingStrategy", "keywords"),
            image_extraction_strategy=data.get("imageExtractionStrategy", "safe"),
            min_image_width=data.get("minImageWidth", 100),
            min_image_height=data.get("minImageHeight", 100),
            aspect_ratio_min=data.get("aspectRatioMin", 0.1),
            aspect_ratio_max=data.get("aspectRatioMax", 1.0),
        )


# Billing types
@dataclass
class MonthCostsResponse:
    """Represents monthly usage and cost breakdown."""

    api_usage: Dict[str, Any] = field(default_factory=dict)
    training_usage: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonthCostsResponse":
        """Create a MonthCostsResponse instance from a dictionary."""
        return cls(
            api_usage=data.get("apiUsage", {}),
            training_usage=data.get("trainingUsage", {}),
        )


# Request Log types
@dataclass
class RequestLog:
    """Represents a request log."""

    id: str
    workspace_id: str = ""
    srt_key: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    words: Optional[int] = None
    tokens: Optional[int] = None
    sentences: Optional[int] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequestLog":
        """Create a RequestLog instance from a dictionary."""
        return cls(
            id=data.get("id", ""),
            workspace_id=data.get("workspaceid", ""),
            srt_key=data.get("srtKey"),
            type=data.get("type"),
            status=data.get("status"),
            words=data.get("words"),
            tokens=data.get("tokens"),
            sentences=data.get("sentences"),
            created_by=data.get("createdBy"),
            updated_by=data.get("updatedBy"),
        )
