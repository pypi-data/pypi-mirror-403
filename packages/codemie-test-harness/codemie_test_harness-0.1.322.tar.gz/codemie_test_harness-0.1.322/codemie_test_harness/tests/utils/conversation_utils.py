import requests
from typing import List, Union, Optional, Dict
from codemie_sdk.models.conversation import (
    ConversationCreateRequest,
    ConversationDetails,
    UpdateConversationRequest,
    UpdateConversationFolderRequest,
    UpdateHistoryByIndexRequest,
    UpsertHistoryRequest,
    HistoryItem,
)
from codemie_sdk.models.assistant import AssistantChatRequest

from codemie_test_harness.tests.utils.base_utils import BaseUtils


class ConversationUtils(BaseUtils):
    def list_conversations(self):
        return self.client.conversations.list()

    def get_conversation_by_assistant_id(self, assistant_id: str):
        return self.client.conversations.list_by_assistant_id(assistant_id)

    def get_conversation_by_id(self, conversation_id: str) -> requests.Response:
        return self.client.conversations.get_conversation(conversation_id)

    def create_conversation(
        self,
        initial_assistant_id: str = None,
        folder: str = None,
        mcp_server_single_usage: bool = False,
        is_workflow_conversation: bool = None,
    ):
        """Create a new conversation."""
        request = ConversationCreateRequest(
            initial_assistant_id=initial_assistant_id,
            folder=folder,
            mcp_server_single_usage=mcp_server_single_usage,
            is_workflow_conversation=is_workflow_conversation,
        )
        return self.client.conversations.create(request)

    def update_conversation(
        self,
        conversation_id: str,
        name: str = None,
        folder: str = None,
        pinned: bool = None,
    ):
        """Update an existing conversation."""
        request = UpdateConversationRequest(name=name, folder=folder, pinned=pinned)
        return self.client.conversations.update(conversation_id, request)

    def delete_conversation(self, conversation_id: str) -> requests.Response:
        return self.client.conversations.delete(conversation_id)

    def delete_all_conversations(self):
        """Delete all conversations for the current user."""
        return self.client.conversations.delete_all()

    def get_conversation_files(self, conversation_id: str) -> list:
        """Get list of files attached to a conversation."""
        return self.client.conversations.get_files(conversation_id)

    # Folder management methods

    def list_folders(self):
        """Get list of all conversation folders."""
        return self.client.conversations.list_folders()

    def create_folder(self, name: str):
        """Create a new conversation folder."""
        request = UpdateConversationFolderRequest(folder=name)
        return self.client.conversations.create_folder(request)

    def update_folder(self, folder: str, new_name: str):
        """Rename an existing conversation folder."""
        request = UpdateConversationFolderRequest(folder=new_name)
        return self.client.conversations.update_folder(folder, request)

    def delete_folder(self, folder: str, remove_conversations: bool = False):
        """Delete a conversation folder."""
        return self.client.conversations.delete_folder(folder, remove_conversations)

    # History management methods

    def upsert_history(
        self,
        conversation_id: str,
        history: List[HistoryItem],
        assistant_id: str = None,
        folder: str = None,
    ):
        """Create or update conversation with history (idempotent upsert)."""
        request = UpsertHistoryRequest(
            history=history, assistant_id=assistant_id, folder=folder
        )
        return self.client.conversations.upsert_history(conversation_id, request)

    def delete_history(self, conversation_id: str):
        """Clear all history from a conversation."""
        return self.client.conversations.delete_history(conversation_id)

    def delete_history_by_index(self, conversation_id: str, history_index: int):
        """Remove a specific history item by index."""
        return self.client.conversations.delete_history_by_index(
            conversation_id, history_index
        )

    def update_history_by_index(
        self, conversation_id: str, history_index: int, message: str
    ):
        """Update a message in conversation history by index."""
        request = UpdateHistoryByIndexRequest(
            messageIndex=history_index, message=message
        )
        return self.client.conversations.update_history_by_index(
            conversation_id, request
        )

    def chat(
        self,
        conversation_id: str,
        request: AssistantChatRequest,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[requests.Response, ConversationDetails]:
        """Send a chat message to a conversation.

        This is used for workflow chat mode where the workflow_id is set
        as the initial_assistant_id when creating the conversation.

        Args:
            conversation_id: Conversation ID to send message to
            request: Chat request details
            headers: Optional additional HTTP headers

        Returns:
            ConversationDetails with updated history or streaming response
        """
        return self.client.conversations.chat(conversation_id, request, headers)

    # Share management methods

    def share_conversation(self, conversation_id: str):
        """Create a shareable link for a conversation."""
        return self.client.conversations.share_conversation(conversation_id)

    def get_shared_conversation(self, share_token: str):
        """Get a shared conversation using the share token."""
        return self.client.conversations.get_shared_conversation(share_token)
