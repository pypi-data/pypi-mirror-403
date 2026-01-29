import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from lite_code.tools import list_files, read_file
from lite_code.utils import (
    validate_path,
    detect_language,
    check_context_limits,
    estimate_tokens,
    MAX_FILES_IN_CONTEXT,
    MAX_TOTAL_CONTEXT_TOKENS,
)

logger = logging.getLogger(__name__)


class CommandHandler:
    """Handle special commands in the interactive CLI."""
    
    def __init__(self) -> None:
        self.context = []
    
    def handle_file_reference(self, file_path: str) -> Tuple[bool, str]:
        """Handle @filename command - add file to context."""
        try:
            is_valid, error_msg = validate_path(file_path)
            if not is_valid:
                return False, error_msg
            
            path = Path(file_path)
            if not path.is_file():
                return False, f"Path is not a file: {file_path}"
            
            if file_path not in self.context:
                self.context.append(file_path)
            
            lang = detect_language(file_path)
            lang_info = f" ({lang})" if lang else ""
            return True, f"Added {file_path}{lang_info} to context"
        
        except Exception as e:
            logger.error(f"Error handling file reference: {e}")
            return False, str(e)
    
    def handle_folder_reference(self, folder_path: str) -> Tuple[bool, str]:
        """Handle /folder command - add folder to context with limits."""
        try:
            is_valid, error_msg = validate_path(folder_path)
            if not is_valid:
                return False, error_msg

            path = Path(folder_path)
            if not path.is_dir():
                return False, f"Path is not a directory: {folder_path}"

            result = list_files(folder_path, include_stats=True)
            if "error" in result:
                return False, result["error"]

            files = result["files"]
            if not files:
                return False, f"No supported files found in {folder_path}"

            # Check file count limit
            if len(files) > MAX_FILES_IN_CONTEXT:
                return False, f"Too many files: {len(files)} (max {MAX_FILES_IN_CONTEXT}). Try a subdirectory."

            # Add files
            added_count = 0
            for file_path in files:
                if file_path not in self.context:
                    self.context.append(file_path)
                    added_count += 1

            # Build response message
            msg_parts = [f"Added folder {folder_path} to context ({added_count} files)"]

            # Add token estimate
            estimated_tokens = result.get("estimated_tokens", 0)
            if estimated_tokens > 0:
                msg_parts.append(f"~{estimated_tokens:,} tokens")

            # Add warnings
            warnings = []
            if result.get("large_files"):
                warnings.append(f"{len(result['large_files'])} large file(s) will be truncated")

            # Check total context
            limits = check_context_limits(self.context)
            if not limits["within_limits"]:
                for w in limits["warnings"]:
                    warnings.append(w)

            if warnings:
                msg_parts.append(f"\u26a0 {'; '.join(warnings)}")

            return True, " | ".join(msg_parts)

        except Exception as e:
            logger.error(f"Error handling folder reference: {e}")
            return False, str(e)
    
    def clear_context(self) -> Tuple[bool, str]:
        """Clear all context."""
        count = len(self.context)
        self.context.clear()
        return True, f"Cleared context ({count} items removed)"
    
    def get_context(self) -> List[str]:
        """Get current context."""
        return self.context.copy()

    def set_context(self, context: List[str]) -> None:
        """Set context from saved state."""
        self.context = context.copy()

    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about the current context."""
        if not self.context:
            return {"file_count": 0, "total_tokens": 0, "within_limits": True}
        return check_context_limits(self.context)
    
    def show_help(self) -> str:
        """Show help message."""
        help_text = """
Available commands:
  @filename  - Reference a file (e.g., @utils.py)
  /folder    - Reference a folder (e.g., /src)
  ask        - Ask questions about code (e.g., ask explain this function)
  ?          - Show this help
  !          - Change settings
  clear      - Clear context
  exit/quit  - Save and exit

Examples:
  @utils.py              Add utils.py to context
  /src                   Add src folder to context
  ask explain main()     Ask about code
  ask generate diagram   Generate code diagram
  Add type hints         Refactoring task
  !                      Open settings menu
"""
        return help_text.strip()
    
    def parse_command(self, user_input: str) -> Tuple[str, str, bool]:
        """Parse user input and return (command, argument, is_command)."""
        user_input = user_input.strip()
        
        if not user_input:
            return "", "", False
        
        if user_input.startswith('@'):
            return "file", user_input[1:].strip(), True
        
        if user_input.startswith('/'):
            return "folder", user_input[1:].strip(), True
        
        if user_input == '?':
            return "help", "", True
        
        if user_input == '!':
            return "settings", "", True
        
        if user_input.lower() in ['clear', 'exit', 'quit']:
            return user_input.lower(), "", True
        
        if user_input.lower().startswith('ask '):
            return "ask", user_input[4:].strip(), True
        
        return "task", user_input, False
