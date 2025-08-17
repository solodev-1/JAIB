import os
import re
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class SimpleUI:
    """A simple terminal UI that mimics c.ai style without rich library."""
    
    def __init__(self):
        try:
            self.width = os.get_terminal_size().columns
        except:
            self.width = 80
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, bot_name: str, nsfw_mode: bool = False, romantic_mode: bool = False):
        """Print a header with bot information."""
        self.clear_screen()
        
        # Top border
        print("╔" + "═" * (self.width - 2) + "╗")
        
        # Title line
        title = f"  Chatting with {bot_name}"
        if nsfw_mode:
            title += " (NSFW Mode)"
        if romantic_mode:
            title += " (Romantic Mode)"
        padding = (self.width - len(title) - 4) // 2
        print("║" + " " * padding + title + " " * (self.width - len(title) - padding - 4) + "║")
        
        # Separator
        print("╠" + "═" * (self.width - 2) + "╣")
        
        # Empty line
        print("║" + " " * (self.width - 2) + "║")
    
    def print_divider(self):
        """Print a divider line."""
        print("╠" + "═" * (self.width - 2) + "╣")
    
    def print_user_message(self, message: str):
        """Print a user message in a bubble."""
        # Split message into lines if it contains newlines
        lines = message.split('\n')
        
        # Top of bubble
        print("║" + " " * (self.width - 2) + "║")
        
        # Message content
        for line in lines:
            # Wrap long lines
            while len(line) > self.width - 6:
                print("║   " + line[:self.width - 6] + "   ║")
                line = line[self.width - 6:]
            print("║   " + line + " " * (self.width - len(line) - 6) + "   ║")
        
        # Bottom of bubble
        print("║" + " " * (self.width - 2) + "║")
    
    def print_bot_message(self, message: str, bot_name: str, chat_color: str = "cyan"):
        """Print a bot message in a bubble with character name."""
        # Split message into lines if it contains newlines
        lines = message.split('\n')
        
        # Top of bubble with character name
        print("║" + " " * (self.width - 2) + "║")
        print("║   " + bot_name + " " * (self.width - len(bot_name) - 6) + "   ║")
        print("║" + "-" * (self.width - 2) + "║")
        
        # Message content
        for line in lines:
            # Process action lines (between asterisks)
            if line.startswith('*') and line.endswith('*'):
                # Italicize action text
                action_text = line[1:-1]
                print("║   *" + action_text + "* " * (self.width - len(action_text) - 8) + "   ║")
            # Process dialogue lines (with character name)
            elif line.startswith(f"{bot_name}:"):
                dialogue = line[len(bot_name)+1:].strip()
                print("║   " + dialogue + " " * (self.width - len(dialogue) - 6) + "   ║")
            # Process empty lines
            elif line.strip() == '':
                print("║" + " " * (self.width - 2) + "║")
            # Process other lines
            else:
                # Wrap long lines
                while len(line) > self.width - 6:
                    print("║   " + line[:self.width - 6] + "   ║")
                    line = line[self.width - 6:]
                print("║   " + line + " " * (self.width - len(line) - 6) + "   ║")
        
        # Bottom of bubble
        print("║" + " " * (self.width - 2) + "║")
    
    def print_system_message(self, message: str):
        """Print a system message."""
        print("║" + " " * (self.width - 2) + "║")
        
        # Center the message
        padding = (self.width - len(message) - 4) // 2
        print("║" + " " * padding + message + " " * (self.width - len(message) - padding - 4) + "║")
        
        print("║" + " " * (self.width - 2) + "║")
    
    def print_footer(self):
        """Print a footer with input prompt."""
        print("╚" + "═" * (self.width - 2) + "╝")
        print("You: ", end="", flush=True)
    
    def get_user_input(self):
        """Get user input and clear the input line."""
        user_input = input().strip()
        # Clear the input line and the line above it
        print("\033[F\033[K", end="")
        return user_input

class RichUI:
    """A rich terminal UI that closely mimics c.ai style using the rich library."""
    
    def __init__(self):
        self.console = Console()
        # Valid Rich colors (simplified list)
        self.valid_colors = {
            "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
            "bright_black", "bright_red", "bright_green", "bright_yellow", 
            "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
            "grey", "gray", "dark_red", "dark_green", "dark_blue", "purple",
            "orange", "turquoise", "skyblue", "pink", "lightblue", "seagreen"
        }
    
    def get_valid_color(self, color_name: str, default: str = "cyan") -> str:
        """Validate color name and return default if invalid."""
        return color_name if color_name.lower() in self.valid_colors else default
    
    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()
    
    def print_header(self, bot_name: str, nsfw_mode: bool = False, romantic_mode: bool = False):
        """Print a header with bot information."""
        self.clear_screen()
        
        title = f"Chatting with {bot_name}"
        if nsfw_mode:
            title += " [red](NSFW Mode)[/red]"
        if romantic_mode:
            title += " [magenta](Romantic Mode)[/magenta]"
        
        header = Panel(
            f"[bold]{title}[/bold]",
            style="blue",
            expand=True
        )
        self.console.print(header)
    
    def print_divider(self):
        """Print a divider line."""
        self.console.print("─" * self.console.width, style="blue")
    
    def print_user_message(self, message: str):
        """Print a user message in a bubble."""
        # Create a panel for the user message
        user_panel = Panel(
            message,
            title="[bold]You[/bold]",
            title_align="right",
            style="green",
            expand=True
        )
        self.console.print(user_panel)
    
    def print_bot_message(self, message: str, bot_name: str, chat_color: str = "cyan"):
        """Print a bot message in a bubble with character name."""
        # Validate the color
        valid_color = self.get_valid_color(chat_color, "cyan")
        
        # Process the message to handle actions and dialogue
        # Convert asterisk-enclosed text to italic (without visible asterisks)
        formatted_message = message
        
        # Replace *text* with [italic]text[/italic] (no visible asterisks)
        import re
        
        def replace_italic(match):
            # Extract the text between asterisks
            text = match.group(1)
            # Return the text with italic formatting but no asterisks
            return f"[italic]{text}[/italic]"
        
        # Replace all occurrences of *text* with italicized text (no asterisks)
        try:
            formatted_message = re.sub(r'\*([^*]+)\*', replace_italic, formatted_message)
        except:
            # If regex fails, just use the original message
            formatted_message = message
        
        # Remove bot name prefixes if present
        lines = formatted_message.split('\n')
        processed_lines = []
        
        for line in lines:
            if line.startswith(f"{bot_name}:"):
                # Remove the bot name prefix for cleaner display
                line = line[len(bot_name)+1:].strip()
            processed_lines.append(line)
        
        # Join the lines back
        formatted_message = '\n'.join(processed_lines)
        
        # Create a panel for the bot message with validated color
        try:
            bot_panel = Panel(
                formatted_message,
                title=f"[bold]{bot_name}[/bold]",
                title_align="left",
                style=valid_color,  # Use the validated color here
                expand=True
            )
            self.console.print(bot_panel)
        except Exception as e:
            # If panel creation fails, fall back to simple printing
            self.console.print(f"[{valid_color}]{bot_name}:[/] {formatted_message}")
    
    def print_system_message(self, message: str):
        """Print a system message."""
        system_panel = Panel(
            f"[yellow]{message}[/yellow]",
            style="yellow",
            expand=True
        )
        self.console.print(system_panel)
    
    def print_footer(self):
        """Print a footer with input prompt."""
        self.console.print("You: ", end="")
    
    def get_user_input(self):
        """Get user input and clear the input line."""
        user_input = input().strip()
        # Clear the input line and the line above it
        print("\033[F\033[K", end="")
        return user_input