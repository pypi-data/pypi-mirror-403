"""
OMNIMIND Interface Layer - Text Interface
Text I/O Handler
"""
from typing import Optional, Generator, Dict, Any
from dataclasses import dataclass


@dataclass
class TextMessage:
    """Text message structure"""
    content: str
    role: str  # 'user', 'assistant', 'system'
    metadata: Dict[str, Any] = None


class TextInterface:
    """
    Text Interface - Text I/O Handler
    
    ทำหน้าที่:
    - Parse user input
    - Format AI output
    - Handle special commands
    - Thai text optimization
    """
    
    def __init__(self, max_response_length: int = 500):
        self.max_response_length = max_response_length
        
        # Special commands
        self.commands = {
            "/help": self._cmd_help,
            "/reset": self._cmd_reset,
            "/stats": self._cmd_stats,
            "/memory": self._cmd_memory,
        }
    
    def parse_input(self, raw_input: str) -> TextMessage:
        """
        Parse raw user input
        
        Args:
            raw_input: Raw text from user
            
        Returns:
            Parsed TextMessage
        """
        content = raw_input.strip()
        
        # Check for special commands
        metadata = {}
        if content.startswith("/"):
            metadata["is_command"] = True
            parts = content.split(maxsplit=1)
            metadata["command"] = parts[0].lower()
            if len(parts) > 1:
                metadata["args"] = parts[1]
        
        return TextMessage(
            content=content,
            role="user",
            metadata=metadata
        )
    
    def format_output(self, response: str, 
                     metadata: Dict[str, Any] = None) -> str:
        """
        Format response for display
        
        Args:
            response: Raw response text
            metadata: Optional metadata (uncertainty, etc.)
            
        Returns:
            Formatted response
        """
        # Trim if too long
        if len(response) > self.max_response_length:
            response = response[:self.max_response_length] + "..."
        
        # Clean up extra whitespace
        response = " ".join(response.split())
        
        return response
    
    def is_command(self, message: TextMessage) -> bool:
        """Check if message is a command"""
        return message.metadata and message.metadata.get("is_command", False)
    
    def execute_command(self, message: TextMessage, omnimind=None) -> str:
        """
        Execute a command
        
        Args:
            message: Parsed message with command
            omnimind: Reference to main OMNIMIND instance
            
        Returns:
            Command result
        """
        cmd = message.metadata.get("command", "")
        
        if cmd in self.commands:
            return self.commands[cmd](message, omnimind)
        
        return f"Unknown command: {cmd}\nUse /help for available commands."
    
    def _cmd_help(self, message: TextMessage, omnimind=None) -> str:
        """Help command"""
        return """🤖 OMNIMIND Commands:
/help     - Show this help
/reset    - Reset conversation
/stats    - Show system statistics
/memory   - Show memory status"""
    
    def _cmd_reset(self, message: TextMessage, omnimind=None) -> str:
        """Reset command"""
        if omnimind:
            omnimind.reset_session()
            return "✅ Session reset. Fresh start!"
        return "Cannot reset - no OMNIMIND instance."
    
    def _cmd_stats(self, message: TextMessage, omnimind=None) -> str:
        """Stats command"""
        if omnimind:
            stats = omnimind.get_stats()
            return f"""📊 OMNIMIND Stats:
• Model: {stats.get('model', 'N/A')}
• Device: {stats.get('device', 'N/A')}
• Tokens processed: {stats.get('tokens_processed', 0)}"""
        return "Cannot get stats - no OMNIMIND instance."
    
    def _cmd_memory(self, message: TextMessage, omnimind=None) -> str:
        """Memory command"""
        if omnimind and hasattr(omnimind, 'memory'):
            stats = omnimind.memory.get_stats()
            return f"""🧠 Memory Status:
Working: {stats['working_memory']['slots_used']}/{stats['working_memory']['max_slots']} slots
Episodic: {stats['episodic_memory']['total_episodes']} episodes
Semantic: {stats['semantic_memory']['total_entries']} entries"""
        return "Cannot get memory stats."
    
    def stream_output(self, 
                     token_generator: Generator[str, None, None]
                     ) -> Generator[str, None, None]:
        """
        Stream output tokens
        
        Args:
            token_generator: Generator yielding tokens
            
        Yields:
            Tokens for display
        """
        total_length = 0
        
        for token in token_generator:
            total_length += len(token)
            
            # Stop if too long
            if total_length > self.max_response_length:
                yield "..."
                break
            
            yield token
