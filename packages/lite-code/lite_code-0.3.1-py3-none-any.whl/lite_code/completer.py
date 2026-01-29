import os
import logging
from pathlib import Path
from typing import List, Optional

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from lite_code.tools import list_files

logger = logging.getLogger(__name__)


class FileCompleter(Completer):
    """Completer for file and folder references."""
    
    def __init__(self):
        self.current_dir = Path.cwd()
        self.cached_files: List[str] = []
        self._refresh_cache()
    
    def _refresh_cache(self):
        """Refresh the cached file list."""
        try:
            result = list_files(str(self.current_dir))
            if "files" in result:
                self.cached_files = result["files"]
        except Exception as e:
            logger.error(f"Error refreshing file cache: {e}")
            self.cached_files = []
    
    def get_completions(self, document: Document, complete_event):
        """Get completions for the current document."""
        text = document.text_before_cursor
        
        if not text:
            return
        
        if text.startswith('@'):
            prefix = text[1:]
            self._refresh_cache()
            
            for file_path in self.cached_files:
                if prefix.lower() in file_path.lower():
                    display = file_path
                    yield Completion(
                        file_path,
                        start_position=-len(prefix),
                        display=display,
                        display_meta='File'
                    )
        
        elif text.startswith('/'):
            prefix = text[1:]
            self._refresh_cache()
            
            folders = set()
            for file_path in self.cached_files:
                folder = str(Path(file_path).parent)
                if folder != '.':
                    folders.add(folder)
            
            for folder in sorted(folders):
                if prefix.lower() in folder.lower():
                    display = folder
                    yield Completion(
                        folder,
                        start_position=-len(prefix),
                        display=display,
                        display_meta='Folder'
                    )
