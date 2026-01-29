"""Configuration management for DevOS."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for DevOS."""
    
    def __init__(self):
        """Initialize configuration."""
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / ".devos"
        self.data_dir = self.config_dir / "data"
        self.config_file = self.config_dir / "config.yml"
        
        self._ensure_directories()
        self._load_config()
    
    def _ensure_directories(self):
        """Ensure necessary directories exist."""
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
    
    def _load_config(self):
        """Load configuration from file or create defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception:
                self.config = {}
        else:
            self.config = {}
            self._save_config()
        
        # Set defaults
        self.config.setdefault('default_language', 'python')
        self.config.setdefault('tracking', {'auto_git': True})
        self.config.setdefault('reports', {'week_start': 'monday'})
    
    def _save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    @property
    def default_language(self) -> str:
        """Get default programming language."""
        return self.get('default_language', 'python')
    
    @property
    def auto_git_tracking(self) -> bool:
        """Get auto git tracking setting."""
        return self.get('tracking.auto_git', True)
    
    @property
    def week_start(self) -> str:
        """Get week start day for reports."""
        return self.get('reports.week_start', 'monday')
