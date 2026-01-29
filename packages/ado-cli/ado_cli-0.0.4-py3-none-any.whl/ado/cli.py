import os
import sys
import webbrowser
from typing import Optional, Tuple
from urllib.parse import quote, unquote

import click

from ado.client import AdoClient
from ado.config import CONFIG_FILE, AdoConfig
from ado.git_utils import (
    checkout_branch,
    fetch_ref,
    get_current_branch,
    get_remote_url,
)
from ado.git_utils import (
    get_diff as get_git_diff,
)
from ado.ui import (
    console,
    print_definition_table,
    print_diff,
    print_error,
    print_info,
    print_issue_detail,
    print_issue_table,
    print_pipeline_table,
    print_pr_detail,
    print_pr_table,
    print_repo_table,
    print_success,
    print_warning,
    prompt_confirm,
    prompt_input,
    spinner_context,
)


def get_client() -> AdoClient:
    """Get configured Azure DevOps client"""
    config = AdoConfig()
    server_url = config.get("server_url")
    pat = config.get("pat")
    collection = config.get("collection", "DefaultCollection")

    if not server_url or not pat:
        print_error("Not configured. Run 'ado auth login' first.")
        sys.exit(1)

    return AdoClient(server_url, pat, collection)


def get_current_repo_info() -> Tuple[Optional[str], Optional[str]]:
    """Get current repository info from git config"""
    try:
        remote_url = get_remote_url()
        if not remote_url:
            return None, None

        # Parse Azure DevOps URL
        # Format: https://server/collection/project/_git/repo
        parts = remote_url.split("/_git/")
        if len(parts) == 2:
            repo = unquote(parts[1].replace(".git", ""))
            project_part = unquote(parts[0].split("/")[-1])
            return project_part, repo
    except Exception:
        pass
    return None, None


def ensure_project_repo(project: Optional[str], repo: Optional[str]) -> Tuple[str, str]:
    """Validate that project and repo are not None, exit if they are"""
    if not project or not repo:
        print_error("Could not determine project/repo")
        sys.exit(1)
    # Type checker doesn't understand sys.exit prevents None reaching here
    assert project is not None and repo is not None
    return project, repo


# ============================================================================
# Main CLI Group
# ============================================================================
@click.group()
@click.version_option(version="1.1.0")
def cli():
    """Azure DevOps Server CLI - gh-like interface for Azure DevOps Server"""
    pass


# ============================================================================
# Auth commands
# ============================================================================
@cli.group()
def auth():
    """Authenticate with Azure DevOps Server"""
    pass


@auth.command()
def login():
    """Login to Azure DevOps Server"""
    config = AdoConfig()

    server_url = prompt_input("Azure DevOps Server URL").strip()
    pat = click.prompt("Personal Access Token", hide_input=True)
    collection = prompt_input("Collection name", default="DefaultCollection")

    # Test connection
    with spinner_context("Testing connection...") as progress:
        progress.add_task("connect", total=None)
        try:
            client = AdoClient(server_url, pat, collection)
            client.get_projects()

            config.set("server_url", server_url)
            config.set("pat", pat)
            config.set("collection", collection)
            progress.stop()

            print_success(f"Logged in to {server_url}")
        except Exception as e:
            progress.stop()
            print_error(f"Failed to authenticate - {str(e)}")
            sys.exit(1)

    # Ask for default project
    default_project = prompt_input("Default project (optional)", default="")
    if default_project.strip():
        config.set("default_project", default_project.strip())
        print_success(f"Set default project to '{default_project.strip()}'")


@auth.command()
def logout():
    """Logout from Azure DevOps Server"""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    print_success("Logged out")


@auth.command()
def status():
    """View authentication status"""
    config = AdoConfig()
    server_url = config.get("server_url")

    if server_url:
        console.print(
            f"[bold green]✓[/bold green] Logged in to [cyan]{server_url}[/cyan]"
        )
        console.print(
            f"  Collection: [yellow]{config.get('collection', 'DefaultCollection')}[/yellow]"
        )
    else:
        print_warning("Not logged in")


# ============================================================================
# Repo commands
# ============================================================================
@cli.group()
def repo():
    """Manage repositories"""
    pass


@repo.command(name="list")
@click.option("--project", help="Project name")
def repo_list(project: Optional[str]):
    """List repositories"""
    client = get_client()
    config = AdoConfig()

    project = project or config.get("default_project")
    if not project:
        print_error("--project required or set a default project")
        sys.exit(1)

    try:
        with spinner_context("Fetching repositories...") as progress:
            progress.add_task("fetch", total=None)
            result = client.get_repos(project)
            progress.stop()

        print_repo_table(result.get("value", []))
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@repo.command(name="view")
@click.argument("repo", required=False)
@click.option("--project", help="Project name")
@click.option("-w", "--web", is_flag=True, help="Open in web browser")
def repo_view(repo: Optional[str], project: Optional[str], web: bool):
    """View repository details"""
    client = get_client()
    config = AdoConfig()

    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    if not project:
        project = config.get("default_project")

    project, repo = ensure_project_repo(project, repo)

    if web:
        collection = config.get("collection", "DefaultCollection")
        url = f"{config.get('server_url')}/{quote(collection)}/{quote(project)}/_git/{quote(repo)}"
        webbrowser.open(url)
        return

    try:
        result = client.get_repos(project)
        for r in result.get("value", []):
            if r["name"] == repo:
                console.print(f"\n[bold]Name:[/bold] [cyan]{r['name']}[/cyan]")
                console.print(f"[bold]ID:[/bold] {r['id']}")
                console.print(f"[bold]URL:[/bold] {r['remoteUrl']}")
                console.print(
                    f"[bold]Default Branch:[/bold] [yellow]{r.get('defaultBranch', 'N/A').replace('refs/heads/', '')}[/yellow]"
                )
                return
        print_error(f"Repository '{repo}' not found")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# Pipeline commands
# ============================================================================
@cli.group()
def pipeline():
    """Manage pipelines"""
    pass


@pipeline.command(name="list")
@click.option("--project", help="Project name")
def pipeline_list(project: Optional[str]):
    """List pipeline definitions"""
    client = get_client()
    config = AdoConfig()

    project = project or config.get("default_project")
    if not project:
        print_error("--project required or set a default project")
        sys.exit(1)

    try:
        with spinner_context("Fetching pipelines...") as progress:
            progress.add_task("fetch", total=None)
            result = client.get_definitions(project)
            progress.stop()

        definitions = result.get("value", [])
        print_definition_table(definitions)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# PR commands
# ============================================================================
@cli.group()
def pr():
    """Manage pull requests"""
    pass


@pr.command(name="list")
@click.option("--project", help="Project name")
@click.option("--repo", help="Repository name")
@click.option(
    "--state",
    type=click.Choice(["active", "completed", "abandoned", "all"]),
    default="active",
    help="Filter by state",
)
@click.option("-L", "--limit", type=int, default=30, help="Maximum number to list")
def pr_list(project: Optional[str], repo: Optional[str], state: str, limit: int):
    """List pull requests"""
    client = get_client()
    config = AdoConfig()

    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    if not project:
        project = config.get("default_project")

    project, repo = ensure_project_repo(project, repo)

    try:
        with spinner_context("Fetching pull requests...") as progress:
            progress.add_task("fetch", total=None)
            result = client.get_pull_requests(project, repo, state)
            prs = result.get("value", [])[:limit]

            # Fetch build status for each active PR
            build_statuses = {}
            for pr_data in prs:
                if pr_data.get("status") == "active":
                    pr_id = pr_data["pullRequestId"]
                    pr_merge_ref = f"refs/pull/{pr_id}/merge"
                    try:
                        builds = client.get_builds(
                            project, branch_name=pr_merge_ref, top=1
                        )
                        pr_builds = builds.get("value", [])
                        if pr_builds:
                            latest = pr_builds[0]
                            result_status = latest.get("result", "")
                            run_status = latest.get("status", "")
                            if result_status == "succeeded":
                                build_statuses[pr_id] = "succeeded"
                            elif result_status == "failed":
                                build_statuses[pr_id] = "failed"
                            elif run_status == "inProgress":
                                build_statuses[pr_id] = "inProgress"
                            else:
                                build_statuses[pr_id] = "pending"
                    except Exception:
                        # If we can't fetch builds, just skip
                        pass
            progress.stop()

        print_pr_table(prs, build_statuses)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@pr.command(name="view")
@click.argument("pr_number", type=int)
@click.option("--project", help="Project name")
@click.option("--repo", help="Repository name")
@click.option("-w", "--web", is_flag=True, help="Open in web browser")
def pr_view(pr_number: int, project: Optional[str], repo: Optional[str], web: bool):
    """View pull request details"""
    client = get_client()
    config = AdoConfig()

    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    if not project:
        project = config.get("default_project")

    project, repo = ensure_project_repo(project, repo)

    if web:
        collection = config.get("collection", "DefaultCollection")
        url = f"{config.get('server_url')}/{quote(collection)}/{quote(project)}/_git/{quote(repo)}/pullrequest/{pr_number}"
        webbrowser.open(url)
        return

    try:
        pr_data = client.get_pull_request(project, repo, pr_number)
        print_pr_detail(pr_data)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@pr.command()
@click.argument("pr_number", type=int)
@click.option("--project", help="Project name")
@click.option("--repo", help="Repository name")
def checkout(pr_number: int, project: Optional[str], repo: Optional[str]):
    """Checkout a pull request branch"""
    client = get_client()

    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    project, repo = ensure_project_repo(project, repo)

    try:
        pr_data = client.get_pull_request(project, repo, pr_number)
        source_branch = pr_data["sourceRefName"].replace("refs/heads/", "")

        print_info(f"Checking out PR #{pr_number}: {pr_data['title']}")

        # Fetch the branch
        with spinner_context("Fetching branch...") as progress:
            progress.add_task("fetch", total=None)
            if fetch_ref("origin", pr_data["sourceRefName"]):
                progress.stop()
                print_success(f"Fetched {source_branch}")
            else:
                progress.stop()
                print_error("Failed to fetch branch")
                sys.exit(1)

        # Checkout the branch
        if checkout_branch(source_branch):
            print_success(f"Switched to branch '{source_branch}'")
        else:
            print_error(f"Failed to checkout branch '{source_branch}'")
            sys.exit(1)

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@pr.command()
@click.argument("pr_number", type=int)
@click.option("--project", help="Project name")
@click.option("--repo", help="Repository name")
def diff(pr_number: int, project: Optional[str], repo: Optional[str]):
    """Show pull request diff"""
    client = get_client()

    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    project, repo = ensure_project_repo(project, repo)

    try:
        with spinner_context("Fetching PR details...") as progress:
            progress.add_task("fetch", total=None)
            pr_data = client.get_pull_request(project, repo, pr_number)
            progress.stop()

        source = pr_data["sourceRefName"].replace("refs/heads/", "")
        target = pr_data["targetRefName"].replace("refs/heads/", "")

        print_info(f"Diff for PR #{pr_number}: {source} → {target}")

        # Try to get diff from git if available
        diff_text = get_git_diff(f"origin/{target}", f"origin/{source}")

        if diff_text:
            print_diff(diff_text)
        else:
            print_warning(
                "Could not generate diff from local git. Fetching from server..."
            )
            # Fallback to API diff (limited)
            try:
                diff_data = client.get_commit_diff(project, repo, target, source)
                print_info("Note: Showing abbreviated diff from API")
                console.print(diff_data)
            except Exception:
                print_error("Could not fetch diff")

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@pr.command(name="create")
@click.option("-t", "--title", help="Pull request title")
@click.option("-b", "--body", help="Pull request description")
@click.option("--base", help="Target branch")
@click.option("--head", help="Source branch")
@click.option("--project", help="Project name")
@click.option("--repo", help="Repository name")
@click.option("--draft", is_flag=True, help="Create as draft")
def pr_create(
    title: Optional[str],
    body: Optional[str],
    base: Optional[str],
    head: Optional[str],
    project: Optional[str],
    repo: Optional[str],
    draft: bool,
):
    """Create a pull request"""
    client = get_client()
    config = AdoConfig()

    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    if not project:
        project = config.get("default_project")

    project, repo = ensure_project_repo(project, repo)

    # Get current branch if head not specified
    head = head or get_current_branch()

    # Interactive mode
    if not title:
        console.print("\n[bold cyan]Create Pull Request[/bold cyan]\n")
        title = prompt_input("Title")
        body = prompt_input("Description (optional)", default="")
        base = prompt_input("Target branch", default="main")
        if not head:
            head = prompt_input("Source branch")
        draft = prompt_confirm("Create as draft?", default=False)
    else:
        body = body or ""
        base = base or "main"
        if not head:
            head = prompt_input("Source branch")

    try:
        pr_data = {
            "sourceRefName": f"refs/heads/{head}",
            "targetRefName": f"refs/heads/{base}",
            "title": title,
            "description": body,
            "isDraft": draft,
        }

        with spinner_context("Creating pull request...") as progress:
            progress.add_task("create", total=None)
            result = client.create_pull_request(project, repo, pr_data)
            progress.stop()

        pr_number = result["pullRequestId"]
        collection = config.get("collection", "DefaultCollection")
        web_url = f"{config.get('server_url')}/{quote(collection)}/{quote(project)}/_git/{quote(repo)}/pullrequest/{pr_number}"

        print_success(f"Created pull request #{pr_number}")
        console.print(f"  [dim]{web_url}[/dim]")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@pr.command()
@click.argument("pr_number", type=int)
@click.option("--project", help="Project name")
@click.option("--repo", help="Repository name")
def close(pr_number: int, project: Optional[str], repo: Optional[str]):
    """Close a pull request"""
    client = get_client()

    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    project, repo = ensure_project_repo(project, repo)

    try:
        client.update_pull_request(project, repo, pr_number, {"status": "abandoned"})
        print_success(f"Closed pull request #{pr_number}")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@pr.command()
@click.argument("pr_number", type=int)
@click.option("--project", help="Project name")
@click.option("--repo", help="Repository name")
def checks(pr_number: int, project: Optional[str], repo: Optional[str]):
    """Show pull request build checks"""
    client = get_client()

    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    project, repo = ensure_project_repo(project, repo)

    try:
        with spinner_context("Fetching PR and builds...") as progress:
            progress.add_task("fetch", total=None)
            # Azure DevOps uses a special merge ref for PR builds
            # Format: refs/pull/{pr_number}/merge
            pr_merge_ref = f"refs/pull/{pr_number}/merge"
            builds = client.get_builds(project, branch_name=pr_merge_ref, top=50)
            progress.stop()

        # Get builds from the response
        pr_builds = builds.get("value", [])

        if pr_builds:
            print_info(f"Builds for PR #{pr_number}")
            print_pipeline_table(pr_builds[:10])
        else:
            print_info(f"No builds found for PR #{pr_number}")

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@pr.command()
@click.argument("pr_number", type=int)
@click.option("-m", "--message", help="Comment text")
@click.option("--project", help="Project name")
@click.option("--repo", help="Repository name")
def comment(
    pr_number: int, message: Optional[str], project: Optional[str], repo: Optional[str]
):
    """Add a comment to a pull request"""
    client = get_client()
    config = AdoConfig()

    # Auto-detect project/repo from git if not provided
    if not project or not repo:
        p, r = get_current_repo_info()
        project = project or p
        repo = repo or r

    if not project:
        project = config.get("default_project")

    project, repo = ensure_project_repo(project, repo)

    # Interactive mode if message not provided
    if not message:
        console.print(f"\n[bold cyan]Add Comment to PR #{pr_number}[/bold cyan]\n")
        message = prompt_input("Comment")

    if not message.strip():
        print_error("Comment cannot be empty")
        sys.exit(1)

    try:
        # Verify PR exists first
        with spinner_context("Verifying pull request...") as progress:
            progress.add_task("verify", total=None)
            client.get_pull_request(project, repo, pr_number)
            progress.stop()

        # Create comment thread payload
        thread_data = {
            "comments": [{"parentCommentId": 0, "content": message, "commentType": 1}],
            "status": 1,
        }

        # Post comment
        with spinner_context("Adding comment...") as progress:
            progress.add_task("comment", total=None)
            result = client.create_pull_request_thread(
                project, repo, pr_number, thread_data
            )
            progress.stop()

        thread_id = result.get("id", "N/A")
        print_success(f"Added comment to PR #{pr_number}")
        console.print(f"  [dim]Thread ID: {thread_id}[/dim]")

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# Pipeline/Run commands
# ============================================================================
@cli.group()
def run():
    """Manage pipeline runs"""
    pass


@run.command(name="list")
@click.option("--project", help="Project name")
@click.option("-L", "--limit", type=int, default=30, help="Maximum number to list")
def run_list(project: Optional[str], limit: int):
    """List pipeline runs"""
    client = get_client()
    config = AdoConfig()

    project = project or config.get("default_project")
    if not project:
        print_error("--project required or set a default project")
        sys.exit(1)

    try:
        with spinner_context("Fetching pipeline runs...") as progress:
            progress.add_task("fetch", total=None)
            result = client.get_builds(project, top=limit)
            progress.stop()

        runs = result.get("value", [])
        print_pipeline_table(runs)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@run.command(name="view")
@click.argument("run_id", type=int)
@click.option("--project", help="Project name")
@click.option("-w", "--web", is_flag=True, help="Open in web browser")
def run_view(run_id: int, project: Optional[str], web: bool):
    """View pipeline run details"""
    client = get_client()
    config = AdoConfig()

    project = project or config.get("default_project")
    if not project:
        print_error("--project required or set a default project")
        sys.exit(1)

    try:
        with spinner_context("Fetching run details...") as progress:
            progress.add_task("fetch", total=None)
            run = client.get_build(project, run_id)
            progress.stop()

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

        console.print(f"\n[bold]Run:[/bold] [cyan]#{run.get('id')}[/cyan]")
        console.print(
            f"[bold]Pipeline:[/bold] {run.get('definition', {}).get('name', 'N/A')}"
        )
        console.print(f"[bold]Status:[/bold] {status_display}")
        console.print(
            f"[bold]Branch:[/bold] [yellow]{run.get('sourceBranch', 'N/A').replace('refs/heads/', '')}[/yellow]"
        )
        console.print(f"[bold]Started:[/bold] {run.get('startTime', 'N/A')}")
        console.print(f"[bold]Finished:[/bold] {run.get('finishTime', 'N/A')}")

        if web:
            url = run.get("_links", {}).get("web", {}).get("href")
            if url:
                webbrowser.open(url)

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# Issue commands
# ============================================================================
@cli.group()
def issue():
    """Manage work items (issues)"""
    pass


@issue.command()
@click.option("--project", help="Project name")
@click.option(
    "--state",
    type=click.Choice(["New", "Active", "Resolved", "Closed", "all"]),
    default="Active",
    help="Filter by state",
)
@click.option("-L", "--limit", type=int, default=30, help="Maximum number to list")
@click.option("--assignee", help="Filter by assignee")
def list(project: Optional[str], state: str, limit: int, assignee: Optional[str]):
    """List work items"""
    client = get_client()
    config = AdoConfig()

    project = project or config.get("default_project")
    if not project:
        print_error("--project required or set a default project")
        sys.exit(1)

    try:
        state_filter = f"AND [State] = '{state}'" if state != "all" else ""
        assignee_filter = f"AND [Assigned To] = '{assignee}'" if assignee else ""

        wiql = f"""
        SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.WorkItemType]
        FROM WorkItems
        WHERE [System.TeamProject] = '{project}' {state_filter} {assignee_filter}
        ORDER BY [System.ChangedDate] DESC
        """

        with spinner_context("Fetching work items...") as progress:
            progress.add_task("fetch", total=None)
            result = client.get_work_items(project, wiql)
            work_items = result.get("workItems", [])[:limit]

            # Fetch full details for each work item
            detailed_items = []
            for wi in work_items:
                detailed_items.append(client.get_work_item(wi["id"]))
            progress.stop()

        print_issue_table(detailed_items)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@issue.command()
@click.argument("issue_id", type=int)
@click.option("-w", "--web", is_flag=True, help="Open in web browser")
def view(issue_id: int, web: bool):
    """View work item details"""
    client = get_client()
    config = AdoConfig()

    if web:
        collection = config.get("collection", "DefaultCollection")
        url = (
            f"{config.get('server_url')}/{quote(collection)}/_workitems/edit/{issue_id}"
        )
        webbrowser.open(url)
        return

    try:
        with spinner_context("Fetching work item...") as progress:
            progress.add_task("fetch", total=None)
            wi = client.get_work_item(issue_id)
            progress.stop()

        print_issue_detail(wi)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@issue.command()
@click.option("-t", "--title", help="Work item title")
@click.option("-b", "--body", help="Work item description")
@click.option("--project", help="Project name")
@click.option(
    "--type", default="Bug", help="Work item type (Bug, Task, User Story, etc.)"
)
def create(
    title: Optional[str], body: Optional[str], project: Optional[str], type: str
):
    """Create a work item"""
    client = get_client()
    config = AdoConfig()

    project = project or config.get("default_project")
    if not project:
        print_error("--project required or set a default project")
        sys.exit(1)

    # Interactive mode
    if not title:
        console.print("\n[bold cyan]Create Work Item[/bold cyan]\n")
        title = prompt_input("Title")
        body = prompt_input("Description (optional)", default="")
        type = prompt_input("Type", default="Bug")
    else:
        body = body or ""

    try:
        wi_data = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": body},
        ]

        with spinner_context("Creating work item...") as progress:
            progress.add_task("create", total=None)
            result = client.create_work_item(project, type, wi_data)
            progress.stop()

        print_success(f"Created {type} #{result['id']}")
        console.print(f"  [dim]{result['_links']['html']['href']}[/dim]")
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


# ============================================================================
# Config commands
# ============================================================================
@cli.group()
def config():
    """Manage configuration"""
    pass


@config.command()
@click.argument("key")
@click.argument("value")
def set(key: str, value: str):
    """Set configuration value"""
    cfg = AdoConfig()
    cfg.set(key, value)
    print_success(f"Set {key} = {value}")


@config.command()
@click.argument("key")
def get(key: str):
    """Get configuration value"""
    cfg = AdoConfig()
    value = cfg.get(key)
    if value:
        console.print(value)
    else:
        print_error(f"Key '{key}' not found")
        sys.exit(1)


# ============================================================================
# Main entry point
# ============================================================================
def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()
