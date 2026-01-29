import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


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
