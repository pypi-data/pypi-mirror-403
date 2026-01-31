"""Conversation service implementation."""

from typing import List, Union, Optional, Dict
import requests

from ..models.conversation import (
    Conversation,
    ConversationDetails,
    ConversationCreateRequest,
    UpdateConversationRequest,
    ConversationFolder,
    UpdateConversationFolderRequest,
    UpdateHistoryByIndexRequest,
    UpsertHistoryRequest,
    UpsertHistoryResponse,
    BaseResponse,
    ConversationShareRequest,
    ConversationShareResponse,
    SharedConversationResponse,
)
from ..models.assistant import AssistantChatRequest
from ..utils import ApiRequestHandler


class ConversationService:
    """Service for managing user conversations."""

    def __init__(self, api_domain: str, token: str, verify_ssl: bool = True):
        """Initialize the conversation service.

        Args:
            api_domain: Base URL for the API
            token: Authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self._api = ApiRequestHandler(api_domain, token, verify_ssl)

    def list(self) -> List[Conversation]:
        """Get list of all conversations for the current user.

        Returns:
            List of all conversations for the current user.
        """
        return self._api.get("/v1/conversations", List[Conversation])

    def list_by_assistant_id(self, assistant_id: str) -> List[Conversation]:
        """Get list of all conversations for the current user that include the specified assistant.

        Args:
            assistant_id: Assistant ID

        Returns:
            List of conversations for the specified assistant.
        """
        return [
            conv
            for conv in self._api.get("/v1/conversations", List[Conversation])
            if assistant_id in conv.assistant_ids
        ]

    def get_conversation(self, conversation_id: str) -> ConversationDetails:
        """Get details for a specific conversation by its ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation details
        """
        return self._api.get(
            f"/v1/conversations/{conversation_id}",
            ConversationDetails,
        )

    def create(self, request: ConversationCreateRequest) -> dict:
        """Create a new conversation.

        Args:
            request: Conversation creation request

        Returns:
            Created conversation details
        """
        return self._api.post(
            "/v1/conversations",
            dict,
            json_data=request.model_dump(exclude_none=True, by_alias=True),
        )

    def chat(
        self,
        conversation_id: str,
        request: AssistantChatRequest,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[requests.Response, ConversationDetails]:
        """Send a chat message to a conversation.

        This method is used for workflow chat mode where the workflow_id is set
        as the initial_assistant_id when creating the conversation.

        Args:
            conversation_id: Conversation ID to send message to
            request: Chat request details
            headers: Optional additional HTTP headers (e.g., X-* for MCP propagation)

        Returns:
            ConversationDetails with updated history or streaming response
        """
        response = self._api.put(
            f"/v1/conversations/{conversation_id}",
            ConversationDetails,
            json_data=request.model_dump(exclude_none=True, by_alias=True),
            stream=request.stream,
            extra_headers=headers,
        )
        return response

    def delete(self, conversation_id: str) -> dict:
        """Delete a specific conversation by its ID.

        Args:
            conversation_id: Conversation ID to delete

        Returns:
            Deletion confirmation
        """
        return self._api.delete(
            f"/v1/conversations/{conversation_id}",
            dict,
        )

    def update(
        self, conversation_id: str, request: UpdateConversationRequest
    ) -> ConversationDetails:
        """Update an existing conversation.

        Args:
            conversation_id: Conversation ID to update
            request: Update request with fields to modify

        Returns:
            Updated conversation details
        """
        return self._api.put(
            f"/v1/conversations/{conversation_id}",
            ConversationDetails,
            json_data=request.model_dump(exclude_none=True),
        )

    def delete_all(self) -> BaseResponse:
        """Delete all conversations for the current user.

        Returns:
            Deletion confirmation
        """
        return self._api.delete("/v1/conversations", BaseResponse)

    def get_files(self, conversation_id: str) -> list:
        """Get list of files attached to a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of file names
        """
        response = self._api.get(
            f"/v1/conversations/{conversation_id}/files",
            dict,
            wrap_response=False,
        )
        # API returns list directly, not wrapped in 'data' field

        return response

    # Folder management methods

    def list_folders(self) -> List[ConversationFolder]:
        """Get list of all conversation folders for the current user.

        Returns:
            List of conversation folders
        """
        return self._api.get("/v1/conversations/folders/list", List[ConversationFolder])

    def create_folder(self, request: UpdateConversationFolderRequest) -> BaseResponse:
        """Create a new conversation folder.

        Args:
            request: Folder creation request with name

        Returns:
            Creation confirmation
        """
        return self._api.post(
            "/v1/conversations/folder",
            BaseResponse,
            json_data=request.model_dump(exclude_none=True),
        )

    def update_folder(
        self, folder: str, request: UpdateConversationFolderRequest
    ) -> BaseResponse:
        """Rename an existing conversation folder.

        Args:
            folder: Current folder name
            request: Update request with new name

        Returns:
            Update confirmation
        """
        return self._api.put(
            f"/v1/conversations/folder/{folder}",
            BaseResponse,
            json_data=request.model_dump(exclude_none=True),
        )

    def delete_folder(
        self, folder: str, remove_conversations: bool = False
    ) -> BaseResponse:
        """Delete a conversation folder.

        Args:
            folder: Folder name to delete
            remove_conversations: Whether to also delete conversations in the folder

        Returns:
            Deletion confirmation
        """
        endpoint = f"/v1/conversations/folder/{folder}"
        if remove_conversations:
            endpoint += "?remove_conversations=true"
        else:
            endpoint += "?remove_conversations=false"

        return self._api.delete(endpoint, BaseResponse)

    # History management methods

    def upsert_history(
        self, conversation_id: str, request: UpsertHistoryRequest
    ) -> UpsertHistoryResponse:
        """Create or update conversation with history (idempotent upsert).

        If conversation doesn't exist, creates it with custom ID and provided history.
        If conversation exists, appends only NEW messages not already present.

        Args:
            conversation_id: Conversation ID (will be created if doesn't exist)
            request: History upsert request with messages

        Returns:
            Upsert response with metadata about operation
        """
        return self._api.put(
            f"/v1/conversations/{conversation_id}/history",
            UpsertHistoryResponse,
            json_data=request.model_dump(mode="json", exclude_none=True),
        )

    def delete_history(self, conversation_id: str) -> ConversationDetails:
        """Clear all history from a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Updated conversation details with empty history
        """
        return self._api.delete(
            f"/v1/conversations/{conversation_id}/history",
            ConversationDetails,
        )

    def delete_history_by_index(
        self, conversation_id: str, history_index: int
    ) -> ConversationDetails:
        """Remove a specific history item by index.

        Args:
            conversation_id: Conversation ID
            history_index: Index of history item to delete

        Returns:
            Updated conversation details
        """
        return self._api.delete(
            f"/v1/conversations/{conversation_id}/history/{history_index}",
            ConversationDetails,
        )

    def update_history_by_index(
        self, conversation_id: str, request: UpdateHistoryByIndexRequest
    ) -> ConversationDetails:
        """Update an Assistant response in conversation history by index.

        Args:
            conversation_id: Conversation ID
            request: Update request with message index and new message content

        Returns:
            Updated conversation details
        """
        return self._api.put(
            f"/v1/conversations/{conversation_id}/history/{request.messageIndex}",
            ConversationDetails,
            json_data=request.model_dump(exclude_none=True),
        )

    def share_conversation(self, chat_id: str) -> ConversationShareResponse:
        """Create a share link for a conversation.

        Args:
            chat_id: Conversation ID to share

        Returns:
            Share response with token and metadata
        """
        request = ConversationShareRequest(chat_id=chat_id)
        return self._api.post(
            "/v1/share/conversations",
            ConversationShareResponse,
            json_data=request.model_dump(exclude_none=True),
        )

    def get_shared_conversation(self, token: str) -> SharedConversationResponse:
        """Get a shared conversation using its share token.

        Args:
            token: Share token

        Returns:
            Shared conversation details including history
        """
        return self._api.get(
            f"/v1/share/conversations/{token}",
            SharedConversationResponse,
        )
