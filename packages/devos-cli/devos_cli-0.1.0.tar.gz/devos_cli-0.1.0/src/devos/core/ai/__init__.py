"""AI module initialization."""

from .provider import (
    AIProvider, AIRequest, AIResponse, CodeSuggestion, 
    AnalysisResult, RequestType, UserPreferences,
    ProjectContext, SessionContext, ai_registry,
    AIServiceError, RateLimitError, ProviderError
)
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider
from .service import AIService, AIServiceConfig, get_ai_service, initialize_ai_service
from .context import ContextBuilder
from .cache import AICache

__all__ = [
    # Core classes
    "AIService",
    "AIServiceConfig",
    "ContextBuilder",
    "AICache",
    
    # Provider system
    "AIProvider",
    "OpenAIProvider",
    "GroqProvider",
    "ai_registry",
    
    # Data models
    "AIRequest",
    "AIResponse", 
    "CodeSuggestion",
    "AnalysisResult",
    "RequestType",
    "UserPreferences",
    "ProjectContext",
    "SessionContext",
    
    # Exceptions
    "AIServiceError",
    "RateLimitError", 
    "ProviderError",
    
    # Service functions
    "get_ai_service",
    "initialize_ai_service"
]
