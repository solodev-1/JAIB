import json
import re
import datetime as dt
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

class MemoryManager:
    """Manages the bot's memory system with improved relevance and extraction."""
    
    def __init__(self, memfile_path: Path, logger: logging.Logger):
        self.memfile_path = memfile_path
        self.logger = logger
        self.memory_cache = None
        self.cache_timestamp = None
        self.keywords_index = defaultdict(set)  # Index for keyword-based memory retrieval
        
    def _build_memory_index(self) -> None:
        """Build an index of keywords for faster memory retrieval."""
        if not self.memfile_path.exists():
            return
            
        self.keywords_index = defaultdict(set)
        
        try:
            with self.memfile_path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        memory = json.loads(line)
                        note = memory.get("note", "").lower()
                        timestamp = memory.get("ts", "")
                        
                        if not timestamp:
                            continue  # Skip memories without timestamp
                        
                        # Extract keywords (simple approach: words longer than 3 chars)
                        words = re.findall(r'\b\w{4,}\b', note)
                        for word in set(words):  # Remove duplicates
                            # Store only the timestamp (hashable) instead of the entire memory dict
                            self.keywords_index[word].add(timestamp)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.error(f"Failed to build memory index: {e}")
    
    def append_memory(self, text: str, tags: Optional[List[str]] = None) -> None:
        """Add a memory entry to the memory file."""
        record = {
            "ts": dt.datetime.now().isoformat(timespec="seconds"),
            "note": text.strip(),
            "tags": tags or [],
            "importance": self._calculate_importance(text)
        }
        try:
            with self.memfile_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
            # Update cache and index
            self.memory_cache = None  # Invalidate cache
            self._build_memory_index()  # Rebuild index
            
            self.logger.debug(f"Added memory: {text[:50]}...")
        except Exception as e:
            self.logger.error(f"Failed to write memory: {e}")
    
    def _calculate_importance(self, text: str) -> int:
        """Calculate importance score for a memory (1-10)."""
        importance = 5  # Base importance
        
        # Increase importance for certain keywords
        important_keywords = [
            "important", "crucial", "vital", "essential", "critical",
            "remember", "never forget", "always", "must", "promise",
            "name", "address", "phone", "birthday", "anniversary"
        ]
        
        text_lower = text.lower()
        for keyword in important_keywords:
            if keyword in text_lower:
                importance += 2
        
        # Increase importance for personal information
        personal_patterns = [
            r"my name is", r"i live in", r"i was born", r"i work at",
            r"my favorite", r"i love", r"i hate", r"i am afraid of"
        ]
        
        for pattern in personal_patterns:
            if re.search(pattern, text_lower):
                importance += 1
        
        # Cap importance at 10
        return min(importance, 10)
    
    def load_all_memories(self) -> List[Dict[str, Any]]:
        """Load all memory entries with caching."""
        # Check if cache is valid
        if self.memory_cache is not None and self.cache_timestamp is not None:
            if self.memfile_path.exists() and self.memfile_path.stat().st_mtime <= self.cache_timestamp:
                return self.memory_cache
        
        # Cache is invalid or doesn't exist, load from file
        if not self.memfile_path.exists():
            return []
        
        try:
            with self.memfile_path.open("r", encoding="utf-8") as f:
                memories = [json.loads(line) for line in f if line.strip()]
            
            # Sort by importance (descending) and then by timestamp (descending)
            memories.sort(key=lambda m: (-m.get("importance", 5), m.get("ts", "")))
            
            # Update cache
            self.memory_cache = memories
            self.cache_timestamp = dt.datetime.now().timestamp()
            
            # Build index if not already built
            if not self.keywords_index:
                self._build_memory_index()
            
            return memories
        except Exception as e:
            self.logger.error(f"Failed to load memories: {e}")
            return []
    
    def load_recent_memories(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Load the most recent memory entries."""
        all_memories = self.load_all_memories()
        return all_memories[:limit]
    
    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories by keyword relevance."""
        if not self.keywords_index:
            self._build_memory_index()
        
        query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
        
        # Score memories by keyword matches
        memory_scores = defaultdict(int)
        
        for word in query_words:
            for timestamp in self.keywords_index.get(word, []):
                memory_scores[timestamp] += 1
        
        # Load all memories to get the full data
        all_memories = self.load_all_memories()
        
        # Create a mapping from timestamp to memory
        memory_by_timestamp = {memory.get("ts", ""): memory for memory in all_memories}
        
        # Get the top memories by score
        sorted_timestamps = sorted(
            memory_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Return the full memory objects for the top timestamps
        return [memory_by_timestamp[timestamp] for timestamp, _ in sorted_timestamps[:limit] if timestamp in memory_by_timestamp]
    
    def format_memories_as_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories for inclusion in the prompt context."""
        if not memories:
            return ""
        
        bullets = []
        for m in memories:
            ts = m.get("ts", "?")
            note = m.get("note", "")
            importance = m.get("importance", 5)
            
            # Add importance indicator
            importance_marker = "!" * min(importance // 3, 3)  # 1-3 exclamation marks
            
            bullets.append(f"- ({ts}) {importance_marker} {note}")
        
        return "Here are a few past notes for continuity:\n" + "\n".join(bullets)
    
    def extract_auto_memories(self, text: str) -> List[str]:
        """Extract potential memories from bot responses using enhanced heuristics."""
        memories = []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Skip very short or very long sentences
            if len(sentence) < 10 or len(sentence) > 200:
                continue
            
            # Check for explicit memory indicators
            memory_indicators = [
                r"(I will|I'll|I am going to) (remember|not forget|keep in mind)",
                r"(Don't|Do not) forget",
                r"(This is|That's) important",
                r"(Promise|I promise)",
                r"(Always|Never) ",
                r"Must (remember|not forget|keep in mind)"
            ]
            
            # Check for personal information sharing
            personal_patterns = [
                r"My (name|age|birthday|address|phone|email)",
                r"I (am|was) (born|from|raised)",
                r"I (work|study) at",
                r"I (live|live in)",
                r"My (favorite|least favorite)",
                r"I (like|love|hate|enjoy|dislike|prefer)",
                r"I am (afraid of|scared of|worried about)",
                r"I have (a|an) .* (experience|story|memory)"
            ]
            
            # Check for future intentions
            intention_patterns = [
                r"I (will|would like to|plan to|intend to)",
                r"Going to ",
                r"In the future"
            ]
            
            # Check if sentence matches any pattern
            is_explicit_memory = any(re.search(pattern, sentence, re.IGNORECASE) 
                                    for pattern in memory_indicators)
            
            is_personal_info = any(re.search(pattern, sentence, re.IGNORECASE) 
                                  for pattern in personal_patterns)
            
            is_intention = any(re.search(pattern, sentence, re.IGNORECASE) 
                              for pattern in intention_patterns)
            
            # If sentence matches any pattern, consider it a memory
            if is_explicit_memory or is_personal_info or is_intention:
                memories.append(sentence)
        
        # Limit to 2 auto-memories per response, prioritizing explicit memories
        explicit_memories = [m for m in memories if any(
            re.search(pattern, m, re.IGNORECASE) for pattern in memory_indicators
        )]
        
        other_memories = [m for m in memories if m not in explicit_memories]
        
        # Return up to 2 memories, prioritizing explicit ones
        result = explicit_memories[:2]
        if len(result) < 2:
            result.extend(other_memories[:2-len(result)])
        
        return result