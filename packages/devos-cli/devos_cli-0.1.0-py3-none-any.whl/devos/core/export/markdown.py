"""
Markdown Export Utilities for AI Analysis Results
Provides standardized templates and export functionality for AI analysis.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class MarkdownExporter:
    """Export AI analysis results to Markdown files."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.cwd() / "analysis_reports"
        self.output_dir.mkdir(exist_ok=True)
    
    def export_analysis(self, 
                       analysis_result: Dict[str, Any], 
                       query: str,
                       enhanced_context: Any,
                       filename: Optional[str] = None) -> Path:
        """Export general analysis results to Markdown."""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.md"
        
        output_path = self.output_dir / filename
        
        # Build Markdown content
        content = self._build_analysis_markdown(analysis_result, query, enhanced_context)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def export_security_scan(self,
                            vulnerabilities: List[Dict[str, Any]], 
                            recommendations: List[Dict[str, Any]],
                            enhanced_context: Any,
                            filename: Optional[str] = None) -> Path:
        """Export security scan results to Markdown."""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_scan_{timestamp}.md"
        
        output_path = self.output_dir / filename
        
        # Build Markdown content
        content = self._build_security_markdown(vulnerabilities, recommendations, enhanced_context)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def export_project_summary(self,
                               summary_data: Dict[str, Any],
                               enhanced_context: Any,
                               filename: Optional[str] = None) -> Path:
        """Export project summary to Markdown."""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"project_summary_{timestamp}.md"
        
        output_path = self.output_dir / filename
        
        # Build Markdown content
        content = self._build_summary_markdown(summary_data, enhanced_context)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def export_architecture_map(self,
                               architecture_data: Dict[str, Any],
                               enhanced_context: Any,
                               filename: Optional[str] = None) -> Path:
        """Export architecture analysis to Markdown."""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"architecture_map_{timestamp}.md"
        
        output_path = self.output_dir / filename
        
        # Build Markdown content
        content = self._build_architecture_markdown(architecture_data, enhanced_context)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_path
    
    def _build_analysis_markdown(self, 
                                analysis_result: Dict[str, Any], 
                                query: str,
                                enhanced_context: Any) -> str:
        """Build Markdown content for general analysis."""
        
        arch = enhanced_context.architecture
        
        content = f"""# DevOS AI Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Query:** {query}  
**Project:** {enhanced_context.base_context.project_path.name}

---

## Project Overview

| Metric | Value |
|--------|-------|
| **Total Files** | {arch.total_files} |
| **Total Lines** | {arch.total_lines:,} |
| **Languages** | {', '.join(arch.languages.keys())} |
| **Frameworks** | {', '.join(arch.frameworks)} |
| **Security Score** | {arch.security_score}/100 |
| **Architecture Patterns** | {', '.join(arch.architecture_patterns)} |

---

## Analysis Results

"""
        
        # Add issues if any
        if analysis_result.get('issues'):
            content += "### 🔍 Issues Found\n\n"
            for i, issue in enumerate(analysis_result['issues'], 1):
                severity_emoji = {'low': '🟡', 'medium': '🟠', 'high': '🔴', 'critical': '🚨'}
                emoji = severity_emoji.get(issue.get('severity', 'medium'), '⚪')
                content += f"{i}. {emoji} **{issue.get('type', 'Unknown').upper()}** - {issue.get('severity', 'medium').title()}\n"
                if issue.get('message'):
                    content += f"   - **Description:** {issue['message']}\n"
                if issue.get('suggestion'):
                    content += f"   - **Suggestion:** {issue['suggestion']}\n"
                if issue.get('file'):
                    content += f"   - **File:** `{issue['file']}`\n"
                content += "\n"
        
        # Add suggestions
        if analysis_result.get('suggestions'):
            content += "### 💡 Recommendations\n\n"
            for i, suggestion in enumerate(analysis_result['suggestions'], 1):
                content += f"{i}. {suggestion}\n"
            content += "\n"
        
        # Add metrics
        if analysis_result.get('metrics'):
            content += "### 📊 Analysis Metrics\n\n"
            metrics = analysis_result['metrics']
            content += f"- **Complexity:** {metrics.get('complexity', 'N/A').title()}\n"
            content += f"- **Maintainability:** {metrics.get('maintainability', 'N/A').title()}\n"
            content += f"- **Readability:** {metrics.get('readability', 'N/A').title()}\n"
            content += f"- **Overall Score:** {analysis_result.get('score', 'N/A')}/100\n\n"
        
        # Add key files
        content += "### 📁 Key Files Analyzed\n\n"
        key_files = list(enhanced_context.file_analysis.keys())[:15]
        for file_path in key_files:
            analysis = enhanced_context.file_analysis[file_path]
            content += f"- **{file_path}** ({analysis.language}, {analysis.complexity_score:.1f} complexity)\n"
        
        content += f"""

---

## Next Steps

1. **Review Issues:** Address the identified issues based on severity
2. **Implement Recommendations:** Apply the suggested improvements
3. **Monitor Progress:** Re-run analysis to track improvements
4. **Documentation:** Keep this report for future reference

---

*Generated by DevOS AI - Your intelligent development companion*
"""
        
        return content
    
    def _build_security_markdown(self,
                                vulnerabilities: List[Dict[str, Any]], 
                                recommendations: List[Dict[str, Any]],
                                enhanced_context: Any) -> str:
        """Build Markdown content for security scan."""
        
        arch = enhanced_context.architecture
        
        content = f"""# DevOS Security Scan Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Project:** {enhanced_context.base_context.project_path.name}

---

## Security Overview

| Metric | Value |
|--------|-------|
| **Security Score** | {arch.security_score}/100 |
| **Total Vulnerabilities** | {len(vulnerabilities)} |
| **Critical Issues** | {len([v for v in vulnerabilities if v.get('severity') == 'critical'])} |
| **High Severity** | {len([v for v in vulnerabilities if v.get('severity') == 'high'])} |
| **Medium Severity** | {len([v for v in vulnerabilities if v.get('severity') == 'medium'])} |
| **Low Severity** | {len([v for v in vulnerabilities if v.get('severity') == 'low'])} |

---

## 🚨 Security Vulnerabilities

"""
        
        # Group vulnerabilities by severity
        severity_order = ['critical', 'high', 'medium', 'low']
        severity_emoji = {'critical': '🚨', 'high': '🔴', 'medium': '🟠', 'low': '🟡'}
        
        for severity in severity_order:
            sev_vulns = [v for v in vulnerabilities if v.get('severity') == severity]
            if sev_vulns:
                content += f"### {severity_emoji[severity]} {severity.title()} Severity\n\n"
                for i, vuln in enumerate(sev_vulns, 1):
                    content += f"{i}. **{vuln.get('type', 'Unknown').upper()}**\n"
                    content += f"   - **File:** `{vuln.get('file', 'Unknown')}`\n"
                    if vuln.get('line'):
                        content += f"   - **Line:** {vuln['line']}\n"
                    content += f"   - **Description:** {vuln.get('description', 'No description')}\n"
                    if vuln.get('recommendation'):
                        content += f"   - **Fix:** {vuln['recommendation']}\n"
                    content += "\n"
        
        # Add AI recommendations
        if recommendations:
            content += "### 🛡️ AI Security Recommendations\n\n"
            for i, rec in enumerate(recommendations, 1):
                content += f"{i}. **{rec.get('title', 'Recommendation')}**\n"
                if rec.get('description'):
                    content += f"   - {rec['description']}\n"
                if rec.get('code'):
                    content += f"   - **Code Example:**\n     ```\n     {rec['code']}\n     ```\n"
                if rec.get('impact'):
                    content += f"   - **Impact:** {rec['impact']}\n"
                content += "\n"
        
        content += f"""

---

## 🎯 Action Plan

### Immediate Actions (Critical/High)
1. Fix all critical and high-severity vulnerabilities
2. Update insecure cryptographic functions
3. Review and secure sensitive data handling

### Short-term Actions (Medium)
1. Address medium-severity issues
2. Implement security best practices
3. Add input validation and sanitization

### Long-term Actions (Low/Maintenance)
1. Regular security scans and audits
2. Security training for team
3. Implement security monitoring tools

---

## 📋 Security Checklist

- [ ] All critical vulnerabilities fixed
- [ ] High-severity issues addressed
- [ ] Security dependencies updated
- [ ] Code reviewed for security patterns
- [ ] Security testing implemented
- [ ] Monitoring and alerting setup

---

*Generated by DevOS AI Security Scanner - Keep your code secure*
"""
        
        return content
    
    def _build_summary_markdown(self,
                               summary_data: Dict[str, Any],
                               enhanced_context: Any) -> str:
        """Build Markdown content for project summary."""
        
        arch = enhanced_context.architecture
        
        content = f"""# DevOS Project Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Project:** {enhanced_context.base_context.project_path.name}

---

## 📊 Project Metrics

| Metric | Value |
|--------|-------|
| **Total Files** | {arch.total_files} |
| **Total Lines of Code** | {arch.total_lines:,} |
| **Security Score** | {arch.security_score}/100 |
| **Security Issues** | {len(enhanced_context.security_issues)} |
| **Code Smells** | {len(enhanced_context.code_smells)} |

---

## 💻 Languages & Frameworks

### Languages
"""
        
        for lang, count in arch.languages.items():
            content += f"- **{lang.title()}:** {count} files\n"
        
        content += "\n### Frameworks\n"
        for framework in arch.frameworks:
            content += f"- **{framework}**\n"
        
        content += "\n### Architecture Patterns\n"
        for pattern in arch.architecture_patterns:
            content += f"- **{pattern}**\n"
        
        # Add AI insights
        if summary_data.get('insights'):
            content += "\n---\n\n## 🧠 AI Insights\n\n"
            insights = summary_data['insights']
            
            if insights.get('project_issues'):
                content += "### 🔍 Project Issues\n\n"
                for issue in insights['project_issues']:
                    content += f"- **{issue.get('type', 'Unknown').title()}:** {issue.get('message', 'No message')}\n"
                    if issue.get('suggestion'):
                        content += f"  - *Suggestion:* {issue['suggestion']}\n"
                content += "\n"
            
            if insights.get('recommendations'):
                content += "### 💡 Recommendations\n\n"
                for rec in insights['recommendations']:
                    content += f"- {rec}\n"
                content += "\n"
        
        # Add top files
        content += "### 📁 Key Files\n\n"
        key_files = list(enhanced_context.file_analysis.keys())[:20]
        for file_path in key_files:
            analysis = enhanced_context.file_analysis[file_path]
            content += f"- **{file_path}** ({analysis.language}, {analysis.complexity_score:.1f} complexity)\n"
        
        content += f"""

---

## 🎯 Project Health Assessment

### Overall Score: {summary_data.get('score', 'N/A')}/100

"""
        
        metrics = summary_data.get('metrics', {})
        if metrics:
            content += "### Quality Metrics\n\n"
            content += f"- **Complexity:** {metrics.get('complexity', 'N/A').title()}\n"
            content += f"- **Maintainability:** {metrics.get('maintainability', 'N/A').title()}\n"
            content += f"- **Readability:** {metrics.get('readability', 'N/A').title()}\n"
            content += "\n"
        
        content += """### Improvement Areas

1. **Code Quality:** Address code smells and improve maintainability
2. **Security:** Fix security vulnerabilities to improve security score
3. **Documentation:** Ensure proper documentation for complex components
4. **Testing:** Maintain good test coverage for critical components

---

## 📈 Next Steps

1. **Priority 1:** Fix security vulnerabilities
2. **Priority 2:** Refactor high-complexity files
3. **Priority 3:** Address code smells
4. **Priority 4:** Improve documentation
5. **Priority 5:** Optimize performance

---

*Generated by DevOS AI Project Analyzer - Your project intelligence companion*
"""
        
        return content
    
    def _build_architecture_markdown(self,
                                    architecture_data: Dict[str, Any],
                                    enhanced_context: Any) -> str:
        """Build Markdown content for architecture analysis."""
        
        arch = enhanced_context.architecture
        
        content = f"""# DevOS Architecture Analysis

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Project:** {enhanced_context.base_context.project_path.name}

---

## 🏗️ Architecture Overview

| Aspect | Details |
|--------|---------|
| **Architecture Type** | {', '.join(arch.architecture_patterns)} |
| **Total Components** | {arch.total_files} |
| **Primary Language** | {max(arch.languages, key=arch.languages.get) if arch.languages else 'Unknown'} |
| **Frameworks Used** | {', '.join(arch.frameworks)} |
| **Complexity Level** | {'High' if arch.total_lines > 10000 else 'Medium' if arch.total_lines > 5000 else 'Low'} |

---

## 📋 Architecture Patterns

"""
        
        for pattern in arch.architecture_patterns:
            content += f"### {pattern.title()}\n\n"
            # Find files that match this pattern
            pattern_files = []
            for file_path, analysis in enhanced_context.file_analysis.items():
                if pattern.lower() in [p.lower() for p in analysis.patterns]:
                    pattern_files.append(file_path)
            
            if pattern_files:
                content += "**Files implementing this pattern:**\n"
                for file_path in pattern_files[:10]:
                    analysis = enhanced_context.file_analysis[file_path]
                    content += f"- `{file_path}` ({analysis.language})\n"
                if len(pattern_files) > 10:
                    content += f"- ... and {len(pattern_files) - 10} more files\n"
            else:
                content += "No files found explicitly implementing this pattern.\n"
            content += "\n"
        
        # Add dependency graph summary
        if arch.dependency_graph:
            content += "### 🔗 Dependencies\n\n"
            content += "**Key Dependencies:**\n"
            for file, deps in list(arch.dependency_graph.items())[:10]:
                content += f"- `{file}` depends on {len(deps)} modules\n"
            content += "\n"
        
        # Add component analysis
        content += "### 🧩 Component Analysis\n\n"
        
        # Group files by type/language
        language_groups = {}
        for file_path, analysis in enhanced_context.file_analysis.items():
            lang = analysis.language
            if lang not in language_groups:
                language_groups[lang] = []
            language_groups[lang].append(file_path)
        
        for lang, files in language_groups.items():
            content += f"#### {lang.title()} Components ({len(files)} files)\n\n"
            
            # Show most complex files
            sorted_files = sorted(files, 
                                key=lambda f: enhanced_context.file_analysis[f].complexity_score, 
                                reverse=True)[:5]
            
            content += "**Most Complex Components:**\n"
            for file_path in sorted_files:
                analysis = enhanced_context.file_analysis[file_path]
                content += f"- `{file_path}` (complexity: {analysis.complexity_score:.1f})\n"
                if analysis.functions:
                    content += f"  - Functions: {', '.join(analysis.functions[:3])}\n"
                if analysis.classes:
                    content += f"  - Classes: {', '.join(analysis.classes[:3])}\n"
            content += "\n"
        
        # Add recommendations
        content += """---

## 🎯 Architecture Recommendations

### Structural Improvements
1. **Pattern Consistency:** Ensure consistent use of architecture patterns across the project
2. **Dependency Management:** Review and optimize inter-component dependencies
3. **Modularity:** Consider breaking down large components into smaller, focused modules

### Best Practices
1. **Separation of Concerns:** Maintain clear boundaries between different architectural layers
2. **Interface Design:** Use well-defined interfaces between components
3. **Documentation:** Document architectural decisions and patterns used

### Scalability Considerations
1. **Loose Coupling:** Design components to be independent and replaceable
2. **Configuration:** Externalize configuration to support different environments
3. **Monitoring:** Add architectural health monitoring and metrics

---

## 📊 Architecture Health Score

**Score:** {arch.security_score}/100 (based on security and complexity metrics)

**Factors:**
- ✅ Well-structured project organization
- ✅ Clear architecture patterns
- ⚠️ Consider reducing complexity in large components
- ⚠️ Review dependency management

---

*Generated by DevOS Architecture Analyzer - Understand your project structure*
"""
        
        return content
