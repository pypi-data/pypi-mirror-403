"""
Enhanced AI Commands - Project-Wide Intelligence
Commands that leverage deep project understanding for intelligent assistance.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import asdict
import click

from devos.core.progress import show_success, show_info, show_warning, show_operation_status
from devos.core.ai_config import get_ai_config_manager, initialize_ai_providers
from devos.core.ai import get_ai_service, AIServiceError, UserPreferences
from devos.core.ai.enhanced_context import EnhancedContextBuilder
from devos.core.export.markdown import MarkdownExporter


@click.command()
@click.argument('query')
@click.option('--model', default='llama-3.1-8b-instant', help='AI model to use')
@click.option('--temp', type=float, default=0.3, help='Temperature (0.0-1.0)')
@click.option('--max-tokens', type=int, default=2000, help='Maximum tokens')
@click.option('--scope', type=click.Choice(['file', 'directory', 'project']), default='project', help='Analysis scope')
@click.option('--focus', type=click.Choice(['security', 'architecture', 'performance', 'all']), default='all', help='Focus area')
@click.option('--export-md', help='Export results to Markdown file')
def groq_analyze(query: str, model: str, temp: float, max_tokens: int, scope: str, focus: str, export_md: Optional[str]):
    """Analyze project with deep AI understanding.
    
    Examples:
        groq-analyze "find security vulnerabilities"
        groq-analyze "explain the architecture" --focus architecture
        groq-analyze "suggest improvements" --scope project
    """
    
    async def _run_analyze():
        try:
            click.echo("🔄 Building enhanced project context...")
            
            # Initialize AI service
            config_manager = get_ai_config_manager()
            providers = initialize_ai_providers()
            ai_service = await get_ai_service()
            
            # Build enhanced context
            context_builder = EnhancedContextBuilder()
            project_path = Path.cwd()
            
            enhanced_context = await context_builder.build_enhanced_context(project_path)
            
            show_success(f"Analyzed {enhanced_context.architecture.total_files} files")
            
            # Build context-aware prompt
            prompt = _build_analysis_prompt(query, enhanced_context, scope, focus)
            
            # Get AI analysis
            from devos.core.ai.provider import AIRequest, RequestType, ProjectContext
            
            request = AIRequest(
                query=prompt,
                request_type=RequestType.ANALYZE,
                context=enhanced_context.base_context,
                session_context={
                    'enhanced_context': enhanced_context,
                    'analysis_scope': scope,
                    'focus_area': focus
                },
                user_preferences=UserPreferences(
                    coding_style="clean",
                    preferred_patterns=[],
                    ai_model=model,
                    temperature=temp,
                    max_tokens=max_tokens
                ),
                metadata={
                    'command': 'groq_analyze',
                    'project_files': enhanced_context.architecture.total_files,
                    'security_score': enhanced_context.architecture.security_score
                }
            )
            
            # Build concise context summary instead of full JSON
            context_summary = _build_concise_context_summary(enhanced_context, scope, focus)
            
            click.echo("🔄 AI analyzing project...")
            response = await ai_service.analyze_code(
                code=context_summary,
                project_path=project_path,
                user_preferences=UserPreferences(
                    coding_style="clean",
                    preferred_patterns=[],
                    ai_model=model,
                    temperature=temp,
                    max_tokens=max_tokens
                ),
                provider_name="groq"
            )
            
            # Display results
            click.echo("\n🧠 Enhanced Analysis Results:")
            click.echo("=" * 50)
            if response.issues:
                click.echo("\n🔍 Issues Found:")
                for issue in response.issues:
                    click.echo(f"  • {issue}")
            if response.suggestions:
                click.echo("\n💡 Suggestions:")
                for suggestion in response.suggestions:
                    click.echo(f"  • {suggestion}")
            
            # Show metrics
            click.echo(f"\n📊 Analysis Metrics:")
            click.echo(f"📁 Files analyzed: {enhanced_context.architecture.total_files}")
            click.echo(f"🔍 Security score: {enhanced_context.architecture.security_score}/100")
            click.echo(f"⚠️ Security issues: {len(enhanced_context.security_issues)}")
            click.echo(f"👃 Code smells: {len(enhanced_context.code_smells)}")
            
            click.echo(f"\n📊 Analysis Score: {response.score}/100")
            if response.metrics:
                click.echo(f"📈 Metrics: {response.metrics}")
            
            # Export to Markdown if requested
            if export_md:
                try:
                    exporter = MarkdownExporter()
                    
                    # Prepare analysis data for export
                    analysis_data = {
                        'issues': response.issues,
                        'suggestions': response.suggestions,
                        'score': response.score,
                        'metrics': response.metrics
                    }
                    
                    output_path = exporter.export_analysis(
                        analysis_result=analysis_data,
                        query=query,
                        enhanced_context=enhanced_context,
                        filename=export_md
                    )
                    
                    show_success(f"Analysis exported to: {output_path}")
                except Exception as e:
                    show_warning(f"Failed to export analysis: {e}")
            
        except AIServiceError as e:
            show_warning(f"AI analysis failed: {e}")
        except Exception as e:
            show_warning(f"Analysis failed: {e}")
    
    asyncio.run(_run_analyze())


@click.command()
@click.option('--model', default='llama-3.1-8b-instant', help='AI model to use')
@click.option('--temp', type=float, default=0.2, help='Temperature (0.0-1.0)')
@click.option('--max-tokens', type=int, default=3000, help='Maximum tokens')
@click.option('--severity', type=click.Choice(['low', 'medium', 'high', 'critical']), default='medium', help='Minimum severity level')
@click.option('--export-md', help='Export results to Markdown file')
def groq_security_scan(model: str, temp: float, max_tokens: int, severity: str, export_md: Optional[str]):
    """Comprehensive security vulnerability scan.
    
    Examples:
        groq-security-scan
        groq-security-scan --severity high
        groq-security-scan --model llama-3.1-70b-versatile
    """
    
    async def _run_security_scan():
        try:
            click.echo("🔄 Scanning for security vulnerabilities...")
            
            # Initialize AI service
            config_manager = get_ai_config_manager()
            providers = initialize_ai_providers()
            ai_service = await get_ai_service()
            
            # Build enhanced context
            context_builder = EnhancedContextBuilder()
            project_path = Path.cwd()
            
            enhanced_context = await context_builder.build_enhanced_context(project_path)
            
            # Filter vulnerabilities by severity
            severity_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
            min_severity_level = severity_order[severity]
            
            filtered_vulnerabilities = [
                v for v in enhanced_context.security_issues
                if severity_order[v.severity] >= min_severity_level
            ]
            
            show_success(f"Found {len(filtered_vulnerabilities)} vulnerabilities (severity: {severity}+)")
            
            if not filtered_vulnerabilities:
                show_info("No security vulnerabilities found! 🎉")
                return
            
            # Display vulnerabilities
            click.echo("\n🚨 Security Vulnerabilities:")
            click.echo("=" * 50)
            
            for i, vuln in enumerate(filtered_vulnerabilities, 1):
                severity_emoji = {'low': '🟡', 'medium': '🟠', 'high': '🔴', 'critical': '🔴'}
                click.echo(f"\n{i}. {severity_emoji.get(vuln.severity, '⚪')} {vuln.type.upper()} - {vuln.severity}")
                click.echo(f"   📁 File: {vuln.file}")
                click.echo(f"   📍 Line: {vuln.line}")
                click.echo(f"   📝 Description: {vuln.description}")
                click.echo(f"   💡 Recommendation: {vuln.recommendation}")
            
            # Get AI recommendations for fixing
            if filtered_vulnerabilities:
                click.echo("🔄 AI generating fix recommendations...")
                
                from devos.core.ai.provider import AIRequest, RequestType
                
                vuln_summary = "\n".join([
                    f"- {v.type} in {v.file} (line {v.line}): {v.description}"
                    for v in filtered_vulnerabilities[:10]  # Limit to 10 for context
                ])
                
                prompt = f"""Here are the security vulnerabilities found in the project:

{vuln_summary}

Please provide:
1. A prioritized action plan to fix these vulnerabilities
2. Specific code examples for the most critical issues
3. Best practices to prevent similar vulnerabilities in the future
4. Any additional security measures recommended for this type of project

Focus on practical, actionable advice."""
                
                request = AIRequest(
                    query=prompt,
                    request_type=RequestType.SUGGEST,
                    context=enhanced_context.base_context,
                    session_context={'vulnerabilities': filtered_vulnerabilities},
                    user_preferences=UserPreferences(
                        coding_style="secure",
                        preferred_patterns=[],
                        ai_model=model,
                        temperature=temp,
                        max_tokens=max_tokens
                    ),
                    metadata={'command': 'groq_security_scan'}
                )
                
                response = await ai_service.suggest_improvements(
                    query=prompt,
                    project_path=project_path,
                    user_preferences=UserPreferences(
                        coding_style="secure",
                        preferred_patterns=[],
                        ai_model=model,
                        temperature=temp,
                        max_tokens=max_tokens
                    ),
                    provider_name="groq"
                )
                
                click.echo("\n🛡️ AI Security Recommendations:")
                click.echo("=" * 50)
                
                # Handle different response types
                if hasattr(response, 'suggestions') and response.suggestions:
                    for suggestion in response.suggestions:
                        click.echo(f"• {suggestion}")
                elif isinstance(response, list):
                    # Handle list response
                    for item in response:
                        click.echo(f"• {item}")
                elif hasattr(response, 'content'):
                    click.echo(response.content)
                else:
                    click.echo("No specific suggestions generated.")
                
                if hasattr(response, 'score'):
                    click.echo(f"\n📊 Analysis Score: {response.score}/100")
                if hasattr(response, 'metrics') and response.metrics:
                    click.echo(f"📈 Metrics: {response.metrics}")
                
                # Export to Markdown if requested
                if export_md:
                    try:
                        exporter = MarkdownExporter()
                        
                        # Prepare vulnerability data for export
                        vulnerabilities_data = []
                        for vuln in filtered_vulnerabilities:
                            vulnerabilities_data.append({
                                'type': vuln.type,
                                'severity': vuln.severity,
                                'file': vuln.file,
                                'line': vuln.line,
                                'description': vuln.description,
                                'recommendation': vuln.recommendation
                            })
                        
                        # Prepare AI recommendations for export
                        recommendations_data = []
                        if hasattr(response, 'suggestions') and response.suggestions:
                            for suggestion in response.suggestions:
                                if hasattr(suggestion, '__dict__'):
                                    recommendations_data.append({
                                        'title': getattr(suggestion, 'title', 'Recommendation'),
                                        'description': getattr(suggestion, 'description', ''),
                                        'code': getattr(suggestion, 'code', ''),
                                        'language': getattr(suggestion, 'language', ''),
                                        'confidence': getattr(suggestion, 'confidence', 0.0),
                                        'impact': getattr(suggestion, 'impact', 'medium')
                                    })
                                else:
                                    recommendations_data.append({
                                        'title': 'Recommendation',
                                        'description': str(suggestion),
                                        'code': '',
                                        'language': '',
                                        'confidence': 0.0,
                                        'impact': 'medium'
                                    })
                        
                        output_path = exporter.export_security_scan(
                            vulnerabilities=vulnerabilities_data,
                            recommendations=recommendations_data,
                            enhanced_context=enhanced_context,
                            filename=export_md
                        )
                        
                        show_success(f"Security scan exported to: {output_path}")
                    except Exception as e:
                        show_warning(f"Failed to export security scan: {e}")
            
        except AIServiceError as e:
            show_warning(f"Security scan failed: {e}")
        except Exception as e:
            show_warning(f"Scan failed: {e}")
    
    asyncio.run(_run_security_scan())


@click.command()
@click.option('--model', default='llama-3.1-8b-instant', help='AI model to use')
@click.option('--temp', type=float, default=0.3, help='Temperature (0.0-1.0)')
@click.option('--max-tokens', type=int, default=2000, help='Maximum tokens')
@click.option('--format', type=click.Choice(['text', 'json', 'markdown']), default='text', help='Output format')
def groq_architecture_map(model: str, temp: float, max_tokens: int, format: str):
    """Generate comprehensive project architecture map.
    
    Examples:
        groq-architecture-map
        groq-architecture-map --format markdown
        groq-architecture-map --model llama-3.1-70b-versatile
    """
    
    async def _run_architecture_map():
        try:
            click.echo("🔄 Mapping project architecture...")
            
            # Build enhanced context
            context_builder = EnhancedContextBuilder()
            project_path = Path.cwd()
            
            enhanced_context = await context_builder.build_enhanced_context(project_path)
            
            show_success(f"Mapped {enhanced_context.architecture.total_files} files")
            
            # Display architecture overview
            if format == 'json':
                architecture_data = {
                    'project_path': str(project_path),
                    'total_files': enhanced_context.architecture.total_files,
                    'total_lines': enhanced_context.architecture.total_lines,
                    'languages': enhanced_context.architecture.languages,
                    'frameworks': enhanced_context.architecture.frameworks,
                    'architecture_patterns': enhanced_context.architecture.architecture_patterns,
                    'dependency_graph': enhanced_context.architecture.dependency_graph,
                    'entry_points': enhanced_context.architecture.entry_points,
                    'config_files': enhanced_context.architecture.config_files,
                    'test_files': enhanced_context.architecture.test_files,
                    'security_score': enhanced_context.architecture.security_score
                }
                click.echo(json.dumps(architecture_data, indent=2))
            
            else:
                # Text/Markdown format
                click.echo("\n🏗️ Project Architecture Map")
                click.echo("=" * 50)
                
                click.echo(f"\n📊 Project Overview:")
                click.echo(f"   📁 Total files: {enhanced_context.architecture.total_files}")
                click.echo(f"   📄 Total lines: {enhanced_context.architecture.total_lines}")
                click.echo(f"   🔒 Security score: {enhanced_context.architecture.security_score}/100")
                
                click.echo(f"\n💻 Languages:")
                for lang, count in enhanced_context.architecture.languages.items():
                    click.echo(f"   {lang}: {count} files")
                
                if enhanced_context.architecture.frameworks:
                    click.echo(f"\n🔧 Frameworks:")
                    for fw in enhanced_context.architecture.frameworks:
                        click.echo(f"   • {fw}")
                
                if enhanced_context.architecture.architecture_patterns:
                    click.echo(f"\n🎨 Architecture Patterns:")
                    for pattern in enhanced_context.architecture.architecture_patterns:
                        click.echo(f"   • {pattern}")
                
                if enhanced_context.architecture.entry_points:
                    click.echo(f"\n🚪 Entry Points:")
                    for entry in enhanced_context.architecture.entry_points:
                        click.echo(f"   • {entry}")
                
                if enhanced_context.architecture.config_files:
                    click.echo(f"\n⚙️ Configuration Files:")
                    for config in enhanced_context.architecture.config_files[:10]:  # Limit display
                        click.echo(f"   • {config}")
                    if len(enhanced_context.architecture.config_files) > 10:
                        click.echo(f"   ... and {len(enhanced_context.architecture.config_files) - 10} more")
                
                # Get AI analysis of architecture
                click.echo("🔄 AI analyzing architecture patterns...")
                
                # Initialize AI service
                config_manager = get_ai_config_manager()
                providers = initialize_ai_providers()
                ai_service = await get_ai_service()
                
                from devos.core.ai.provider import AIRequest, RequestType
                
                prompt = f"""Analyze this project architecture and provide insights:

Languages: {list(enhanced_context.architecture.languages.keys())}
Frameworks: {enhanced_context.architecture.frameworks}
Patterns: {enhanced_context.architecture.architecture_patterns}
Files: {enhanced_context.architecture.total_files}
Security Score: {enhanced_context.architecture.security_score}

Please provide:
1. Overall architecture assessment
2. Strengths and potential weaknesses
3. Scalability considerations
4. Recommendations for improvements
5. Best practices for this type of architecture"""
                
                request = AIRequest(
                    query=prompt,
                    request_type=RequestType.ANALYZE,
                    context=enhanced_context.base_context,
                    session_context={'architecture': enhanced_context.architecture},
                    user_preferences=UserPreferences(
                        coding_style="clean",
                        preferred_patterns=[],
                        ai_model=model,
                        temperature=temp,
                        max_tokens=max_tokens
                    ),
                    metadata={'command': 'groq_architecture_map'}
                )
                
                response = await ai_service.analyze_code(
                    code=json.dumps(asdict(enhanced_context.architecture), default=str, indent=2),
                    project_path=project_path,
                    user_preferences=UserPreferences(
                        coding_style="clean",
                        preferred_patterns=[],
                        ai_model=model,
                        temperature=temp,
                        max_tokens=max_tokens
                    ),
                    provider_name="groq"
                )
                
                click.echo("\n🧠 AI Architecture Analysis:")
                click.echo("=" * 50)
                if response.issues:
                    click.echo("\n🔍 Architecture Issues:")
                    for issue in response.issues:
                        click.echo(f"  • {issue}")
                if response.suggestions:
                    click.echo("\n💡 Architecture Suggestions:")
                    for suggestion in response.suggestions:
                        click.echo(f"  • {suggestion}")
                
                click.echo(f"\n📊 Analysis Score: {response.score}/100")
            if response.metrics:
                click.echo(f"📈 Metrics: {response.metrics}")
            
        except Exception as e:
            show_warning(f"Architecture mapping failed: {e}")
    
    asyncio.run(_run_architecture_map())


@click.command()
@click.argument('query')
@click.option('--model', default='llama-3.1-8b-instant', help='AI model to use')
@click.option('--temp', type=float, default=0.4, help='Temperature (0.0-1.0)')
@click.option('--max-tokens', type=int, default=3000, help='Maximum tokens')
@click.option('--write', is_flag=True, help='Write improvements to files')
@click.option('--dry-run', is_flag=True, help='Show what would be changed without writing')
def groq_enhance(query: str, model: str, temp: float, max_tokens: int, write: bool, dry_run: bool):
    """Enhance codebase with AI-driven improvements.
    
    Examples:
        groq-enhance "add error handling to all functions"
        groq-enhance "optimize database queries" --write
        groq-enhance "add type hints" --dry-run
    """
    
    async def _run_enhance():
        try:
            click.echo("🔄 Analyzing codebase for enhancement opportunities...")
            
            # Initialize AI service
            config_manager = get_ai_config_manager()
            providers = initialize_ai_providers()
            ai_service = await get_ai_service()
            
            # Build enhanced context
            context_builder = EnhancedContextBuilder()
            project_path = Path.cwd()
            
            enhanced_context = await context_builder.build_enhanced_context(project_path)
            
            show_success(f"Analyzed {enhanced_context.architecture.total_files} files")
            
            # Get AI enhancement plan
            from devos.core.ai.provider import AIRequest, RequestType
            
            prompt = f"""I want to enhance this codebase with: {query}

Project context:
- Languages: {list(enhanced_context.architecture.languages.keys())}
- Frameworks: {enhanced_context.architecture.frameworks}
- Files: {enhanced_context.architecture.total_files}
- Security score: {enhanced_context.architecture.security_score}

Please provide:
1. A detailed enhancement plan
2. Specific files that need modification
3. Code examples for the improvements
4. Step-by-step implementation guide
5. Potential risks and mitigation strategies

Focus on practical, implementable improvements."""
            
            request = AIRequest(
                query=prompt,
                request_type=RequestType.SUGGEST,
                context=enhanced_context.base_context,
                session_context={'enhancement_query': query},
                user_preferences=UserPreferences(
                    coding_style="enhanced",
                    preferred_patterns=[],
                    ai_model=model,
                    temperature=temp,
                    max_tokens=max_tokens
                ),
                metadata={'command': 'groq_enhance'}
            )
            
            response = await ai_service.suggest_improvements(
                query=prompt,
                project_path=project_path,
                user_preferences=UserPreferences(
                    coding_style="enhanced",
                    preferred_patterns=[],
                    ai_model=model,
                    temperature=temp,
                    max_tokens=max_tokens
                ),
                provider_name="groq"
            )
            
            click.echo("\n🚀 Enhancement Plan:")
            click.echo("=" * 50)
            click.echo(response.content)
            
            if write or dry_run:
                click.echo(f"\n{'🔍' if dry_run else '✏️'} {'Dry run: ' if dry_run else ''}Enhancement mode")
                # In a full implementation, this would parse the AI response
                # and apply the suggested changes to files
                if dry_run:
                    show_info("Dry run mode - no files will be modified")
                else:
                    show_warning("Automatic file writing not yet implemented")
                    show_info("Please manually apply the suggested improvements")
            
            click.echo(f"\n📊 Analysis Score: {response.score}/100")
            if response.metrics:
                click.echo(f"📈 Metrics: {response.metrics}")
            
        except AIServiceError as e:
            show_warning(f"Enhancement failed: {e}")
        except Exception as e:
            show_warning(f"Enhancement failed: {e}")
    
    asyncio.run(_run_enhance())


@click.command()
@click.option('--model', default='llama-3.1-8b-instant', help='AI model to use')
@click.option('--temp', type=float, default=0.2, help='Temperature (0.0-1.0)')
@click.option('--max-tokens', type=int, default=2000, help='Maximum tokens')
@click.option('--export-md', help='Export results to Markdown file')
def groq_project_summary(model: str, temp: float, max_tokens: int, export_md: Optional[str]):
    """Get comprehensive project summary with AI insights.
    
    Examples:
        groq-project-summary
        groq-project-summary --model llama-3.1-70b-versatile
    """
    
    async def _run_project_summary():
        try:
            click.echo("🔄 Generating project summary...")
            
            # Build enhanced context
            context_builder = EnhancedContextBuilder()
            project_path = Path.cwd()
            
            enhanced_context = await context_builder.build_enhanced_context(project_path)
            summary = await context_builder.get_project_summary(project_path)
            
            if 'error' in summary:
                show_warning(f"Failed to generate summary: {summary['error']}")
                return
            
            # Display summary
            click.echo("\n📊 Project Summary")
            click.echo("=" * 50)
            
            click.echo(f"\n📁 Project: {summary['project_path']}")
            click.echo(f"📄 Files: {summary['total_files']}")
            click.echo(f"💻 Languages: {', '.join(summary['languages'].keys())}")
            
            if summary['frameworks']:
                click.echo(f"🔧 Frameworks: {', '.join(summary['frameworks'])}")
            
            click.echo(f"🔒 Security Score: {summary['security_score']}/100")
            click.echo(f"⚠️ Security Issues: {summary['security_issues']}")
            click.echo(f"👃 Code Smells: {summary['code_smells']}")
            
            if summary['recommendations']:
                click.echo(f"\n💡 Top Recommendations:")
                for i, rec in enumerate(summary['recommendations'], 1):
                    click.echo(f"   {i}. {rec}")
            
            # Get AI insights
            click.echo("🔄 AI generating insights...")
            
            # Initialize AI service
            config_manager = get_ai_config_manager()
            providers = initialize_ai_providers()
            ai_service = await get_ai_service()
            
            from devos.core.ai.provider import AIRequest, RequestType
            
            prompt = f"""Based on this project summary, provide insights and recommendations:

{json.dumps(summary, indent=2)}

Please analyze:
1. Overall project health and maturity
2. Technology stack assessment
3. Development best practices adherence
4. Potential areas for improvement
5. Growth and scalability considerations

Keep it concise and actionable."""
            
            # Create a minimal context for this request
            from devos.core.ai.context import ContextBuilder
            base_builder = ContextBuilder()
            base_context = await base_builder.build_project_context(project_path)
            
            request = AIRequest(
                query=prompt,
                request_type=RequestType.ANALYZE,
                context=base_context,
                session_context={'project_summary': summary},
                user_preferences=UserPreferences(
                    coding_style="clean",
                    preferred_patterns=[],
                    ai_model=model,
                    temperature=temp,
                    max_tokens=max_tokens
                ),
                metadata={'command': 'groq_project_summary'}
            )
            
            response = await ai_service.analyze_code(
                    code=json.dumps(summary, default=str, indent=2),
                    project_path=project_path,
                    user_preferences=UserPreferences(
                        coding_style="clean",
                        preferred_patterns=[],
                        ai_model=model,
                        temperature=temp,
                        max_tokens=max_tokens
                    ),
                    provider_name="groq"
                )
            
            click.echo("\n🧠 AI Insights:")
            click.echo("=" * 50)
            if response.issues:
                click.echo("\n🔍 Project Issues:")
                for issue in response.issues:
                    click.echo(f"  • {issue}")
            if response.suggestions:
                click.echo("\n💡 Project Insights:")
                for suggestion in response.suggestions:
                    click.echo(f"  • {suggestion}")
            
            click.echo(f"\n📊 Analysis Score: {response.score}/100")
            if response.metrics:
                click.echo(f"📈 Metrics: {response.metrics}")
            
            # Export to Markdown if requested
            if export_md:
                try:
                    exporter = MarkdownExporter()
                    
                    # Prepare summary data for export
                    summary_data = {
                        'issues': response.issues if response.issues else [],
                        'suggestions': response.suggestions if response.suggestions else [],
                        'score': response.score,
                        'metrics': response.metrics if response.metrics else {},
                        'insights': {
                            'project_issues': response.issues if response.issues else [],
                            'recommendations': response.suggestions if response.suggestions else []
                        }
                    }
                    
                    output_path = exporter.export_project_summary(
                        summary_data=summary_data,
                        enhanced_context=enhanced_context,
                        filename=export_md
                    )
                    
                    show_success(f"Project summary exported to: {output_path}")
                except Exception as e:
                    show_warning(f"Failed to export project summary: {e}")
            
        except Exception as e:
            show_warning(f"Summary generation failed: {e}")
    
    asyncio.run(_run_project_summary())


def _build_analysis_prompt(query: str, enhanced_context, scope: str, focus: str) -> str:
    """Build context-aware analysis prompt."""
    context_info = {
        'total_files': enhanced_context.architecture.total_files,
        'languages': list(enhanced_context.architecture.languages.keys()),
        'frameworks': enhanced_context.architecture.frameworks,
        'security_score': enhanced_context.architecture.security_score,
        'security_issues': len(enhanced_context.security_issues),
        'code_smells': len(enhanced_context.code_smells),
        'patterns': enhanced_context.architecture.architecture_patterns
    }
    
    prompt = f"""Analyze this project with the query: "{query}"

Project Context:
{json.dumps(context_info, indent=2)}

Scope: {scope}
Focus: {focus}

Please provide:
1. Detailed analysis based on the query
2. Specific findings with file references
3. Actionable recommendations
4. Code examples where relevant
5. Best practices for this type of project

Consider the project's architecture, security posture, and code quality in your analysis."""
    
    return prompt


def _build_concise_context_summary(enhanced_context, scope: str, focus: str) -> str:
    """Build a concise context summary to avoid token limits."""
    arch = enhanced_context.architecture
    
    # Build basic project info
    summary = f"""PROJECT ANALYSIS SUMMARY
========================

Project Type: Python CLI Application
Total Files: {arch.total_files}
Total Lines: {arch.total_lines:,}
Languages: {', '.join(arch.languages.keys())}
Frameworks: {', '.join(arch.frameworks)}
Architecture Patterns: {', '.join(arch.architecture_patterns)}
Security Score: {arch.security_score}/100

"""
    
    # Add focus-specific information
    if focus == 'security' or focus == 'all':
        summary += f"SECURITY ISSUES ({len(enhanced_context.security_issues)}):\n"
        for i, issue in enumerate(enhanced_context.security_issues[:5], 1):
            summary += f"  {i}. {issue.type}: {issue.description[:100]}...\n"
        if len(enhanced_context.security_issues) > 5:
            summary += f"  ... and {len(enhanced_context.security_issues) - 5} more\n"
        summary += "\n"
    
    if focus == 'architecture' or focus == 'all':
        summary += f"KEY FILES:\n"
        key_files = list(enhanced_context.file_analysis.keys())[:10]
        for file_path in key_files:
            analysis = enhanced_context.file_analysis[file_path]
            summary += f"  - {file_path} ({analysis.language}, {analysis.complexity_score:.1f} complexity)\n"
        summary += "\n"
    
    if focus == 'performance' or focus == 'all':
        summary += f"CODE SMELLS ({len(enhanced_context.code_smells)}):\n"
        for i, smell in enumerate(enhanced_context.code_smells[:5], 1):
            summary += f"  {i}. {smell.get('type', 'unknown')}: {smell.get('message', 'no message')[:80]}...\n"
        if len(enhanced_context.code_smells) > 5:
            summary += f"  ... and {len(enhanced_context.code_smells) - 5} more\n"
        summary += "\n"
    
    summary += f"ANALYSIS SCOPE: {scope}\n"
    summary += f"FOCUS AREA: {focus}\n"
    
    return summary
