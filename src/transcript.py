import json
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any

class TranscriptExporter:
    """Handles exporting conversation transcripts."""
    
    @staticmethod
    def ensure_dir(path: Path) -> None:
        """Ensure a directory exists, creating it if necessary."""
        path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def export_transcript(
        messages: List[Dict[str, str]], 
        out_dir: Path, 
        botname: str, 
        format_type: str = "json"
    ) -> Path:
        """Export the conversation transcript in the specified format."""
        TranscriptExporter.ensure_dir(out_dir)
        timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if format_type.lower() == "json":
            fname = out_dir / f"{botname}_{timestamp}.json"
            payload = {
                "created": dt.datetime.now().isoformat(timespec="seconds"), 
                "messages": messages
            }
            fname.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            
        elif format_type.lower() == "txt":
            fname = out_dir / f"{botname}_{timestamp}.txt"
            with fname.open("w", encoding="utf-8") as f:
                f.write(f"Transcript with {botname} - {timestamp}\n")
                f.write("=" * 50 + "\n\n")
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if role == "system":
                        continue  # Skip system messages in text export
                    speaker = botname if role == "assistant" else "User"
                    f.write(f"{speaker}: {content}\n\n")
                    
        elif format_type.lower() == "markdown":
            fname = out_dir / f"{botname}_{timestamp}.md"
            with fname.open("w", encoding="utf-8") as f:
                f.write(f"# Transcript with {botname}\n\n")
                f.write(f"**Date:** {timestamp}\n\n")
                f.write("---\n\n")
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if role == "system":
                        continue  # Skip system messages in markdown export
                    speaker = botname if role == "assistant" else "User"
                    f.write(f"## {speaker}\n\n{content}\n\n")
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
            
        return fname