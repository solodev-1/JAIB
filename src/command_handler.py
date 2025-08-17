import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Callable, Optional
from abc import ABC, abstractmethod

from src.transcript import TranscriptExporter
from src.ui import SimpleUI, RichUI
from src.bot import show_persona_rich, show_persona_simple, build_system_prompt
from src.config import TRANSCRIPT_DIR


class BaseCommand(ABC):
    """Base class for all commands."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(
        self, 
        args: List[str], 
        context: "CommandContext"
    ) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        """
        Execute the command.
        
        Returns:
            A tuple of (should_continue, messages, nsfw_mode, romantic_mode)
        """
        pass


class CommandContext:
    """Context object containing all the state needed for command execution."""
    
    def __init__(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        memory_manager,
        bot: Dict[str, Any],
        export_format: str,
        logger: logging.Logger,
        conversation_logger,
        nsfw_mode: bool,
        romantic_mode: bool,
        ui
    ):
        self.messages = messages
        self.system_prompt = system_prompt
        self.memory_manager = memory_manager
        self.bot = bot
        self.export_format = export_format
        self.logger = logger
        self.conversation_logger = conversation_logger
        self.nsfw_mode = nsfw_mode
        self.romantic_mode = romantic_mode
        self.ui = ui


class QuitCommand(BaseCommand):
    """Exit the program."""
    
    def __init__(self):
        super().__init__("/quit", "Exit the program")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        context.conversation_logger.log_message("System", "Conversation ended")
        return False, context.messages, context.nsfw_mode, context.romantic_mode


class HelpCommand(BaseCommand):
    """Show help for all commands."""
    
    def __init__(self, command_handler):
        super().__init__("/help", "Show this help")
        self.command_handler = command_handler
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        help_text = "Commands:\n"
        for cmd in self.command_handler.commands.values():
            help_text += f"{cmd.name.ljust(15)} {cmd.description}\n"
        context.ui.print_system_message(help_text)
        return True, context.messages, context.nsfw_mode, context.romantic_mode


class ResetCommand(BaseCommand):
    """Clear the current conversation."""
    
    def __init__(self):
        super().__init__("/reset", "Clear the current conversation (keeps long-term memory)")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        # Rebuild system prompt with current NSFW and romantic modes
        new_system_prompt = build_system_prompt(
            context.bot, 
            nsfw_mode=context.nsfw_mode, 
            romantic_mode=context.romantic_mode
        )
        messages = [{"role": "system", "content": new_system_prompt}]
        context.ui.print_system_message("[session reset]")
        context.conversation_logger.log_message("System", "Session reset")
        # Print header again
        context.ui.print_header(context.bot["NAME"], context.nsfw_mode, context.romantic_mode)
        return True, messages, context.nsfw_mode, context.romantic_mode


class RememberCommand(BaseCommand):
    """Add a manual memory."""
    
    def __init__(self):
        super().__init__("/remember", "Add a manual memory snippet (stored to memories.jsonl)")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        note = " ".join(args).strip()
        if note:
            context.memory_manager.append_memory(note, tags=["manual"])
            context.ui.print_system_message("[remembered]")
            context.conversation_logger.log_message("System", f"Manual memory added: {note}")
        else:
            context.ui.print_system_message("[!] Provide text after /remember")
        return True, context.messages, context.nsfw_mode, context.romantic_mode


class RewindCommand(BaseCommand):
    """Go back to the previous bot message."""
    
    def __init__(self):
        super().__init__("/rewind", "Go back to the previous bot message (removes last exchange)")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        # Check if there are enough messages to rewind (at least 3: system + one exchange)
        if len(context.messages) < 3:
            context.ui.print_system_message("[!] Cannot rewind: not enough messages in conversation")
            return True, context.messages, context.nsfw_mode, context.romantic_mode
            
        # Remove the last two messages (user and assistant)
        last_assistant = context.messages.pop()  # Last message is assistant
        last_user = context.messages.pop()       # Second last is user
        
        # Get the previous assistant message (now the last message)
        prev_assistant = context.messages[-1]
        
        # Display the previous assistant message
        context.ui.print_system_message("[rewound to previous message]")
        context.ui.print_bot_message(
            prev_assistant["content"], 
            context.bot["NAME"], 
            context.bot.get("CHAT_COLOR", "cyan")
        )
        
        # Log the rewind action
        context.conversation_logger.log_message("System", "Rewound to previous message")
        
        return True, context.messages, context.nsfw_mode, context.romantic_mode


class ExportCommand(BaseCommand):
    """Save the current transcript."""
    
    def __init__(self):
        super().__init__("/export", "Save the current transcript to the transcripts/ folder")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        try:
            out = TranscriptExporter.export_transcript(
                context.messages, 
                Path(TRANSCRIPT_DIR), 
                context.bot["NAME"], 
                context.export_format
            )
            context.ui.print_system_message(f"[saved] {out}")
            context.conversation_logger.log_message("System", f"Transcript exported to {out}")
        except Exception as e:
            context.logger.error(f"Export failed: {e}")
            context.ui.print_system_message(f"[!] Export failed: {e}")
        return True, context.messages, context.nsfw_mode, context.romantic_mode


class PersonaCommand(BaseCommand):
    """Show the loaded BotInfo persona."""
    
    def __init__(self):
        super().__init__("/persona", "Show the loaded BotInfo persona")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        if isinstance(context.ui, RichUI):
            show_persona_rich(context.ui, context.bot)
        else:
            show_persona_simple(context.ui, context.bot)
        return True, context.messages, context.nsfw_mode, context.romantic_mode


class NsfwCommand(BaseCommand):
    """Toggle NSFW mode."""
    
    def __init__(self):
        super().__init__("/nsfw", "Enable/disable NSFW mode for adult-oriented roleplay")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        if not args:
            context.ui.print_system_message("[!] Please specify 'on' or 'off'")
            return True, context.messages, context.nsfw_mode, context.romantic_mode
            
        action = args[0].lower()
        new_nsfw_mode = context.nsfw_mode
        
        if action == "on":
            if not context.nsfw_mode:
                new_nsfw_mode = True
                context.ui.print_system_message("[NSFW mode enabled]")
                context.conversation_logger.log_message("System", "NSFW mode enabled")
            else:
                context.ui.print_system_message("[NSFW mode already enabled]")
        elif action == "off":
            if context.nsfw_mode:
                new_nsfw_mode = False
                context.ui.print_system_message("[NSFW mode disabled]")
                context.conversation_logger.log_message("System", "NSFW mode disabled")
            else:
                context.ui.print_system_message("[NSFW mode already disabled]")
        else:
            context.ui.print_system_message("[!] Please specify 'on' or 'off'")
            return True, context.messages, context.nsfw_mode, context.romantic_mode
        
        # Update system prompt if mode changed
        if new_nsfw_mode != context.nsfw_mode:
            new_system_prompt = build_system_prompt(
                context.bot, 
                nsfw_mode=new_nsfw_mode, 
                romantic_mode=context.romantic_mode
            )
            # Update the first message (system prompt)
            if context.messages and context.messages[0]["role"] == "system":
                context.messages[0]["content"] = new_system_prompt
            # Update header
            context.ui.print_header(context.bot["NAME"], new_nsfw_mode, context.romantic_mode)
        
        return True, context.messages, new_nsfw_mode, context.romantic_mode


class RomanticCommand(BaseCommand):
    """Toggle romantic mode."""
    
    def __init__(self):
        super().__init__("/romantic", "Enable/disable romantic mode")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        if not args:
            context.ui.print_system_message("[!] Please specify 'on' or 'off'")
            return True, context.messages, context.nsfw_mode, context.romantic_mode
            
        action = args[0].lower()
        new_romantic_mode = context.romantic_mode
        
        if action == "on":
            if not context.romantic_mode:
                new_romantic_mode = True
                context.ui.print_system_message("[Romantic mode enabled]")
                context.conversation_logger.log_message("System", "Romantic mode enabled")
            else:
                context.ui.print_system_message("[Romantic mode already enabled]")
        elif action == "off":
            if context.romantic_mode:
                new_romantic_mode = False
                context.ui.print_system_message("[Romantic mode disabled]")
                context.conversation_logger.log_message("System", "Romantic mode disabled")
            else:
                context.ui.print_system_message("[Romantic mode already disabled]")
        else:
            context.ui.print_system_message("[!] Please specify 'on' or 'off'")
            return True, context.messages, context.nsfw_mode, context.romantic_mode
        
        # Update system prompt if mode changed
        if new_romantic_mode != context.romantic_mode:
            new_system_prompt = build_system_prompt(
                context.bot, 
                nsfw_mode=context.nsfw_mode, 
                romantic_mode=new_romantic_mode
            )
            # Update the first message (system prompt)
            if context.messages and context.messages[0]["role"] == "system":
                context.messages[0]["content"] = new_system_prompt
            # Update header
            context.ui.print_header(context.bot["NAME"], context.nsfw_mode, new_romantic_mode)
        
        return True, context.messages, context.nsfw_mode, new_romantic_mode


class SearchCommand(BaseCommand):
    """Search memories."""
    
    def __init__(self):
        super().__init__("/search", "Search memories for keywords")
    
    def execute(self, args: List[str], context: CommandContext) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        if not args:
            context.ui.print_system_message("[!] Please provide search terms")
            return True, context.messages, context.nsfw_mode, context.romantic_mode
            
        query = " ".join(args)
        results = context.memory_manager.search_memories(query, limit=5)
        
        if results:
            context.ui.print_system_message(f"[Found {len(results)} memories matching '{query}']:")
            for i, memory in enumerate(results, 1):
                ts = memory.get("ts", "?")
                note = memory.get("note", "")
                context.ui.print_system_message(f"{i}. ({ts}) {note[:80]}...")
        else:
            context.ui.print_system_message(f"[No memories found matching '{query}']")
        
        return True, context.messages, context.nsfw_mode, context.romantic_mode


class CommandHandler:
    """Handles command processing using the command pattern."""
    
    def __init__(self):
        self.commands = {
            "/quit": QuitCommand(),
            "/exit": QuitCommand(),  # Alias for /quit
            "/help": HelpCommand(self),
            "/reset": ResetCommand(),
            "/remember": RememberCommand(),
            "/rewind": RewindCommand(),
            "/export": ExportCommand(),
            "/persona": PersonaCommand(),
            "/nsfw": NsfwCommand(),
            "/romantic": RomanticCommand(),
            "/search": SearchCommand(),
        }
    
    def handle_command(
        self, 
        command: str, 
        messages: List[Dict[str, str]], 
        system_prompt: str, 
        memory_manager,
        bot: Dict[str, Any],
        export_format: str,
        logger: logging.Logger,
        conversation_logger,
        nsfw_mode: bool,
        romantic_mode: bool,
        ui
    ) -> Tuple[bool, List[Dict[str, str]], bool, bool]:
        """Process user commands and return whether to continue, updated messages, and mode states."""
        # Parse command and arguments
        parts = command.strip().split(maxsplit=1)
        command_name = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []
        
        # Find the command
        cmd = self.commands.get(command_name)
        if not cmd:
            # Not a recognized command
            return True, messages, nsfw_mode, romantic_mode
        
        # Create context and execute command
        context = CommandContext(
            messages=messages,
            system_prompt=system_prompt,
            memory_manager=memory_manager,
            bot=bot,
            export_format=export_format,
            logger=logger,
            conversation_logger=conversation_logger,
            nsfw_mode=nsfw_mode,
            romantic_mode=romantic_mode,
            ui=ui
        )
        
        return cmd.execute(args, context)