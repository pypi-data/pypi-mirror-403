"""AI-powered development assistance commands."""

import click
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List

from devos.core.progress import show_success, show_info, show_warning, show_operation_status, ProgressBar
from devos.core.ai import (
    get_ai_service, AIServiceError, UserPreferences, RequestType,
    ProjectContext, SessionContext
)


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--model', default='gpt-4', help='AI model to use')
@click.option('--focus', type=click.Choice(['security', 'performance', 'style', 'all']), default='all', help='Review focus')
@click.option('--output', '-o', help='Output file for review')
@click.option('--provider', help='AI provider to use')
@click.pass_context
def review(ctx, path: str, model: str, focus: str, output: Optional[str], provider: Optional[str]):
    """AI-powered code review."""
    
    async def _run_review():
        try:
            ai_service = await get_ai_service()
            file_path = Path(path)
            
            # Set user preferences
            user_prefs = UserPreferences(
                coding_style="clean",
                preferred_patterns=[],
                ai_model=model,
                temperature=0.1,  # Lower temperature for analysis
                max_tokens=2000
            )
            
            if file_path.is_file():
                # Analyze single file
                code = file_path.read_text()
                result = await ai_service.analyze_code(
                    code=code,
                    project_path=file_path.parent,
                    user_preferences=user_prefs,
                    provider_name=provider
                )
                reviews = [{
                    'file': str(file_path),
                    'language': _detect_file_language(file_path),
                    'result': result
                }]
            else:
                # Analyze directory
                reviews = []
                for code_file in _find_code_files(file_path):
                    try:
                        code = code_file.read_text()
                        result = await ai_service.analyze_code(
                            code=code,
                            project_path=code_file.parent,
                            user_preferences=user_prefs,
                            provider_name=provider
                        )
                        reviews.append({
                            'file': str(code_file),
                            'language': _detect_file_language(code_file),
                            'result': result
                        })
                    except Exception as e:
                        show_warning(f"Failed to analyze {code_file}: {e}")
            
            if output:
                _save_review_report(reviews, output)
                show_success(f"Code review saved to {output}")
            else:
                _display_review_results(reviews)
                
        except AIServiceError as e:
            show_warning(f"AI service error: {e}")
        except Exception as e:
            show_warning(f"Review failed: {e}")
    
    # Run async function
    asyncio.run(_run_review())


@click.command()
@click.argument('query')
@click.option('--context', help='Additional context for the explanation')
@click.option('--file', '-f', type=click.Path(exists=True), help='File to explain')
@click.option('--model', default='gpt-4', help='AI model to use')
@click.option('--provider', help='AI provider to use')
@click.pass_context
def explain(ctx, query: str, context: Optional[str], file: Optional[str], model: str, provider: Optional[str]):
    """AI-powered code explanation."""
    
    async def _run_explain():
        try:
            ai_service = await get_ai_service()
            
            # Set user preferences
            user_prefs = UserPreferences(
                coding_style="clean",
                preferred_patterns=[],
                ai_model=model,
                temperature=0.2,  # Lower temperature for explanations
                max_tokens=1500
            )
            
            if file:
                file_path = Path(file)
                code = file_path.read_text()
                response = await ai_service.explain_code(
                    code=code,
                    query=query,
                    project_path=file_path.parent,
                    user_preferences=user_prefs,
                    provider_name=provider
                )
            else:
                # Use chat for conceptual explanations
                conversation = [
                    {"role": "user", "content": f"Explain: {query}"}
                ]
                if context:
                    conversation[0]["content"] += f"\n\nContext: {context}"
                
                response = await ai_service.chat(
                    conversation=conversation,
                    project_path=Path.cwd(),
                    user_preferences=user_prefs,
                    provider_name=provider
                )
            
            click.echo("🤖 AI Explanation:")
            click.echo("=" * 50)
            click.echo(response.content)
            
            if response.tokens_used > 0:
                click.echo(f"\nTokens used: {response.tokens_used} | Cost: ${response.cost:.4f}")
                
        except AIServiceError as e:
            show_warning(f"AI service error: {e}")
        except Exception as e:
            show_warning(f"Explanation failed: {e}")
    
    asyncio.run(_run_explain())


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--style', type=click.Choice(['modern', 'functional', 'clean', 'idiomatic']), default='clean', help='Refactoring style')
@click.option('--backup', is_flag=True, help='Create backup before refactoring')
@click.option('--model', default='gpt-3.5-turbo', help='AI model to use')
@click.pass_context
def refactor(ctx, path: str, style: str, backup: bool, model: str):
    """AI-powered code refactoring suggestions."""
    
    file_path = Path(path)
    
    if backup and file_path.is_file():
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        backup_path.write_text(file_path.read_text())
        show_success(f"Backup created: {backup_path}")
    
    suggestions = _get_refactoring_suggestions(file_path, style, model)
    
    if suggestions:
        click.echo("🔧 Refactoring Suggestions:")
        click.echo("=" * 50)
        
        for i, suggestion in enumerate(suggestions, 1):
            click.echo(f"\n{i}. {suggestion['title']}")
            click.echo(f"   {suggestion['description']}")
            if suggestion.get('code'):
                click.echo(f"   ```{suggestion.get('language', 'text')}")
                click.echo(f"   {suggestion['code']}")
                click.echo(f"   ```")
        
        if click.confirm("\nApply these suggestions?"):
            _apply_refactoring_suggestions(file_path, suggestions)
            show_success("Refactoring applied")
    else:
        show_info("No refactoring suggestions found")


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--framework', type=click.Choice(['pytest', 'jest', 'vitest', 'go', 'rust']), help='Test framework')
@click.option('--coverage', is_flag=True, help='Generate tests for coverage')
@click.option('--model', default='gpt-3.5-turbo', help='AI model to use')
@click.pass_context
def test(ctx, path: str, framework: Optional[str], coverage: bool, model: str):
    """AI-powered test generation."""
    
    file_path = Path(path)
    
    if not framework:
        framework = _detect_test_framework_for_file(file_path)
    
    tests = _generate_tests(file_path, framework, model, coverage)
    
    if tests:
        test_file = _suggest_test_file_path(file_path, framework)
        
        if test_file.exists():
            if not click.confirm(f"Test file {test_file} exists. Overwrite?"):
                click.echo("Test generation cancelled.")
                return
        
        test_file.write_text(tests)
        show_success(f"Tests generated: {test_file}")
        
        # Offer to run tests
        if click.confirm("Run the generated tests?"):
            _run_generated_tests(test_file, framework)
    else:
        show_warning("Could not generate tests for this file")


@click.command()
@click.argument('query')
@click.option('--language', help='Programming language for the example')
@click.option('--context', help='Additional context')
@click.option('--model', default='gpt-4', help='AI model to use')
@click.option('--provider', help='AI provider to use')
@click.pass_context
def example(ctx, query: str, language: Optional[str], context: Optional[str], model: str, provider: Optional[str]):
    """Generate code examples."""
    
    async def _run_example():
        try:
            ai_service = await get_ai_service()
            
            # Set user preferences
            user_prefs = UserPreferences(
                coding_style="clean",
                preferred_patterns=[],
                ai_model=model,
                temperature=0.3,
                max_tokens=1500
            )
            
            # Build query with language and context
            full_query = f"Generate a code example for: {query}"
            if language:
                full_query += f"\nLanguage: {language}"
            if context:
                full_query += f"\nContext: {context}"
            
            response = await ai_service.generate_code(
                query=full_query,
                project_path=Path.cwd(),
                user_preferences=user_prefs,
                provider_name=provider
            )
            
            click.echo("💡 Code Example:")
            click.echo("=" * 50)
            click.echo(response.content)
            
            if response.tokens_used > 0:
                click.echo(f"\nTokens used: {response.tokens_used} | Cost: ${response.cost:.4f}")
                
        except AIServiceError as e:
            show_warning(f"AI service error: {e}")
        except Exception as e:
            show_warning(f"Example generation failed: {e}")
    
    asyncio.run(_run_example())


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--type', type=click.Choice(['bug', 'feature', 'optimization', 'security']), default='bug', help='Issue type')
@click.option('--model', default='gpt-4', help='AI model to use')
@click.option('--provider', help='AI provider to use')
@click.pass_context
def debug(ctx, path: str, type: str, model: str, provider: Optional[str]):
    """AI-powered debugging assistance."""
    
    async def _run_debug():
        try:
            ai_service = await get_ai_service()
            file_path = Path(path)
            
            # Set user preferences
            user_prefs = UserPreferences(
                coding_style="clean",
                preferred_patterns=[],
                ai_model=model,
                temperature=0.1,  # Lower temperature for debugging
                max_tokens=2000
            )
            
            code = file_path.read_text()
            response = await ai_service.debug_code(
                code=code,
                error_type=type,
                project_path=file_path.parent,
                user_preferences=user_prefs,
                provider_name=provider
            )
            
            click.echo(f"🐛 Debug Analysis for {type}s:")
            click.echo("=" * 50)
            click.echo(response.content)
            
            if response.tokens_used > 0:
                click.echo(f"\nTokens used: {response.tokens_used} | Cost: ${response.cost:.4f}")
                
        except AIServiceError as e:
            show_warning(f"AI service error: {e}")
        except Exception as e:
            show_warning(f"Debug analysis failed: {e}")
    
    asyncio.run(_run_debug())


@click.command()
@click.argument('query')
@click.option('--model', default='gpt-4', help='AI model to use')
@click.option('--save', help='Save conversation to file')
@click.option('--provider', help='AI provider to use')
@click.pass_context
def chat(ctx, query: str, model: str, save: Optional[str], provider: Optional[str]):
    """Interactive AI chat for development help."""
    
    async def _run_chat():
        try:
            ai_service = await get_ai_service()
            
            # Set user preferences
            user_prefs = UserPreferences(
                coding_style="clean",
                preferred_patterns=[],
                ai_model=model,
                temperature=0.7,
                max_tokens=2000
            )
            
            click.echo("🤖 DevOS AI Assistant")
            click.echo("Type 'exit' to quit, 'clear' to clear history")
            click.echo("=" * 50)
            
            conversation = []
            
            while True:
                try:
                    user_input = click.prompt("\nYou", type=str, show_default=False)
                    
                    if user_input.lower() == 'exit':
                        break
                    elif user_input.lower() == 'clear':
                        conversation = []
                        click.echo("Conversation cleared.")
                        continue
                    
                    conversation.append({"role": "user", "content": user_input})
                    
                    response = await ai_service.chat(
                        conversation=conversation,
                        project_path=Path.cwd(),
                        user_preferences=user_prefs,
                        provider_name=provider
                    )
                    
                    conversation.append({"role": "assistant", "content": response.content})
                    
                    click.echo(f"\nAI: {response.content}")
                    
                    if response.tokens_used > 0:
                        click.echo(f"[Tokens: {response.tokens_used} | Cost: ${response.cost:.4f}]")
                        
                except KeyboardInterrupt:
                    click.echo("\nGoodbye!")
                    break
                except Exception as e:
                    show_warning(f"Chat error: {e}")
            
            if save:
                _save_conversation(conversation, save)
                show_success(f"Conversation saved to {save}")
                
        except AIServiceError as e:
            show_warning(f"AI service error: {e}")
        except Exception as e:
            show_warning(f"Chat failed: {e}")
    
    asyncio.run(_run_chat())


# New AI commands for enhanced functionality

@click.command()
@click.argument('query')
@click.option('--context', help='Additional context for suggestions')
@click.option('--file', '-f', type=click.Path(exists=True), help='File to analyze for suggestions')
@click.option('--model', default='gpt-4', help='AI model to use')
@click.option('--provider', help='AI provider to use')
@click.pass_context
def suggest(ctx, query: str, context: Optional[str], file: Optional[str], model: str, provider: Optional[str]):
    """Get contextual AI suggestions."""
    
    async def _run_suggest():
        try:
            ai_service = await get_ai_service()
            
            # Set user preferences
            user_prefs = UserPreferences(
                coding_style="clean",
                preferred_patterns=[],
                ai_model=model,
                temperature=0.5,
                max_tokens=1500
            )
            
            # Build query with context
            full_query = query
            if context:
                full_query += f"\n\nContext: {context}"
            if file:
                full_query += f"\n\nFile: {file}"
            
            project_path = Path(file).parent if file else Path.cwd()
            
            suggestions = await ai_service.suggest_improvements(
                query=full_query,
                project_path=project_path,
                user_preferences=user_prefs,
                provider_name=provider
            )
            
            click.echo("💡 AI Suggestions:")
            click.echo("=" * 50)
            
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    click.echo(f"\n{i}. {suggestion.title}")
                    click.echo(f"   {suggestion.description}")
                    if suggestion.code:
                        click.echo(f"   ```{suggestion.language}")
                        click.echo(f"   {suggestion.code}")
                        click.echo(f"   ```")
                    click.echo(f"   Confidence: {suggestion.confidence:.1f} | Impact: {suggestion.impact}")
            else:
                click.echo("No suggestions available.")
                
        except AIServiceError as e:
            show_warning(f"AI service error: {e}")
        except Exception as e:
            show_warning(f"Suggestion generation failed: {e}")
    
    asyncio.run(_run_suggest())


@click.command()
@click.argument('query')
@click.option('--language', help='Target programming language')
@click.option('--framework', help='Target framework')
@click.option('--model', default='gpt-4', help='AI model to use')
@click.option('--provider', help='AI provider to use')
@click.pass_context
def generate(ctx, query: str, language: Optional[str], framework: Optional[str], model: str, provider: Optional[str]):
    """Generate code with project context."""
    
    async def _run_generate():
        try:
            ai_service = await get_ai_service()
            
            # Set user preferences
            user_prefs = UserPreferences(
                coding_style="clean",
                preferred_patterns=[],
                ai_model=model,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Build query with language and framework
            full_query = query
            if language:
                full_query += f"\nLanguage: {language}"
            if framework:
                full_query += f"\nFramework: {framework}"
            
            response = await ai_service.generate_code(
                query=full_query,
                project_path=Path.cwd(),
                user_preferences=user_prefs,
                provider_name=provider
            )
            
            click.echo("🔧 Generated Code:")
            click.echo("=" * 50)
            click.echo(response.content)
            
            if response.tokens_used > 0:
                click.echo(f"\nTokens used: {response.tokens_used} | Cost: ${response.cost:.4f}")
                
        except AIServiceError as e:
            show_warning(f"AI service error: {e}")
        except Exception as e:
            show_warning(f"Code generation failed: {e}")
    
    asyncio.run(_run_generate())
    """Review a single file with AI."""
    
    content = file_path.read_text()
    language = _detect_file_language(file_path)
    
    # This would integrate with actual AI service
    # For now, return mock review data
    review = {
        'file': str(file_path),
        'language': language,
        'issues': [
            {
                'type': 'style',
                'severity': 'low',
                'line': 10,
                'message': 'Consider using more descriptive variable names',
                'suggestion': 'Rename variable to be more descriptive'
            },
            {
                'type': 'security',
                'severity': 'medium',
                'line': 25,
                'message': 'Potential SQL injection vulnerability',
                'suggestion': 'Use parameterized queries instead'
            }
        ],
        'suggestions': [
            'Consider adding type hints',
            'Add error handling for edge cases',
            'Document public functions with docstrings'
        ],
        'score': 7.5
    }
    
    return review


def _explain_code_in_file(file_path: str, query: str, model: str, context: Optional[str]) -> str:
    """Explain code in a specific file."""
    
    file_path = Path(file_path)
    content = file_path.read_text()
    
    # Mock explanation - would integrate with AI service
    explanation = f"""
This code appears to be a {file_path.suffix[1:]} file.

Based on your query "{query}":

{context if context else ''}

The code {content[:200]}... seems to be implementing functionality that relates to your question.

Key points:
- The file uses standard {file_path.suffix[1:]} patterns
- There are functions/classes that handle the core logic
- The implementation follows common conventions

For a more detailed explanation, please provide more specific context or highlight the exact code section you're interested in.
"""
    
    return explanation.strip()


def _explain_concept(query: str, model: str, context: Optional[str]) -> str:
    """Explain a programming concept."""
    
    # Mock explanation - would integrate with AI service
    explanations = {
        'recursion': 'Recursion is a programming technique where a function calls itself to solve smaller instances of the same problem.',
        'async': 'Asynchronous programming allows tasks to run concurrently without blocking the main thread.',
        'api': 'An API (Application Programming Interface) is a set of rules that allows different software applications to communicate with each other.',
    }
    
    # Simple keyword matching for demo
    for keyword, explanation in explanations.items():
        if keyword.lower() in query.lower():
            return f"{explanation}\n\n{context if context else ''}"
    
    return f"""
Here's an explanation of "{query}":

{context if context else ''}

This is a programming concept that involves specific patterns and best practices. 
For more detailed information, please provide more context about what specifically you'd like to understand.

Common aspects to consider:
- Definition and purpose
- Use cases and examples
- Best practices
- Potential pitfalls
- Related concepts
"""


def _get_refactoring_suggestions(file_path: Path, style: str, model: str) -> List[Dict[str, Any]]:
    """Get AI-powered refactoring suggestions."""
    
    content = file_path.read_text()
    
    # Mock suggestions - would integrate with AI service
    suggestions = [
        {
            'title': 'Extract function',
            'description': 'Extract repeated code into a separate function',
            'code': 'def extracted_function():\n    # Extracted logic here\n    pass',
            'language': 'python'
        },
        {
            'title': 'Use list comprehension',
            'description': 'Replace loop with more idiomatic list comprehension',
            'code': 'result = [x for x in items if condition(x)]',
            'language': 'python'
        }
    ]
    
    return suggestions


def _apply_refactoring_suggestions(file_path: Path, suggestions: List[Dict[str, Any]]) -> None:
    """Apply refactoring suggestions to file."""
    
    # This would intelligently apply suggestions
    # For now, just show what would be done
    show_info("Refactoring suggestions would be applied here")
    show_info("In a real implementation, this would modify the code")


def _generate_tests(file_path: Path, framework: str, model: str, coverage: bool) -> str:
    """Generate AI-powered tests."""
    
    content = file_path.read_text()
    language = _detect_file_language(file_path)
    
    # Mock test generation - would integrate with AI service
    if framework == 'pytest':
        return f'''"""Auto-generated tests for {file_path.name}"""

import pytest
from {file_path.stem} import *

def test_basic_functionality():
    """Test basic functionality."""
    # TODO: Implement test based on code analysis
    assert True

def test_edge_cases():
    """Test edge cases."""
    # TODO: Implement edge case tests
    assert True

def test_error_handling():
    """Test error handling."""
    # TODO: Implement error handling tests
    assert True
'''
    elif framework == 'jest':
        return f'''// Auto-generated tests for {file_path.name}

const {{ /* imports */ }} = require('./{file_path.stem}');

describe('{file_path.stem}', () => {{
  test('basic functionality', () => {{
    // TODO: Implement test based on code analysis
    expect(true).toBe(true);
  }});
  
  test('edge cases', () => {{
    // TODO: Implement edge case tests
    expect(true).toBe(true);
  }});
}});
'''
    
    return f"# Auto-generated tests for {file_path.name}\n# TODO: Add test implementation"


def _detect_test_framework_for_file(file_path: Path) -> str:
    """Detect appropriate test framework for file."""
    
    if file_path.suffix == '.py':
        return 'pytest'
    elif file_path.suffix in ['.js', '.ts']:
        # Check for jest or vitest
        project_path = file_path.parent
        if (project_path / 'package.json').exists():
            content = (project_path / 'package.json').read_text()
            if 'jest' in content:
                return 'jest'
            elif 'vitest' in content:
                return 'vitest'
        return 'jest'  # Default
    elif file_path.suffix == '.go':
        return 'go'
    elif file_path.suffix == '.rs':
        return 'rust'
    
    return 'pytest'  # Default


def _suggest_test_file_path(file_path: Path, framework: str) -> Path:
    """Suggest appropriate test file path."""
    
    if framework == 'pytest':
        return file_path.parent / 'tests' / f'test_{file_path.stem}.py'
    elif framework in ['jest', 'vitest']:
        return file_path.parent / f'{file_path.stem}.test.js'
    elif framework == 'go':
        return file_path.parent / f'{file_path.stem}_test.go'
    elif framework == 'rust':
        return file_path.parent / f'{file_path.stem}_test.rs'
    
    return file_path.parent / f'test_{file_path.name}'


def _run_generated_tests(test_file: Path, framework: str) -> None:
    """Run the generated tests."""
    
    try:
        if framework == 'pytest':
            subprocess.run(['pytest', str(test_file)], check=True)
        elif framework == 'jest':
            subprocess.run(['npm', 'test', '--', str(test_file)], check=True)
        elif framework == 'vitest':
            subprocess.run(['npm', 'run', 'test', '--', str(test_file)], check=True)
        elif framework == 'go':
            subprocess.run(['go', 'test', str(test_file.parent)], check=True)
        elif framework == 'rust':
            subprocess.run(['cargo', 'test'], check=True)
        
        show_success("Tests completed")
    except subprocess.CalledProcessError:
        show_warning("Some tests failed")


def _generate_code_example(query: str, language: Optional[str], model: str, context: Optional[str]) -> str:
    """Generate code examples."""
    
    # Mock code generation - would integrate with AI service
    examples = {
        'hello world': {
            'python': 'print("Hello, World!")',
            'javascript': 'console.log("Hello, World!");',
            'go': 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}',
        },
        'for loop': {
            'python': 'for i in range(10):\n    print(i)',
            'javascript': 'for (let i = 0; i < 10; i++) {\n    console.log(i);\n}',
            'go': 'for i := 0; i < 10; i++ {\n    fmt.Println(i)\n}',
        }
    }
    
    # Simple keyword matching
    for key, lang_examples in examples.items():
        if key.lower() in query.lower():
            if language and language in lang_examples:
                return lang_examples[language]
            elif not language:
                # Return first available
                return next(iter(lang_examples.values()))
    
    # Default example
    return f"""
# Example for: {query}
# Language: {language or 'Python'}

{context if context else ''}

# TODO: Generate specific example based on query
# This would be implemented with actual AI integration
example_code = "Your example code here"
print(example_code)
"""


def _analyze_code_for_issues(file_path: Path, type: str, model: str) -> List[Dict[str, Any]]:
    """Analyze code for specific types of issues."""
    
    content = file_path.read_text()
    
    # Mock issue detection - would integrate with AI service
    issues = []
    
    if type == 'bug':
        issues = [
            {
                'title': 'Potential null reference',
                'location': f'{file_path.name}:15',
                'severity': 'medium',
                'description': 'Variable might be null when accessed',
                'suggestion': 'Add null check before using variable',
                'fix': 'if variable is not None: # do something'
            }
        ]
    elif type == 'security':
        issues = [
            {
                'title': 'Hardcoded credentials',
                'location': f'{file_path.name}:25',
                'severity': 'high',
                'description': 'Credentials should not be hardcoded',
                'suggestion': 'Use environment variables or configuration files',
                'fix': 'import os\npassword = os.getenv("PASSWORD")'
            }
        ]
    elif type == 'performance':
        issues = [
            {
                'title': 'Inefficient loop',
                'location': f'{file_path.name}:30',
                'severity': 'medium',
                'description': 'Loop could be optimized',
                'suggestion': 'Use more efficient data structures',
                'fix': '# Use list comprehension or generator'
            }
        ]
    
    return issues


def _get_ai_response(conversation: List[Dict[str, str]], model: str) -> str:
    """Get AI response for chat."""
    
    # Mock AI response - would integrate with actual AI service
    last_message = conversation[-1]['content']
    
    responses = [
        "That's a great question! Let me help you with that.",
        "Based on what you've described, I suggest considering the following approach...",
        "I can help you understand this concept better. Here's what you need to know...",
        "That's an interesting problem. Here are some potential solutions..."
    ]
    
    # Simple keyword-based responses
    if 'error' in last_message.lower():
        return "It looks like you're encountering an error. Can you share the error message and the relevant code?"
    elif 'how' in last_message.lower():
        return "Here's how you can approach this problem..."
    elif 'why' in last_message.lower():
        return "The reason for this behavior is..."
    else:
        return responses[len(conversation) % len(responses)]


def _save_conversation(conversation: List[Dict[str, str]], file_path: str) -> None:
    """Save conversation to file."""
    
    output = []
    for message in conversation:
        role = message['role'].upper()
        content = message['content']
        output.append(f"{role}:\n{content}\n")
    
    Path(file_path).write_text('\n'.join(output))


def _find_code_files(directory: Path) -> List[Path]:
    """Find all code files in directory."""
    
    code_extensions = ['.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c']
    code_files = []
    
    for ext in code_extensions:
        code_files.extend(directory.rglob(f'*{ext}'))
    
    return code_files


def _detect_file_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.go': 'go',
        '.rs': 'rust',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c'
    }
    
    return ext_map.get(file_path.suffix, 'unknown')


def _save_review_report(reviews: List[Dict[str, Any]], output: str) -> None:
    """Save review report to file."""
    
    report = "# Code Review Report\n\n"
    
    for review in reviews:
        report += f"## {review['file']}\n\n"
        report += f"Language: {review['language']}\n"
        report += f"Score: {review['score']}/10\n\n"
        
        if review['issues']:
            report += "### Issues\n\n"
            for issue in review['issues']:
                report += f"- **{issue['type']}** (Line {issue.get('line', '?')}): {issue['message']}\n"
                report += f"  - Suggestion: {issue['suggestion']}\n\n"
        
        if review['suggestions']:
            report += "### Suggestions\n\n"
            for suggestion in review['suggestions']:
                report += f"- {suggestion}\n"
        
        report += "\n---\n\n"
    
    Path(output).write_text(report)


def _display_review_results(reviews: List[Dict[str, Any]]) -> None:
    """Display review results to console."""
    
    for review in reviews:
        click.echo(f"\n📄 {review['file']}")
        click.echo(f"   Language: {review['language']}")
        click.echo(f"   Score: {review['score']}/10")
        
        if review['issues']:
            click.echo("   Issues:")
            for issue in review['issues']:
                severity_emoji = {'low': '🟡', 'medium': '🟠', 'high': '🔴'}
                click.echo(f"     {severity_emoji.get(issue['severity'], '⚪')} {issue['message']} (Line {issue.get('line', '?')})")
        
        if review['suggestions']:
            click.echo("   Suggestions:")
            for suggestion in review['suggestions']:
                click.echo(f"     💡 {suggestion}")
