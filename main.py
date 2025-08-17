#!/usr/bin/env python3
"""
Roleplay Bot using Llama 3.1 (via Ollama) + Python with c.ai-style interface
- Loads persona from BotInfo.json (NAME, AGE, GENDER, PERSONALITY, PRONOUNS, INTRO MESSAGE, LOVES, HATES, CHAT_COLOR)
- Builds a system prompt that keeps the bot in character
- Enhanced memory system with smarter auto-recall
- c.ai-style interface with action formatting
- Saves conversation logs to the logs folder
- Saves all chat messages to a single file in the chats folder
- Works offline with Ollama (https://ollama.ai)
- Optional NSFW mode for adult-oriented roleplay
- Optional romantic mode for semi-romantic interactions
Usage:
  1) pip install ollama
  2) ollama pull llama3.1
  3) python main.py --model llama3.1
"""
import argparse
import logging
import sys
from pathlib import Path
try:
    import ollama
except ImportError:
    print("Missing dependency: pip install ollama", file=sys.stderr)
    sys.exit(1)

# Import from src directory
from src.config import setup_logging, DEFAULT_MODEL, DEFAULT_BOTINFO, DEFAULT_MEMFILE, TRANSCRIPT_DIR, LOG_DIR, CHAT_DIR
from src.memory import MemoryManager
from src.transcript import TranscriptExporter
from src.conversation_logger import ConversationLogger
from src.ui import SimpleUI, RichUI, HAS_RICH
from src.bot import load_botinfo, build_system_prompt
from src.command_handler import CommandHandler
from src.parser import make_parser
from src.conversation_manager import ConversationManager

def make_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description="AI Roleplay Bot")
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Ollama model to use (default: llama3.1)"
    )
    parser.add_argument(
        "--botinfo",
        type=str,
        default=DEFAULT_BOTINFO,
        help="Path to BotInfo.json (default: BotInfo.json)"
    )
    parser.add_argument(
        "--memfile",
        type=str,
        default=DEFAULT_MEMFILE,
        help="Path to memory file (default: memory.json)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--simple-ui",
        action="store_true",
        help="Force simple UI even if rich is available"
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable memory system"
    )
    parser.add_argument(
        "--export-format",
        type=str,
        default="txt",
        choices=["txt", "json"],
        help="Export format for transcripts (default: txt)"
    )
    parser.add_argument(
        "--nsfw",
        action="store_true",
        help="Enable NSFW mode for adult-oriented roleplay"
    )
    parser.add_argument(
        "--romantic-mode",
        action="store_true",
        help="Enable romantic mode for semi-romantic interactions"
    )
    return parser

class RoleplayBotApp:
    """Main application class for the Roleplay Bot."""
    
    def __init__(self, args):
        self.args = args
        self.logger = setup_logging(args.log_level)
        self.ui = self._create_ui()
        self.bot = None
        self.memory_manager = None
        self.conversation_logger = None
        self.conversation_manager = None
        self.command_handler = CommandHandler()
        self.nsfw_mode = args.nsfw
        self.romantic_mode = args.romantic_mode
    
    def _create_ui(self):
        """Create the appropriate UI based on availability and user preference."""
        if HAS_RICH and not self.args.simple_ui:
            return RichUI()
        return SimpleUI()
    
    def _initialize_components(self):
        """Initialize all components of the application."""
        try:
            # Load bot information
            botinfo_path = Path(self.args.botinfo)
            self.bot = load_botinfo(botinfo_path, self.logger)
            
            # Initialize memory manager
            memfile = Path(self.args.memfile)
            self.memory_manager = MemoryManager(memfile, self.logger)
            
            # Initialize conversation logger
            self.conversation_logger = ConversationLogger(self.bot["NAME"], Path(CHAT_DIR))
            
            # Build system prompt
            system_prompt = build_system_prompt(
                self.bot, 
                nsfw_mode=self.nsfw_mode, 
                romantic_mode=self.romantic_mode
            )
            
            # Initialize conversation manager
            self.conversation_manager = ConversationManager(
                system_prompt=system_prompt,
                memory_manager=self.memory_manager,
                conversation_logger=self.conversation_logger,
                bot_info=self.bot,
                logger=self.logger,
                use_memory=not self.args.no_memory
            )
            
            # Log initialization
            self.logger.info(f"Starting Roleplay Bot: {self.bot['NAME']} (model: {self.args.model})")
            if self.nsfw_mode:
                self.logger.info("NSFW mode enabled")
            if self.romantic_mode:
                self.logger.info("Romantic mode enabled")
                
            return True
            
        except Exception as e:
            self.logger.critical(f"Failed to initialize components: {e}", exc_info=True)
            self.ui.print_system_message(f"[!] Critical error: {e}")
            return False
    
    def _display_intro(self):
        """Display the bot's introduction message."""
        # Print header
        self.ui.print_header(self.bot["NAME"], self.nsfw_mode, self.romantic_mode)
        
        # Use the intro message from BotInfo if available
        intro_message = self.bot.get("INTRO MESSAGE", "Greetings, traveler. What brings you here?")
        self.ui.print_bot_message(intro_message, self.bot["NAME"], self.bot.get("CHAT_COLOR", "cyan"))
        self.conversation_manager.add_message("assistant", intro_message)
    
    def _process_user_input(self, user_input):
        """Process user input and generate bot response."""
        # Check if input is a command
        if user_input.startswith("/"):
            should_continue, messages, nsfw_mode, romantic_mode = self.command_handler.handle_command(
                user_input, 
                self.conversation_manager.messages,
                self.conversation_manager.system_prompt,
                self.memory_manager,
                self.bot,
                self.args.export_format,
                self.logger,
                self.conversation_logger,
                self.nsfw_mode,
                self.romantic_mode,
                self.ui
            )
            
            # Update mode states if they changed
            if nsfw_mode != self.nsfw_mode or romantic_mode != self.romantic_mode:
                self.nsfw_mode = nsfw_mode
                self.romantic_mode = romantic_mode
                
                # Update system prompt
                new_system_prompt = build_system_prompt(
                    self.bot, 
                    nsfw_mode=self.nsfw_mode, 
                    romantic_mode=self.romantic_mode
                )
                self.conversation_manager.update_system_prompt(new_system_prompt)
            
            # Update conversation manager's messages
            self.conversation_manager.messages = messages
            
            return should_continue
        
        # Regular user message
        # Print user message
        self.ui.print_user_message(user_input)
        
        # Build context with optional memory
        context_prefix = self.conversation_manager.get_memory_context()
        
        # Add the user message (with memory context prepended)
        user_payload = context_prefix + user_input if context_prefix else user_input
        self.conversation_manager.add_message("user", user_payload)
        
        # Get model response
        try:
            resp = ollama.chat(model=self.args.model, messages=self.conversation_manager.get_messages_for_api())
            reply = resp["message"]["content"].strip()
            
            # Print and store response
            self.ui.print_bot_message(reply, self.bot["NAME"], self.bot.get("CHAT_COLOR", "cyan"))
            self.conversation_manager.add_message("assistant", reply)
            
            # Auto-memory extraction
            if not self.args.no_memory:
                auto_memories = self.memory_manager.extract_auto_memories(reply)
                for memory in auto_memories:
                    self.memory_manager.append_memory(memory, tags=["auto"])
                    self.logger.debug(f"Auto-remembered: {memory[:50]}...")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model error: {e}")
            self.ui.print_system_message(f"[!] Model error: {e}")
            
            # Remove the last user message to keep history clean if it failed
            self.conversation_manager.messages.pop()
            
            return True
    
    def run(self):
        """Run the main application loop."""
        # Initialize components
        if not self._initialize_components():
            return 1
        
        # Display introduction
        self._display_intro()
        
        # Main conversation loop
        while True:
            try:
                self.ui.print_footer()
                user_input = self.ui.get_user_input()
            except (EOFError, KeyboardInterrupt):
                self.ui.print_system_message("\n[bye]")
                self.conversation_logger.log_message("System", "Conversation ended")
                break
                
            if not user_input:
                continue
                
            # Process user input
            should_continue = self._process_user_input(user_input)
            if not should_continue:
                break
        
        return 0

def main():
    """Main application entry point."""
    args = make_parser().parse_args()
    app = RoleplayBotApp(args)
    return app.run()

if __name__ == "__main__":
    sys.exit(main())