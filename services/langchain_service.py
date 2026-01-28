"""
LangChain Service - Handles conversation memory and RAG
"""
from typing import List, Dict, Optional
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from config import Config
import json


class LangChainService:
    def __init__(self):
        self.memories = {}  # Store memories by conversation_id
        self.max_tokens = Config.MEMORY_MAX_TOKENS
        self.context_window = Config.CONTEXT_WINDOW

    def get_memory(self, conversation_id: str) -> ConversationBufferMemory:
        """Get or create memory for a conversation"""
        if conversation_id not in self.memories:
            self.memories[conversation_id] = ConversationBufferMemory(
                return_messages=True,
                output_key="output",
                input_key="input"
            )
        return self.memories[conversation_id]

    def add_message(
            self,
            conversation_id: str,
            user_message: str,
            ai_message: str
    ):
        """Add a message pair to memory"""
        memory = self.get_memory(conversation_id)
        memory.save_context(
            {"input": user_message},
            {"output": ai_message}
        )

    def get_context(
            self,
            conversation_id: str,
            max_messages: Optional[int] = None
    ) -> List[Dict]:
        """Get conversation context"""
        memory = self.get_memory(conversation_id)
        messages = memory.chat_memory.messages

        max_messages = max_messages or self.context_window

        # Get last N messages
        recent_messages = messages[-max_messages * 2:] if messages else []

        # Convert to dict format
        context = []
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                context.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                context.append({"role": "assistant", "content": msg.content})

        return context

    def clear_memory(self, conversation_id: str):
        """Clear conversation memory"""
        if conversation_id in self.memories:
            self.memories[conversation_id].clear()

    def get_all_conversations(self) -> List[str]:
        """Get list of all conversation IDs"""
        return list(self.memories.keys())
