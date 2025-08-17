import json
import datetime as dt
from pathlib import Path

class ConversationLogger:
    """Handles logging conversation messages to a single text file per character."""
    
    def __init__(self, bot_name: str, chat_dir: Path):
        self.bot_name = bot_name
        self.chat_dir = chat_dir
        # Ensure the chats directory exists
        self.chat_dir.mkdir(exist_ok=True)
        # Create or open the chat file for this character
        self.chat_file = self.chat_dir / f"{bot_name}.txt"
        # If file doesn't exist, create it with a header
        if not self.chat_file.exists():
            with self.chat_file.open("w", encoding="utf-8") as f:
                f.write(f"Chat Log for {bot_name}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Started: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
    def log_message(self, speaker: str, content: str) -> None:
        """Log a message to the character's chat file."""
        timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with self.chat_file.open("a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {speaker}:\n")
                f.write(f"{content}\n\n")
        except Exception as e:
            print(f"[!] Failed to log message to chat file: {e}")