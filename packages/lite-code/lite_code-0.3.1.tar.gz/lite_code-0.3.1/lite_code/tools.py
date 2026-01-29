import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from lite_code.utils import (
    estimate_tokens,
    truncate_content,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_TOKENS,
)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.md', '.css', '.html'}
IGNORED_DIRS = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'dist', 'build', '.next', '.cache'}


def list_files(root_path: str, extensions: Optional[List[str]] = None, include_stats: bool = False) -> Dict[str, Any]:
    """List supported files in directory with optional size stats."""
    try:
        root = Path(root_path)
        if not root.exists():
            return {"error": f"Path does not exist: {root_path}"}

        if not root.is_dir():
            return {"error": f"Path is not a directory: {root_path}"}

        ext_filter = set(extensions) if extensions else SUPPORTED_EXTENSIONS
        files = []
        total_size = 0
        large_files = []

        for file_path in root.rglob('*'):
            if file_path.is_file():
                if file_path.suffix.lower() in ext_filter:
                    if not any(ignored in file_path.parts for ignored in IGNORED_DIRS):
                        files.append(str(file_path))
                        if include_stats:
                            size = file_path.stat().st_size
                            total_size += size
                            if size > MAX_FILE_SIZE_BYTES:
                                large_files.append({"path": str(file_path), "size_kb": size // 1024})

        logger.info(f"Found {len(files)} files in {root_path}")

        result = {"files": files, "count": len(files)}
        if include_stats:
            result["total_size_kb"] = total_size // 1024
            result["estimated_tokens"] = total_size // 4
            if large_files:
                result["large_files"] = large_files
                result["warning"] = f"{len(large_files)} file(s) exceed size limit and will be truncated"

        return result

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"error": str(e)}


def read_file(file_path: str, max_tokens: int = MAX_FILE_TOKENS) -> Dict[str, Any]:
    """Read content of a file with size limits and truncation."""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File does not exist: {file_path}"}

        if not path.is_file():
            return {"error": f"Path is not a file: {file_path}"}

        # Check file size first
        size_bytes = path.stat().st_size
        if size_bytes > MAX_FILE_SIZE_BYTES * 2:  # Hard limit: 200KB
            return {
                "error": f"File too large: {size_bytes // 1024}KB (max 200KB)",
                "file_path": file_path,
                "size_bytes": size_bytes
            }

        content = path.read_text(encoding='utf-8', errors='ignore')
        tokens = estimate_tokens(content)
        truncated = False

        # Truncate if needed
        if tokens > max_tokens:
            content, truncated = truncate_content(content, max_tokens)
            logger.warning(f"Truncated file {file_path}: {tokens} -> {max_tokens} tokens")

        logger.info(f"Read file: {file_path} ({len(content)} chars, ~{estimate_tokens(content)} tokens)")
        return {
            "content": content,
            "file_path": file_path,
            "tokens": estimate_tokens(content),
            "truncated": truncated,
            "original_tokens": tokens if truncated else None
        }

    except UnicodeDecodeError as e:
        logger.error(f"Encoding error reading {file_path}: {e}")
        return {"error": f"Cannot read file (encoding error): {file_path}"}
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return {"error": str(e)}


def search_code(pattern: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """Search for regex pattern across files or single file."""
    try:
        regex = re.compile(pattern, re.MULTILINE)
        results = []
        
        if file_path:
            files_to_search = [file_path]
        else:
            files_result = list_files(os.getcwd())
            if "error" in files_result:
                return files_result
            files_to_search = files_result["files"]
        
        for fp in files_to_search:
            path = Path(fp)
            if not path.exists():
                continue
            
            try:
                content = path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    matches = regex.finditer(line)
                    for match in matches:
                        results.append({
                            "file_path": fp,
                            "line_number": line_num,
                            "match": match.group(),
                            "context": line.strip()
                        })
            except Exception as e:
                logger.warning(f"Could not search in {fp}: {e}")
                continue
        
        logger.info(f"Found {len(results)} matches for pattern: {pattern}")
        return {"matches": results, "count": len(results)}
    
    except re.error as e:
        logger.error(f"Invalid regex pattern: {e}")
        return {"error": f"Invalid regex pattern: {str(e)}"}
    except Exception as e:
        logger.error(f"Error searching code: {e}")
        return {"error": str(e)}


def generate_diff(original_content: str, modified_content: str) -> Dict[str, Any]:
    """Generate unified diff string for review."""
    try:
        import difflib
        
        original_lines = original_content.splitlines(keepends=True)
        modified_lines = modified_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile='original',
            tofile='modified',
            lineterm=''
        )
        
        diff_text = ''.join(diff)
        logger.info(f"Generated diff ({len(diff_text)} chars)")
        return {"diff": diff_text}
    
    except Exception as e:
        logger.error(f"Error generating diff: {e}")
        return {"error": str(e)}


def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """Write content to file."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        logger.info(f"Wrote file: {file_path}")
        return {"success": True, "file_path": file_path}
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return {"error": str(e)}


def read_multiple_files(file_paths: List[str], max_total_tokens: int = 80000) -> Dict[str, Any]:
    """Read multiple files with token tracking and limits."""
    try:
        files_data = {}
        total_tokens = 0
        total_chars = 0
        truncated_files = []
        skipped_files = []
        errors = []

        # Calculate per-file token budget
        per_file_tokens = max(5000, max_total_tokens // max(1, len(file_paths)))

        for file_path in file_paths:
            # Check if we're approaching limits
            if total_tokens >= max_total_tokens * 0.95:
                skipped_files.append(file_path)
                logger.warning(f"Skipping {file_path}: token limit reached")
                continue

            result = read_file(file_path, max_tokens=per_file_tokens)

            if "error" in result:
                errors.append({"file": file_path, "error": result["error"]})
                continue

            files_data[file_path] = result["content"]
            file_tokens = result.get("tokens", estimate_tokens(result["content"]))
            total_tokens += file_tokens
            total_chars += len(result["content"])

            if result.get("truncated"):
                truncated_files.append(file_path)

        logger.info(f"Read {len(files_data)} files ({total_chars} chars, ~{total_tokens} tokens)")

        return {
            "files": files_data,
            "count": len(files_data),
            "total_chars": total_chars,
            "total_tokens": total_tokens,
            "truncated_files": truncated_files if truncated_files else None,
            "skipped_files": skipped_files if skipped_files else None,
            "errors": errors if errors else None
        }

    except Exception as e:
        logger.error(f"Error reading multiple files: {e}")
        return {"error": str(e)}
