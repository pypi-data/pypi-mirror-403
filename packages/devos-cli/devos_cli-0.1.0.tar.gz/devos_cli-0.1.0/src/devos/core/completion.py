"""Shell auto-completion support for DevOS CLI."""

import click
from pathlib import Path
from typing import List, Tuple


def get_completion_script(shell: str) -> str:
    """Generate completion script for the specified shell."""
    
    if shell == 'bash':
        return _get_bash_completion()
    elif shell == 'zsh':
        return _get_zsh_completion()
    elif shell == 'fish':
        return _get_fish_completion()
    elif shell == 'powershell':
        return _get_powershell_completion()
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def _get_bash_completion() -> str:
    """Generate bash completion script."""
    
    return '''# DevOS bash completion
_devos_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        opts="init track env report ship config interactive now done status today projects recent setup help"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
    
    # Subcommands based on main command
    case "${prev}" in
        track|t|time)
            opts="start stop status list"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        env|e|environment)
            opts="set get list delete generate-example export"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        report|r|stats)
            opts="weekly summary projects"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        ship|s|deploy|release)
            opts="release changelog version"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        config|c|settings)
            opts="show set reset init"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        *)
            # Options and file completion
            if [[ "${cur}" == -* ]]; then
                opts="--help --verbose --version"
                COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            else
                # Default to file completion
                COMPREPLY=( $(compgen -f -- ${cur}) )
            fi
            ;;
    esac
}

complete -F _devos_completion devos
'''


def _get_zsh_completion() -> str:
    """Generate zsh completion script."""
    
    return '''#compdef devos

_devos() {
    local -a commands
    commands=(
        'init:Initialize a new project'
        'track:Time tracking commands'
        'env:Environment variable management'
        'report:Generate reports'
        'ship:Release management'
        'config:Configuration management'
        'interactive:Interactive mode'
        'now:Quick start tracking'
        'done:Quick stop tracking'
        'status:Show status overview'
        'today:Show today\\'s summary'
        'projects:List projects'
        'recent:Show recent activity'
        'setup:Quick setup wizard'
        'help:Show help'
    )
    
    if [[ CURRENT -eq 1 ]]; then
        _describe 'command' commands
        return
    fi
    
    case $words[1] in
        track|t|time)
            local -a track_commands
            track_commands=(
                'start:Start a new session'
                'stop:Stop current session'
                'status:Show tracking status'
                'list:List sessions'
            )
            _describe 'track command' track_commands
            ;;
        env|e|environment)
            local -a env_commands
            env_commands=(
                'set:Set environment variable'
                'get:Get environment variable'
                'list:List variables'
                'delete:Delete variable'
                'generate-example:Generate .env.example'
                'export:Export for shell'
            )
            _describe 'env command' env_commands
            ;;
        report|r|stats)
            local -a report_commands
            report_commands=(
                'weekly:Weekly report'
                'summary:Summary report'
                'projects:Project breakdown'
            )
            _describe 'report command' report_commands
            ;;
        ship|s|deploy|release)
            local -a ship_commands
            ship_commands=(
                'release:Create release'
                'changelog:Generate changelog'
                'version:Show version'
            )
            _describe 'ship command' ship_commands
            ;;
        config|c|settings)
            local -a config_commands
            config_commands=(
                'show:Show configuration'
                'set:Set configuration value'
                'reset:Reset configuration'
                'init:Initialize configuration'
            )
            _describe 'config command' config_commands
            ;;
    esac
    
    # File completion
    _files
}

_devos "$@"
'''


def _get_fish_completion() -> str:
    """Generate fish completion script."""
    
    return '''# DevOS fish completion

function __devos_commands
    echo init track env report ship config interactive now done status today projects recent setup help
end

function __devos_track_commands
    echo start stop status list
end

function __devos_env_commands
    echo set get list delete generate-example export
end

function __devos_report_commands
    echo weekly summary projects
end

function __devos_ship_commands
    echo release changelog version
end

function __devos_config_commands
    echo show set reset init
end

function __devos_complete
    set -l cmd (commandline -opc)
    set -l cursor (commandline -C)

    if test (count $cmd) -eq 1
        __devos_commands
    else
        switch $cmd[2]
            case track t time
                __devos_track_commands
            case env e environment
                __devos_env_commands
            case report r stats
                __devos_report_commands
            case ship s deploy release
                __devos_ship_commands
            case config c settings
                __devos_config_commands
        end
    end
end

complete -c devos -f -a '(__devos_complete)'
'''


def _get_powershell_completion() -> str:
    """Generate PowerShell completion script."""
    
    return '''# DevOS PowerShell completion

Register-ArgumentCompleter -Native -CommandName devos -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    
    $commands = @(
        'init', 'track', 'env', 'report', 'ship', 'config', 
        'interactive', 'now', 'done', 'status', 'today', 
        'projects', 'recent', 'setup', 'help'
    )
    
    $trackCommands = @('start', 'stop', 'status', 'list')
    $envCommands = @('set', 'get', 'list', 'delete', 'generate-example', 'export')
    $reportCommands = @('weekly', 'summary', 'projects')
    $shipCommands = @('release', 'changelog', 'version')
    $configCommands = @('show', 'set', 'reset', 'init')
    
    $commandElements = $commandAst.CommandElements
    $commandCount = $commandElements.Count
    
    if ($commandCount -eq 1) {
        $commands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
    } elseif ($commandCount -eq 2) {
        $mainCommand = $commandElements[1].Value
        switch ($mainCommand) {
            { $_ -in @('track', 't', 'time') } {
                $trackCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            { $_ -in @('env', 'e', 'environment') } {
                $envCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            { $_ -in @('report', 'r', 'stats') } {
                $reportCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            { $_ -in @('ship', 's', 'deploy', 'release') } {
                $shipCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
            { $_ -in @('config', 'c', 'settings') } {
                $configCommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
                    [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
                }
            }
        }
    }
}
'''


def install_completion(shell: str) -> bool:
    """Install completion for the specified shell."""
    
    try:
        script = get_completion_script(shell)
        
        if shell == 'bash':
            completion_file = Path.home() / '.bash_completion.d' / 'devos'
            completion_file.parent.mkdir(exist_ok=True)
            completion_file.write_text(script)
            
            # Add to .bashrc if not already there
            bashrc = Path.home() / '.bashrc'
            if bashrc.exists():
                content = bashrc.read_text()
                if 'devos completion' not in content:
                    bashrc.write_text(content + '\n# DevOS completion\nsource ~/.bash_completion.d/devos\n')
        
        elif shell == 'zsh':
            completion_file = Path.home() / '.zsh' / '_devos'
            completion_file.parent.mkdir(exist_ok=True)
            completion_file.write_text(script)
            
            # Add to .zshrc if not already there
            zshrc = Path.home() / '.zshrc'
            if zshrc.exists():
                content = zshrc.read_text()
                if 'devos completion' not in content:
                    zshrc.write_text(content + '\n# DevOS completion\nfpath+=~/.zsh\nautoload -U compinit && compinit\n')
        
        elif shell == 'fish':
            completion_file = Path.home() / '.config' / 'fish' / 'completions' / 'devos.fish'
            completion_file.parent.mkdir(parents=True, exist_ok=True)
            completion_file.write_text(script)
        
        elif shell == 'powershell':
            # For PowerShell, we need to add to profile
            script = get_completion_script('powershell')
            
            # Get PowerShell profile path
            import subprocess
            result = subprocess.run(['powershell', '-Command', 'echo $PROFILE'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                profile_path = Path(result.stdout.strip())
                profile_path.parent.mkdir(parents=True, exist_ok=True)
                
                if profile_path.exists():
                    content = profile_path.read_text()
                    if 'DevOS completion' not in content:
                        profile_path.write_text(content + '\n# DevOS completion\n' + script + '\n')
                else:
                    profile_path.write_text('# DevOS completion\n' + script + '\n')
        
        return True
        
    except Exception:
        return False


def get_available_shells() -> List[str]:
    """Get list of available shells for completion."""
    
    shells = ['bash', 'zsh', 'fish', 'powershell']
    available = []
    
    for shell in shells:
        if shell == 'bash' and (Path('/bin/bash').exists() or Path('/usr/bin/bash').exists()):
            available.append(shell)
        elif shell == 'zsh' and (Path('/bin/zsh').exists() or Path('/usr/bin/zsh').exists()):
            available.append(shell)
        elif shell == 'fish' and (Path('/usr/bin/fish').exists() or Path('/bin/fish').exists()):
            available.append(shell)
        elif shell == 'powershell':
            # Check if running on Windows
            import platform
            if platform.system() == 'Windows':
                available.append(shell)
    
    return available
