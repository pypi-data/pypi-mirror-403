"""Enhanced error handling and edge cases for AI integration."""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import json

from .provider import AIServiceError, AuthenticationError, QuotaExceededError, RateLimitError, ProviderError


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling."""
    AUTHENTICATION = "authentication"
    QUOTA = "quota"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    PROVIDER = "provider"
    VALIDATION = "validation"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str
    provider: Optional[str] = None
    model: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: float = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EnhancedError:
    """Enhanced error information with context and suggestions."""
    original_error: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    suggestions: List[str]
    context: ErrorContext
    retry_after: Optional[float] = None
    fallback_available: bool = False


class AIErrorHandler:
    """Advanced error handling for AI operations."""
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_base": 2.0
        }
    
    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize error pattern matching."""
        return {
            "authentication": {
                "patterns": [
                    "authentication", "unauthorized", "invalid api key",
                    "401", "auth failed", "credentials"
                ],
                "severity": ErrorSeverity.HIGH,
                "suggestions": [
                    "Check API key configuration",
                    "Verify API key is valid and active",
                    "Run: devos ai-config set-api-key <provider>",
                    "Check environment variables"
                ],
                "retry": False
            },
            "quota": {
                "patterns": [
                    "quota", "limit", "insufficient credits", "billing",
                    "usage limit", "402", "payment required"
                ],
                "severity": ErrorSeverity.HIGH,
                "suggestions": [
                    "Check account balance",
                    "Upgrade to higher tier",
                    "Use cheaper model (e.g., llama3-8b instead of llama3-70b)",
                    "Monitor usage with: devos ai-config usage-stats"
                ],
                "retry": False
            },
            "rate_limit": {
                "patterns": [
                    "rate limit", "too many requests", "429", "throttle",
                    "rate exceeded", "request limit"
                ],
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Wait before retrying",
                    "Use smaller requests",
                    "Switch to faster provider (Groq)",
                    "Implement request batching"
                ],
                "retry": True,
                "retry_after": 60.0
            },
            "network": {
                "patterns": [
                    "connection", "timeout", "network", "dns", "ssl",
                    "connection refused", "connection timeout"
                ],
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Check internet connection",
                    "Try different provider",
                    "Use smaller request",
                    "Check firewall settings"
                ],
                "retry": True
            },
            "provider": {
                "patterns": [
                    "internal error", "server error", "500", "502", "503",
                    "service unavailable", "provider error"
                ],
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Try again in a few moments",
                    "Switch to backup provider",
                    "Check provider status page",
                    "Use cached response if available"
                ],
                "retry": True
            },
            "validation": {
                "patterns": [
                    "invalid", "malformed", "bad request", "400",
                    "validation error", "parameter error"
                ],
                "severity": ErrorSeverity.LOW,
                "suggestions": [
                    "Check request parameters",
                    "Verify input format",
                    "Reduce request size",
                    "Check model availability"
                ],
                "retry": False
            }
        }
    
    def categorize_error(self, error: Exception, error_message: str) -> ErrorCategory:
        """Categorize error based on message content."""
        error_message_lower = error_message.lower()
        
        for category, config in self.error_patterns.items():
            for pattern in config["patterns"]:
                if pattern in error_message_lower:
                    return ErrorCategory(category)
        
        return ErrorCategory.UNKNOWN
    
    def get_severity(self, category: ErrorCategory) -> ErrorSeverity:
        """Get severity level for error category."""
        if category.value in self.error_patterns:
            return self.error_patterns[category.value]["severity"]
        return ErrorSeverity.MEDIUM
    
    def get_suggestions(self, category: ErrorCategory) -> List[str]:
        """Get suggestions for error category."""
        if category.value in self.error_patterns:
            return self.error_patterns[category.value]["suggestions"]
        return ["Try again", "Check configuration", "Contact support"]
    
    def should_retry(self, category: ErrorCategory) -> bool:
        """Check if error is retryable."""
        if category.value in self.error_patterns:
            return self.error_patterns[category.value].get("retry", False)
        return False
    
    def get_retry_delay(self, category: ErrorCategory, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        if category.value in self.error_patterns and "retry_after" in self.error_patterns[category.value]:
            return self.error_patterns[category.value]["retry_after"]
        
        # Exponential backoff
        delay = self.retry_config["base_delay"] * (self.retry_config["exponential_base"] ** attempt)
        return min(delay, self.retry_config["max_delay"])
    
    def create_enhanced_error(
        self, 
        original_error: Exception, 
        context: ErrorContext
    ) -> EnhancedError:
        """Create enhanced error with context and suggestions."""
        error_message = str(original_error)
        category = self.categorize_error(original_error, error_message)
        severity = self.get_severity(category)
        suggestions = self.get_suggestions(category)
        retry_after = None
        
        if category in self.error_patterns and "retry_after" in self.error_patterns[category.name]:
            retry_after = self.error_patterns[category.name]["retry_after"]
        
        # Check if fallback is available
        fallback_available = self._check_fallback_availability(context.provider)
        
        return EnhancedError(
            original_error=original_error,
            category=category,
            severity=severity,
           message=self._create_user_friendly_message(original_error, category),
            suggestions=suggestions,
            context=context,
            retry_after=retry_after,
            fallback_available=fallback_available
        )
    
    def _create_user_friendly_message(self, error: Exception, category: ErrorCategory) -> str:
        """Create user-friendly error message."""
        base_messages = {
            ErrorCategory.AUTHENTICATION: "AI service authentication failed",
            ErrorCategory.QUOTA: "AI service quota exceeded",
            ErrorCategory.RATE_LIMIT: "AI service rate limit exceeded",
            ErrorCategory.NETWORK: "Network connection to AI service failed",
            ErrorCategory.PROVIDER: "AI service provider error",
            ErrorCategory.VALIDATION: "Invalid request to AI service",
            ErrorCategory.SYSTEM: "System error occurred",
            ErrorCategory.UNKNOWN: "Unknown error occurred"
        }
        
        base_message = base_messages.get(category, "AI service error")
        return f"{base_message}: {str(error)}"
    
    def _check_fallback_availability(self, failed_provider: Optional[str]) -> bool:
        """Check if fallback provider is available."""
        try:
            from .ai_config import get_ai_config_manager
            config_manager = get_ai_config_manager()
            providers = config_manager.list_providers()
            
            available_providers = [p for p, configured in providers.items() 
                                if configured and p != failed_provider]
            return len(available_providers) > 0
        except:
            return False
    
    async def handle_error_with_retry(
        self, 
        operation: callable, 
        context: ErrorContext,
        max_retries: Optional[int] = None
    ) -> Any:
        """Handle operation with intelligent retry logic."""
        max_retries = max_retries or self.retry_config["max_retries"]
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                enhanced_error = self.create_enhanced_error(e, context)
                last_error = enhanced_error
                
                logger.warning(f"AI operation failed (attempt {attempt + 1}): {enhanced_error.message}")
                
                # Don't retry if error is not retryable or we've exhausted retries
                if not self.should_retry(enhanced_error.category) or attempt >= max_retries:
                    break
                
                # Calculate delay and wait
                delay = self.get_retry_delay(enhanced_error.category, attempt)
                if delay > 0:
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
        
        # All retries exhausted, return enhanced error
        raise last_error.original_error from last_error.original_error
    
    def log_error(self, enhanced_error: EnhancedError):
        """Log enhanced error with context."""
        log_data = {
            "error": str(enhanced_error.original_error),
            "category": enhanced_error.category.value,
            "severity": enhanced_error.severity.value,
            "operation": enhanced_error.context.operation,
            "provider": enhanced_error.context.provider,
            "model": enhanced_error.context.model,
            "timestamp": enhanced_error.context.timestamp,
            "suggestions": enhanced_error.suggestions
        }
        
        if enhanced_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.error(f"AI Error: {json.dumps(log_data, indent=2)}")
        elif enhanced_error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"AI Error: {json.dumps(log_data)}")
        else:
            logger.info(f"AI Error: {json.dumps(log_data)}")


class ResilientAIService:
    """AI service with enhanced error handling and fallback."""
    
    def __init__(self, primary_service, fallback_providers: List[str] = None):
        self.primary_service = primary_service
        self.fallback_providers = fallback_providers or ["groq", "openai"]
        self.error_handler = AIErrorHandler()
        self.circuit_breaker = CircuitBreaker()
    
    async def generate_code_with_fallback(
        self, 
        query: str, 
        project_path, 
        user_preferences,
        provider_name: Optional[str] = None
    ):
        """Generate code with automatic fallback."""
        providers_to_try = [provider_name] if provider_name else [self.primary_service.config.default_provider]
        providers_to_try.extend([p for p in self.fallback_providers if p not in providers_to_try])
        
        last_error = None
        
        for provider in providers_to_try:
            try:
                context = ErrorContext(
                    operation="generate_code",
                    provider=provider,
                    model=user_preferences.ai_model
                )
                
                operation = lambda: self.primary_service.generate_code(
                    query, project_path, user_preferences, provider
                )
                
                return await self.error_handler.handle_error_with_retry(operation, context)
                
            except Exception as e:
                enhanced_error = self.error_handler.create_enhanced_error(e, context)
                last_error = enhanced_error
                
                self.error_handler.log_error(enhanced_error)
                
                if enhanced_error.fallback_available and provider != providers_to_try[-1]:
                    logger.info(f"Falling back to next provider after {provider} failure")
                    continue
                else:
                    break
        
        # All providers failed, raise the last error with suggestions
        if last_error:
            self._display_error_to_user(last_error)
            raise last_error.original_error
        
        raise AIServiceError("No providers available")
    
    def _display_error_to_user(self, enhanced_error: EnhancedError):
        """Display user-friendly error message with suggestions."""
        print(f"\n❌ AI Service Error: {enhanced_error.message}")
        print(f"🔧 Category: {enhanced_error.category.value}")
        print(f"📊 Severity: {enhanced_error.severity.value}")
        
        if enhanced_error.suggestions:
            print("\n💡 Suggestions:")
            for i, suggestion in enumerate(enhanced_error.suggestions, 1):
                print(f"  {i}. {suggestion}")
        
        if enhanced_error.fallback_available:
            print("\n🔄 Fallback providers are available")
        
        if enhanced_error.retry_after:
            print(f"\n⏰ Retry recommended after {enhanced_error.retry_after} seconds")


class CircuitBreaker:
    """Circuit breaker pattern for AI service resilience."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call_allowed(self) -> bool:
        """Check if call is allowed based on circuit state."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# Global error handler instance
error_handler = AIErrorHandler()


def handle_ai_error(error: Exception, operation: str, provider: Optional[str] = None) -> EnhancedError:
    """Convenience function to handle AI errors."""
    context = ErrorContext(
        operation=operation,
        provider=provider
    )
    enhanced_error = error_handler.create_enhanced_error(error, context)
    error_handler.log_error(enhanced_error)
    return enhanced_error
