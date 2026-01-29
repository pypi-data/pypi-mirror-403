"""
Interactive AI Chat Mode - Conversational AI with Project Context
Provides an interactive chat interface with deep project understanding.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import asdict
import click
import sys
from datetime import datetime

from devos.core.progress import show_success, show_info, show_warning, show_operation_status
from devos.core.ai_config import get_ai_config_manager, initialize_ai_providers
from devos.core.ai import get_ai_service, AIServiceError, UserPreferences
from devos.core.ai.enhanced_context import EnhancedContextBuilder


class ChatSession:
    """Interactive chat session with project context."""
    
    def __init__(self, project_path: Path, model: str, temperature: float, max_tokens: int):
        self.project_path = project_path
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.conversation_history: List[Dict[str, str]] = []
        self.enhanced_context = None
        self.ai_service = None
        self.session_start = datetime.now()
        
    async def initialize(self):
        """Initialize the chat session with project context."""
        try:
            click.echo("🔄 Building project context for chat...")
            
            # Initialize AI service
            config_manager = get_ai_config_manager()
            initialize_ai_providers()
            self.ai_service = await get_ai_service()
            
            # Build enhanced context
            context_builder = EnhancedContextBuilder()
            self.enhanced_context = await context_builder.build_enhanced_context(self.project_path)
            
            show_success(f"Chat initialized with {self.enhanced_context.architecture.total_files} files")
            
            # Add system context
            system_prompt = f"""You are DevOS AI Assistant, a highly intelligent coding assistant with deep understanding of this project:

Project Overview:
- Location: {self.project_path}
- Files: {self.enhanced_context.architecture.total_files} files
- Languages: {list(self.enhanced_context.architecture.languages.keys())}
- Frameworks: {self.enhanced_context.architecture.frameworks}
- Security Score: {self.enhanced_context.architecture.security_score}/100

Architecture Patterns: {self.enhanced_context.architecture.architecture_patterns}
Entry Points: {len(self.enhanced_context.architecture.entry_points)} identified

You have comprehensive knowledge of the codebase structure, dependencies, and can provide detailed assistance.
Be helpful, accurate, and provide specific code examples when relevant.
If you don't know something, admit it rather than guessing."""

            self.conversation_history.append({"role": "system", "content": system_prompt})
            
        except Exception as e:
            show_warning(f"Failed to initialize chat: {e}")
            raise
    
    async def process_message(self, user_message: str) -> str:
        """Process a user message and generate AI response."""
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Build context-aware prompt
            context_summary = {
                "project_files": self.enhanced_context.architecture.total_files,
                "languages": list(self.enhanced_context.architecture.languages.keys()),
                "frameworks": self.enhanced_context.architecture.frameworks,
                "security_score": self.enhanced_context.architecture.security_score,
                "recent_activity": "Project analysis completed"
            }
            
            # Get AI response
            response = await self.ai_service.chat(
                conversation=self.conversation_history,
                project_path=self.project_path,
                user_preferences=UserPreferences(
                    coding_style="clean",
                    preferred_patterns=[],
                    ai_model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                ),
                provider_name="groq"
            )
            
            # Add AI response to history
            self.conversation_history.append({"role": "assistant", "content": response.content})
            
            return response.content
            
        except Exception as e:
            error_msg = f"Failed to process message: {e}"
            show_warning(error_msg)
            return error_msg
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        duration = datetime.now() - self.session_start
        return {
            "duration": str(duration),
            "messages": len([m for m in self.conversation_history if m["role"] == "user"]),
            "project_files": self.enhanced_context.architecture.total_files if self.enhanced_context else 0,
            "model": self.model
        }


@click.command()
@click.option('--model', default='llama-3.1-8b-instant', help='AI model to use')
@click.option('--temp', type=float, default=0.7, help='Temperature (0.0-1.0)')
@click.option('--max-tokens', type=int, default=2000, help='Maximum tokens per response')
@click.option('--context', is_flag=True, help='Show project context summary')
def groq_chat(model: str, temp: float, max_tokens: int, context: bool):
    """Interactive AI chat with deep project understanding.
    
    Examples:
        groq-chat
        groq-chat --model llama-3.1-70b-versatile
        groq-chat --temp 0.9 --context
    """
    
    async def run_chat():
        project_path = Path.cwd()
        chat_session = ChatSession(project_path, model, temp, max_tokens)
        
        try:
            await chat_session.initialize()
            
            if context:
                # Show project context
                click.echo("\n📊 Project Context:")
                click.echo("=" * 50)
                click.echo(f"📁 Files: {chat_session.enhanced_context.architecture.total_files}")
                click.echo(f"💻 Languages: {', '.join(chat_session.enhanced_context.architecture.languages.keys())}")
                if chat_session.enhanced_context.architecture.frameworks:
                    click.echo(f"🔧 Frameworks: {', '.join(chat_session.enhanced_context.architecture.frameworks)}")
                click.echo(f"🔒 Security Score: {chat_session.enhanced_context.architecture.security_score}/100")
                click.echo(f"🎨 Patterns: {', '.join(chat_session.enhanced_context.architecture.architecture_patterns)}")
                click.echo("")
            
            # Welcome message
            click.echo("🤖 DevOS AI Chat - Type 'exit' to quit, 'help' for commands")
            click.echo("=" * 60)
            
            while True:
                try:
                    # Get user input
                    user_input = click.prompt("\n💬 You", type=str).strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle commands
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        stats = chat_session.get_session_stats()
                        click.echo(f"\n👋 Chat ended. Session stats: {stats['messages']} messages, {stats['duration']}")
                        break
                    
                    elif user_input.lower() == 'help':
                        click.echo("\n📚 Chat Commands:")
                        click.echo("  help  - Show this help")
                        click.echo("  context - Show project context") 
                        click.echo("  stats - Show session statistics")
                        click.echo("  clear - Clear conversation history")
                        click.echo("  exit  - End chat session")
                        continue
                    
                    elif user_input.lower() == 'context':
                        if chat_session.enhanced_context:
                            click.echo(f"\n📊 Project: {chat_session.enhanced_context.architecture.total_files} files")
                            click.echo(f"💻 Languages: {list(chat_session.enhanced_context.architecture.languages.keys())}")
                            click.echo(f"🔒 Security: {chat_session.enhanced_context.architecture.security_score}/100")
                        continue
                    
                    elif user_input.lower() == 'stats':
                        stats = chat_session.get_session_stats()
                        click.echo(f"\n📈 Session Stats:")
                        click.echo(f"  Duration: {stats['duration']}")
                        click.echo(f"  Messages: {stats['messages']}")
                        click.echo(f"  Project Files: {stats['project_files']}")
                        click.echo(f"  Model: {stats['model']}")
                        continue
                    
                    elif user_input.lower() == 'clear':
                        # Keep system prompt, clear rest
                        system_msg = chat_session.conversation_history[0] if chat_session.conversation_history else None
                        chat_session.conversation_history = [system_msg] if system_msg else []
                        click.echo("🧹 Conversation history cleared")
                        continue
                    
                    # Process message
                    click.echo("🤔 Thinking...")
                    response = await chat_session.process_message(user_input)
                    
                    click.echo(f"\n🤖 AI: {response}")
                    
                except KeyboardInterrupt:
                    click.echo("\n\n👋 Chat interrupted. Goodbye!")
                    break
                except EOFError:
                    click.echo("\n\n👋 Chat ended. Goodbye!")
                    break
                    
        except Exception as e:
            show_warning(f"Chat session failed: {e}")
    
    asyncio.run(run_chat())
