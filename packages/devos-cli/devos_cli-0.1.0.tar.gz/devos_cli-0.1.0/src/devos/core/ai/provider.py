"""AI provider abstraction layer for DevOS."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio
from pathlib import Path


class RequestType(Enum):
    """Types of AI requests."""
    GENERATE = "generate"
    ANALYZE = "analyze"
    SUGGEST = "suggest"
    REFACTOR = "refactor"
    REVIEW = "review"
    CHAT = "chat"
    EXPLAIN = "explain"
    DEBUG = "debug"


@dataclass
class ProjectContext:
    """Project context for AI requests."""
    project_path: Path
    language: str
    framework: Optional[str]
    dependencies: Dict[str, str]
    patterns: List[str]
    architecture: Dict[str, Any]
    last_updated: str


@dataclass
class SessionContext:
    """Session context for AI requests."""
    session_id: str
    current_file: Optional[Path]
    recent_files: List[Path]
    work_duration: int
    notes: Optional[str]


@dataclass
class UserPreferences:
    """User preferences for AI."""
    coding_style: str
    preferred_patterns: List[str]
    ai_model: str
    temperature: float
    max_tokens: int


@dataclass
class AIRequest:
    """AI request structure."""
    query: str
    request_type: RequestType
    context: ProjectContext
    session_context: Optional[SessionContext]
    user_preferences: UserPreferences
    metadata: Dict[str, Any]


@dataclass
class AIResponse:
    """AI response structure."""
    content: str
    confidence: float
    tokens_used: int
    cost: float
    cached: bool
    metadata: Dict[str, Any]
    provider: str


@dataclass
class CodeSuggestion:
    """Code suggestion from AI."""
    title: str
    description: str
    code: str
    language: str
    confidence: float
    impact: str


@dataclass
class AnalysisResult:
    """Code analysis result."""
    issues: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    score: float
    metrics: Dict[str, Any]


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self._rate_limiter = RateLimiter()
    
    @abstractmethod
    async def generate_code(
        self, 
        request: AIRequest
    ) -> AIResponse:
        """Generate code based on request."""
        pass
    
    @abstractmethod
    async def analyze_code(
        self, 
        code: str, 
        request: AIRequest
    ) -> AnalysisResult:
        """Analyze code and return results."""
        pass
    
    @abstractmethod
    async def suggest_improvements(
        self, 
        request: AIRequest
    ) -> List[CodeSuggestion]:
        """Suggest improvements for code."""
        pass
    
    @abstractmethod
    async def chat_response(
        self, 
        conversation: List[Dict[str, str]], 
        request: AIRequest
    ) -> AIResponse:
        """Generate chat response."""
        pass
    
    @abstractmethod
    async def explain_code(
        self, 
        code: str, 
        query: str, 
        request: AIRequest
    ) -> AIResponse:
        """Explain code functionality."""
        pass
    
    @abstractmethod
    async def debug_code(
        self, 
        code: str, 
        error_type: str, 
        request: AIRequest
    ) -> AIResponse:
        """Debug code issues."""
        pass
    
    @abstractmethod
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get provider usage statistics."""
        pass
    
    async def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits."""
        return await self._rate_limiter.check_limit()


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def check_limit(self) -> bool:
        """Check if we can make a request."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            if len(self.requests) < self.requests_per_minute:
                self.requests.append(now)
                return True
            return False


class AIProviderRegistry:
    """Registry for AI providers."""
    
    def __init__(self):
        self._providers: Dict[str, AIProvider] = {}
        self._default_provider: Optional[str] = None
    
    def register(self, provider: AIProvider) -> None:
        """Register an AI provider."""
        self._providers[provider.name] = provider
        if self._default_provider is None:
            self._default_provider = provider.name
    
    def get_provider(self, name: Optional[str] = None) -> AIProvider:
        """Get an AI provider by name."""
        provider_name = name or self._default_provider
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not registered")
        return self._providers[provider_name]
    
    def list_providers(self) -> List[str]:
        """List all registered providers."""
        return list(self._providers.keys())
    
    def set_default(self, name: str) -> None:
        """Set default provider."""
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered")
        self._default_provider = name


# Global provider registry
ai_registry = AIProviderRegistry()


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class RateLimitError(AIServiceError):
    """Raised when rate limit is exceeded."""
    pass


class ProviderError(AIServiceError):
    """Raised when provider encounters an error."""
    pass


class ContextError(AIServiceError):
    """Raised when context building fails."""
    pass


class AuthenticationError(AIServiceError):
    """Raised when authentication fails."""
    pass


class QuotaExceededError(AIServiceError):
    """Raised when quota is exceeded."""
    pass
