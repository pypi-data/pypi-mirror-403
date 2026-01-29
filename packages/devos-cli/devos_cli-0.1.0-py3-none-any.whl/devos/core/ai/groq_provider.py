"""Groq provider implementation."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from .provider import (
    AIProvider, AIRequest, AIResponse, CodeSuggestion, 
    AnalysisResult, RequestType, AIServiceError, 
    AuthenticationError, QuotaExceededError, ProviderError
)


logger = logging.getLogger(__name__)


class GroqProvider(AIProvider):
    """Groq provider implementation."""
    
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        super().__init__("groq", model)
        
        if not GROQ_AVAILABLE:
            raise AIServiceError("Groq package not installed. Install with: pip install groq")
        
        self.client = AsyncGroq(api_key=api_key)
        self._usage_stats = {
            "requests": 0,
            "tokens_used": 0,
            "cost": 0.0,
            "errors": 0
        }
    
    async def generate_code(self, request: AIRequest) -> AIResponse:
        """Generate code based on request."""
        try:
            if not await self._check_rate_limit():
                raise AIServiceError("Rate limit exceeded")
            
            prompt = self._build_code_generation_prompt(request)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(request)},
                    {"role": "user", "content": prompt}
                ],
                temperature=request.user_preferences.temperature,
                max_tokens=request.user_preferences.max_tokens
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self._calculate_cost(tokens_used)
            
            self._update_usage_stats(tokens_used, cost)
            
            return AIResponse(
                content=content,
                confidence=0.8,
                tokens_used=tokens_used,
                cost=cost,
                cached=False,
                metadata={"model": self.model, "request_type": "generate"},
                provider=self.name
            )
            
        except Exception as e:
            self._handle_error(e)
            raise
    
    async def analyze_code(self, code: str, request: AIRequest) -> AnalysisResult:
        """Analyze code and return results."""
        try:
            prompt = self._build_code_analysis_prompt(code, request)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code analysis expert. Provide structured analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self._calculate_cost(tokens_used)
            
            # Parse the structured response
            analysis = self._parse_analysis_response(content)
            
            self._update_usage_stats(tokens_used, cost)
            
            return analysis
            
        except Exception as e:
            self._handle_error(e)
            raise
    
    async def suggest_improvements(self, request: AIRequest) -> List[CodeSuggestion]:
        """Suggest improvements for code."""
        try:
            prompt = self._build_suggestion_prompt(request)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code improvement expert. Provide actionable suggestions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self._calculate_cost(tokens_used)
            
            suggestions = self._parse_suggestions(content)
            
            self._update_usage_stats(tokens_used, cost)
            
            return suggestions
            
        except Exception as e:
            self._handle_error(e)
            raise
    
    async def chat_response(self, conversation: List[Dict[str, str]], request: AIRequest) -> AIResponse:
        """Generate chat response."""
        try:
            messages = [
                {"role": "system", "content": self._get_chat_system_prompt(request)}
            ]
            messages.extend(conversation)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=request.user_preferences.temperature,
                max_tokens=request.user_preferences.max_tokens
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self._calculate_cost(tokens_used)
            
            self._update_usage_stats(tokens_used, cost)
            
            return AIResponse(
                content=content,
                confidence=0.9,
                tokens_used=tokens_used,
                cost=cost,
                cached=False,
                metadata={"model": self.model, "conversation_length": len(conversation)},
                provider=self.name
            )
            
        except Exception as e:
            self._handle_error(e)
            raise
    
    async def explain_code(self, code: str, query: str, request: AIRequest) -> AIResponse:
        """Explain code functionality."""
        try:
            prompt = self._build_explanation_prompt(code, query, request)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code explanation expert. Explain code clearly and concisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self._calculate_cost(tokens_used)
            
            self._update_usage_stats(tokens_used, cost)
            
            return AIResponse(
                content=content,
                confidence=0.85,
                tokens_used=tokens_used,
                cost=cost,
                cached=False,
                metadata={"model": self.model, "code_length": len(code)},
                provider=self.name
            )
            
        except Exception as e:
            self._handle_error(e)
            raise
    
    async def debug_code(self, code: str, error_type: str, request: AIRequest) -> AIResponse:
        """Debug code issues."""
        try:
            prompt = self._build_debug_prompt(code, error_type, request)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a debugging expert. Identify and fix code issues."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self._calculate_cost(tokens_used)
            
            self._update_usage_stats(tokens_used, cost)
            
            return AIResponse(
                content=content,
                confidence=0.8,
                tokens_used=tokens_used,
                cost=cost,
                cached=False,
                metadata={"model": self.model, "error_type": error_type},
                provider=self.name
            )
            
        except Exception as e:
            self._handle_error(e)
            raise
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get provider usage statistics."""
        return self._usage_stats.copy()
    
    def _get_system_prompt(self, request: AIRequest) -> str:
        """Get system prompt based on request context."""
        context_info = []
        
        if request.context.language:
            context_info.append(f"Language: {request.context.language}")
        
        if request.context.framework:
            context_info.append(f"Framework: {request.context.framework}")
        
        if request.context.patterns:
            context_info.append(f"Patterns: {', '.join(request.context.patterns)}")
        
        system_prompt = f"""You are an expert software developer and AI assistant for DevOS, powered by Groq's fast inference.

Project Context:
{chr(10).join(context_info)}

Coding Style: {request.user_preferences.coding_style}

Guidelines:
- Provide clean, production-ready code
- Follow best practices and security standards
- Consider the project's existing patterns
- Include relevant error handling
- Be concise but thorough
- Leverage Groq's speed for quick, accurate responses"""
        
        return system_prompt
    
    def _get_chat_system_prompt(self, request: AIRequest) -> str:
        """Get chat-specific system prompt."""
        return f"""You are DevOS AI, powered by Groq's fast inference - a helpful development assistant.

Current Project:
- Language: {request.context.language}
- Framework: {request.context.framework}
- Path: {request.context.project_path}

You have access to the project context and can provide specific, actionable advice.
Be helpful, concise, and focus on practical solutions. Groq's speed allows for quick, iterative development."""
    
    def _build_code_generation_prompt(self, request: AIRequest) -> str:
        """Build prompt for code generation."""
        prompt = f"""Generate code for the following request:

Request: {request.query}

Context:
- Project: {request.context.project_path}
- Language: {request.context.language}
- Framework: {request.context.framework}

Please provide:
1. Complete, working code
2. Brief explanation
3. Any relevant imports or dependencies
4. Error handling where appropriate

Generate code that follows the project's existing patterns and conventions.
Leverage fast inference to provide high-quality, well-structured code."""
        
        return prompt
    
    def _build_code_analysis_prompt(self, code: str, request: AIRequest) -> str:
        """Build prompt for code analysis."""
        return f"""Analyze the following code:

```{request.context.language}
{code}
```

Provide analysis in JSON format:
{{
  "issues": [
    {{
      "type": "security|performance|style|bug",
      "severity": "low|medium|high",
      "line": number,
      "message": "description",
      "suggestion": "how to fix"
    }}
  ],
  "suggestions": [
    "improvement suggestion 1",
    "improvement suggestion 2"
  ],
  "score": 0.0,
  "metrics": {{
    "complexity": "low|medium|high",
    "maintainability": "low|medium|high",
    "readability": "low|medium|high"
  }}
}}

Focus on providing actionable insights quickly and accurately."""
    
    def _build_suggestion_prompt(self, request: AIRequest) -> str:
        """Build prompt for improvement suggestions."""
        return f"""Based on the request: "{request.query}"

Provide specific, actionable suggestions for improvement.

Format each suggestion as:
## Title
Description: [brief description]
Code: [code example if applicable]
Confidence: [0.0-1.0]
Impact: [low|medium|high]

Focus on practical improvements that enhance code quality, performance, or maintainability.
Provide clear, implementable suggestions quickly."""
    
    def _build_explanation_prompt(self, code: str, query: str, request: AIRequest) -> str:
        """Build prompt for code explanation."""
        return f"""Explain this code in the context of: "{query}"

```{request.context.language}
{code}
```

Provide:
1. High-level overview
2. Key components and their roles
3. How it addresses the query
4. Important patterns or concepts used

Be clear and concise. Focus on the most relevant aspects.
Explain efficiently using Groq's fast inference capabilities."""
    
    def _build_debug_prompt(self, code: str, error_type: str, request: AIRequest) -> str:
        """Build prompt for debugging."""
        return f"""Debug this code for {error_type} issues:

```{request.context.language}
{code}
```

Provide:
1. Identified issues
2. Root cause analysis
3. Specific fixes
4. Preventive measures

Be thorough and provide working solutions.
Debug quickly and accurately using fast inference."""
    
    def _parse_analysis_response(self, content: str) -> AnalysisResult:
        """Parse analysis response from AI."""
        try:
            # Try to extract JSON from response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
                data = json.loads(json_str)
            else:
                # Fallback parsing
                data = {
                    "issues": [],
                    "suggestions": [],
                    "score": 7.0,
                    "metrics": {"complexity": "medium", "maintainability": "medium", "readability": "medium"}
                }
            
            return AnalysisResult(
                issues=data.get("issues", []),
                suggestions=data.get("suggestions", []),
                score=data.get("score", 7.0),
                metrics=data.get("metrics", {})
            )
        except Exception:
            # Fallback if parsing fails
            return AnalysisResult(
                issues=[],
                suggestions=[content],
                score=7.0,
                metrics={}
            )
    
    def _parse_suggestions(self, content: str) -> List[CodeSuggestion]:
        """Parse suggestions from AI response."""
        suggestions = []
        
        # Simple parsing - in production, use more sophisticated parsing
        lines = content.split('\n')
        current_suggestion = None
        
        for line in lines:
            if line.startswith('##'):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = CodeSuggestion(
                    title=line[3:].strip(),
                    description="",
                    code="",
                    language="",
                    confidence=0.7,
                    impact="medium"
                )
            elif current_suggestion and line.startswith('Description:'):
                current_suggestion.description = line[12:].strip()
            elif current_suggestion and line.startswith('Code:'):
                current_suggestion.code = line[5:].strip()
        
        if current_suggestion:
            suggestions.append(current_suggestion)
        
        return suggestions
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate cost based on token usage."""
        # Groq pricing (as of 2024)
        if self.model.startswith("llama3-70b"):
            return tokens * 0.00059  # $0.59 per 1M tokens
        elif self.model.startswith("llama3-8b"):
            return tokens * 0.00005  # $0.05 per 1M tokens
        elif self.model.startswith("mixtral"):
            return tokens * 0.00024  # $0.24 per 1M tokens
        elif self.model.startswith("gemma"):
            return tokens * 0.00007  # $0.07 per 1M tokens
        else:
            return tokens * 0.0001  # Default pricing
    
    def _update_usage_stats(self, tokens: int, cost: float) -> None:
        """Update usage statistics."""
        self._usage_stats["requests"] += 1
        self._usage_stats["tokens_used"] += tokens
        self._usage_stats["cost"] += cost
    
    def _handle_error(self, error: Exception) -> None:
        """Handle provider-specific errors."""
        self._usage_stats["errors"] += 1
        
        error_str = str(error).lower()
        
        if "authentication" in error_str or "unauthorized" in error_str:
            raise AuthenticationError(f"Groq authentication failed: {error}")
        elif "quota" in error_str or "limit" in error_str:
            raise QuotaExceededError(f"Groq quota exceeded: {error}")
        elif "rate" in error_str:
            raise AIServiceError(f"Groq rate limit exceeded: {error}")
        else:
            raise ProviderError(f"Groq provider error: {error}")
