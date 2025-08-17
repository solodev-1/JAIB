import argparse
from src.config import DEFAULT_MODEL, DEFAULT_BOTINFO, DEFAULT_MEMFILE

def make_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    p = argparse.ArgumentParser(description="Roleplay bot using Llama 3.1 via Ollama")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Model name in Ollama (default: llama3.1)")
    p.add_argument("--botinfo", default=DEFAULT_BOTINFO, help="Path to BotInfo.json")
    p.add_argument("--memfile", default=DEFAULT_MEMFILE, help="Path to memories.jsonl")
    p.add_argument("--no-memory", action="store_true", help="Disable memory recall")
    p.add_argument("--export-format", default="json", choices=["json", "txt", "markdown"], 
                  help="Transcript export format (default: json)")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                  help="Logging level (default: INFO)")
    p.add_argument("--nsfw", action="store_true", help="Enable NSFW mode for adult-oriented roleplay")
    p.add_argument("--romantic", action="store_true", help="Enable romantic mode")
    p.add_argument("--simple-ui", action="store_true", help="Use simple UI instead of rich UI")
    return p