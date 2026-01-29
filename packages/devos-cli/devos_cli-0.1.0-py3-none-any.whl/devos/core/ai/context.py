"""Context management system for DevOS AI."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import ast
import re

from .provider import ProjectContext, SessionContext, UserPreferences, ContextError


logger = logging.getLogger(__name__)


@dataclass
class CodePattern:
    """Represents a detected coding pattern."""
    name: str
    type: str  # "architectural", "stylistic", "structural"
    frequency: int
    examples: List[str]
    confidence: float


@dataclass
class DependencyInfo:
    """Information about project dependencies."""
    name: str
    version: str
    type: str  # "runtime", "dev", "test"
    security_issues: List[str]


@dataclass
class ArchitectureInfo:
    """Project architecture information."""
    pattern: str  # "mvc", "layered", "microservices", etc.
    layers: List[str]
    main_components: List[str]
    entry_points: List[str]


class ContextBuilder:
    """Builds and manages project context."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".devos" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._context_cache: Dict[str, ProjectContext] = {}
    
    async def build_project_context(self, project_path: Path) -> ProjectContext:
        """Build comprehensive project context."""
        project_path = project_path.resolve()
        
        # Check cache first
        cache_key = self._get_cache_key(project_path)
        if cache_key in self._context_cache:
            cached_context = self._context_cache[cache_key]
            # Check if cache is still valid (within 1 hour)
            if self._is_cache_valid(cached_context.last_updated):
                return cached_context
        
        try:
            # Build context components
            language = await self._detect_language(project_path)
            framework = await self._detect_framework(project_path, language)
            dependencies = await self._analyze_dependencies(project_path)
            patterns = await self._detect_patterns(project_path)
            architecture = await self._analyze_architecture(project_path, language)
            
            context = ProjectContext(
                project_path=project_path,
                language=language,
                framework=framework,
                dependencies=dependencies,
                patterns=[p.name for p in patterns],
                architecture=asdict(architecture),
                last_updated=datetime.now().isoformat()
            )
            
            # Cache the context
            self._context_cache[cache_key] = context
            await self._save_context_to_cache(cache_key, context)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build context for {project_path}: {e}")
            raise ContextError(f"Context building failed: {e}")
    
    async def build_session_context(self, session_id: str) -> SessionContext:
        """Build session context from tracking data."""
        # This would integrate with the tracking system
        # For now, return basic session context
        return SessionContext(
            session_id=session_id,
            current_file=None,
            recent_files=[],
            work_duration=0,
            notes=None
        )
    
    async def update_context(self, project_path: Path, changes: Dict[str, Any]) -> None:
        """Update project context based on changes."""
        project_path = project_path.resolve()
        cache_key = self._get_cache_key(project_path)
        
        if cache_key in self._context_cache:
            context = self._context_cache[cache_key]
            # Update relevant fields
            if "dependencies" in changes:
                context.dependencies.update(changes["dependencies"])
            if "patterns" in changes:
                context.patterns.extend(changes["patterns"])
            
            context.last_updated = datetime.now().isoformat()
            await self._save_context_to_cache(cache_key, context)
    
    async def _detect_language(self, project_path: Path) -> str:
        """Detect primary programming language."""
        language_counts = {}
        
        # Common file extensions and their languages
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                ext = file_path.suffix.lower()
                if ext in extensions:
                    lang = extensions[ext]
                    language_counts[lang] = language_counts.get(lang, 0) + 1
        
        if not language_counts:
            return "unknown"
        
        # Return the language with the most files
        return max(language_counts, key=language_counts.get)
    
    async def _detect_framework(self, project_path: Path, language: str) -> Optional[str]:
        """Detect the framework being used."""
        framework_indicators = {
            'python': {
                'django': ['manage.py', 'django', 'wsgi.py'],
                'flask': ['flask', 'app.py', 'wsgi.py'],
                'fastapi': ['fastapi', 'main.py', 'api'],
                'pytest': ['pytest', 'test_', 'conftest.py']
            },
            'javascript': {
                'react': ['react', 'jsx', 'components'],
                'vue': ['vue', 'components'],
                'angular': ['angular', 'components'],
                'express': ['express', 'app.js', 'routes'],
                'next': ['next', 'pages', '_app']
            },
            'typescript': {
                'react': ['react', 'tsx', 'components'],
                'angular': ['angular', 'components'],
                'nest': ['@nestjs', 'controller'],
                'next': ['next', 'pages', '_app']
            }
        }
        
        if language not in framework_indicators:
            return None
        
        # Check for framework indicators in files and dependencies
        for framework, indicators in framework_indicators[language].items():
            for indicator in indicators:
                # Check in file names
                for file_path in project_path.rglob('*'):
                    if file_path.is_file() and indicator.lower() in file_path.name.lower():
                        return framework
                
                # Check in package files
                package_files = ['package.json', 'requirements.txt', 'pyproject.toml', 'Cargo.toml']
                for pkg_file in package_files:
                    pkg_path = project_path / pkg_file
                    if pkg_path.exists():
                        content = pkg_path.read_text().lower()
                        if indicator.lower() in content:
                            return framework
        
        return None
    
    async def _analyze_dependencies(self, project_path: Path) -> Dict[str, str]:
        """Analyze project dependencies."""
        dependencies = {}
        
        # Check different dependency files
        dependency_files = {
            'package.json': self._parse_package_json,
            'requirements.txt': self._parse_requirements_txt,
            'pyproject.toml': self._parse_pyproject_toml,
            'Cargo.toml': self._parse_cargo_toml,
            'go.mod': self._parse_go_mod,
            'pom.xml': self._parse_pom_xml
        }
        
        for filename, parser in dependency_files.items():
            file_path = project_path / filename
            if file_path.exists():
                try:
                    deps = await parser(file_path)
                    dependencies.update(deps)
                except Exception as e:
                    logger.warning(f"Failed to parse {filename}: {e}")
        
        return dependencies
    
    async def _detect_patterns(self, project_path: Path) -> List[CodePattern]:
        """Detect coding patterns in the project."""
        patterns = []
        
        # Analyze source files for patterns
        source_files = []
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx']:
            source_files.extend(project_path.rglob(f'*{ext}'))
        
        # Filter out ignored files
        source_files = [f for f in source_files if not self._should_ignore_file(f)]
        
        # Pattern detection
        pattern_detectors = {
            'mvc': self._detect_mvc_pattern,
            'repository': self._detect_repository_pattern,
            'factory': self._detect_factory_pattern,
            'observer': self._detect_observer_pattern,
            'singleton': self._detect_singleton_pattern,
            'dependency_injection': self._detect_di_pattern
        }
        
        for pattern_name, detector in pattern_detectors.items():
            try:
                pattern = await detector(source_files)
                if pattern:
                    patterns.append(pattern)
            except Exception as e:
                logger.warning(f"Failed to detect {pattern_name} pattern: {e}")
        
        return patterns
    
    async def _analyze_architecture(self, project_path: Path, language: str) -> ArchitectureInfo:
        """Analyze project architecture."""
        # Detect architectural pattern
        pattern = await self._detect_architectural_pattern(project_path, language)
        
        # Identify layers
        layers = await self._identify_layers(project_path, language)
        
        # Find main components
        main_components = await self._find_main_components(project_path, language)
        
        # Find entry points
        entry_points = await self._find_entry_points(project_path, language)
        
        return ArchitectureInfo(
            pattern=pattern,
            layers=layers,
            main_components=main_components,
            entry_points=entry_points
        )
    
    async def _parse_package_json(self, file_path: Path) -> Dict[str, str]:
        """Parse package.json for dependencies."""
        try:
            content = file_path.read_text()
            data = json.loads(content)
            deps = {}
            
            for section in ['dependencies', 'devDependencies', 'peerDependencies']:
                if section in data:
                    deps.update(data[section])
            
            return deps
        except Exception:
            return {}
    
    async def _parse_requirements_txt(self, file_path: Path) -> Dict[str, str]:
        """Parse requirements.txt for dependencies."""
        try:
            content = file_path.read_text()
            deps = {}
            
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name and version
                    if '==' in line:
                        name, version = line.split('==', 1)
                    elif '>=' in line:
                        name, version = line.split('>=', 1)
                    elif '<=' in line:
                        name, version = line.split('<=', 1)
                    else:
                        name, version = line, 'latest'
                    deps[name.strip()] = version.strip()
            
            return deps
        except Exception:
            return {}
    
    async def _parse_pyproject_toml(self, file_path: Path) -> Dict[str, str]:
        """Parse pyproject.toml for dependencies."""
        try:
            # Simple TOML parsing (in production, use toml library)
            content = file_path.read_text()
            deps = {}
            
            in_dependencies = False
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('[dependencies]'):
                    in_dependencies = True
                elif line.startswith('['):
                    in_dependencies = False
                elif in_dependencies and '=' in line:
                    dep = line.split('=')[0].strip().strip('"\'')
                    version = line.split('=')[1].strip().strip('"\'')
                    deps[dep] = version
            
            return deps
        except Exception:
            return {}
    
    async def _parse_cargo_toml(self, file_path: Path) -> Dict[str, str]:
        """Parse Cargo.toml for dependencies."""
        # Similar to pyproject.toml parsing
        return await self._parse_pyproject_toml(file_path)
    
    async def _parse_go_mod(self, file_path: Path) -> Dict[str, str]:
        """Parse go.mod for dependencies."""
        try:
            content = file_path.read_text()
            deps = {}
            
            for line in content.split('\n'):
                if line.strip().startswith('require') or line.strip().startswith('\t'):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        deps[parts[0]] = parts[1].strip().strip('"\'')
            
            return deps
        except Exception:
            return {}
    
    async def _parse_pom_xml(self, file_path: Path) -> Dict[str, str]:
        """Parse pom.xml for dependencies."""
        # Simple XML parsing (in production, use xml library)
        return {}
    
    async def _detect_mvc_pattern(self, source_files: List[Path]) -> Optional[CodePattern]:
        """Detect MVC pattern."""
        controllers = []
        models = []
        views = []
        
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore').lower()
                filename = file_path.name.lower()
                
                if 'controller' in filename or 'controller' in content:
                    controllers.append(str(file_path))
                elif 'model' in filename or 'model' in content:
                    models.append(str(file_path))
                elif 'view' in filename or 'template' in filename or 'component' in filename:
                    views.append(str(file_path))
            except (UnicodeDecodeError, IOError):
                continue
        
        if controllers and models and (views or len(controllers) > 1):
            return CodePattern(
                name="MVC",
                type="architectural",
                frequency=len(controllers) + len(models) + len(views),
                examples=controllers[:3] + models[:3] + views[:3],
                confidence=0.8
            )
        
        return None
    
    async def _detect_repository_pattern(self, source_files: List[Path]) -> Optional[CodePattern]:
        """Detect repository pattern."""
        repositories = []
        
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if 'repository' in content or 'Repository' in content:
                    repositories.append(str(file_path))
            except (UnicodeDecodeError, IOError):
                # Skip files that can't be read as text
                continue
        
        if repositories:
            return CodePattern(
                name="Repository",
                type="architectural",
                frequency=len(repositories),
                examples=repositories[:3],
                confidence=0.7
            )
        
        return None
    
    async def _detect_factory_pattern(self, source_files: List[Path]) -> Optional[CodePattern]:
        """Detect factory pattern."""
        factories = []
        
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if 'factory' in content or 'Factory' in content:
                    factories.append(str(file_path))
            except (UnicodeDecodeError, IOError):
                continue
        
        if factories:
            return CodePattern(
                name="Factory",
                type="creational",
                frequency=len(factories),
                examples=factories[:3],
                confidence=0.6
            )
        
        return None
    
    async def _detect_observer_pattern(self, source_files: List[Path]) -> Optional[CodePattern]:
        """Detect observer pattern."""
        observers = []
        
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if 'observer' in content or 'Observer' in content or 'subscribe' in content:
                    observers.append(str(file_path))
            except (UnicodeDecodeError, IOError):
                continue
        
        if observers:
            return CodePattern(
                name="Observer",
                type="behavioral",
                frequency=len(observers),
                examples=observers[:3],
                confidence=0.6
            )
        
        return None
    
    async def _detect_singleton_pattern(self, source_files: List[Path]) -> Optional[CodePattern]:
        """Detect singleton pattern."""
        singletons = []
        
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if 'singleton' in content or 'Singleton' in content:
                    singletons.append(str(file_path))
            except (UnicodeDecodeError, IOError):
                continue
        
        if singletons:
            return CodePattern(
                name="Singleton",
                type="creational",
                frequency=len(singletons),
                examples=singletons[:3],
                confidence=0.7
            )
        
        return None
    
    async def _detect_di_pattern(self, source_files: List[Path]) -> Optional[CodePattern]:
        """Detect dependency injection pattern."""
        di_files = []
        
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if 'inject' in content or 'Inject' in content or 'container' in content:
                    di_files.append(str(file_path))
            except (UnicodeDecodeError, IOError):
                continue
        
        if di_files:
            return CodePattern(
                name="Dependency Injection",
                type="architectural",
                frequency=len(di_files),
                examples=di_files[:3],
                confidence=0.6
            )
        
        return None
    
    async def _detect_architectural_pattern(self, project_path: Path, language: str) -> str:
        """Detect overall architectural pattern."""
        # Check directory structure
        dirs = [d.name.lower() for d in project_path.iterdir() if d.is_dir()]
        
        if 'src' in dirs and 'tests' in dirs:
            return "layered"
        elif any('controller' in d for d in dirs):
            return "mvc"
        elif any('service' in d for d in dirs):
            return "service-oriented"
        elif any('microservice' in d or 'service' in d for d in dirs):
            return "microservices"
        else:
            return "monolith"
    
    async def _identify_layers(self, project_path: Path, language: str) -> List[str]:
        """Identify architectural layers."""
        layers = []
        dirs = [d.name.lower() for d in project_path.iterdir() if d.is_dir()]
        
        layer_mapping = {
            'controller': 'presentation',
            'ui': 'presentation',
            'view': 'presentation',
            'service': 'business',
            'logic': 'business',
            'model': 'data',
            'repository': 'data',
            'database': 'data',
            'util': 'common',
            'helper': 'common',
            'config': 'configuration'
        }
        
        for dir_name in dirs:
            for pattern, layer in layer_mapping.items():
                if pattern in dir_name and layer not in layers:
                    layers.append(layer)
        
        return layers
    
    async def _find_main_components(self, project_path: Path, language: str) -> List[str]:
        """Find main application components."""
        components = []
        
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                filename = file_path.name.lower()
                
                # Common main component files
                if filename in ['main.py', 'app.py', 'index.js', 'app.js', 'main.ts', 'app.ts']:
                    components.append(file_path.name)
                elif filename.startswith('controller') or filename.startswith('service'):
                    components.append(file_path.name)
        
        return list(set(components))[:10]  # Limit to 10 main components
    
    async def _find_entry_points(self, project_path: Path, language: str) -> List[str]:
        """Find application entry points."""
        entry_points = []
        
        entry_files = {
            'python': ['main.py', 'app.py', 'wsgi.py', 'manage.py'],
            'javascript': ['index.js', 'app.js', 'server.js'],
            'typescript': ['index.ts', 'app.ts', 'main.ts', 'server.ts'],
            'go': ['main.go'],
            'java': ['Main.java', 'Application.java'],
            'rust': ['main.rs', 'lib.rs']
        }
        
        if language in entry_files:
            for entry_file in entry_files[language]:
                file_path = project_path / entry_file
                if file_path.exists():
                    entry_points.append(entry_file)
        
        return entry_points
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored during analysis."""
        ignore_patterns = [
            'node_modules', '__pycache__', '.git', '.vscode', 
            'dist', 'build', 'target', '.pytest_cache',
            '.venv', 'venv', 'env', '.env'
        ]
        
        for pattern in ignore_patterns:
            if pattern in str(file_path):
                return True
        
        return False
    
    def _get_cache_key(self, project_path: Path) -> str:
        """Generate cache key for project."""
        return hashlib.sha256(str(project_path).encode()).hexdigest()
    
    def _is_cache_valid(self, last_updated: str) -> bool:
        """Check if cache is still valid."""
        try:
            updated_time = datetime.fromisoformat(last_updated)
            now = datetime.now()
            return (now - updated_time).total_seconds() < 3600  # 1 hour
        except Exception:
            return False
    
    async def _save_context_to_cache(self, cache_key: str, context: ProjectContext) -> None:
        """Save context to cache file."""
        try:
            cache_file = self.cache_dir / f"context_{cache_key}.json"
            data = asdict(context)
            cache_file.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Failed to save context to cache: {e}")
    
    async def _load_context_from_cache(self, cache_key: str) -> Optional[ProjectContext]:
        """Load context from cache file."""
        try:
            cache_file = self.cache_dir / f"context_{cache_key}.json"
            if cache_file.exists():
                data = json.loads(cache_file.read_text())
                return ProjectContext(**data)
        except Exception as e:
            logger.warning(f"Failed to load context from cache: {e}")
        
        return None
