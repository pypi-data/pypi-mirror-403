"""Quick AI commands - Fast responses without deep analysis."""

import click
import asyncio
from pathlib import Path
from typing import Optional

from devos.core.progress import show_success, show_info, show_warning, show_operation_status
from devos.core.ai_config import get_ai_config_manager, initialize_ai_providers
from devos.core.ai import get_ai_service, AIServiceError, UserPreferences


@click.command()
@click.argument('prompt')
@click.option('--model', default='llama-3.1-8b-instant', help='AI model to use')
@click.option('--temp', type=float, default=0.7, help='Temperature (0.0-1.0)')
@click.option('--max-tokens', type=int, default=1000, help='Maximum tokens')
@click.option('--file', '-f', type=click.Path(exists=True), help='Include file context')
def quick_ai(prompt: str, model: str, temp: float, max_tokens: int, file: Optional[str]):
    """Ultra-fast AI assistance without deep project analysis.
    
    Perfect for quick questions, code snippets, and simple tasks.
    
    Examples:
        quick-ai "what is python?"
        quick-ai "create a hello world function" --file main.py
        quick-ai "how to sort a list in python?"
    """
    
    async def _run_quick_ai():
        try:
            ai_service = await get_ai_service()
            
            # Build simple prompt without deep analysis
            full_prompt = prompt
            
            if file:
                file_path = Path(file)
                file_content = file_path.read_text()
                full_prompt += f"\n\nFile: {file}\n```\n{file_content}\n```"
            
            response = await ai_service.generate_code(
                query=full_prompt,
                project_path=Path.cwd(),
                user_preferences=UserPreferences(
                    coding_style="clean",
                    preferred_patterns=[],
                    ai_model=model,
                    temperature=temp,
                    max_tokens=max_tokens
                ),
                provider_name="groq"
            )
            
            click.echo("⚡ Quick AI Response:")
            click.echo("=" * 50)
            click.echo(response.content)
            
            if response.tokens_used > 0:
                click.echo(f"\n⚡ Tokens: {response.tokens_used} | Cost: ${response.cost:.6f}")
                click.echo(f"🦊 Model: {model} | Ultra Fast!")
                
        except AIServiceError as e:
            show_warning(f"AI error: {e}")
        except Exception as e:
            show_warning(f"Command failed: {e}")
    
    asyncio.run(_run_quick_ai())
