#!/usr/bin/env python3
"""
QA Agent CLI - AI-powered code quality analysis tool
Usage: python qa_agent.py scan ./path/to/repo

Uses Groq API with Llama 3.1-8b-instant for fast AI analysis.
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
from dotenv import load_dotenv

# Groq SDK
from groq import Groq

# Load environment variables
load_dotenv()

console = Console()

# =============================================================================
# Data Models
# =============================================================================

@dataclass
class RiskExplanation:
    what_can_go_wrong: str
    when_will_it_break: str
    is_risky_now_or_later: str  # "now", "later", or "both"
    risk_level: str

@dataclass
class Issue:
    id: str
    file: str
    line: int
    severity: str  # high, medium, low
    category: str  # bug, security, maintainability
    title: str
    description: str
    why_it_matters: str
    suggestion: str
    code_snippet: Optional[str] = None
    risk_explanation: Optional[RiskExplanation] = None

@dataclass
class FileAnalysis:
    path: str
    language: str
    lines_of_code: int
    issues: list = field(default_factory=list)

@dataclass
class ScanResult:
    id: str
    timestamp: str
    repository_path: str
    quality_score: int
    total_files: int
    files_scanned: int
    total_issues: int
    issues_by_severity: dict
    issues_by_category: dict
    files: list
    scan_duration: float
    status: str

# =============================================================================
# File Scanner
# =============================================================================

SUPPORTED_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.env': 'env',
    '.html': 'html',
    '.css': 'css',
}

SKIP_DIRS = {
    'node_modules', '.git', 'dist', 'build', '.next', '__pycache__',
    'venv', '.venv', 'env', '.env', '.idea', '.vscode', 'coverage',
    '.pytest_cache', '.mypy_cache', 'eggs', '*.egg-info', '.tox'
}

def get_language(file_path: Path) -> Optional[str]:
    """Get language from file extension."""
    return SUPPORTED_EXTENSIONS.get(file_path.suffix.lower())

def should_skip_dir(dir_name: str) -> bool:
    """Check if directory should be skipped."""
    return dir_name in SKIP_DIRS or dir_name.startswith('.')

def scan_directory(repo_path: Path, extensions: Optional[list] = None, max_files: int = 50) -> list:
    """Recursively scan directory for code files."""
    files = []
    
    if extensions:
        allowed_ext = {f'.{e.lstrip(".")}' for e in extensions}
    else:
        allowed_ext = set(SUPPORTED_EXTENSIONS.keys())
    
    for root, dirs, filenames in os.walk(repo_path):
        # Filter out directories to skip
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        
        for filename in filenames:
            file_path = Path(root) / filename
            
            if file_path.suffix.lower() not in allowed_ext:
                continue
            
            language = get_language(file_path)
            if not language:
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                relative_path = file_path.relative_to(repo_path)
                
                files.append({
                    'path': str(relative_path),
                    'content': content,
                    'language': language,
                    'lines': len(content.splitlines())
                })
                
                if len(files) >= max_files:
                    return files
                    
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
    
    return files

# =============================================================================
# AI Analyzer (Groq with Llama)
# =============================================================================

def get_groq_client() -> Groq:
    """Initialize Groq client."""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        console.print("[red]Error: GROQ_API_KEY environment variable not set[/red]")
        console.print("\n[yellow]To fix this:[/yellow]")
        console.print("  1. Get your API key from https://console.groq.com/keys")
        console.print("  2. Set it in your terminal:")
        console.print("     [dim]Windows (PowerShell):[/dim] $env:GROQ_API_KEY = 'your-api-key'")
        console.print("     [dim]Windows (CMD):[/dim] set GROQ_API_KEY=your-api-key")
        console.print("     [dim]Linux/Mac:[/dim] export GROQ_API_KEY='your-api-key'")
        sys.exit(1)

    return Groq(api_key=api_key)

def extract_json_from_response(text: str) -> str:
    """Extract and repair JSON array from AI response."""
    # ... existing extraction logic ...
    
    # NEW: Try to repair truncated JSON
    json_text = extracted_text
    
    # Count brackets to check if JSON is complete
    open_brackets = json_text.count('[') - json_text.count(']')
    open_braces = json_text.count('{') - json_text.count('}')
    
    # Close any unclosed brackets/braces
    if open_braces > 0:
        # Remove incomplete last object
        last_complete = json_text.rfind('},')
        if last_complete > 0:
            json_text = json_text[:last_complete + 1]
    
    # Close the array if needed
    if not json_text.rstrip().endswith(']'):
        json_text = json_text.rstrip().rstrip(',') + ']'
    
    return json_text


def analyze_files_with_ai(files: list, model: str, verbose: bool = False) -> list:
    """Analyze files using Groq with Llama model."""
    client = get_groq_client()
    all_issues = []
    successful_batches = 0
    batch_errors: list[str] = []
    
    # Process in batches
    batch_size = 5
    batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing code with AI...", total=len(batches))
        
        for batch_idx, batch in enumerate(batches):
            files_content = []
            for f in batch:
                # Limit content size to avoid token limits
                content = f['content'][:6000] if len(f['content']) > 6000 else f['content']
                files_content.append(f"=== FILE: {f['path']} ({f['language']}) ===\n{content}\n")
            
            all_files_text = "\n".join(files_content)
            
            prompt = f"""You are an expert code reviewer. Your job is to find REAL issues in code.

ANALYZE THESE FILES CAREFULLY:
{all_files_text}

FIND ISSUES IN THESE CATEGORIES:
1. SECURITY: hardcoded secrets/passwords, SQL injection, XSS, insecure API calls, exposed credentials
2. BUGS: null pointer errors, unhandled exceptions, race conditions, logic errors, off-by-one errors
3. MAINTAINABILITY: missing error handling, code smells, unused variables, poor naming, missing validation

IMPORTANT INSTRUCTIONS:
- Be THOROUGH - look at every function and every line
- Look for REAL issues, not theoretical ones
- If code has no imports for error handling, that's an issue
- Missing input validation is an issue
- Console.log statements in production code are issues
- Hardcoded URLs, ports, or configuration values are issues
- Any TODO or FIXME comments indicate issues

RESPOND WITH A JSON ARRAY of issues found. Each issue must have:
{{
  "file": "exact/path/to/file.ext",
  "line": 42,
  "severity": "high" | "medium" | "low",
  "category": "security" | "bug" | "maintainability",
  "title": "Short clear title",
  "description": "What the issue is",
  "why_it_matters": "Why this matters for the project",
  "suggestion": "How to fix it with example code",
  "code_snippet": "the problematic code",
  "risk_explanation": {{
    "what_can_go_wrong": "Plain language explanation",
    "when_will_it_break": "Under what conditions",
    "is_risky_now_or_later": "now" | "later" | "both",
    "risk_level": "One sentence summary"
  }}
}}

Return ONLY valid JSON. Start with [ and end with ].
If truly no issues exist, return [].
"""

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert code reviewer. Always respond with valid JSON arrays only. Be thorough and find real issues."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4096
                )
                
                response_text = response.choices[0].message.content.strip()
                response_text = extract_json_from_response(response_text)
                
                if verbose:
                    console.print(f"[dim]AI Response (batch {batch_idx + 1}):[/dim]")
                    console.print(f"[dim]{response_text[:500]}...[/dim]")
                
                issues = json.loads(response_text)
                successful_batches += 1
                
                if not isinstance(issues, list):
                    if verbose:
                        console.print(f"[yellow]Warning: Response is not a list, got: {type(issues)}[/yellow]")
                    issues = []
                
                for idx, issue in enumerate(issues):
                    if not isinstance(issue, dict):
                        continue
                        
                    risk_exp = issue.get('risk_explanation', {})
                    if not isinstance(risk_exp, dict):
                        risk_exp = {}
                        
                    all_issues.append(Issue(
                        id=f"issue-{batch_idx}-{idx}",
                        file=str(issue.get('file', 'unknown')),
                        line=int(issue.get('line', 1)),
                        severity=str(issue.get('severity', 'medium')).lower(),
                        category=str(issue.get('category', 'maintainability')).lower(),
                        title=str(issue.get('title', 'Issue found')),
                        description=str(issue.get('description', '')),
                        why_it_matters=str(issue.get('why_it_matters', '')),
                        suggestion=str(issue.get('suggestion', '')),
                        code_snippet=issue.get('code_snippet'),
                        risk_explanation=RiskExplanation(
                            what_can_go_wrong=str(risk_exp.get('what_can_go_wrong', '')),
                            when_will_it_break=str(risk_exp.get('when_will_it_break', '')),
                            is_risky_now_or_later=str(risk_exp.get('is_risky_now_or_later', 'now')),
                            risk_level=str(risk_exp.get('risk_level', ''))
                        ) if risk_exp else None
                    ))
                
                if verbose:
                    console.print(f"[green]Batch {batch_idx + 1}: Found {len(issues)} issues[/green]")
                    
            except json.JSONDecodeError as e:
                console.print(f"[yellow]Warning: Could not parse AI response for batch {batch_idx + 1}[/yellow]")
                batch_errors.append(f"batch {batch_idx + 1}: JSON parse error: {e}")
                if verbose:
                    console.print(f"[dim]JSON Error: {e}[/dim]")
                    console.print(f"[dim]Response was: {response_text[:300]}...[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: AI analysis failed for batch {batch_idx + 1}: {e}[/yellow]")
                batch_errors.append(f"batch {batch_idx + 1}: {e}")
                if verbose:
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")
            
            progress.update(task, advance=1)
    
    if successful_batches == 0:
        last_error = batch_errors[-1] if batch_errors else "Unknown error"
        raise RuntimeError(
            f"AI analysis failed for all batches. Check your GROQ_API_KEY and model name. "
            f"Last error: {last_error}"
        )

    return all_issues

# =============================================================================
# Quality Score Calculator
# =============================================================================

def calculate_quality_score(issues: list) -> int:
    """Calculate quality score based on issues found."""
    high_count = sum(1 for i in issues if i.severity == 'high')
    medium_count = sum(1 for i in issues if i.severity == 'medium')
    low_count = sum(1 for i in issues if i.severity == 'low')
    
    penalty = (high_count * 10) + (medium_count * 5) + (low_count * 2)
    score = max(0, 100 - penalty)
    
    return score

# =============================================================================
# Report Generators
# =============================================================================

def generate_json_report(result: ScanResult, output_path: str):
    """Generate JSON report."""
    # Convert dataclasses to dicts
    data = asdict(result)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    console.print(f"[green]✓ JSON report saved to: {output_path}[/green]")

def generate_pdf_report(result: ScanResult, output_path: str):
    """Generate PDF report."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        console.print("[red]Error: reportlab not installed. Run: pip install reportlab[/red]")
        return
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#00CED1'))
    story.append(Paragraph("QA Agent Scan Report", title_style))
    story.append(Spacer(1, 20))
    
    # Summary
    summary_data = [
        ["Repository", result.repository_path],
        ["Scan Date", result.timestamp],
        ["Quality Score", f"{result.quality_score}/100"],
        ["Files Scanned", f"{result.files_scanned}/{result.total_files}"],
        ["Total Issues", str(result.total_issues)],
        ["High Severity", str(result.issues_by_severity.get('high', 0))],
        ["Medium Severity", str(result.issues_by_severity.get('medium', 0))],
        ["Low Severity", str(result.issues_by_severity.get('low', 0))],
    ]
    
    summary_table = Table(summary_data, colWidths=[150, 350])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#16213e')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#333')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Issues
    story.append(Paragraph("Issues Found", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    for file_analysis in result.files:
        for issue_data in file_analysis.get('issues', []):
            if isinstance(issue_data, dict):
                severity = issue_data.get('severity', 'medium')
                title = issue_data.get('title', 'Issue')
                file_path = issue_data.get('file', 'unknown')
                line = issue_data.get('line', 0)
                description = issue_data.get('description', '')
            else:
                severity = issue_data.severity
                title = issue_data.title
                file_path = issue_data.file
                line = issue_data.line
                description = issue_data.description
            
            severity_color = {'high': '#ff4757', 'medium': '#ffa502', 'low': '#2ed573'}.get(severity, '#999')
            
            issue_text = f"<font color='{severity_color}'>[{severity.upper()}]</font> <b>{title}</b><br/>"
            issue_text += f"<font color='#888'>File: {file_path}:{line}</font><br/>"
            issue_text += f"{description}"
            
            story.append(Paragraph(issue_text, styles['Normal']))
            story.append(Spacer(1, 15))
    
    doc.build(story)
    console.print(f"[green]✓ PDF report saved to: {output_path}[/green]")

# =============================================================================
# CLI Display
# =============================================================================

def display_results(result: ScanResult, verbose: bool = False):
    """Display scan results in terminal."""
    # Header panel
    score_color = "green" if result.quality_score >= 70 else "yellow" if result.quality_score >= 50 else "red"
    
    header = f"""
[bold cyan]QA AGENT SCAN REPORT[/bold cyan]

[dim]Repository:[/dim] {result.repository_path}
[dim]Scan Time:[/dim] {result.scan_duration:.1f}s
[dim]Files Scanned:[/dim] {result.files_scanned}/{result.total_files}

[bold]Quality Score: [{score_color}]{result.quality_score}/100[/{score_color}][/bold]
"""
    console.print(Panel(header, border_style="cyan"))
    
    # Issues summary table
    summary_table = Table(show_header=True, header_style="bold cyan")
    summary_table.add_column("Severity", style="dim")
    summary_table.add_column("Count", justify="right")
    summary_table.add_column("Category", style="dim")
    summary_table.add_column("Count", justify="right")
    
    summary_table.add_row(
        "🔴 High", str(result.issues_by_severity.get('high', 0)),
        "🐛 Bug", str(result.issues_by_category.get('bug', 0))
    )
    summary_table.add_row(
        "🟡 Medium", str(result.issues_by_severity.get('medium', 0)),
        "🔒 Security", str(result.issues_by_category.get('security', 0))
    )
    summary_table.add_row(
        "🟢 Low", str(result.issues_by_severity.get('low', 0)),
        "🔧 Maintainability", str(result.issues_by_category.get('maintainability', 0))
    )
    
    console.print(summary_table)
    console.print()
    
    # Detailed issues
    if result.total_issues > 0:
        console.print("[bold]Issues Found:[/bold]\n")
        console.print("─" * 80)
        
        for file_analysis in result.files:
            issues = file_analysis.get('issues', [])
            if not issues:
                continue
            
            for issue_data in issues:
                if isinstance(issue_data, dict):
                    issue = Issue(**{k.replace('-', '_'): v for k, v in issue_data.items() if k != 'risk_explanation'})
                    if 'risk_explanation' in issue_data and issue_data['risk_explanation']:
                        issue.risk_explanation = RiskExplanation(**issue_data['risk_explanation'])
                else:
                    issue = issue_data
                
                severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(issue.severity, '⚪')
                severity_color = {'high': 'red', 'medium': 'yellow', 'low': 'green'}.get(issue.severity, 'white')
                category_emoji = {'security': '🔒', 'bug': '🐛', 'maintainability': '🔧'}.get(issue.category, '📝')
                
                # Issue header
                console.print(f"\n{severity_emoji} {category_emoji} [{severity_color} bold]{issue.title}[/{severity_color} bold]")
                console.print(f"   📍 [cyan]{issue.file}[/cyan]:[bold]{issue.line}[/bold]")
                
                # Description - What is the issue
                console.print(f"\n   [bold]📋 What's wrong:[/bold]")
                console.print(f"      {issue.description}")
                
                # Code snippet if available
                if issue.code_snippet:
                    console.print(f"\n   [bold]💻 Problematic code:[/bold]")
                    console.print(f"      [dim]{issue.code_snippet}[/dim]")
                
                # Why it matters - plain language
                if issue.why_it_matters:
                    console.print(f"\n   [bold]⚠️  Why it matters:[/bold]")
                    console.print(f"      [yellow]{issue.why_it_matters}[/yellow]")
                
                # Risk explanation panel - plain language
                if issue.risk_explanation:
                    console.print(f"\n   [bold]🎯 Risk Assessment:[/bold]")
                    if issue.risk_explanation.what_can_go_wrong:
                        console.print(f"      [red]• What can go wrong:[/red] {issue.risk_explanation.what_can_go_wrong}")
                    if issue.risk_explanation.when_will_it_break:
                        console.print(f"      [yellow]• When will it break:[/yellow] {issue.risk_explanation.when_will_it_break}")
                    if issue.risk_explanation.is_risky_now_or_later:
                        timing_label = {'now': '⚡ Immediate', 'later': '⏳ Future', 'both': '🔄 Ongoing'}.get(
                            issue.risk_explanation.is_risky_now_or_later, '❓ Unknown'
                        )
                        console.print(f"      [magenta]• Risk timing:[/magenta] {timing_label}")
                    if issue.risk_explanation.risk_level:
                        console.print(f"      [bold]• Summary:[/bold] {issue.risk_explanation.risk_level}")
                
                # Suggestion - how to fix
                if issue.suggestion:
                    console.print(f"\n   [bold]✅ How to fix:[/bold]")
                    console.print(f"      [green]{issue.suggestion}[/green]")
                
                console.print("\n" + "─" * 80)
    else:
        console.print("[green]✓ No issues found! Your code looks clean.[/green]")

# =============================================================================
# CLI Commands
# =============================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="qa-agent")
def cli():
    """QA Agent - AI-powered code quality analysis using Groq Llama"""
    pass


@cli.command()
@click.argument('repo_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output JSON report path')
@click.option('--pdf', '-p', help='Output PDF report path')
@click.option('--extensions', '-e', multiple=True, help='File extensions to analyze (e.g., -e py -e js)')
@click.option('--threshold', '-t', type=int, help='Minimum quality score (exit 1 if below)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.option('--max-files', '-m', type=int, default=50, help='Maximum files to scan')
@click.option('--model', default='llama-3.1-8b-instant', show_default=True, help='Groq model to use')
def scan(repo_path: str, output: str, pdf: str, extensions: tuple, threshold: int, verbose: bool, max_files: int, model: str):
    """Scan a repository for code quality issues."""
    start_time = time.time()
    repo = Path(repo_path).resolve()
    
    console.print(f"\n🔍 Scanning repository: [bold]{repo}[/bold]\n")
    
    # Scan files
    ext_list = list(extensions) if extensions else None
    files = scan_directory(repo, ext_list, max_files)
    
    if not files:
        console.print("[yellow]No supported files found in repository[/yellow]")
        return
    
    console.print(f"Found [bold]{len(files)}[/bold] files to analyze\n")
    
    if verbose:
        for f in files[:10]:
            console.print(f"  [dim]- {f['path']} ({f['lines']} lines)[/dim]")
        if len(files) > 10:
            console.print(f"  [dim]... and {len(files) - 10} more[/dim]")
        console.print()
    
    # Analyze with AI
    try:
        issues = analyze_files_with_ai(files, model=model, verbose=verbose)
    except Exception as e:
        console.print("\n[red]✗ Scan failed: AI analysis did not run successfully.[/red]")
        console.print(f"[red]{e}[/red]")
        sys.exit(2)
    
    # Calculate score
    quality_score = calculate_quality_score(issues)
    
    # Build result
    scan_duration = time.time() - start_time
    
    # Group issues by file
    files_with_issues = []
    for f in files:
        file_issues = [i for i in issues if i.file == f['path']]
        files_with_issues.append({
            'path': f['path'],
            'language': f['language'],
            'lines_of_code': f['lines'],
            'issues': [asdict(i) for i in file_issues]
        })
    
    result = ScanResult(
        id=f"scan-{int(time.time())}",
        timestamp=datetime.now().isoformat(),
        repository_path=str(repo),
        quality_score=quality_score,
        total_files=len(files),
        files_scanned=len(files),
        total_issues=len(issues),
        issues_by_severity={
            'high': sum(1 for i in issues if i.severity == 'high'),
            'medium': sum(1 for i in issues if i.severity == 'medium'),
            'low': sum(1 for i in issues if i.severity == 'low'),
        },
        issues_by_category={
            'bug': sum(1 for i in issues if i.category == 'bug'),
            'security': sum(1 for i in issues if i.category == 'security'),
            'maintainability': sum(1 for i in issues if i.category == 'maintainability'),
        },
        files=files_with_issues,
        scan_duration=scan_duration,
        status='completed'
    )
    
    # Display results
    display_results(result, verbose)
    
    # Generate reports
    if output:
        generate_json_report(result, output)
    
    if pdf:
        generate_pdf_report(result, pdf)
    
    console.print(f"\n[dim]Scan completed in {scan_duration:.1f}s[/dim]")
    
    # Check threshold
    if threshold and quality_score < threshold:
        console.print(f"\n[red]✗ Quality score {quality_score} is below threshold {threshold}[/red]")
        sys.exit(1)


@cli.command()
def doctor():
    """Check if QA Agent is properly configured."""
    console.print("\n🩺 [bold]QA Agent Doctor[/bold]\n")
    
    all_ok = True
    
    # Check GROQ_API_KEY
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        console.print("[green]✓[/green] GROQ_API_KEY is set")
        
        # Test API connection
        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Say 'OK' only."}],
                max_tokens=10
            )
            console.print("[green]✓[/green] Groq API connection successful")
        except Exception as e:
            console.print(f"[red]✗[/red] Groq API error: {e}")
            all_ok = False
    else:
        console.print("[red]✗[/red] GROQ_API_KEY is not set")
        console.print("  [dim]Get your key from: https://console.groq.com/keys[/dim]")
        all_ok = False
    
    # Check groq package
    try:
        import groq
        console.print(f"[green]✓[/green] groq package installed")
    except ImportError:
        console.print("[red]✗[/red] groq package not installed")
        console.print("  [dim]Run: pip install groq[/dim]")
        all_ok = False
    
    if all_ok:
        console.print("\n[green]All checks passed! QA Agent is ready to use.[/green]")
    else:
        console.print("\n[yellow]Some issues found. Please fix them before running scans.[/yellow]")
        sys.exit(1)


@cli.command(name="list-models")
def list_models():
    """List available Groq models for code analysis."""
    console.print("\n📋 [bold]Available Groq Models[/bold]\n")
    
    models = [
        ("llama-3.1-8b-instant", "Fast, efficient, great for most code analysis (default)"),
        ("llama-3.3-70b-versatile", "More powerful, better at complex analysis"),
        ("llama-3.1-70b-versatile", "Balanced performance and quality"),
        ("mixtral-8x7b-32768", "Good for longer files (32k context)"),
        ("gemma2-9b-it", "Google's model, good general performance"),
    ]
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Model", style="cyan")
    table.add_column("Description")
    
    for model, desc in models:
        table.add_row(model, desc)
    
    console.print(table)
    console.print("\n[dim]Use with: qa-agent scan ./repo --model MODEL_NAME[/dim]")


@cli.command()
def version():
    """Show version information."""
    console.print("[bold cyan]QA Agent CLI[/bold cyan] v1.0.0")
    console.print("AI-powered code quality analysis using Groq Llama")


if __name__ == '__main__':
    cli()
