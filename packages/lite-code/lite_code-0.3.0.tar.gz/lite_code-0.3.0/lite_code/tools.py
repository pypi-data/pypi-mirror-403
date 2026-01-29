import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts'}
IGNORED_DIRS = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'dist', 'build'}


def list_files(root_path: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """List Python and JavaScript/TypeScript files in directory."""
    try:
        root = Path(root_path)
        if not root.exists():
            return {"error": f"Path does not exist: {root_path}"}
        
        if not root.is_dir():
            return {"error": f"Path is not a directory: {root_path}"}
        
        ext_filter = set(extensions) if extensions else SUPPORTED_EXTENSIONS
        files = []
        
        for file_path in root.rglob('*'):
            if file_path.is_file():
                if file_path.suffix.lower() in ext_filter:
                    if not any(ignored in file_path.parts for ignored in IGNORED_DIRS):
                        files.append(str(file_path))
        
        logger.info(f"Found {len(files)} files in {root_path}")
        return {"files": files, "count": len(files)}
    
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"error": str(e)}


def read_file(file_path: str) -> Dict[str, Any]:
    """Read full content of a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File does not exist: {file_path}"}
        
        if not path.is_file():
            return {"error": f"Path is not a file: {file_path}"}
        
        content = path.read_text(encoding='utf-8')
        logger.info(f"Read file: {file_path} ({len(content)} chars)")
        return {"content": content, "file_path": file_path}
    
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


def read_multiple_files(file_paths: List[str]) -> Dict[str, Any]:
    """Read multiple files and return combined content."""
    try:
        files_data = {}
        total_chars = 0
        
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                continue
            
            content = path.read_text(encoding='utf-8')
            files_data[file_path] = content
            total_chars += len(content)
        
        logger.info(f"Read {len(files_data)} files ({total_chars} chars)")
        return {"files": files_data, "count": len(files_data), "total_chars": total_chars}
    
    except Exception as e:
        logger.error(f"Error reading multiple files: {e}")
        return {"error": str(e)}
