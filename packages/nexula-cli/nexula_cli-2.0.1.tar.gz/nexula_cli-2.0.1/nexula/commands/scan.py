import click
import time
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.live import Live
from rich.layout import Layout
from rich.tree import Tree
from ..config import config
from ..api_client import APIClient, APIError

console = Console()

SCANNER_TYPES = [
    "sast", "cve", "secrets", "ml_poisoning", "dataset_poisoning",
    "llm_security", "rag_security", "model_provenance", "container_registry", "license"
]


@click.group()
def scan():
    """Security scanning commands"""
    pass


@scan.command()
@click.option("--project-id", type=int, help="Project ID (overrides .nexula.yaml)")
@click.option("--wait", is_flag=True, help="Wait for scan completion")
@click.option("--interactive", is_flag=True, help="Interactive remediation mode")
def run(project_id: int, wait: bool, interactive: bool):
    """Run security scan on project"""
    try:
        client = APIClient()
        
        # Get project ID
        if not project_id:
            project_id = config.get_project_id()
            if not project_id:
                console.print("[red]✗[/red] No project configured. Run [bold]nexula init[/bold] first.")
                raise click.Abort()
        
        console.print(f"[blue]ℹ[/blue] Running unified security scan on project {project_id}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Starting scan...", total=None)
            
            result = client.run_scan(project_id)
            scan_id = result["id"]
            
            progress.update(task, completed=True)
        
        console.print(f"[green]✓[/green] Scan started: ID {scan_id}")
        
        if wait or interactive:
            console.print("\n[blue]ℹ[/blue] Waiting for scan completion...")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Scanning...", total=100)
                
                while True:
                    status = client.get_scan_status(scan_id)
                    state = status.get("status", "running")
                    progress_pct = status.get("progress", 0)
                    
                    progress.update(task, completed=progress_pct)
                    
                    if state in ["completed", "failed"]:
                        break
                    
                    time.sleep(2)
            
            if state == "completed":
                console.print(f"\n[green]✓[/green] Scan completed successfully")
                
                if interactive:
                    # Launch interactive remediation
                    _interactive_remediation(client, scan_id)
                else:
                    console.print(f"View results: [bold]nexula scan results {scan_id}[/bold]")
            else:
                console.print(f"\n[red]✗[/red] Scan failed")
        else:
            console.print(f"Check status: [bold]nexula scan status {scan_id}[/bold]")
        
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()


@scan.command()
@click.argument("scan_id", type=int)
def status(scan_id: int):
    """Check scan status"""
    try:
        client = APIClient()
        status = client.get_scan_status(scan_id)
        
        console.print(Panel.fit(
            f"Scan ID: [bold]{scan_id}[/bold]\n"
            f"Status: [bold]{status.get('status', 'unknown')}[/bold]\n"
            f"Progress: {status.get('progress', 0)}%\n"
            f"Started: {status.get('started_at', 'N/A')}\n"
            f"Completed: {status.get('completed_at', 'N/A')}",
            title="[blue]Scan Status[/blue]",
            border_style="blue"
        ))
        
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()


@scan.command()
@click.argument("scan_id", type=int)
@click.option("--format", type=click.Choice(["table", "json"]), default="table")
def results(scan_id: int, format: str):
    """View scan results"""
    try:
        client = APIClient()
        results = client.get_scan_results(scan_id)
        
        if format == "json":
            import json
            console.print_json(json.dumps(results, indent=2))
            return
        
        # Display summary
        summary = results.get("summary", {})
        scan_info = results.get("scan", {})
        
        console.print(Panel.fit(
            f"Scan ID: [bold]{scan_id}[/bold]\n"
            f"Status: [bold]{scan_info.get('status', 'unknown')}[/bold]\n"
            f"Type: {scan_info.get('scan_type', 'unified')}\n\n"
            f"Total Findings: [bold]{summary.get('total_findings', 0)}[/bold]\n"
            f"Critical: [red]{summary.get('critical', 0)}[/red]\n"
            f"High: [red]{summary.get('high', 0)}[/red]\n"
            f"Medium: [yellow]{summary.get('medium', 0)}[/yellow]\n"
            f"Low: [blue]{summary.get('low', 0)}[/blue]\n"
            f"Info: [dim]{summary.get('info', 0)}[/dim]",
            title="[blue]Scan Results Summary[/blue]",
            border_style="blue"
        ))
        
        # Display findings
        findings = results.get("findings", [])
        if findings:
            # Group by scanner type
            by_scanner = {}
            for finding in findings:
                scanner = finding.get("scanner_type", "unknown")
                if scanner not in by_scanner:
                    by_scanner[scanner] = []
                by_scanner[scanner].append(finding)
            
            for scanner, scanner_findings in by_scanner.items():
                table = Table(title=f"{scanner.upper()} Findings ({len(scanner_findings)})")
                table.add_column("Severity", style="cyan")
                table.add_column("Title")
                table.add_column("Description")
                
                for finding in scanner_findings[:10]:  # Show first 10
                    severity_color = {
                        "critical": "red",
                        "high": "red",
                        "medium": "yellow",
                        "low": "blue",
                        "info": "dim"
                    }.get(finding.get("severity", "info").lower(), "white")
                    
                    table.add_row(
                        f"[{severity_color}]{finding.get('severity', 'N/A')}[/{severity_color}]",
                        finding.get("title", "N/A"),
                        (finding.get("description", "N/A")[:50] + "...") if len(finding.get("description", "")) > 50 else finding.get("description", "N/A")
                    )
                
                console.print(table)
                console.print()
        
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()


@scan.command()
@click.option("--project-id", type=int, help="Project ID")
def list(project_id: int):
    """List scans for project"""
    try:
        client = APIClient()
        
        if not project_id:
            project_id = config.get_project_id()
            if not project_id:
                console.print("[red]✗[/red] No project configured. Run [bold]nexula init[/bold] first.")
                raise click.Abort()
        
        scans = client.list_scans(project_id)
        
        if not scans:
            console.print("[yellow]![/yellow] No scans found. Run [bold]nexula scan run[/bold]")
            return
        
        table = Table(title=f"Scans for Project {project_id}")
        table.add_column("ID", style="cyan")
        table.add_column("AIBOM ID")
        table.add_column("Status")
        table.add_column("Findings", justify="right")
        table.add_column("Started")
        
        for scan in scans:
            status_color = {
                "completed": "green",
                "running": "yellow",
                "failed": "red"
            }.get(scan.get("status", "unknown"), "white")
            
            table.add_row(
                str(scan["id"]),
                str(scan.get("aibom_id", "N/A")),
                f"[{status_color}]{scan.get('status', 'unknown')}[/{status_color}]",
                str(scan.get("total_findings", 0)),
                scan.get("started_at", "N/A")
            )
        
        console.print(table)
        
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()


def _interactive_remediation(client: APIClient, scan_id: int):
    """Interactive remediation wizard"""
    try:
        results = client.get_scan_results(scan_id)
        findings = results.get("findings", [])
        
        if not findings:
            console.print("\n[green]✓[/green] No vulnerabilities found!")
            return
        
        # Count fixable findings
        fixable = [f for f in findings if f.get("auto_fixable", False)]
        
        console.print(f"\n[yellow]⚠[/yellow] Found {len(findings)} vulnerabilities")
        console.print(f"[green]✓[/green] {len(fixable)} can be auto-fixed\n")
        
        if fixable and Confirm.ask("Fix all auto-fixable issues?"):
            _batch_fix(client, fixable)
            return
        
        # Interactive review
        for idx, finding in enumerate(findings, 1):
            _review_finding(client, finding, idx, len(findings))
        
        console.print("\n[green]✓[/green] Remediation complete!")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Remediation failed: {e}")


def _review_finding(client: APIClient, finding: dict, idx: int, total: int):
    """Review single finding interactively"""
    severity = finding.get("severity", "info").lower()
    severity_color = {
        "critical": "red",
        "high": "red",
        "medium": "yellow",
        "low": "blue",
        "info": "dim"
    }.get(severity, "white")
    
    # Display finding
    console.print(Panel(
        f"[{severity_color}]{severity.upper()}[/{severity_color}]: {finding.get('title', 'N/A')}\n\n"
        f"{finding.get('description', 'N/A')}\n\n"
        f"File: [cyan]{finding.get('file_path', 'N/A')}:{finding.get('line_number', 'N/A')}[/cyan]\n"
        f"Scanner: {finding.get('scanner_type', 'N/A')}",
        title=f"[bold]Finding {idx}/{total}[/bold]",
        border_style=severity_color
    ))
    
    # Show remediation if available
    remediation = finding.get("remediation", "")
    if remediation:
        console.print("\n[bold cyan]Remediation:[/bold cyan]")
        console.print(Panel(remediation, border_style="cyan"))
    
    # Show code context if available
    code_snippet = finding.get("code_snippet", "")
    if code_snippet:
        console.print("\n[bold yellow]Code:[/bold yellow]")
        syntax = Syntax(code_snippet, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
    
    # Action menu
    console.print("\n[bold]Actions:[/bold]")
    if finding.get("auto_fixable", False):
        console.print("  [F] Fix automatically")
    console.print("  [S] Suggest fix")
    console.print("  [I] Ignore")
    console.print("  [N] Next")
    console.print("  [Q] Quit\n")
    
    action = Prompt.ask("Choose action", choices=["f", "s", "i", "n", "q"], default="n").lower()
    
    if action == "f" and finding.get("auto_fixable"):
        _apply_fix(client, finding)
    elif action == "s":
        _suggest_fix(client, finding)
    elif action == "i":
        console.print("[dim]Ignored[/dim]")
    elif action == "q":
        raise click.Abort()
    
    console.print("\n" + "─" * 80 + "\n")


def _apply_fix(client: APIClient, finding: dict):
    """Apply automated fix"""
    finding_id = finding.get("id")
    
    console.print("[blue]ℹ[/blue] Applying fix...")
    
    try:
        # Show preview
        fix_preview = client.get_fix_preview(finding_id)
        
        if fix_preview.get("diff"):
            console.print("\n[bold yellow]Changes:[/bold yellow]")
            syntax = Syntax(fix_preview["diff"], "diff", theme="monokai")
            console.print(syntax)
        
        if Confirm.ask("\nApply this fix?"):
            result = client.apply_fix(finding_id)
            if result.get("success"):
                console.print("[green]✓[/green] Fix applied successfully")
            else:
                console.print(f"[red]✗[/red] Fix failed: {result.get('error')}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to apply fix: {e}")


def _suggest_fix(client: APIClient, finding: dict):
    """Show AI-generated fix suggestions"""
    finding_id = finding.get("id")
    
    with console.status("[bold cyan]Generating fix suggestions..."):
        try:
            suggestions = client.get_fix_suggestions(finding_id)
            
            console.print("\n[bold cyan]Fix Suggestions:[/bold cyan]\n")
            
            for idx, suggestion in enumerate(suggestions.get("suggestions", []), 1):
                console.print(Panel(
                    f"[bold]{suggestion.get('title')}[/bold]\n\n"
                    f"{suggestion.get('description')}\n\n"
                    f"[dim]Confidence: {suggestion.get('confidence', 0)}%[/dim]",
                    title=f"Suggestion {idx}",
                    border_style="cyan"
                ))
                
                if suggestion.get("code"):
                    syntax = Syntax(suggestion["code"], "python", theme="monokai")
                    console.print(syntax)
                    console.print()
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to generate suggestions: {e}")


def _batch_fix(client: APIClient, findings: list):
    """Apply fixes to multiple findings"""
    console.print(f"\n[blue]ℹ[/blue] Fixing {len(findings)} vulnerabilities...\n")
    
    fixed = 0
    failed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Applying fixes...", total=len(findings))
        
        for finding in findings:
            try:
                result = client.apply_fix(finding.get("id"))
                if result.get("success"):
                    fixed += 1
                else:
                    failed += 1
            except:
                failed += 1
            
            progress.advance(task)
    
    console.print(f"\n[green]✓[/green] Fixed: {fixed}")
    if failed:
        console.print(f"[red]✗[/red] Failed: {failed}")


@scan.command()
@click.argument("scan_id", type=int)
def remediate(scan_id: int):
    """Interactive remediation for scan results"""
    try:
        client = APIClient()
        _interactive_remediation(client, scan_id)
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()


@scan.command()
@click.argument("finding_id", type=int)
@click.option("--preview", is_flag=True, help="Preview fix before applying")
def fix(finding_id: int, preview: bool):
    """Apply automated fix for a finding"""
    try:
        client = APIClient()
        
        if preview:
            fix_preview = client.get_fix_preview(finding_id)
            
            console.print(Panel(
                f"Finding: {fix_preview.get('title')}\n"
                f"File: {fix_preview.get('file_path')}\n\n"
                f"[bold]Changes:[/bold]",
                title="Fix Preview",
                border_style="cyan"
            ))
            
            if fix_preview.get("diff"):
                syntax = Syntax(fix_preview["diff"], "diff", theme="monokai")
                console.print(syntax)
            
            if not Confirm.ask("\nApply this fix?"):
                console.print("[yellow]![/yellow] Fix cancelled")
                return
        
        result = client.apply_fix(finding_id)
        
        if result.get("success"):
            console.print("[green]✓[/green] Fix applied successfully")
            if result.get("files_modified"):
                console.print(f"Modified: {', '.join(result['files_modified'])}")
        else:
            console.print(f"[red]✗[/red] Fix failed: {result.get('error')}")
    
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()


@scan.command()
@click.argument("finding_id", type=int)
def suggest(finding_id: int):
    """Get AI-powered fix suggestions"""
    try:
        client = APIClient()
        
        with console.status("[bold cyan]Analyzing vulnerability and generating suggestions..."):
            suggestions = client.get_fix_suggestions(finding_id)
        
        finding = suggestions.get("finding", {})
        
        console.print(Panel(
            f"[bold]{finding.get('title')}[/bold]\n"
            f"Severity: {finding.get('severity')}\n"
            f"File: {finding.get('file_path')}:{finding.get('line_number')}",
            title="Vulnerability Details",
            border_style="yellow"
        ))
        
        console.print("\n[bold cyan]AI-Powered Fix Suggestions:[/bold cyan]\n")
        
        for idx, suggestion in enumerate(suggestions.get("suggestions", []), 1):
            console.print(Panel(
                f"[bold]{suggestion.get('title')}[/bold]\n\n"
                f"{suggestion.get('description')}\n\n"
                f"[bold]Steps:[/bold]\n{suggestion.get('steps', 'N/A')}\n\n"
                f"[dim]Confidence: {suggestion.get('confidence', 0)}% | "
                f"Effort: {suggestion.get('effort', 'Unknown')}[/dim]",
                title=f"Suggestion {idx}",
                border_style="cyan"
            ))
            
            if suggestion.get("code"):
                console.print("\n[bold]Suggested Code:[/bold]")
                syntax = Syntax(suggestion["code"], suggestion.get("language", "python"), theme="monokai", line_numbers=True)
                console.print(syntax)
            
            console.print()
    
    except APIError as e:
        console.print(f"[red]✗[/red] {e}", style="red")
        raise click.Abort()
