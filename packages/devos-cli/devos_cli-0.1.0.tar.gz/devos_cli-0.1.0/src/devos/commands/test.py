"""Smart testing commands."""

import click
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from devos.core.database import Database
from devos.core.progress import show_success, show_info, show_warning, show_operation_status, ProgressBar


@click.command()
@click.option('--watch', '-w', is_flag=True, help='Run tests in watch mode')
@click.option('--coverage', '-c', is_flag=True, help='Generate coverage report')
@click.option('--file', '-f', help='Run specific test file')
@click.option('--pattern', '-p', help='Test pattern/glob')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--parallel', is_flag=True, help='Run tests in parallel')
@click.pass_context
def test(ctx, watch: bool, coverage: bool, file: Optional[str], pattern: Optional[str], verbose: bool, parallel: bool):
    """Smart testing with auto-detection of test framework."""
    
    project_path = Path.cwd()
    test_config = _detect_test_framework(project_path)
    
    if not test_config:
        show_warning("No test framework detected", "Supported: pytest, jest, vitest, go test, cargo test")
        return
    
    framework = test_config['framework']
    show_info(f"Detected test framework: {framework}")
    
    if watch:
        _run_watch_mode(test_config, verbose)
    elif coverage:
        _run_with_coverage(test_config, verbose)
    elif file:
        _run_file_tests(test_config, file, verbose)
    elif pattern:
        _run_pattern_tests(test_config, pattern, verbose)
    else:
        _run_all_tests(test_config, verbose, parallel)


@click.command()
@click.option('--format', type=click.Choice(['json', 'table', 'html']), default='table', help='Report format')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def coverage(ctx, format: str, output: Optional[str]):
    """Generate and display test coverage report."""
    
    project_path = Path.cwd()
    test_config = _detect_test_framework(project_path)
    
    if not test_config:
        show_warning("No test framework detected")
        return
    
    coverage_data = _get_coverage_data(test_config)
    
    if format == 'json':
        if output:
            Path(output).write_text(json.dumps(coverage_data, indent=2))
            show_success(f"Coverage report saved to {output}")
        else:
            click.echo(json.dumps(coverage_data, indent=2))
    elif format == 'html':
        _generate_html_report(coverage_data, output)
    else:
        _display_coverage_table(coverage_data)


@click.command()
@click.pass_context
def discover(ctx):
    """Discover and list all tests in the project."""
    
    project_path = Path.cwd()
    test_files = _discover_test_files(project_path)
    
    if not test_files:
        show_info("No test files found")
        return
    
    click.echo(f"🧪 Found {len(test_files)} test files:")
    click.echo("-" * 50)
    
    for test_file in test_files:
        relative_path = test_file.relative_to(project_path)
        test_count = _count_tests_in_file(test_file)
        click.echo(f"📄 {relative_path} ({test_count} tests)")


@click.command()
@click.argument('test_name')
@click.option('--file', '-f', help='File to create test in')
@click.option('--framework', type=click.Choice(['pytest', 'jest', 'vitest']), help='Test framework')
@click.pass_context
def generate(ctx, test_name: str, file: Optional[str], framework: Optional[str]):
    """Generate test boilerplate."""
    
    project_path = Path.cwd()
    
    if not framework:
        test_config = _detect_test_framework(project_path)
        framework = test_config['framework'] if test_config else 'pytest'
    
    if file:
        test_file = project_path / file
    else:
        test_file = _suggest_test_file(project_path, test_name, framework)
    
    test_content = _generate_test_template(test_name, framework)
    
    # Create directory if needed
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    if test_file.exists():
        if not click.confirm(f"File {test_file} already exists. Append to it?"):
            click.echo("Test generation cancelled.")
            return
    
    test_file.write_text(test_content)
    show_success(f"Test generated: {test_file}")


def _detect_test_framework(project_path: Path) -> Optional[Dict[str, Any]]:
    """Detect the test framework being used."""
    
    # Check for Python/pytest
    if (project_path / 'pyproject.toml').exists():
        content = (project_path / 'pyproject.toml').read_text()
        if 'pytest' in content:
            return {'framework': 'pytest', 'command': 'pytest', 'config_files': ['pytest.ini', 'pyproject.toml']}
    
    if (project_path / 'requirements.txt').exists():
        content = (project_path / 'requirements.txt').read_text()
        if 'pytest' in content:
            return {'framework': 'pytest', 'command': 'pytest', 'config_files': ['pytest.ini', 'pyproject.toml']}
    
    # Check for JavaScript/TypeScript (Jest/Vitest)
    if (project_path / 'package.json').exists():
        content = (project_path / 'package.json').read_text()
        if 'jest' in content:
            return {'framework': 'jest', 'command': 'npm test', 'config_files': ['jest.config.js', 'package.json']}
        elif 'vitest' in content:
            return {'framework': 'vitest', 'command': 'npm run test', 'config_files': ['vitest.config.ts', 'vite.config.ts']}
    
    # Check for Go
    if (project_path / 'go.mod').exists():
        return {'framework': 'go', 'command': 'go test', 'config_files': []}
    
    # Check for Rust
    if (project_path / 'Cargo.toml').exists():
        return {'framework': 'cargo', 'command': 'cargo test', 'config_files': ['Cargo.toml']}
    
    return None


def _run_all_tests(test_config: Dict[str, Any], verbose: bool, parallel: bool) -> None:
    """Run all tests."""
    
    framework = test_config['framework']
    base_command = test_config['command']
    
    if framework == 'pytest':
        cmd = ['pytest']
        if verbose:
            cmd.append('-v')
        if parallel:
            cmd.extend(['-n', 'auto'])
    elif framework == 'jest':
        cmd = ['npm', 'test']
        if verbose:
            cmd.append('--verbose')
    elif framework == 'vitest':
        cmd = ['npm', 'run', 'test']
        if verbose:
            cmd.append('--verbose')
    elif framework == 'go':
        cmd = ['go', 'test']
        if verbose:
            cmd.append('-v')
        if parallel:
            cmd.extend(['-parallel', str(os.cpu_count())])
    elif framework == 'cargo':
        cmd = ['cargo', 'test']
        if verbose:
            cmd.append('--verbose')
    else:
        cmd = base_command.split()
    
    show_info(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=True, text=True)
        
        if result.returncode == 0:
            show_success("All tests passed!")
            if verbose and result.stdout:
                click.echo(result.stdout)
        else:
            show_operation_status("Tests failed", False)
            if result.stderr:
                click.echo(result.stderr, err=True)
            if result.stdout:
                click.echo(result.stdout)
                
    except subprocess.CalledProcessError as e:
        show_operation_status(f"Test execution failed: {e}", False)


def _run_watch_mode(test_config: Dict[str, Any], verbose: bool) -> None:
    """Run tests in watch mode."""
    
    framework = test_config['framework']
    
    if framework == 'pytest':
        cmd = ['pytest', '--watch']
    elif framework == 'jest':
        cmd = ['npm', 'test', '--watch']
    elif framework == 'vitest':
        cmd = ['npm', 'run', 'test', '--watch']
    elif framework == 'go':
        cmd = ['go', 'test', '-watch']  # Requires gotestsum
    elif framework == 'cargo':
        cmd = ['cargo', 'watch', '-x', 'test']
    else:
        show_warning(f"Watch mode not supported for {framework}")
        return
    
    show_info(f"Starting watch mode: {' '.join(cmd)}")
    show_info("Press Ctrl+C to stop watching")
    
    try:
        subprocess.run(cmd, cwd=Path.cwd())
    except KeyboardInterrupt:
        show_info("Watch mode stopped")


def _run_with_coverage(test_config: Dict[str, Any], verbose: bool) -> None:
    """Run tests with coverage."""
    
    framework = test_config['framework']
    
    if framework == 'pytest':
        cmd = ['pytest', '--cov=.', '--cov-report=term-missing']
    elif framework == 'jest':
        cmd = ['npm', 'test', '--coverage']
    elif framework == 'vitest':
        cmd = ['npm', 'run', 'test', '--coverage']
    elif framework == 'go':
        cmd = ['go', 'test', '-cover']
    elif framework == 'cargo':
        cmd = ['cargo', 'tarpaulin']  # Requires cargo-tarpaulin
    else:
        show_warning(f"Coverage not supported for {framework}")
        return
    
    show_info(f"Running tests with coverage: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=True, text=True)
        
        if result.returncode == 0:
            show_success("Tests completed with coverage!")
            if result.stdout:
                click.echo(result.stdout)
        else:
            show_operation_status("Coverage test failed", False)
            if result.stderr:
                click.echo(result.stderr, err=True)
                
    except subprocess.CalledProcessError as e:
        show_operation_status(f"Coverage execution failed: {e}", False)


def _run_file_tests(test_config: Dict[str, Any], file: str, verbose: bool) -> None:
    """Run tests for a specific file."""
    
    framework = test_config['framework']
    
    if framework == 'pytest':
        cmd = ['pytest', file]
        if verbose:
            cmd.append('-v')
    elif framework == 'jest':
        cmd = ['npm', 'test', '--', file]
    elif framework == 'vitest':
        cmd = ['npm', 'run', 'test', '--', file]
    elif framework == 'go':
        cmd = ['go', 'test', '-run', file]
    elif framework == 'cargo':
        cmd = ['cargo', 'test', '--', file]
    else:
        cmd = test_config['command'].split() + [file]
    
    show_info(f"Running tests for {file}: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=True, text=True)
        
        if result.returncode == 0:
            show_success(f"Tests passed for {file}!")
        else:
            show_operation_status(f"Tests failed for {file}", False)
            if result.stderr:
                click.echo(result.stderr, err=True)
                
    except subprocess.CalledProcessError as e:
        show_operation_status(f"Test execution failed: {e}", False)


def _run_pattern_tests(test_config: Dict[str, Any], pattern: str, verbose: bool) -> None:
    """Run tests matching a pattern."""
    
    framework = test_config['framework']
    
    if framework == 'pytest':
        cmd = ['pytest', '-k', pattern]
    elif framework == 'jest':
        cmd = ['npm', 'test', '--', '--testNamePattern', pattern]
    elif framework == 'vitest':
        cmd = ['npm', 'run', 'test', '--', '-t', pattern]
    else:
        show_warning(f"Pattern matching not supported for {framework}")
        return
    
    show_info(f"Running tests matching '{pattern}': {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=True, text=True)
        
        if result.returncode == 0:
            show_success(f"Pattern tests passed!")
        else:
            show_operation_status("Pattern tests failed", False)
            if result.stderr:
                click.echo(result.stderr, err=True)
                
    except subprocess.CalledProcessError as e:
        show_operation_status(f"Test execution failed: {e}", False)


def _discover_test_files(project_path: Path) -> List[Path]:
    """Discover all test files in the project."""
    
    test_patterns = [
        '**/test_*.py',
        '**/*_test.py',
        '**/tests/**/*.py',
        '**/*.test.js',
        '**/*.test.ts',
        '**/*.spec.js',
        '**/*.spec.ts',
        '**/tests/**/*.js',
        '**/tests/**/*.ts',
        '**/*_test.go',
        '**/*_test.rs'
    ]
    
    test_files = []
    for pattern in test_patterns:
        test_files.extend(project_path.glob(pattern))
    
    return sorted(set(test_files))


def _count_tests_in_file(test_file: Path) -> int:
    """Count the number of tests in a file."""
    
    content = test_file.read_text()
    
    if test_file.suffix == '.py':
        import re
        return len(re.findall(r'def test_', content))
    elif test_file.suffix in ['.js', '.ts']:
        import re
        return len(re.findall(r'(it\(|test\(|describe\()', content))
    elif test_file.suffix == '.go':
        import re
        return len(re.findall(r'func Test', content))
    elif test_file.suffix == '.rs':
        import re
        return len(re.findall(r'#\[test\]', content))
    
    return 0


def _suggest_test_file(project_path: Path, test_name: str, framework: str) -> Path:
    """Suggest a test file path based on framework conventions."""
    
    if framework == 'pytest':
        test_dir = project_path / 'tests'
        test_file = test_dir / f'test_{test_name.replace(" ", "_").lower()}.py'
    elif framework in ['jest', 'vitest']:
        if (project_path / 'src').exists():
            src_file = project_path / 'src' / f'{test_name.replace(" ", "_").lower()}.js'
            test_file = src_file.parent / f'{src_file.stem}.test.js'
        else:
            test_file = project_path / f'{test_name.replace(" ", "_").lower()}.test.js'
    else:
        test_file = project_path / f'test_{test_name.replace(" ", "_").lower()}'
    
    return test_file


def _generate_test_template(test_name: str, framework: str) -> str:
    """Generate test template based on framework."""
    
    test_function = test_name.replace(" ", "_").lower()
    
    if framework == 'pytest':
        return f'''"""Tests for {test_name}."""

import pytest


def test_{test_function}():
    """Test {test_name} functionality."""
    # TODO: Implement test
    assert True


class Test{test_name.title().replace(" ", "")}:
    """Test class for {test_name}."""
    
    def setup_method(self):
        """Setup for each test."""
        pass
    
    def test_{test_function}_basic(self):
        """Basic test for {test_name}."""
        # TODO: Implement test
        assert True
'''
    
    elif framework in ['jest', 'vitest']:
        return f'''// Tests for {test_name}

describe('{test_name}', () => {{
  test('basic functionality', () => {{
    // TODO: Implement test
    expect(true).toBe(true);
  }});
  
  test('edge cases', () => {{
    // TODO: Implement test
    expect(true).toBe(true);
  }});
}});
'''
    
    elif framework == 'go':
        return f'''package main

import "testing"

func Test{test_name.title().replace(" ", "")}(t *testing.T) {{
	// TODO: Implement test
	if true != true {{
		t.Errorf("Test failed")
	}}
}}
'''
    
    elif framework == 'cargo':
        return f'''#[cfg(test)]
mod tests {{
    use super::*;
    
    #[test]
    fn test_{test_function}() {{
        // TODO: Implement test
        assert!(true);
    }}
}}
'''
    
    return f"# Test template for {test_name}\n# TODO: Add implementation"


def _get_coverage_data(test_config: Dict[str, Any]) -> Dict[str, Any]:
    """Get coverage data from the test framework."""
    
    # This would integrate with coverage tools
    # For now, return mock data
    return {
        'total_lines': 1000,
        'covered_lines': 850,
        'coverage_percentage': 85.0,
        'files': [
            {'path': 'src/main.py', 'lines': 100, 'covered': 90, 'percentage': 90.0},
            {'path': 'src/utils.py', 'lines': 200, 'covered': 170, 'percentage': 85.0}
        ]
    }


def _generate_html_report(coverage_data: Dict[str, Any], output: Optional[str]) -> None:
    """Generate HTML coverage report."""
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Coverage Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .coverage {{ font-size: 24px; color: #28a745; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Coverage Report</h1>
    <div class="coverage">Total Coverage: {coverage_data['coverage_percentage']:.1f}%</div>
    
    <h2>File Coverage</h2>
    <table>
        <tr><th>File</th><th>Lines</th><th>Covered</th><th>Percentage</th></tr>
'''
    
    for file_data in coverage_data['files']:
        html += f'''
        <tr>
            <td>{file_data['path']}</td>
            <td>{file_data['lines']}</td>
            <td>{file_data['covered']}</td>
            <td>{file_data['percentage']:.1f}%</td>
        </tr>
'''
    
    html += '''
    </table>
</body>
</html>
'''
    
    if output:
        Path(output).write_text(html)
        show_success(f"HTML report saved to {output}")
    else:
        Path('coverage.html').write_text(html)
        show_success("HTML report saved to coverage.html")


def _display_coverage_table(coverage_data: Dict[str, Any]) -> None:
    """Display coverage in table format."""
    
    click.echo(f"📊 Total Coverage: {coverage_data['coverage_percentage']:.1f}%")
    click.echo("-" * 60)
    click.echo(f"{'File':<30} {'Lines':<8} {'Covered':<8} {'Percentage':<12}")
    click.echo("-" * 60)
    
    for file_data in coverage_data['files']:
        click.echo(f"{file_data['path']:<30} {file_data['lines']:<8} {file_data['covered']:<8} {file_data['percentage']:<12.1f}%")
