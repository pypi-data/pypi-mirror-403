"""AI configuration management."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from .exceptions import ConfigurationError


logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """AI configuration settings."""
    default_provider: str = "openai"
    default_model: str = "gpt-4"
    api_keys: Dict[str, str] = None
    cache_enabled: bool = True
    max_context_size: int = 100000
    rate_limit_per_minute: int = 60
    cost_limit_per_hour: float = 10.0
    temperature: float = 0.7
    max_tokens: int = 2000
    
    def __post_init__(self):
        if self.api_keys is None:
            self.api_keys = {}


class AIConfigManager:
    """Manages AI configuration."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".devos"
        self.config_file = self.config_dir / "ai_config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self) -> AIConfig:
        """Load AI configuration."""
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text())
                return AIConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load AI config: {e}")
                return AIConfig()
        else:
            # Create default config
            config = AIConfig()
            self.save_config(config)
            return config
    
    def save_config(self, config: AIConfig) -> None:
        """Save AI configuration."""
        try:
            data = asdict(config)
            self.config_file.write_text(json.dumps(data, indent=2))
            logger.info("AI configuration saved")
        except Exception as e:
            logger.error(f"Failed to save AI config: {e}")
            raise ConfigurationError(f"Failed to save AI configuration: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for provider."""
        config = self.load_config()
        
        # Check config file first
        if provider in config.api_keys:
            return config.api_keys[provider]
        
        # Check environment variables
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_AI_API_KEY",
            "groq": "GROQ_API_KEY"
        }
        
        if provider in env_var_map:
            api_key = os.getenv(env_var_map[provider])
            if api_key:
                # Save to config for future use
                config.api_keys[provider] = api_key
                self.save_config(config)
                return api_key
        
        return None
    
    def set_api_key(self, provider: str, api_key: str) -> None:
        """Set API key for provider."""
        config = self.load_config()
        config.api_keys[provider] = api_key
        self.save_config(config)
        logger.info(f"API key set for {provider}")
    
    def remove_api_key(self, provider: str) -> None:
        """Remove API key for provider."""
        config = self.load_config()
        if provider in config.api_keys:
            del config.api_keys[provider]
            self.save_config(config)
            logger.info(f"API key removed for {provider}")
    
    def list_providers(self) -> Dict[str, bool]:
        """List available providers and whether they have API keys."""
        config = self.load_config()
        providers = ["openai", "anthropic", "google", "groq"]
        return {provider: provider in config.api_keys for provider in providers}
    
    def update_setting(self, key: str, value: Any) -> None:
        """Update a specific setting."""
        config = self.load_config()
        if hasattr(config, key):
            setattr(config, key, value)
            self.save_config(config)
            logger.info(f"AI setting updated: {key} = {value}")
        else:
            raise ConfigurationError(f"Unknown AI setting: {key}")
    
    def get_setting(self, key: str) -> Any:
        """Get a specific setting."""
        config = self.load_config()
        if hasattr(config, key):
            return getattr(config, key)
        else:
            raise ConfigurationError(f"Unknown AI setting: {key}")


# Global config manager instance
_ai_config_manager: Optional[AIConfigManager] = None


def get_ai_config_manager() -> AIConfigManager:
    """Get the global AI config manager."""
    global _ai_config_manager
    if _ai_config_manager is None:
        _ai_config_manager = AIConfigManager()
    return _ai_config_manager


def initialize_ai_providers() -> None:
    """Initialize AI providers with available API keys."""
    from .ai import ai_registry, OpenAIProvider, GroqProvider
    
    config_manager = get_ai_config_manager()
    providers = config_manager.list_providers()
    
    for provider_name, has_key in providers.items():
        if has_key:
            api_key = config_manager.get_api_key(provider_name)
            if api_key:
                try:
                    if provider_name == "openai":
                        provider = OpenAIProvider(api_key)
                        ai_registry.register(provider)
                        logger.info(f"Registered {provider_name} provider")
                    elif provider_name == "groq":
                        provider = GroqProvider(api_key)
                        ai_registry.register(provider)
                        logger.info(f"Registered {provider_name} provider")
                except Exception as e:
                    logger.error(f"Failed to register {provider_name} provider: {e}")
    
    if not ai_registry.list_providers():
        logger.warning("No AI providers configured. Use 'devos ai-config set-api-key' to configure.")
