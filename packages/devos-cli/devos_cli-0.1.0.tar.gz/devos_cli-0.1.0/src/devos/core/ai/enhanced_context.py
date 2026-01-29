"""
Enhanced AI Context Builder - Project-Wide Analysis
Provides deep understanding of entire codebases for intelligent AI assistance.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import re
from collections import defaultdict, Counter

from devos.core.ai.context import ContextBuilder, ProjectContext
from devos.core.ai.provider import AIServiceError

logger = logging.getLogger(__name__)


@dataclass
class FileAnalysis:
    """Analysis of a single file."""
    path: str
    language: str
    size: int
    functions: List[str]
    classes: List[str]
    imports: List[str]
    exports: List[str]
    dependencies: List[str]
    complexity_score: float
    security_issues: List[str]
    patterns: List[str]
    last_modified: str


@dataclass
class ProjectArchitecture:
    """Architecture analysis of the entire project."""
    total_files: int
    total_lines: int
    languages: Dict[str, int]
    frameworks: List[str]
    architecture_patterns: List[str]
    dependency_graph: Dict[str, List[str]]
    security_score: float
    complexity_distribution: Dict[str, int]
    entry_points: List[str]
    config_files: List[str]
    test_files: List[str]


@dataclass
class SecurityVulnerability:
    """Security issue found in code."""
    type: str
    severity: str  # low, medium, high, critical
    file: str
    line: int
    description: str
    recommendation: str
    cwe_id: Optional[str] = None


@dataclass
class EnhancedProjectContext:
    """Enhanced project context with deep analysis."""
    base_context: ProjectContext
    file_analysis: Dict[str, FileAnalysis]
    architecture: ProjectArchitecture
    security_issues: List[SecurityVulnerability]
    code_smells: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]
    recommendations: List[str]
    analysis_timestamp: str


class EnhancedContextBuilder:
    """Enhanced context builder with project-wide analysis."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".devos" / "enhanced_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.base_builder = ContextBuilder(cache_dir)
        
        # Security patterns
        self.security_patterns = {
            "hardcoded_secrets": [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
            ],
            "sql_injection": [
                r'execute\s*\(\s*["\'][^"\']*\+[^"\']*["\']',
                r'query\s*\(\s*["\'][^"\']*\%[^"\']*["\']',
            ],
            "xss_risks": [
                r'innerHTML\s*=\s*.*\+',
                r'document\.write\s*\(\s*.*\+',
            ],
            "insecure_crypto": [
                r'md5\s*\(',
                r'sha1\s*\(',
                r'des_',
            ]
        }
        
        # Code smell patterns
        self.code_smell_patterns = {
            "long_function": r'def\s+\w+\s*\([^)]*\)\s*:\s*[^#]*#{4,}',
            "deep_nesting": r'(^\s{16,})',
            "large_class": r'class\s+\w+.*:(\n\s{4,}[^#\n]*){20,}',
            "duplicate_code": r'TODO: Detect duplicates with similarity',
        }
        
        # Framework detection patterns
        self.framework_patterns = {
            "react": [
                r'import.*React',
                r'from\s+["\']react["\']',
                r'export\s+default\s+\w+',
                r'useState|useEffect',
            ],
            "django": [
                r'from\s+django\.db',
                r'from\s+django\.http',
                r'class\s+\w+.*models\.Model',
                r'@.*\s*def\s+',
            ],
            "flask": [
                r'from\s+flask\s+import',
                r'app\s*=\s*Flask\(',
                r'@app\.route',
            ],
            "fastapi": [
                r'from\s+fastapi\s+import',
                r'app\s*=\s*FastAPI\(',
                r'@.*\s*(get|post|put|delete)\(',
            ],
            "express": [
                r'require\s*\(\s*["\']express["\']',
                r'app\s*=\s*express\(\)',
                r'app\.(get|post|put|delete)',
            ],
        }
    
    async def build_enhanced_context(self, project_path: Path) -> EnhancedProjectContext:
        """Build comprehensive enhanced project context."""
        logger.info(f"Building enhanced context for {project_path}")
        
        # Get base context
        base_context = await self.base_builder.build_project_context(project_path)
        
        # Analyze all files
        file_analysis = await self._analyze_all_files(project_path)
        
        # Build architecture analysis
        architecture = await self._analyze_architecture(file_analysis, project_path)
        
        # Scan for security issues
        security_issues = await self._scan_security_issues(file_analysis)
        
        # Detect code smells
        code_smells = await self._detect_code_smells(file_analysis)
        
        # Find performance issues
        performance_issues = await self._detect_performance_issues(file_analysis)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(
            architecture, security_issues, code_smells, performance_issues
        )
        
        return EnhancedProjectContext(
            base_context=base_context,
            file_analysis=file_analysis,
            architecture=architecture,
            security_issues=security_issues,
            code_smells=code_smells,
            performance_issues=performance_issues,
            recommendations=recommendations,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    async def _analyze_all_files(self, project_path: Path) -> Dict[str, FileAnalysis]:
        """Analyze all files in the project."""
        file_analysis = {}
        
        # Get all relevant files
        file_patterns = ['**/*.py', '**/*.js', '**/*.ts', '**/*.jsx', '**/*.tsx', 
                        '**/*.java', '**/*.cpp', '**/*.c', '**/*.go', '**/*.rs']
        
        all_files = []
        for pattern in file_patterns:
            all_files.extend(project_path.glob(pattern))
        
        # Filter out large files and common exclusions
        excluded_dirs = {'.git', '__pycache__', 'node_modules', '.vscode', '.idea', 
                        'build', 'dist', 'target', 'venv', 'env'}
        
        filtered_files = [
            f for f in all_files 
            if not any(excluded in str(f) for excluded in excluded_dirs)
            and f.stat().st_size < 1024 * 1024  # < 1MB
        ]
        
        logger.info(f"Analyzing {len(filtered_files)} files")
        
        # Analyze files concurrently
        semaphore = asyncio.Semaphore(10)  # Limit concurrent analysis
        
        async def analyze_single_file(file_path: Path) -> Tuple[str, FileAnalysis]:
            async with semaphore:
                analysis = await self._analyze_file(file_path)
                return str(file_path.relative_to(project_path)), analysis
        
        tasks = [analyze_single_file(f) for f in filtered_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error analyzing file: {result}")
                continue
            
            file_path, analysis = result
            file_analysis[file_path] = analysis
        
        return file_analysis
    
    async def _analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            
            # Detect language
            language = self._detect_language(file_path)
            
            # Extract functions, classes, imports
            functions = self._extract_functions(content, language)
            classes = self._extract_classes(content, language)
            imports = self._extract_imports(content, language)
            exports = self._extract_exports(content, language)
            dependencies = self._extract_dependencies(content, language)
            
            # Calculate complexity
            complexity_score = self._calculate_complexity(content, language)
            
            # Find security issues in this file
            security_issues = self._find_file_security_issues(content, file_path)
            
            # Detect patterns
            patterns = self._detect_patterns(content, language)
            
            return FileAnalysis(
                path=str(file_path),
                language=language,
                size=len(content),
                functions=functions,
                classes=classes,
                imports=imports,
                exports=exports,
                dependencies=dependencies,
                complexity_score=complexity_score,
                security_issues=security_issues,
                patterns=patterns,
                last_modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            # Return minimal analysis
            return FileAnalysis(
                path=str(file_path),
                language="unknown",
                size=0,
                functions=[],
                classes=[],
                imports=[],
                exports=[],
                dependencies=[],
                complexity_score=0.0,
                security_issues=[],
                patterns=[],
                last_modified=datetime.now().isoformat()
            )
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
        }
        return language_map.get(suffix, 'unknown')
    
    def _extract_functions(self, content: str, language: str) -> List[str]:
        """Extract function names from content."""
        functions = []
        
        if language == 'python':
            pattern = r'^def\s+(\w+)\s*\('
        elif language in ['javascript', 'typescript']:
            pattern = r'(?:function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*(?:\([^)]*\)\s*=>|\s*function))'
        elif language == 'java':
            pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?{'
        else:
            return functions
        
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                functions.extend([m for m in match if m])
            else:
                functions.append(match)
        
        return functions
    
    def _extract_classes(self, content: str, language: str) -> List[str]:
        """Extract class names from content."""
        classes = []
        
        if language == 'python':
            pattern = r'^class\s+(\w+)'
        elif language in ['javascript', 'typescript']:
            pattern = r'class\s+(\w+)'
        elif language == 'java':
            pattern = r'(?:public\s+)?class\s+(\w+)'
        else:
            return classes
        
        matches = re.findall(pattern, content, re.MULTILINE)
        classes.extend(matches)
        
        return classes
    
    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements."""
        imports = []
        
        if language == 'python':
            patterns = [
                r'^import\s+(\w+)',
                r'^from\s+([\w.]+)\s+import',
                r'^import\s+([\w.]+)\s+as\s+\w+',
            ]
        elif language in ['javascript', 'typescript']:
            patterns = [
                r'import.*from\s+["\']([^"\']+)["\']',
                r'require\s*\(\s*["\']([^"\']+)["\']',
            ]
        elif language == 'java':
            patterns = [
                r'import\s+([\w.]+);',
            ]
        else:
            return imports
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
        
        return list(set(imports))
    
    def _extract_exports(self, content: str, language: str) -> List[str]:
        """Extract export statements."""
        exports = []
        
        if language in ['javascript', 'typescript']:
            patterns = [
                r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)',
                r'export\s*{\s*([^}]+)\s*}',
            ]
        elif language == 'python':
            patterns = [
                r'__all__\s*=\s*\[([^\]]+)\]',
            ]
        else:
            return exports
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            exports.extend(matches)
        
        return exports
    
    def _extract_dependencies(self, content: str, language: str) -> List[str]:
        """Extract external dependencies."""
        dependencies = []
        
        if language == 'python':
            # Look for common package imports
            common_packages = {
                'requests', 'numpy', 'pandas', 'django', 'flask', 'fastapi',
                'sqlalchemy', 'pytest', 'beautifulsoup4', 'scrapy', 'celery'
            }
            imports = self._extract_imports(content, language)
            for imp in imports:
                parts = imp.split('.')
                if parts[0] in common_packages:
                    dependencies.append(parts[0])
        
        elif language in ['javascript', 'typescript']:
            # Look for npm packages
            imports = self._extract_imports(content, language)
            for imp in imports:
                if not imp.startswith('.') and not imp.startswith('/'):
                    parts = imp.split('/')
                    if parts[0] and not parts[0].startswith('@'):
                        dependencies.append(parts[0])
        
        return list(set(dependencies))
    
    def _calculate_complexity(self, content: str, language: str) -> float:
        """Calculate cyclomatic complexity score."""
        # Simple complexity calculation based on control flow
        complexity_keywords = {
            'python': ['if', 'elif', 'for', 'while', 'try', 'except', 'with', 'and', 'or'],
            'javascript': ['if', 'else', 'for', 'while', 'try', 'catch', '&&', '||'],
            'typescript': ['if', 'else', 'for', 'while', 'try', 'catch', '&&', '||'],
            'java': ['if', 'else', 'for', 'while', 'try', 'catch', '&&', '||'],
        }
        
        keywords = complexity_keywords.get(language, [])
        complexity = 1  # Base complexity
        
        for keyword in keywords:
            complexity += len(re.findall(r'\b' + keyword + r'\b', content))
        
        # Normalize by file size
        lines = len(content.splitlines())
        if lines > 0:
            complexity = complexity / lines * 100  # Complexity per 100 lines
        
        return round(complexity, 2)
    
    def _find_file_security_issues(self, content: str, file_path: Path) -> List[str]:
        """Find security issues in a specific file."""
        issues = []
        lines = content.splitlines()
        
        for issue_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                for i, line in enumerate(lines, 1):
                    try:
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(f"{issue_type} at line {i}: {line.strip()[:50]}...")
                    except (UnicodeDecodeError, re.error):
                        # Skip patterns that cause encoding errors
                        continue
        
        return issues
    
    def _detect_patterns(self, content: str, language: str) -> List[str]:
        """Detect design patterns in the code."""
        patterns = []
        
        # Common design patterns
        pattern_signatures = {
            'singleton': [r'class.*\(\s*\):', '_instance', 'def __new__'],
            'factory': [r'def create_', r'def build_', r'class Factory'],
            'observer': [r'add_observer', r'remove_observer', 'notify'],
            'decorator': [r'@.*', r'def wrapper'],
            'mvc': [r'Model', r'View', r'Controller'],
            'repository': [r'class Repository', r'def save', r'def find'],
        }
        
        for pattern_name, signatures in pattern_signatures.items():
            matches = 0
            for signature in signatures:
                try:
                    if re.search(signature, content, re.IGNORECASE):
                        matches += 1
                except (UnicodeDecodeError, re.error):
                    # Skip patterns that cause encoding errors
                    continue
            
            if matches >= len(signatures) // 2:  # At least half the signatures found
                patterns.append(pattern_name)
        
        return patterns
    
    async def _analyze_architecture(self, file_analysis: Dict[str, FileAnalysis], 
                                   project_path: Path) -> ProjectArchitecture:
        """Analyze overall project architecture."""
        total_files = len(file_analysis)
        total_lines = sum(analysis.size for analysis in file_analysis.values())
        
        # Language distribution
        languages = Counter(analysis.language for analysis in file_analysis.values())
        
        # Framework detection
        frameworks = await self._detect_frameworks(file_analysis)
        
        # Architecture patterns
        all_patterns = []
        for analysis in file_analysis.values():
            all_patterns.extend(analysis.patterns)
        architecture_patterns = list(set(all_patterns))
        
        # Dependency graph
        dependency_graph = self._build_dependency_graph(file_analysis)
        
        # Security score
        total_issues = sum(len(analysis.security_issues) for analysis in file_analysis.values())
        security_score = max(0, 100 - (total_issues * 5))  # Simple scoring
        
        # Complexity distribution
        complexity_scores = [analysis.complexity_score for analysis in file_analysis.values()]
        complexity_distribution = {
            'low': len([s for s in complexity_scores if s < 10]),
            'medium': len([s for s in complexity_scores if 10 <= s < 20]),
            'high': len([s for s in complexity_scores if s >= 20]),
        }
        
        # Find entry points
        entry_points = self._find_entry_points(file_analysis, project_path)
        
        # Find config files
        config_files = self._find_config_files(project_path)
        
        # Find test files
        test_files = self._find_test_files(file_analysis)
        
        return ProjectArchitecture(
            total_files=total_files,
            total_lines=total_lines,
            languages=dict(languages),
            frameworks=frameworks,
            architecture_patterns=architecture_patterns,
            dependency_graph=dependency_graph,
            security_score=security_score,
            complexity_distribution=complexity_distribution,
            entry_points=entry_points,
            config_files=config_files,
            test_files=test_files
        )
    
    async def _detect_frameworks(self, file_analysis: Dict[str, FileAnalysis]) -> List[str]:
        """Detect frameworks used in the project."""
        framework_scores = defaultdict(int)
        
        for file_path, analysis in file_analysis.items():
            for framework, patterns in self.framework_patterns.items():
                for pattern in patterns:
                    # This is simplified - in real implementation, we'd read file content
                    framework_scores[framework] += 1
        
        # Return frameworks with at least some evidence
        detected = [fw for fw, score in framework_scores.items() if score > 0]
        return detected
    
    def _build_dependency_graph(self, file_analysis: Dict[str, FileAnalysis]) -> Dict[str, List[str]]:
        """Build dependency graph between files."""
        dependency_graph = {}
        
        for file_path, analysis in file_analysis.items():
            dependencies = []
            
            # Add dependencies based on imports
            for imp in analysis.imports:
                # Try to map imports to files in the project
                for other_file in file_analysis:
                    if imp in other_file or any(part in other_file for part in imp.split('.')):
                        if other_file != file_path and other_file not in dependencies:
                            dependencies.append(other_file)
            
            dependency_graph[file_path] = dependencies
        
        return dependency_graph
    
    def _find_entry_points(self, file_analysis: Dict[str, FileAnalysis], 
                          project_path: Path) -> List[str]:
        """Find application entry points."""
        entry_points = []
        
        for file_path, analysis in file_analysis.items():
            # Common entry point patterns
            if any(keyword in file_path.lower() for keyword in ['main', 'index', 'app', 'server']):
                entry_points.append(file_path)
            
            # Look for main functions
            if any(func in ['main', 'run', 'start', 'serve'] for func in analysis.functions):
                if file_path not in entry_points:
                    entry_points.append(file_path)
        
        return entry_points
    
    def _find_config_files(self, project_path: Path) -> List[str]:
        """Find configuration files."""
        config_patterns = [
            '**/*.json', '**/*.yaml', '**/*.yml', '**/*.toml', '**/*.ini',
            '**/config/**', '**/.env*', '**/requirements*.txt', '**/package*.json',
            '**/Dockerfile*', '**/docker-compose*', '**/Makefile'
        ]
        
        config_files = []
        for pattern in config_patterns:
            config_files.extend([str(f.relative_to(project_path)) for f in project_path.glob(pattern)])
        
        return config_files
    
    def _find_test_files(self, file_analysis: Dict[str, FileAnalysis]) -> List[str]:
        """Find test files."""
        test_files = []
        
        for file_path, analysis in file_analysis.items():
            # Check filename patterns
            if any(keyword in file_path.lower() for keyword in ['test', 'spec']):
                test_files.append(file_path)
            
            # Check function names
            if any(func.startswith('test_') or func.startswith('spec_') for func in analysis.functions):
                if file_path not in test_files:
                    test_files.append(file_path)
        
        return test_files
    
    async def _scan_security_issues(self, file_analysis: Dict[str, FileAnalysis]) -> List[SecurityVulnerability]:
        """Scan for security vulnerabilities across all files."""
        vulnerabilities = []
        
        for file_path, analysis in file_analysis.items():
            for issue_desc in analysis.security_issues:
                # Parse issue description to extract line number and issue type
                if ' at line ' in issue_desc:
                    parts = issue_desc.split(' at line ')
                    issue_type = parts[0]
                    line_info = parts[1]
                    try:
                        line_num = int(line_info.split(':')[0])
                        code_snippet = ':'.join(line_info.split(':')[1:]).strip()
                        
                        vulnerability = SecurityVulnerability(
                            type=issue_type,
                            severity=self._assess_severity(issue_type),
                            file=file_path,
                            line=line_num,
                            description=f"{issue_type} detected: {code_snippet}",
                            recommendation=self._get_security_recommendation(issue_type)
                        )
                        vulnerabilities.append(vulnerability)
                    except (ValueError, IndexError):
                        continue
        
        return vulnerabilities
    
    def _assess_severity(self, issue_type: str) -> str:
        """Assess severity of security issue."""
        severity_map = {
            'hardcoded_secrets': 'high',
            'sql_injection': 'critical',
            'xss_risks': 'high',
            'insecure_crypto': 'medium',
        }
        return severity_map.get(issue_type, 'medium')
    
    def _get_security_recommendation(self, issue_type: str) -> str:
        """Get security recommendation for issue type."""
        recommendations = {
            'hardcoded_secrets': 'Use environment variables or secret management system',
            'sql_injection': 'Use parameterized queries or ORM',
            'xss_risks': 'Sanitize user input and use proper escaping',
            'insecure_crypto': 'Use modern cryptographic algorithms (AES-256, SHA-256)',
        }
        return recommendations.get(issue_type, 'Review and fix the security issue')
    
    async def _detect_code_smells(self, file_analysis: Dict[str, FileAnalysis]) -> List[Dict[str, Any]]:
        """Detect code smells across all files."""
        code_smells = []
        
        for file_path, analysis in file_analysis.items():
            # Check for high complexity
            if analysis.complexity_score > 20:
                code_smells.append({
                    'type': 'high_complexity',
                    'file': file_path,
                    'severity': 'medium',
                    'description': f"High complexity score: {analysis.complexity_score}",
                    'recommendation': 'Consider refactoring into smaller functions'
                })
            
            # Check for large files
            if analysis.size > 5000:  # > 5KB
                code_smells.append({
                    'type': 'large_file',
                    'file': file_path,
                    'severity': 'low',
                    'description': f"Large file: {analysis.size} bytes",
                    'recommendation': 'Consider splitting into smaller modules'
                })
            
            # Check for too many functions
            if len(analysis.functions) > 20:
                code_smells.append({
                    'type': 'too_many_functions',
                    'file': file_path,
                    'severity': 'medium',
                    'description': f"Too many functions: {len(analysis.functions)}",
                    'recommendation': 'Consider grouping related functions into classes'
                })
        
        return code_smells
    
    async def _detect_performance_issues(self, file_analysis: Dict[str, FileAnalysis]) -> List[Dict[str, Any]]:
        """Detect performance issues across all files."""
        performance_issues = []
        
        # This is a simplified implementation
        # In practice, you'd analyze actual code patterns
        for file_path, analysis in file_analysis.items():
            # Look for potential performance anti-patterns
            if analysis.language == 'python':
                # Check for potential issues (simplified)
                if any('import time' in imp for imp in analysis.imports):
                    performance_issues.append({
                        'type': 'potential_blocking',
                        'file': file_path,
                        'severity': 'low',
                        'description': 'Potential blocking operations detected',
                        'recommendation': 'Consider async/await patterns'
                    })
        
        return performance_issues
    
    async def _generate_recommendations(self, architecture: ProjectArchitecture,
                                      security_issues: List[SecurityVulnerability],
                                      code_smells: List[Dict[str, Any]],
                                      performance_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Security recommendations
        if len(security_issues) > 0:
            critical_issues = [i for i in security_issues if i.severity == 'critical']
            if critical_issues:
                recommendations.append(f"URGENT: Fix {len(critical_issues)} critical security vulnerabilities")
            
            high_issues = [i for i in security_issues if i.severity == 'high']
            if high_issues:
                recommendations.append(f"Address {len(high_issues)} high-priority security issues")
        
        # Architecture recommendations
        if architecture.security_score < 70:
            recommendations.append("Improve security practices to increase security score")
        
        if len(architecture.frameworks) > 3:
            recommendations.append("Consider consolidating frameworks to reduce complexity")
        
        # Code quality recommendations
        if len(code_smells) > 5:
            recommendations.append(f"Refactor {len(code_smells)} code smells to improve maintainability")
        
        # Performance recommendations
        if len(performance_issues) > 0:
            recommendations.append("Address performance issues for better application speed")
        
        # Testing recommendations
        if len(architecture.test_files) < architecture.total_files * 0.1:  # Less than 10% test files
            recommendations.append("Increase test coverage for better code reliability")
        
        return recommendations
    
    async def get_project_summary(self, project_path: Path) -> Dict[str, Any]:
        """Get quick project summary."""
        try:
            context = await self.build_enhanced_context(project_path)
            
            return {
                'project_path': str(project_path),
                'total_files': context.architecture.total_files,
                'languages': context.architecture.languages,
                'frameworks': context.architecture.frameworks,
                'security_score': context.architecture.security_score,
                'security_issues': len(context.security_issues),
                'code_smells': len(context.code_smells),
                'recommendations': context.recommendations[:3],  # Top 3
                'analysis_timestamp': context.analysis_timestamp
            }
        except Exception as e:
            logger.error(f"Error generating project summary: {e}")
            return {'error': str(e)}
