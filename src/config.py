import os
import sys
import datetime as dt
from pathlib import Path
import logging

# ---------- Config ----------
DEFAULT_MODEL = "llama3.1"
DEFAULT_BOTINFO = "BotInfo.json"
DEFAULT_MEMFILE = "memories.jsonl"
TRANSCRIPT_DIR = "transcripts"
LOG_DIR = "logs"
CHAT_DIR = "chats"

# Set up logging
def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application."""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"roleplay_bot_{dt.datetime.now().strftime('%Y-%m-%d')}.log"
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Suppress httpx logs (used by ollama)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return logging.getLogger("roleplay_bot")