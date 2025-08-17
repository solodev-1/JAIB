import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from src.memory import MemoryManager
from src.conversation_logger import ConversationLogger


class ConversationManager:
    """Manages the conversation flow between user and bot."""
    
    def __init__(
        self, 
        system_prompt: str, 
        memory_manager: MemoryManager,
        conversation_logger: ConversationLogger,
        bot_info: Dict[str, Any],
        logger: logging.Logger,
        use_memory: bool = True
    ):
        self.system_prompt = system_prompt
        self.memory_manager = memory_manager
        self.conversation_logger = conversation_logger
        self.bot_info = bot_info
        self.logger = logger
        self.use_memory = use_memory
        self.messages = [{"role": "system", "content": system_prompt}]
        self.conversation_summary = ""
        self.turn_count = 0
        self.max_context_length = 50  # Maximum messages to keep in context
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})
        self.turn_count += 1
        
        # Log the message
        speaker = self.bot_info["NAME"] if role == "assistant" else ("User" if role == "user" else "System")
        self.conversation_logger.log_message(speaker, content)
        
        # If context is getting too long, summarize older messages
        if len(self.messages) > self.max_context_length:
            self._summarize_old_messages()
    
    def _summarize_old_messages(self) -> None:
        """Summarize older messages to prevent context from getting too long."""
        # Keep system prompt and recent messages
        system_message = self.messages[0]
        recent_messages = self.messages[-20:]  # Keep last 20 messages
        
        # Messages to summarize (everything between system and recent)
        old_messages = self.messages[1:-20]
        
        if old_messages:
            # Create a simple summary of the old messages
            summary_parts = []
            user_inputs = [msg["content"] for msg in old_messages if msg["role"] == "user"]
            bot_responses = [msg["content"] for msg in old_messages if msg["role"] == "assistant"]
            
            if user_inputs:
                summary_parts.append(f"User mentioned topics like: {', '.join(set(user_inputs))[:100]}...")
            if bot_responses:
                summary_parts.append(f"Bot shared information about: {', '.join(set(bot_responses))[:100]}...")
            
            self.conversation_summary = " | ".join(summary_parts)
            
            # Rebuild messages with summary
            summary_message = {
                "role": "system", 
                "content": f"Earlier in the conversation: {self.conversation_summary}"
            }
            
            self.messages = [system_message, summary_message] + recent_messages
            self.logger.debug("Conversation summarized to prevent context overflow")
    
    def get_memory_context(self) -> str:
        """Get formatted memory context for the next prompt."""
        if not self.use_memory:
            return ""
        
        # Adjust memory limit based on conversation length
        memory_limit = min(8, max(3, 10 - (self.turn_count // 5)))
        recent_mems = self.memory_manager.load_recent_memories(limit=memory_limit)
        
        return self.memory_manager.format_memories_as_context(recent_mems)
    
    def reset_conversation(self, new_system_prompt: Optional[str] = None) -> None:
        """Reset the conversation history, keeping memory intact."""
        system_prompt = new_system_prompt or self.system_prompt
        self.messages = [{"role": "system", "content": system_prompt}]
        self.turn_count = 0
        self.conversation_summary = ""
        self.logger.debug("Conversation reset")
    
    def rewind_last_exchange(self) -> bool:
        """Remove the last user-assistant exchange from the conversation."""
        if len(self.messages) < 3:  # Need at least system + one exchange
            return False
        
        # Remove last two messages (user and assistant)
        self.messages.pop()  # Assistant
        self.messages.pop()  # User
        self.turn_count -= 1
        
        self.logger.debug("Rewound last exchange")
        return True
    
    def update_system_prompt(self, new_system_prompt: str) -> None:
        """Update the system prompt and reset the conversation."""
        self.system_prompt = new_system_prompt
        self.reset_conversation(new_system_prompt)
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get messages formatted for API call."""
        return self.messages.copy()