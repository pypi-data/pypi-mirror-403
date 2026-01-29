"""Project initialization command."""

import click
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from devos.core.database import Database


@click.command()
@click.argument('template_name', required=False)
@click.option('--name', '-n', help='Project name')
@click.option('--path', '-p', help='Project path (default: current directory)')
@click.option('--language', '-l', help='Programming language')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.pass_context
def init(ctx, template_name: str, name: str, path: str, language: str, interactive: bool):
    """Initialize a new project with templates."""
    
    config = ctx.obj['config']
    db = ctx.obj['db']
    
    # Interactive mode if no template specified or interactive flag
    if interactive or not template_name:
        return _interactive_init(config, db)
    
    # Parse template name
    if '-' in template_name:
        lang, project_type = template_name.split('-', 1)
    else:
        lang = template_name
        project_type = 'basic'
    
    # Set defaults
    if not name:
        name = f"my-{template_name}-project"
    
    if not path:
        path = Path.cwd() / name
    
    if not language:
        language = lang
    
    # Convert to absolute path
    project_path = Path(path).resolve()
    
    # Check if directory exists
    if project_path.exists() and any(project_path.iterdir()):
        if not click.confirm(f"Directory '{project_path}' is not empty. Continue?"):
            click.echo("Initialization cancelled.")
            return
    
    # Create project
    try:
        project_id = _create_project(config, db, project_path, name, language, project_type)
        click.echo(f"✓ Project '{name}' created at {project_path}")
        click.echo(f"✓ Project ID: {project_id}")
        
        # Show next steps
        click.echo("\nNext steps:")
        click.echo(f"  cd {project_path}")
        click.echo("  devos track start")
        
    except Exception as e:
        click.echo(f"Error creating project: {e}", err=True)


def _interactive_init(config: Any, db: Database) -> None:
    """Interactive project initialization."""
    click.echo("🚀 DevOS Project Initialization")
    click.echo("=" * 40)
    
    # Project name
    name = click.prompt("Project name", default="my-project")
    
    # Language
    languages = ['python', 'javascript', 'typescript', 'go', 'rust']
    language = click.prompt(
        "Programming language",
        type=click.Choice(languages),
        default=config.default_language
    )
    
    # Project type
    project_types = {
        'python': ['basic', 'api', 'cli', 'web'],
        'javascript': ['basic', 'api', 'web', 'cli'],
        'typescript': ['basic', 'api', 'web', 'cli'],
        'go': ['basic', 'api', 'cli'],
        'rust': ['basic', 'cli', 'api']
    }
    
    available_types = project_types.get(language, ['basic'])
    project_type = click.prompt(
        "Project type",
        type=click.Choice(available_types),
        default='basic'
    )
    
    # Path
    default_path = Path.cwd() / name
    path_str = click.prompt("Project path", default=str(default_path))
    project_path = Path(path_str).resolve()
    
    # Confirm
    click.echo(f"\nProject summary:")
    click.echo(f"  Name: {name}")
    click.echo(f"  Language: {language}")
    click.echo(f"  Type: {project_type}")
    click.echo(f"  Path: {project_path}")
    
    if not click.confirm("\nCreate project?"):
        click.echo("Initialization cancelled.")
        return
    
    # Create project
    try:
        project_id = _create_project(config, db, project_path, name, language, project_type)
        click.echo(f"\n✓ Project '{name}' created at {project_path}")
        click.echo(f"✓ Project ID: {project_id}")
        
        # Show next steps
        click.echo("\nNext steps:")
        click.echo(f"  cd {project_path}")
        click.echo("  devos track start")
        
    except Exception as e:
        click.echo(f"Error creating project: {e}", err=True)


def _create_project(config: Any, db: Database, project_path: Path, name: str, language: str, project_type: str) -> str:
    """Create a new project."""
    # Generate project ID
    project_id = f"{language}_{name}_{int(datetime.now().timestamp())}"
    
    # Create directory
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Generate project files
    _generate_project_files(project_path, name, language, project_type)
    
    # Initialize git if not already a git repo
    if not (project_path / '.git').exists():
        try:
            subprocess.run(['git', 'init'], cwd=project_path, check=True, capture_output=True)
            subprocess.run(['git', 'add', '.'], cwd=project_path, check=True, capture_output=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=project_path, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Git not available or failed - continue without git
            pass
    
    # Save to database
    db.create_project(project_id, name, str(project_path), language)
    
    return project_id


def _generate_project_files(project_path: Path, name: str, language: str, project_type: str) -> None:
    """Generate project files based on language and type."""
    
    if language == 'python':
        _generate_python_project(project_path, name, project_type)
    elif language == 'javascript':
        _generate_javascript_project(project_path, name, project_type)
    elif language == 'typescript':
        _generate_typescript_project(project_path, name, project_type)
    elif language == 'go':
        _generate_go_project(project_path, name, project_type)
    elif language == 'rust':
        _generate_rust_project(project_path, name, project_type)
    else:
        _generate_basic_project(project_path, name, language)


def _generate_python_project(project_path: Path, name: str, project_type: str) -> None:
    """Generate Python project files."""
    
    # Basic structure
    (project_path / 'src').mkdir(exist_ok=True)
    (project_path / 'tests').mkdir(exist_ok=True)
    
    # pyproject.toml
    pyproject_content = f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = ""
authors = [{{name = "Developer"}}]
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-dir]
"" = "src"
'''
    
    (project_path / 'pyproject.toml').write_text(pyproject_content)
    
    # README.md
    readme_content = f'''# {name}

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

TODO: Add usage instructions

## Development

```bash
# Run tests
pytest

# Format code
black src/
```
'''
    
    (project_path / 'README.md').write_text(readme_content)
    
    # .gitignore
    gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local
.env.*.local
'''
    
    (project_path / '.gitignore').write_text(gitignore_content)
    
    # .env.example
    env_example = '''# Environment variables
DEBUG=true
PORT=8000
'''
    
    (project_path / '.env.example').write_text(env_example)
    
    # Main module
    if project_type == 'api':
        _generate_python_api(project_path, name)
    elif project_type == 'cli':
        _generate_python_cli(project_path, name)
    elif project_type == 'web':
        _generate_python_web(project_path, name)
    else:
        _generate_python_basic(project_path, name)


def _generate_python_basic(project_path: Path, name: str) -> None:
    """Generate basic Python project."""
    main_content = f'''"""Main module for {name}."""

def hello():
    """Say hello."""
    return "Hello, World!"


if __name__ == "__main__":
    print(hello())
'''
    
    (project_path / 'src' / f'{name.replace("-", "_")}.py').write_text(main_content)


def _generate_python_api(project_path: Path, name: str) -> None:
    """Generate Python API project."""
    main_content = f'''"""FastAPI application for {name}."""

from fastapi import FastAPI

app = FastAPI(title="{name}")


@app.get("/")
async def root():
    return {{"message": "Hello World"}}


@app.get("/health")
async def health():
    return {{"status": "ok"}}
'''
    
    (project_path / 'src' / 'main.py').write_text(main_content)
    
    # Add FastAPI to dependencies
    pyproject_path = project_path / 'pyproject.toml'
    content = pyproject_path.read_text()
    content = content.replace(
        'dependencies = [',
        '''dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0",
'''
    )
    pyproject_path.write_text(content)


def _generate_python_cli(project_path: Path, name: str) -> None:
    """Generate Python CLI project."""
    main_content = f'''"""CLI application for {name}."""

import click


@click.group()
def cli():
    """{name} CLI."""
    pass


@cli.command()
def hello():
    """Say hello."""
    click.echo("Hello, World!")


if __name__ == "__main__":
    cli()
'''
    
    (project_path / 'src' / 'cli.py').write_text(main_content)
    
    # Add Click to dependencies
    pyproject_path = project_path / 'pyproject.toml'
    content = pyproject_path.read_text()
    content = content.replace(
        'dependencies = [',
        '''dependencies = [
    "click>=8.0.0",
'''
    )
    pyproject_path.write_text(content)


def _generate_python_web(project_path: Path, name: str) -> None:
    """Generate Python web project."""
    main_content = f'''"""Flask web application for {name}."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True)
'''
    
    (project_path / 'src' / 'app.py').write_text(main_content)
    
    # Add Flask to dependencies
    pyproject_path = project_path / 'pyproject.toml'
    content = pyproject_path.read_text()
    content = content.replace(
        'dependencies = [',
        '''dependencies = [
    "flask>=2.0.0",
'''
    )
    pyproject_path.write_text(content)


def _generate_javascript_project(project_path: Path, name: str, project_type: str) -> None:
    """Generate JavaScript project files."""
    # package.json
    package_content = f'''{{
  "name": "{name}",
  "version": "1.0.0",
  "description": "",
  "main": "src/index.js",
  "scripts": {{
    "start": "node src/index.js",
    "test": "jest",
    "dev": "nodemon src/index.js"
  }},
  "keywords": [],
  "author": "",
  "license": "MIT",
  "devDependencies": {{
    "jest": "^29.0.0",
    "nodemon": "^3.0.0"
  }}
}}
'''
    
    (project_path / 'package.json').write_text(package_content)
    
    # Basic structure
    (project_path / 'src').mkdir(exist_ok=True)
    (project_path / 'tests').mkdir(exist_ok=True)
    
    # README.md
    readme_content = f'''# {name}

## Installation

```bash
npm install
```

## Usage

```bash
npm start
```

## Development

```bash
npm run dev
```
'''
    
    (project_path / 'README.md').write_text(readme_content)
    
    # .gitignore
    gitignore_content = '''# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
'''
    
    (project_path / '.gitignore').write_text(gitignore_content)
    
    # .env.example
    env_example = '''# Environment variables
NODE_ENV=development
PORT=3000
'''
    
    (project_path / '.env.example').write_text(env_example)
    
    # Main file
    main_content = f'''// Main entry point for {name}

console.log('Hello, World!');
'''
    
    (project_path / 'src' / 'index.js').write_text(main_content)


def _generate_typescript_project(project_path: Path, name: str, project_type: str) -> None:
    """Generate TypeScript project files."""
    # package.json
    package_content = f'''{{
  "name": "{name}",
  "version": "1.0.0",
  "description": "",
  "main": "dist/index.js",
  "scripts": {{
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.ts",
    "test": "jest"
  }},
  "keywords": [],
  "author": "",
  "license": "MIT",
  "devDependencies": {{
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "ts-node": "^10.0.0",
    "jest": "^29.0.0",
    "@types/jest": "^29.0.0"
  }}
}}
'''
    
    (project_path / 'package.json').write_text(package_content)
    
    # tsconfig.json
    tsconfig_content = '''{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
'''
    
    (project_path / 'tsconfig.json').write_text(tsconfig_content)
    
    # Basic structure
    (project_path / 'src').mkdir(exist_ok=True)
    (project_path / 'tests').mkdir(exist_ok=True)
    
    # README.md
    readme_content = f'''# {name}

## Installation

```bash
npm install
```

## Usage

```bash
npm run build
npm start
```

## Development

```bash
npm run dev
```
'''
    
    (project_path / 'README.md').write_text(readme_content)
    
    # .gitignore
    gitignore_content = '''# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# TypeScript
dist/
*.tsbuildinfo

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
'''
    
    (project_path / '.gitignore').write_text(gitignore_content)
    
    # .env.example
    env_example = '''# Environment variables
NODE_ENV=development
PORT=3000
'''
    
    (project_path / '.env.example').write_text(env_example)
    
    # Main file
    main_content = f'''// Main entry point for {name}

console.log('Hello, World!');
'''
    
    (project_path / 'src' / 'index.ts').write_text(main_content)


def _generate_go_project(project_path: Path, name: str, project_type: str) -> None:
    """Generate Go project files."""
    # go.mod
    try:
        subprocess.run(['go', 'mod', 'init', name], cwd=project_path, check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Go not available - create basic files anyway
        pass
    
    # Basic structure
    (project_path / 'cmd').mkdir(exist_ok=True)
    (project_path / 'internal').mkdir(exist_ok=True)
    
    # README.md
    readme_content = f'''# {name}

## Installation

```bash
go build -o bin/{name} ./cmd/{name}
```

## Usage

```bash
./bin/{name}
```
'''
    
    (project_path / 'README.md').write_text(readme_content)
    
    # .gitignore
    gitignore_content = '''# Go
*.exe
*.exe~
*.dll
*.so
*.dylib
bin/
*.test
*.out
go.work

# IDE
.vscode/
.idea/
*.swp
*.swo
'''
    
    (project_path / '.gitignore').write_text(gitignore_content)
    
    # Main file
    main_content = f'''package main

import "fmt"

func main() {{
    fmt.Println("Hello, World!")
}}
'''
    
    (project_path / 'cmd' / f'{name.replace("-", "_")}.go').write_text(main_content)


def _generate_rust_project(project_path: Path, name: str, project_type: str) -> None:
    """Generate Rust project files."""
    # Cargo.toml
    cargo_content = f'''[package]
name = "{name.replace("-", "_")}"
version = "0.1.0"
edition = "2021"

[dependencies]
'''
    
    (project_path / 'Cargo.toml').write_text(cargo_content)
    
    # src directory
    (project_path / 'src').mkdir(exist_ok=True)
    
    # README.md
    readme_content = f'''# {name}

## Installation

```bash
cargo build --release
```

## Usage

```bash
cargo run
```
'''
    
    (project_path / 'README.md').write_text(readme_content)
    
    # .gitignore
    gitignore_content = '''# Rust
/target/
**/*.rs.bk
Cargo.lock

# IDE
.vscode/
.idea/
*.swp
*.swo
'''
    
    (project_path / '.gitignore').write_text(gitignore_content)
    
    # Main file
    main_content = f'''fn main() {{
    println!("Hello, World!");
}}
'''
    
    (project_path / 'src' / 'main.rs').write_text(main_content)


def _generate_basic_project(project_path: Path, name: str, language: str) -> None:
    """Generate basic project structure for unsupported languages."""
    # Basic structure
    (project_path / 'src').mkdir(exist_ok=True)
    
    # README.md
    readme_content = f'''# {name}

A {language} project.

## Usage

TODO: Add usage instructions
'''
    
    (project_path / 'README.md').write_text(readme_content)
    
    # .gitignore
    gitignore_content = '''# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local
'''
    
    (project_path / '.gitignore').write_text(gitignore_content)
    
    # .env.example
    env_example = '''# Environment variables
# TODO: Add your environment variables here
'''
    
    (project_path / '.env.example').write_text(env_example)
    
    # Basic main file
    main_content = f'''// Main file for {name}
// TODO: Add your code here

console.log("Hello, World!");
'''
    
    (project_path / 'src' / 'main.{_get_file_extension(language)}').write_text(main_content)


def _get_file_extension(language: str) -> str:
    """Get file extension for language."""
    extensions = {
        'python': 'py',
        'javascript': 'js',
        'typescript': 'ts',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'c++': 'cpp',
        'ruby': 'rb',
        'php': 'php',
        'swift': 'swift',
        'kotlin': 'kt',
        'scala': 'scala',
        'r': 'r',
        'dart': 'dart'
    }
    return extensions.get(language.lower(), 'txt')
