import os
import re
import json
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Model context limits (zai-glm-4.7)
MODEL_CONTEXT_LIMIT = 131072  # tokens
MAX_OUTPUT_TOKENS = 8192  # reserve for output
SAFE_CONTEXT_LIMIT = MODEL_CONTEXT_LIMIT - MAX_OUTPUT_TOKENS  # ~123K tokens for input

# File limits
MAX_FILE_SIZE_BYTES = 100 * 1024  # 100KB per file
MAX_FILE_TOKENS = 25000  # ~25K tokens per file
MAX_TOTAL_CONTEXT_TOKENS = 100000  # 100K tokens total for all context
MAX_FILES_IN_CONTEXT = 50  # max files to add at once


def estimate_tokens(text: str) -> int:
    """Estimate token count for text. Rough approximation: ~4 chars per token for code."""
    if not text:
        return 0
    return len(text) // 4 + 1


def estimate_file_tokens(file_path: str) -> Tuple[int, Optional[str]]:
    """Estimate tokens for a file. Returns (token_count, error_message)."""
    try:
        path = Path(file_path)
        if not path.exists():
            return 0, f"File not found: {file_path}"

        size_bytes = path.stat().st_size
        if size_bytes > MAX_FILE_SIZE_BYTES:
            return size_bytes // 4, f"File too large: {size_bytes // 1024}KB (max {MAX_FILE_SIZE_BYTES // 1024}KB)"

        content = path.read_text(encoding='utf-8', errors='ignore')
        tokens = estimate_tokens(content)
        return tokens, None
    except Exception as e:
        return 0, str(e)


def truncate_content(content: str, max_tokens: int = MAX_FILE_TOKENS) -> Tuple[str, bool]:
    """Truncate content to fit within token limit. Returns (content, was_truncated)."""
    estimated = estimate_tokens(content)
    if estimated <= max_tokens:
        return content, False

    # Truncate to approximate character limit
    max_chars = max_tokens * 4
    truncated = content[:max_chars]

    # Try to truncate at a line boundary
    last_newline = truncated.rfind('\n')
    if last_newline > max_chars * 0.8:  # Only if we don't lose too much
        truncated = truncated[:last_newline]

    truncated += f"\n\n... [TRUNCATED: {estimated - max_tokens} tokens omitted] ..."
    return truncated, True


def check_context_limits(file_paths: List[str]) -> Dict[str, Any]:
    """Check if context files fit within limits. Returns status and details."""
    total_tokens = 0
    file_details = []
    warnings = []
    errors = []

    for fp in file_paths:
        tokens, error = estimate_file_tokens(fp)
        if error:
            if "too large" in error.lower():
                warnings.append(error)
            else:
                errors.append(error)
        total_tokens += tokens
        file_details.append({"path": fp, "tokens": tokens, "error": error})

    if len(file_paths) > MAX_FILES_IN_CONTEXT:
        warnings.append(f"Too many files: {len(file_paths)} (max {MAX_FILES_IN_CONTEXT})")

    if total_tokens > MAX_TOTAL_CONTEXT_TOKENS:
        warnings.append(f"Context too large: ~{total_tokens:,} tokens (max {MAX_TOTAL_CONTEXT_TOKENS:,})")

    return {
        "total_tokens": total_tokens,
        "file_count": len(file_paths),
        "files": file_details,
        "warnings": warnings,
        "errors": errors,
        "within_limits": total_tokens <= MAX_TOTAL_CONTEXT_TOKENS and len(file_paths) <= MAX_FILES_IN_CONTEXT
    }


def extract_json_from_response(content: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Extract JSON from model response, handling various formats. Returns (json_dict, error)."""
    if not content:
        return None, "Empty response"

    content = content.strip()

    # Try direct JSON parse first
    try:
        return json.loads(content), None
    except:
        pass

    # Try to extract JSON from markdown code blocks
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
        r'\{[\s\S]*\}',                   # Raw JSON object
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            try:
                # Clean up the match
                json_str = match.strip()
                if not json_str.startswith('{'):
                    continue
                result = json.loads(json_str)
                if isinstance(result, dict):
                    return result, None
            except:
                continue

    # Try to find JSON object boundaries
    start = content.find('{')
    if start != -1:
        # Find matching closing brace
        depth = 0
        for i, char in enumerate(content[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(content[start:i+1]), None
                    except:
                        break

    return None, f"Could not extract JSON from response"




def validate_path(path: str) -> Tuple[bool, str]:
    """Validate if path exists and is accessible."""
    try:
        p = Path(path)
        if not p.exists():
            return False, f"Path does not exist: {path}"
        return True, ""
    except Exception as e:
        return False, f"Error validating path: {str(e)}"


def detect_language(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript'
    }
    return lang_map.get(ext)


def create_backup_folder(source_path: str) -> str:
    """Create timestamped backup folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"refactored_{timestamp}"
    backup_path = Path(source_path).parent / backup_name
    
    try:
        backup_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created backup folder: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Error creating backup folder: {e}")
        raise


def copy_to_backup(source_path: str, backup_path: str) -> None:
    """Copy entire source directory to backup."""
    try:
        source = Path(source_path)
        backup = Path(backup_path)
        
        if source.is_file():
            shutil.copy2(source, backup / source.name)
        else:
            if backup.exists():
                shutil.rmtree(backup)
            shutil.copytree(source, backup)
        
        logger.info(f"Copied {source_path} to {backup_path}")
    except Exception as e:
        logger.error(f"Error copying to backup: {e}")
        raise


def format_diff_for_display(diff: str, file_path: str) -> str:
    """Format diff for Rich console display."""
    if not diff:
        return f"No changes for {file_path}"
    
    lines = diff.split('\n')
    formatted = []
    
    for line in lines:
        if line.startswith('+++') or line.startswith('---'):
            formatted.append(f"[dim]{line}[/dim]")
        elif line.startswith('@@'):
            formatted.append(f"[cyan]{line}[/cyan]")
        elif line.startswith('+'):
            formatted.append(f"[green]{line}[/green]")
        elif line.startswith('-'):
            formatted.append(f"[red]{line}[/red]")
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
