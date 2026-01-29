from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import List, Dict, Any, Optional

console = Console()


def print_error(message: str):
    """Print error message"""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_success(message: str):
    """Print success message"""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_info(message: str):
    """Print info message"""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_pr_table(
    prs: List[Dict[str, Any]], build_statuses: Optional[Dict[int, str]] = None
):
    """Print pull requests as a table

    Args:
        prs: List of pull request dictionaries
        build_statuses: Optional dict mapping PR ID to build status string.
                       Status should be one of: 'succeeded', 'failed', 'inProgress', 'pending', or None
    """
    if not prs:
        print_info("No pull requests found")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Title", style="white")
    table.add_column("Author", style="yellow", width=20)
    table.add_column("Checks", width=10)
    table.add_column("Status", width=12)

    for pr in prs:
        status = pr["status"]
        if status == "active":
            status_display = "[green]●[/green] Active"
        elif status == "completed":
            status_display = "[blue]✓[/blue] Completed"
        else:
            status_display = "[red]✗[/red] Abandoned"

        # Build/checks status
        build_status = (
            build_statuses.get(pr["pullRequestId"]) if build_statuses else None
        )
        if build_status == "succeeded":
            checks_display = "[green]✓ Pass[/green]"
        elif build_status == "failed":
            checks_display = "[red]✗ Fail[/red]"
        elif build_status == "inProgress":
            checks_display = "[yellow]● Running[/yellow]"
        elif build_status == "pending":
            checks_display = "[dim]○ Pending[/dim]"
        else:
            checks_display = "[dim]—[/dim]"

        table.add_row(
            str(pr["pullRequestId"]),
            pr["title"],
            pr["createdBy"]["displayName"],
            checks_display,
            status_display,
        )

    console.print(table)


def print_pr_detail(pr: Dict[str, Any]):
    """Print pull request details"""
    status = pr["status"]
    if status == "active":
        status_display = "[green]● Active[/green]"
    elif status == "completed":
        status_display = "[blue]✓ Completed[/blue]"
    else:
        status_display = "[red]✗ Abandoned[/red]"

    content = f"""[bold]Title:[/bold] {pr["title"]}
[bold]Status:[/bold] {status_display}
[bold]Author:[/bold] {pr["createdBy"]["displayName"]}
[bold]Created:[/bold] {pr["creationDate"]}
[bold]Source:[/bold] {pr["sourceRefName"].replace("refs/heads/", "")}
[bold]Target:[/bold] {pr["targetRefName"].replace("refs/heads/", "")}"""

    if pr.get("description"):
        content += f"\n\n[bold]Description:[/bold]\n{pr['description']}"

    console.print(
        Panel(
            content, title=f"Pull Request #{pr['pullRequestId']}", border_style="blue"
        )
    )


def print_issue_table(issues: List[Dict[str, Any]]):
    """Print work items as a table"""
    if not issues:
        print_info("No work items found")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=8)
    table.add_column("Title", style="white")
    table.add_column("State", width=12)
    table.add_column("Type", style="yellow", width=15)

    for issue in issues:
        fields = issue["fields"]
        state = fields.get("System.State", "N/A")

        if state == "Active":
            state_display = "[green]● Active[/green]"
        elif state == "Resolved":
            state_display = "[blue]✓ Resolved[/blue]"
        elif state == "Closed":
            state_display = "[dim]✓ Closed[/dim]"
        else:
            state_display = state

        table.add_row(
            str(issue["id"]),
            fields.get("System.Title", "N/A"),
            state_display,
            fields.get("System.WorkItemType", "N/A"),
        )

    console.print(table)


def print_issue_detail(wi: Dict[str, Any]):
    """Print work item details"""
    fields = wi["fields"]

    state = fields.get("System.State", "N/A")
    if state == "Active":
        state_display = "[green]● Active[/green]"
    elif state == "Resolved":
        state_display = "[blue]✓ Resolved[/blue]"
    elif state == "Closed":
        state_display = "[dim]✓ Closed[/dim]"
    else:
        state_display = state

    content = f"""[bold]ID:[/bold] {wi["id"]}
[bold]Type:[/bold] {fields.get("System.WorkItemType", "N/A")}
[bold]Title:[/bold] {fields["System.Title"]}
[bold]State:[/bold] {state_display}
[bold]Assigned To:[/bold] {fields.get("System.AssignedTo", {}).get("displayName", "Unassigned")}
[bold]Created:[/bold] {fields.get("System.CreatedDate", "N/A")}"""

    if fields.get("System.Description"):
        content += f"\n\n[bold]Description:[/bold]\n{fields['System.Description']}"

    console.print(Panel(content, title=f"Work Item #{wi['id']}", border_style="blue"))


def print_repo_table(repos: List[Dict[str, Any]]):
    """Print repositories as a table"""
    if not repos:
        print_info("No repositories found")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Default Branch", style="yellow")
    table.add_column("Link", style="dim", width=6)

    for repo in repos:
        remote_url = repo.get("remoteUrl", "")
        # Use Rich's hyperlink syntax so the link works regardless of terminal width
        link_display = f"[link={remote_url}]View[/link]" if remote_url else "N/A"
        table.add_row(
            repo["name"],
            repo.get("defaultBranch", "N/A").replace("refs/heads/", ""),
            link_display,
        )

    console.print(table)


def print_definition_table(definitions: List[Dict[str, Any]]):
    """Print pipeline definitions as a table"""
    if not definitions:
        print_info("No pipelines found")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Name", style="white")
    table.add_column("Path", style="yellow")
    table.add_column("Type", width=15)

    for definition in definitions:
        table.add_row(
            str(definition.get("id", "N/A")),
            definition.get("name", "N/A"),
            definition.get("path", "\\"),
            definition.get("type", "N/A"),
        )

    console.print(table)


def print_pipeline_table(runs: List[Dict[str, Any]]):
    """Print pipeline runs as a table"""
    if not runs:
        print_info("No pipeline runs found")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Pipeline", style="white")
    table.add_column("Status", width=15)
    table.add_column("Branch", style="yellow", width=20)
    table.add_column("Started", width=20)

    for run in runs:
        status = run.get("status", "unknown")
        result = run.get("result", "")

        if result == "succeeded":
            status_display = "[green]✓ Succeeded[/green]"
        elif result == "failed":
            status_display = "[red]✗ Failed[/red]"
        elif status == "inProgress":
            status_display = "[yellow]● In Progress[/yellow]"
        else:
            status_display = f"{status}"

        table.add_row(
            str(run.get("id", "N/A")),
            run.get("definition", {}).get("name", "N/A"),
            status_display,
            run.get("sourceBranch", "N/A").replace("refs/heads/", ""),
            run.get("startTime", "N/A")[:19] if run.get("startTime") else "N/A",
        )

    console.print(table)


def print_diff(diff_text: str, language: str = "diff"):
    """Print syntax highlighted diff"""
    syntax = Syntax(diff_text, language, theme="monokai", line_numbers=False)
    console.print(syntax)


def prompt_input(question: str, default: Optional[str] = None) -> str:
    """Prompt for user input"""
    result = Prompt.ask(question, default=default)
    return result if result is not None else ""


def prompt_confirm(question: str, default: bool = False) -> bool:
    """Prompt for confirmation"""
    return Confirm.ask(question, default=default)


def spinner_context(message: str):
    """Return a progress spinner context manager"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )
