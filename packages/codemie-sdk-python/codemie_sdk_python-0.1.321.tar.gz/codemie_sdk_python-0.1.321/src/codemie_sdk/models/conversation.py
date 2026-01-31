"""Models for conversation-related data structures."""

from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from codemie_sdk.models.assistant import ContextType


class Conversation(BaseModel):
    """
    Model for conversation summary data as returned from the list endpoint.
    """

    id: str
    name: str
    folder: Optional[str]
    pinned: bool
    date: str
    assistant_ids: List[str]
    initial_assistant_id: Optional[str]


class Mark(BaseModel):
    """Model for conversation review/mark data."""

    mark: str
    rating: int
    comments: str
    date: datetime
    operator: Optional["Operator"] = None


class Operator(BaseModel):
    """Represents an operator involved in marking a conversation."""

    user_id: str
    name: str


class Thought(BaseModel):
    """Model for reasoning or tool-invocation within a message's history."""

    id: str
    parent_id: Optional[str]
    metadata: dict
    in_progress: bool
    input_text: Optional[str]
    message: Optional[str]
    author_type: str
    author_name: str
    output_format: str
    error: Optional[bool]
    children: List[str]


class HistoryMark(BaseModel):
    """Model for conversation history review/mark data."""

    mark: str
    rating: int
    comments: Optional[str]
    date: datetime


class HistoryItem(BaseModel):
    """Represents an individual message within a conversation's history."""

    role: str
    message: str
    historyIndex: int
    date: datetime
    responseTime: Optional[float] = None
    inputTokens: Optional[int] = None
    outputTokens: Optional[int] = None
    cacheCreationInputTokens: Optional[int] = None
    cacheReadInputTokens: Optional[int] = None
    moneySpent: Optional[float] = None
    userMark: Optional[HistoryMark] = None
    operatorMark: Optional[HistoryMark] = None
    messageRaw: Optional[str] = None
    fileNames: List[str]
    assistantId: Optional[str] = None
    thoughts: Optional[List[Thought]] = Field(default_factory=list)
    workflowExecutionRef: Optional[Union[str, bool]] = None
    executionId: Optional[str] = None


class ContextItem(BaseModel):
    """Represents contextual settings for conversation."""

    context_type: Optional[ContextType]
    name: str


class ToolItem(BaseModel):
    """Represents a tool used by an assistant, including configuration and description."""

    name: str
    label: Optional[str]
    settings_config: Optional[bool]
    description: Optional[str] = None
    user_description: Optional[str]


class AssistantDataItem(BaseModel):
    """Model represents details for an assistant included in a conversation."""

    assistant_id: str
    assistant_name: str
    assistant_icon: Optional[str]
    assistant_type: Optional[str]
    context: Optional[List[Union[ContextItem, str]]] = None
    tools: Optional[List[ToolItem]] = None
    conversation_starters: List[str] = []


class ConversationDetailsData(BaseModel):
    """Extended details about a conversation's configuration and context."""

    llm_model: Optional[str]
    context: List[ContextItem]
    app_name: Optional[str]
    repo_name: Optional[str]
    index_type: Optional[str]


class AssistantDetailsData(BaseModel):
    """Extended details about an assistant included in a conversation."""

    assistant_id: str
    assistant_name: str
    assistant_icon: Optional[str]
    assistant_type: Optional[str]
    context: List[Union[ContextItem, str]]
    tools: List[ToolItem]
    conversation_starters: List[str]


class ConversationCreateRequest(BaseModel):
    """Model for creating a new conversation."""

    initial_assistant_id: Optional[str] = None
    folder: Optional[str] = None
    mcp_server_single_usage: Optional[bool] = False
    is_workflow_conversation: Optional[bool] = Field(
        default=None, serialization_alias="is_workflow"
    )


class ConversationDetails(BaseModel):
    """Summary information for a user conversation as returned from list endpoints."""

    id: str
    date: datetime
    update_date: datetime
    conversation_id: str
    conversation_name: str
    llm_model: Optional[str]
    folder: Optional[str]
    pinned: bool
    history: List[HistoryItem]
    user_id: str
    user_name: str
    assistant_ids: List[str]
    assistant_data: List[AssistantDataItem]
    initial_assistant_id: str
    final_user_mark: Optional[Mark]
    final_operator_mark: Optional[Mark]
    project: Optional[str]
    conversation_details: Optional[ConversationDetailsData]
    assistant_details: Optional[AssistantDetailsData]
    user_abilities: Optional[List[str]]
    is_folder_migrated: bool
    is_workflow_conversation: Optional[bool] = None
    category: Optional[str]
    mcp_server_single_usage: Optional[bool] = False


class ConversationShareRequest(BaseModel):
    """Model for creating share conversation request."""

    chat_id: str


class ConversationShareResponse(BaseModel):
    """Model for conversation share response."""

    share_id: str
    token: str
    created_at: str
    access_count: int


class SharedConversationResponse(BaseModel):
    """Model for shared conversation details response."""

    conversation: ConversationDetails
    shared_by: str
    created_at: str
    access_count: int


class BaseResponse(BaseModel):
    """Generic base response model with message field."""

    message: str


class UpdateConversationRequest(BaseModel):
    """Model for updating an existing conversation."""

    name: Optional[str] = None
    folder: Optional[str] = None
    pinned: Optional[bool] = None


class ConversationFolder(BaseModel):
    """Model for conversation folder metadata."""

    id: str
    user_id: str
    folder_name: str
    date: str
    update_date: str
    user_abilities: List[str]


class UpdateConversationFolderRequest(BaseModel):
    """Model for creating or updating a folder name."""

    folder: str


class UpdateHistoryByIndexRequest(BaseModel):
    """Model for updating message content in conversation history by index."""

    messageIndex: int
    message: str


class UpsertHistoryRequest(BaseModel):
    """Model for upserting conversation history."""

    history: List[HistoryItem]
    assistant_id: Optional[str] = None
    folder: Optional[str] = None


class UpsertHistoryResponse(BaseModel):
    """Response model for conversation history upsert operation."""

    conversation_id: str
    new_messages: int
    total_messages: int
    created: bool
