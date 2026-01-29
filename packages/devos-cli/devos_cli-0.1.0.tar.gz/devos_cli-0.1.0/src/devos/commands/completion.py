"""Shell completion commands."""

import click
import platform
from pathlib import Path

from devos.core.completion import get_completion_script, install_completion, get_available_shells
from devos.core.progress import show_success, show_info, show_warning, show_operation_status


@click.command()
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish', 'powershell']))
@click.option('--install', is_flag=True, help='Install completion to shell config')
@click.pass_context
def completion(ctx, shell: str, install: bool):
    """Generate or install shell completion."""
    
    if install:
        success = install_completion(shell)
        if success:
            show_success(f"Completion installed for {shell}", 
                        f"Restart your shell or run 'source ~/.{shell}rc' to enable")
        else:
            show_operation_status(f"Failed to install completion for {shell}", False)
    else:
        script = get_completion_script(shell)
        click.echo(script)
        
        show_info(f"To install, run:", f"devos completion {shell} --install")


@click.command()
def shells():
    """List available shells for completion."""
    
    available = get_available_shells()
    
    if not available:
        show_warning("No supported shells found")
        return
    
    click.echo("Available shells for completion:")
    for shell in available:
        click.echo(f"  • {shell}")
    
    click.echo("\nInstallation:")
    click.echo("  devos completion <shell> --install")


@click.command()
@click.pass_context
def setup_completion(ctx):
    """Setup shell completion interactively."""
    
    click.echo("🔧 Shell Completion Setup")
    click.echo("=" * 30)
    
    # Detect current shell
    current_shell = _detect_current_shell()
    
    if current_shell:
        click.echo(f"Detected shell: {current_shell}")
        if click.confirm(f"Install completion for {current_shell}?"):
            success = install_completion(current_shell)
            if success:
                show_success(f"Completion installed for {current_shell}")
                _show_shell_instructions(current_shell)
            else:
                show_operation_status("Failed to install completion", False)
            return
    
    # Manual selection
    available = get_available_shells()
    if not available:
        show_warning("No supported shells found")
        return
    
    click.echo("\nAvailable shells:")
    for i, shell in enumerate(available, 1):
        click.echo(f"{i}. {shell}")
    
    choice = click.prompt("Select shell", type=click.IntRange(1, len(available)))
    selected_shell = available[choice - 1]
    
    success = install_completion(selected_shell)
    if success:
        show_success(f"Completion installed for {selected_shell}")
        _show_shell_instructions(selected_shell)
    else:
        show_operation_status("Failed to install completion", False)


def _detect_current_shell() -> str:
    """Detect the current shell."""
    
    import os
    
    # Check SHELL environment variable
    shell_path = os.environ.get('SHELL', '')
    if 'bash' in shell_path:
        return 'bash'
    elif 'zsh' in shell_path:
        return 'zsh'
    elif 'fish' in shell_path:
        return 'fish'
    
    # Windows detection
    if platform.system() == 'Windows':
        return 'powershell'
    
    return None


def _show_shell_instructions(shell: str) -> None:
    """Show shell-specific instructions."""
    
    if shell == 'bash':
        click.echo("\nTo enable completion:")
        click.echo("  source ~/.bashrc")
        click.echo("  Or restart your terminal")
    elif shell == 'zsh':
        click.echo("\nTo enable completion:")
        click.echo("  source ~/.zshrc")
        click.echo("  Or restart your terminal")
    elif shell == 'fish':
        click.echo("\nTo enable completion:")
        click.echo("  Restart your fish shell")
        click.echo("  Or run: source ~/.config/fish/config.fish")
    elif shell == 'powershell':
        click.echo("\nTo enable completion:")
        click.echo("  Restart PowerShell")
        click.echo("  Or run: . $PROFILE")
