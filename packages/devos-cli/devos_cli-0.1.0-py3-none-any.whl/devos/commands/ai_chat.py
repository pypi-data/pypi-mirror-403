"""
Interactive AI Chat Mode - Conversational AI with Project Context
Provides an interactive chat interface with AI that understands your project.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import click

from devos.core.progress import show_success, show_info, show_warning
from devos.core.ai_config import get_ai_config_manager, initialize_ai_providers
from devos.core.ai import get_ai_service, AIServiceError, UserPreferences
from devos.core.ai.enhanced_context import EnhancedContextBuilder


class AIChatSession:
    """Interactive AI chat session with project context."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.enhanced_context = None
        self.chat_history: List[Dict[str, Any]] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def initialize(self):
        """Initialize chat session with project context."""
        try:
            # Build enhanced context
            context_builder = EnhancedContextBuilder()
            self.enhanced_context = await context_builder.build_enhanced_context(self.project_path)
            
            show_info(f"🤖 AI Chat initialized for project: {self.project_path.name}")
            show_info(f"📁 Analyzed {self.enhanced_context.architecture.total_files} files")
            show_info(f"💻 Languages: {', '.join(self.enhanced_context.architecture.languages.keys())}")
            
        except Exception as e:
            show_warning(f"Failed to build project context: {e}")
            self.enhanced_context = None
    
    async def chat_loop(self, context_focus: Optional[str] = None):
        """Run the interactive chat loop."""
        # Initialize AI service
        config_manager = get_ai_config_manager()
        initialize_ai_providers()
        ai_service = await get_ai_service()
        
        # Build context prompt
        context_prompt = self._build_context_prompt(context_focus)
        
        click.echo("\n" + "="*60)
        click.echo("🤖 DevOS AI Chat - Type 'exit' to quit, 'help' for commands")
        click.echo("="*60)
        
        while True:
            try:
                # Get user input
                user_input = click.prompt("\n💬 You", type=str).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    click.echo("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'clear':
                    self.chat_history.clear()
                    click.echo("🧹 Chat history cleared")
                    continue
                elif user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                elif user_input.lower().startswith('save'):
                    self._save_session(user_input)
                    continue
                
                # Add to history
                self.chat_history.append({
                    'role': 'user',
                    'content': user_input,
                    'timestamp': datetime.now()
                })
                
                # Get AI response
                click.echo("🤔 Thinking...")
                
                full_prompt = f"{context_prompt}\n\nChat History:\n{self._format_chat_history()}\n\nCurrent Question: {user_input}"
                
                response = await ai_service.chat(
                    message=full_prompt,
                    user_preferences=UserPreferences(
                        coding_style="conversational",
                        preferred_patterns=[],
                        ai_model="llama-3.1-8b-instant",
                        temperature=0.7,
                        max_tokens=1000
                    ),
                    provider_name="groq"
                )
                
                # Display response
                click.echo(f"\n🤖 AI: {response}")
                
                # Add to history
                self.chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now()
                })
                
            except KeyboardInterrupt:
                click.echo("\n👋 Goodbye!")
                break
            except Exception as e:
                show_warning(f"Chat error: {e}")
                continue
    
    def _build_context_prompt(self, context_focus: Optional[str]) -> str:
        """Build context prompt for AI."""
        if not self.enhanced_context:
            return "You are a helpful AI assistant for developers."
        
        arch = self.enhanced_context.architecture
        
        context_info = f"""
You are DevOS AI, a helpful assistant for developers working on the project "{self.project_path.name}".

Project Overview:
- Total Files: {arch.total_files}
- Total Lines: {arch.total_lines:,}
- Languages: {', '.join(arch.languages.keys())}
- Frameworks: {', '.join(arch.frameworks)}
- Security Score: {arch.security_score}/100
- Architecture Patterns: {', '.join(arch.architecture_patterns)}

Context Focus: {context_focus or 'general'}

Provide helpful, concise responses about this project. You can:
- Explain code and architecture
- Suggest improvements
- Help with debugging
- Answer questions about the project structure
- Provide best practices and recommendations
"""
        
        return context_info
    
    def _format_chat_history(self) -> str:
        """Format chat history for AI context."""
        if not self.chat_history:
            return "No previous conversation."
        
        # Include last 10 messages for context
        recent_history = self.chat_history[-10:]
        formatted = []
        
        for msg in recent_history:
            role = "User" if msg['role'] == 'user' else "AI"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def _show_help(self):
        """Show chat help."""
        help_text = """
🤖 DevOS AI Chat Commands:
  help     - Show this help message
  clear    - Clear chat history
  stats    - Show session statistics
  save     - Save chat session to file
  exit     - Exit chat mode

💡 Tips:
- Ask about specific files: "What does main.py do?"
- Request code help: "How to implement authentication?"
- Get architecture insights: "Explain the project structure"
- Debug issues: "Why am I getting this error?"
"""
        click.echo(help_text)
    
    def _show_stats(self):
        """Show session statistics."""
        stats = {
            'session_id': self.session_id,
            'messages': len(self.chat_history),
            'user_messages': len([m for m in self.chat_history if m['role'] == 'user']),
            'ai_responses': len([m for m in self.chat_history if m['role'] == 'assistant']),
            'duration': (datetime.now() - datetime.strptime(self.session_id, "%Y%m%d_%H%M%S")).total_seconds() / 60
        }
        
        click.echo(f"""
📊 Session Statistics:
  Session ID: {stats['session_id']}
  Total Messages: {stats['messages']}
  User Messages: {stats['user_messages']}
  AI Responses: {stats['ai_responses']}
  Duration: {stats['duration']:.1f} minutes
""")
    
    def _save_session(self, command: str):
        """Save chat session to file."""
        try:
            # Extract filename from command
            parts = command.split()
            filename = parts[1] if len(parts) > 1 else f"chat_session_{self.session_id}.txt"
            
            # Format session for saving
            session_content = f"""DevOS AI Chat Session
Session ID: {self.session_id}
Project: {self.project_path}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}

"""
            
            for msg in self.chat_history:
                role = "USER" if msg['role'] == 'user' else "AI"
                timestamp = msg['timestamp'].strftime('%H:%M:%S')
                session_content += f"[{timestamp}] {role}:\n{msg['content']}\n\n"
            
            # Save to file
            output_path = self.project_path / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(session_content)
            
            show_success(f"Chat session saved to {output_path}")
            
        except Exception as e:
            show_warning(f"Failed to save session: {e}")


@click.command()
@click.option('--context', help='Chat context: security, architecture, performance, general')
@click.option('--history', is_flag=True, help='Load previous chat history')
@click.option('--save', help='Save chat session to file')
def ai_interactive_chat(context: Optional[str], history: bool, save: Optional[str]):
    """Start interactive AI chat with project context.
    
    Examples:
        ai-interactive-chat
        ai-interactive-chat --context security
        ai-interactive-chat --history
        ai-interactive-chat --save session.txt
    """
    
    async def run_chat():
        project_path = Path.cwd()
        chat_session = AIChatSession(project_path)
        
        # Initialize session
        await chat_session.initialize()
        
        # Load history if requested
        if history:
            # TODO: Implement history loading
            show_info("History loading not yet implemented")
        
        # Run chat loop
        await chat_session.chat_loop(context_focus=context)
        
        # Save session if requested
        if save:
            try:
                session_content = f"Chat Session - {datetime.now()}\n\n"
                for msg in chat_session.chat_history:
                    role = "USER" if msg['role'] == 'user' else "AI"
                    session_content += f"{role}: {msg['content']}\n\n"
                
                with open(save, 'w', encoding='utf-8') as f:
                    f.write(session_content)
                
                show_success(f"Chat saved to {save}")
            except Exception as e:
                show_warning(f"Failed to save chat: {e}")
    
    asyncio.run(run_chat())
