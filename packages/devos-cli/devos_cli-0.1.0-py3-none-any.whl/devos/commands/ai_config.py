"""AI configuration commands."""

import click
import asyncio
from pathlib import Path
from typing import Optional

from devos.core.progress import show_success, show_info, show_warning, show_operation_status
from devos.core.ai_config import get_ai_config_manager, initialize_ai_providers
from devos.core.ai import get_ai_service, AIServiceError


@click.group()
def ai_config():
    """Manage AI configuration and providers."""
    pass


@ai_config.command()
@click.argument('provider', type=click.Choice(['openai', 'anthropic', 'google', 'groq']))
@click.option('--key', help='API key (will prompt if not provided)')
def set_api_key(provider: str, key: Optional[str]):
    """Set API key for AI provider."""
    
    if not key:
        key = click.prompt(f'Enter {provider.upper()} API key', hide_input=True)
    
    config_manager = get_ai_config_manager()
    config_manager.set_api_key(provider, key)
    
    show_success(f"API key set for {provider}")
    
    # Reinitialize providers
    initialize_ai_providers()


@ai_config.command()
@click.argument('provider', type=click.Choice(['openai', 'anthropic', 'google', 'groq']))
def remove_api_key(provider: str):
    """Remove API key for AI provider."""
    
    config_manager = get_ai_config_manager()
    config_manager.remove_api_key(provider)
    
    show_success(f"API key removed for {provider}")


@ai_config.command()
def list_providers():
    """List AI providers and their status."""
    
    config_manager = get_ai_config_manager()
    providers = config_manager.list_providers()
    
    click.echo("AI Providers:")
    click.echo("=" * 30)
    
    for provider, has_key in providers.items():
        status = "✅ Configured" if has_key else "❌ Not configured"
        click.echo(f"{provider:12} {status}")


@ai_config.command()
def show_config():
    """Show current AI configuration."""
    
    config_manager = get_ai_config_manager()
    config = config_manager.load_config()
    
    click.echo("AI Configuration:")
    click.echo("=" * 30)
    click.echo(f"Default Provider: {config.default_provider}")
    click.echo(f"Default Model: {config.default_model}")
    click.echo(f"Cache Enabled: {config.cache_enabled}")
    click.echo(f"Max Context Size: {config.max_context_size}")
    click.echo(f"Rate Limit: {config.rate_limit_per_minute}/min")
    click.echo(f"Cost Limit: ${config.cost_limit_per_hour}/hour")
    click.echo(f"Temperature: {config.temperature}")
    click.echo(f"Max Tokens: {config.max_tokens}")


@ai_config.command()
@click.argument('setting')
@click.argument('value')
def set_setting(setting: str, value: str):
    """Set AI configuration setting."""
    
    config_manager = get_ai_config_manager()
    
    # Convert value to appropriate type
    if setting in ['cache_enabled']:
        value = value.lower() in ('true', '1', 'yes', 'on')
    elif setting in ['max_context_size', 'rate_limit_per_minute', 'max_tokens']:
        value = int(value)
    elif setting in ['cost_limit_per_hour', 'temperature']:
        value = float(value)
    
    try:
        config_manager.update_setting(setting, value)
        show_success(f"Setting updated: {setting} = {value}")
    except Exception as e:
        show_warning(f"Failed to update setting: {e}")


@ai_config.command()
@click.option('--provider', help='Test specific provider')
def test_connection(provider: Optional[str]):
    """Test AI provider connection."""
    
    async def _test_connection():
        try:
            ai_service = await get_ai_service()
            stats = await ai_service.get_usage_stats()
            
            click.echo("✅ AI service is working")
            click.echo(f"Providers: {ai_service.config.default_provider}")
            
            if stats:
                click.echo(f"Total requests: {stats.get('requests', 0)}")
                click.echo(f"Total cost: ${stats.get('total_cost', 0):.4f}")
            
        except AIServiceError as e:
            show_warning(f"AI service error: {e}")
        except Exception as e:
            show_warning(f"Connection test failed: {e}")
    
    asyncio.run(_test_connection())


@ai_config.command()
def clear_cache():
    """Clear AI response cache."""
    
    async def _clear_cache():
        try:
            ai_service = await get_ai_service()
            if ai_service.cache:
                await ai_service.cache.clear()
                show_success("AI cache cleared")
            else:
                show_info("Cache is disabled")
        except Exception as e:
            show_warning(f"Failed to clear cache: {e}")
    
    asyncio.run(_clear_cache())


@ai_config.command()
def usage_stats():
    """Show AI usage statistics."""
    
    async def _show_stats():
        try:
            ai_service = await get_ai_service()
            stats = await ai_service.get_usage_stats()
            
            click.echo("AI Usage Statistics:")
            click.echo("=" * 30)
            click.echo(f"Total Requests: {stats.get('requests', 0)}")
            click.echo(f"Tokens Used: {stats.get('tokens_used', 0)}")
            click.echo(f"Total Cost: ${stats.get('total_cost', 0):.4f}")
            click.echo(f"Cache Hits: {stats.get('cache_hits', 0)}")
            click.echo(f"Errors: {stats.get('errors', 0)}")
            
            # Provider breakdown
            by_provider = stats.get('by_provider', {})
            if by_provider:
                click.echo("\nBy Provider:")
                for provider, provider_stats in by_provider.items():
                    click.echo(f"  {provider}:")
                    click.echo(f"    Requests: {provider_stats.get('requests', 0)}")
                    click.echo(f"    Cost: ${provider_stats.get('cost', 0):.4f}")
            
            # Request type breakdown
            by_type = stats.get('by_request_type', {})
            if by_type:
                click.echo("\nBy Request Type:")
                for req_type, count in by_type.items():
                    click.echo(f"  {req_type}: {count}")
            
        except Exception as e:
            show_warning(f"Failed to get usage stats: {e}")
    
    asyncio.run(_show_stats())
