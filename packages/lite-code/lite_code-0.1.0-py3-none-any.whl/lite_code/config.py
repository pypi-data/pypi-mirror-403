import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration management for lite-code."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".lite-code"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, api_key: str, model: str, context: List[str], backup_mode: bool) -> None:
        """Save configuration to file."""
        try:
            config_data = {
                "api_key": api_key,
                "model": model,
                "context": context,
                "backup_mode": backup_mode
            }
            self.config_file.write_text(json.dumps(config_data, indent=2))
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if not self.config_file.exists():
                return {}
            
            config_data = json.loads(self.config_file.read_text())
            logger.info("Configuration loaded")
            return config_data
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def clear(self) -> None:
        """Clear configuration file."""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
                logger.info("Configuration cleared")
        except Exception as e:
            logger.error(f"Error clearing config: {e}")
