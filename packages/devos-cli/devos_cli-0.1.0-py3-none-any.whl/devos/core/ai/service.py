"""Main AI service integration."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from .provider import (
    AIProvider, AIRequest, AIResponse, CodeSuggestion, 
    AnalysisResult, RequestType, UserPreferences, 
    ai_registry, AIServiceError
)
from .context import ContextBuilder, ProjectContext, SessionContext
from .cache import AICache


logger = logging.getLogger(__name__)


@dataclass
class AIServiceConfig:
    """AI service configuration."""
    default_provider: str = "openai"
    default_model: str = "gpt-4"
    cache_enabled: bool = True
    max_context_size: int = 100000
    rate_limit_per_minute: int = 60
    cost_limit_per_hour: float = 10.0


class AIService:
    """Main AI service for DevOS."""
    
    def __init__(self, config: AIServiceConfig):
        self.config = config
        self.context_builder = ContextBuilder()
        self.cache = AICache() if config.cache_enabled else None
        self._usage_tracker = UsageTracker()
        
    async def initialize(self) -> None:
        """Initialize the AI service."""
        # Verify at least one provider is registered
        providers = ai_registry.list_providers()
        if not providers:
            raise AIServiceError("No AI providers registered")
        
        logger.info(f"AI Service initialized with providers: {providers}")
    
    async def generate_code(
        self, 
        query: str, 
        project_path: Path,
        user_preferences: Optional[UserPreferences] = None,
        provider_name: Optional[str] = None
    ) -> AIResponse:
        """Generate code based on query and project context."""
        try:
            # Build request
            request = await self._build_request(
                query=query,
                request_type=RequestType.GENERATE,
                project_path=project_path,
                user_preferences=user_preferences,
                provider_name=provider_name
            )
            
            # Check cache
            if self.cache:
                cached_response = await self.cache.get(request)
                if cached_response:
                    logger.info("Returning cached response")
                    return cached_response
            
            # Get provider and generate response
            provider = ai_registry.get_provider(provider_name or self.config.default_provider)
            response = await provider.generate_code(request)
            
            # Cache response
            if self.cache:
                await self.cache.set(request, response)
            
            # Track usage
            await self._usage_tracker.track_request(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise AIServiceError(f"Code generation failed: {e}")
    
    async def analyze_code(
        self, 
        code: str, 
        project_path: Path,
        user_preferences: Optional[UserPreferences] = None,
        provider_name: Optional[str] = None
    ) -> AnalysisResult:
        """Analyze code with project context."""
        try:
            request = await self._build_request(
                query=f"Analyze this code",
                request_type=RequestType.ANALYZE,
                project_path=project_path,
                user_preferences=user_preferences,
                provider_name=provider_name
            )
            
            provider = ai_registry.get_provider(provider_name or self.config.default_provider)
            result = await provider.analyze_code(code, request)
            
            await self._usage_tracker.track_request(request, AIResponse(
                content="",
                confidence=0.8,
                tokens_used=0,
                cost=0.0,
                cached=False,
                metadata={},
                provider=provider.name
            ))
            
            return result
            
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            raise AIServiceError(f"Code analysis failed: {e}")
    
    async def suggest_improvements(
        self, 
        query: str, 
        project_path: Path,
        user_preferences: Optional[UserPreferences] = None,
        provider_name: Optional[str] = None
    ) -> List[CodeSuggestion]:
        """Get improvement suggestions."""
        try:
            request = await self._build_request(
                query=query,
                request_type=RequestType.SUGGEST,
                project_path=project_path,
                user_preferences=user_preferences,
                provider_name=provider_name
            )
            
            provider = ai_registry.get_provider(provider_name or self.config.default_provider)
            suggestions = await provider.suggest_improvements(request)
            
            await self._usage_tracker.track_request(request, AIResponse(
                content="",
                confidence=0.8,
                tokens_used=0,
                cost=0.0,
                cached=False,
                metadata={},
                provider=provider.name
            ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            raise AIServiceError(f"Suggestion generation failed: {e}")
    
    async def chat(
        self, 
        conversation: List[Dict[str, str]], 
        project_path: Path,
        user_preferences: Optional[UserPreferences] = None,
        provider_name: Optional[str] = None
    ) -> AIResponse:
        """Generate chat response."""
        try:
            request = await self._build_request(
                query=conversation[-1]["content"] if conversation else "",
                request_type=RequestType.CHAT,
                project_path=project_path,
                user_preferences=user_preferences,
                provider_name=provider_name
            )
            
            provider = ai_registry.get_provider(provider_name or self.config.default_provider)
            response = await provider.chat_response(conversation, request)
            
            await self._usage_tracker.track_request(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat response failed: {e}")
            raise AIServiceError(f"Chat response failed: {e}")
    
    async def explain_code(
        self, 
        code: str, 
        query: str, 
        project_path: Path,
        user_preferences: Optional[UserPreferences] = None,
        provider_name: Optional[str] = None
    ) -> AIResponse:
        """Explain code functionality."""
        try:
            request = await self._build_request(
                query=query,
                request_type=RequestType.EXPLAIN,
                project_path=project_path,
                user_preferences=user_preferences,
                provider_name=provider_name
            )
            
            provider = ai_registry.get_provider(provider_name or self.config.default_provider)
            response = await provider.explain_code(code, query, request)
            
            await self._usage_tracker.track_request(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Code explanation failed: {e}")
            raise AIServiceError(f"Code explanation failed: {e}")
    
    async def debug_code(
        self, 
        code: str, 
        error_type: str, 
        project_path: Path,
        user_preferences: Optional[UserPreferences] = None,
        provider_name: Optional[str] = None
    ) -> AIResponse:
        """Debug code issues."""
        try:
            request = await self._build_request(
                query=f"Debug {error_type} issue",
                request_type=RequestType.DEBUG,
                project_path=project_path,
                user_preferences=user_preferences,
                provider_name=provider_name
            )
            
            provider = ai_registry.get_provider(provider_name or self.config.default_provider)
            response = await provider.debug_code(code, error_type, request)
            
            await self._usage_tracker.track_request(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Code debugging failed: {e}")
            raise AIServiceError(f"Code debugging failed: {e}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return await self._usage_tracker.get_stats()
    
    async def _build_request(
        self,
        query: str,
        request_type: RequestType,
        project_path: Path,
        user_preferences: Optional[UserPreferences] = None,
        provider_name: Optional[str] = None
    ) -> AIRequest:
        """Build AI request with context."""
        # Build project context
        project_context = await self.context_builder.build_project_context(project_path)
        
        # Build session context (placeholder for now)
        session_context = SessionContext(
            session_id="current",
            current_file=None,
            recent_files=[],
            work_duration=0,
            notes=None
        )
        
        # Set default user preferences
        if user_preferences is None:
            user_preferences = UserPreferences(
                coding_style="clean",
                preferred_patterns=[],
                ai_model=self.config.default_model,
                temperature=0.7,
                max_tokens=2000
            )
        
        return AIRequest(
            query=query,
            request_type=request_type,
            context=project_context,
            session_context=session_context,
            user_preferences=user_preferences,
            metadata={
                "provider": provider_name or self.config.default_provider,
                "timestamp": asyncio.get_event_loop().time()
            }
        )


class UsageTracker:
    """Track AI service usage."""
    
    def __init__(self):
        self._stats = {
            "requests": 0,
            "tokens_used": 0,
            "total_cost": 0.0,
            "cache_hits": 0,
            "errors": 0,
            "by_provider": {},
            "by_request_type": {}
        }
    
    async def track_request(self, request: AIRequest, response: AIResponse) -> None:
        """Track a single request."""
        self._stats["requests"] += 1
        self._stats["tokens_used"] += response.tokens_used
        self._stats["total_cost"] += response.cost
        
        if response.cached:
            self._stats["cache_hits"] += 1
        
        # Track by provider
        provider = response.provider
        if provider not in self._stats["by_provider"]:
            self._stats["by_provider"][provider] = {
                "requests": 0,
                "tokens_used": 0,
                "cost": 0.0
            }
        
        self._stats["by_provider"][provider]["requests"] += 1
        self._stats["by_provider"][provider]["tokens_used"] += response.tokens_used
        self._stats["by_provider"][provider]["cost"] += response.cost
        
        # Track by request type
        req_type = request.request_type.value
        if req_type not in self._stats["by_request_type"]:
            self._stats["by_request_type"][req_type] = 0
        self._stats["by_request_type"][req_type] += 1
    
    async def track_error(self, error: Exception) -> None:
        """Track an error."""
        self._stats["errors"] += 1
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self._stats.copy()


# Global AI service instance
_ai_service: Optional[AIService] = None


async def get_ai_service() -> AIService:
    """Get the global AI service instance."""
    global _ai_service
    if _ai_service is None:
        config = AIServiceConfig()
        _ai_service = AIService(config)
        await _ai_service.initialize()
    return _ai_service


async def initialize_ai_service(config: AIServiceConfig) -> AIService:
    """Initialize the global AI service."""
    global _ai_service
    _ai_service = AIService(config)
    await _ai_service.initialize()
    return _ai_service
