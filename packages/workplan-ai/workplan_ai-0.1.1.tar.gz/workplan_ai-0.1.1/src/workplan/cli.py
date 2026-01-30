import typer
import json
import csv
import os
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import date, datetime, timedelta
from pathlib import Path
from .storage import (
    init_storage, load_project, save_project, 
    load_week, save_week, 
    load_usage, save_usage,
    load_history, save_history,
    load_intelligence, save_intelligence,
    set_api_key, get_api_key, load_registry,
    WeekState, Task, TaskEstimation, TaskSignals
)
from .ai import WorkplanAIClient, get_project_context
from .git_utils import map_commits_to_tasks, get_recent_commits

app = typer.Typer(help="Workplan AI - Developer-first weekly planning assistant.")
console = Console()

@app.command()
def init():
    """Initializes Workplan AI and sets up secure API access."""
    init_storage()
    
    if not get_api_key():
        console.print("[bold yellow]Groq API Key missing![/bold yellow]")
        console.print("1. Visit [cyan]https://console.groq.com/home[/cyan]")
        console.print("2. Sign in and generate an API key")
        api_key = typer.prompt("3. Paste your API key here", hide_input=True)
        set_api_key(api_key)
        console.print("[bold green]Success![/bold green] API key stored securely in system keychain.")
    
    console.print("[bold green]Success![/bold green] Workplan AI initialized in .workplan/")

@app.command()
def details(project: Optional[str] = typer.Option(None, help="Project name to view details from")):
    """Shows the current goal and task progress. Use --project to view other projects."""
    
    # If project is specified, load from that project's directory
    if project:
        registry = load_registry()
        target_path = None
        for path_str in registry.project_paths:
            path = Path(path_str)
            if path.name.lower() == project.lower():
                target_path = path
                break
        
        if not target_path:
            console.print(f"[yellow]Project '{project}' not found in registry.[/yellow]")
            console.print("Run [cyan]workplan dashboard[/cyan] to see all registered projects.")
            return
        
        # Temporarily switch to that project's directory
        original_cwd = Path.cwd()
        try:
            os.chdir(target_path)
            week = load_week()
            usage = load_usage()
        finally:
            os.chdir(original_cwd)
    else:
        week = load_week()
        usage = load_usage()
    
    if not week:
        console.print(f"[yellow]No goal set for {'this week' if not project else f'project {project}'}. Use `workplan plan` to start.[/yellow]")
        return

    console.print(f"[bold blue]Goal for {week.week_id}:[/bold blue] {week.goal}")
    
    if not week.tasks:
        console.print("[yellow]No tasks planned yet.[/yellow]")
        return

    table = Table(title="Weekly Tasks")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Task", style="magenta")
    table.add_column("Status", justify="center")

    for task in week.tasks:
        status_style = {
            "todo": "white",
            "in_progress": "yellow",
            "done": "green",
            "blocked": "red"
        }.get(task.status, "white")
        
        table.add_row(task.task_id, task.title, f"[{status_style}]{task.status}[/{status_style}]")

    console.print(table)
    
    # Calculate current progress
    completed_planned = sum(t.estimation.points for t in week.tasks if t.status == "done" and not t.signals.carryover)
    completed_carryover = sum(t.estimation.points for t in week.tasks if t.status == "done" and t.signals.carryover)
    
    total_planned = sum(t.estimation.points for t in week.tasks if not t.signals.carryover)
    total_carryover = sum(t.estimation.points for t in week.tasks if t.signals.carryover)
    
    total_points = total_planned + total_carryover
    completed_points = completed_planned + completed_carryover
    progress_pct = (completed_points / total_points * 100) if total_points > 0 else 0
    
    usage = load_usage()
    plan_tag = f"[bold green]{usage.plan.upper()}[/bold green]" if usage.plan == "premium" else f"[bold yellow]{usage.plan.upper()}[/bold yellow]"
    console.print(f"\n[bold blue]Weekly Summary:[/bold blue] (Plan: {plan_tag})")
    
    points_line = f"Points: [green]{completed_points}[/green]"
    if total_carryover > 0:
        points_line += f" ([cyan]{completed_carryover} Carryover[/cyan] + [white]{completed_planned} Planned[/white])"
    points_line += f" / [white]{total_points}[/white] ({progress_pct:.0f}%)"
    
    console.print(points_line)
    
    # Simple Focus Score logic (can be more complex later)
    focus_score = week.metrics.focus_score
    score_color = "green" if focus_score >= 0.8 else "yellow" if focus_score >= 0.5 else "red"
    console.print(f"Focus Score: [{score_color}]{focus_score:.2f}[/{score_color}]")

@app.command()
def plan(goal_description: str = typer.Argument(..., help="The goal for this week")):
    """Sets a weekly goal and derives a multi-stage plan using AI expansion."""
    init_storage()
    
    # Validate goal is not empty
    if not goal_description.strip():
        console.print("[bold red]Error:[/bold red] Goal cannot be empty.")
        console.print("Example: [cyan]workplan plan \"Build user authentication system\"[/cyan]")
        return
    
    current_date = date.today()
    current_week_id = current_date.strftime("%Y-W%V")
    
    # Calculate week boundaries
    start_date = current_date - timedelta(days=current_date.weekday())
    end_date = start_date + timedelta(days=6)
    
    week = WeekState(
        week_id=current_week_id,
        goal=goal_description,
        start_date=start_date,
        end_date=end_date
    )
    
    # Backup existing plan before overwriting
    existing_week = load_week()
    if existing_week and existing_week.tasks:
        from .storage import WORKPLAN_DIR
        backup_path = Path.cwd() / WORKPLAN_DIR / f"week_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(backup_path, 'w') as f:
                json.dump(existing_week.dict(), f, indent=2, default=str)
            console.print(f"[dim]✓ Previous plan backed up to {backup_path.name}[/dim]")
        except Exception:
            pass  # Non-critical, continue anyway
    
    with console.status("[bold blue]Stage 1-9: Expanding intent and grounding context...", spinner="dots"):
        ai_client = WorkplanAIClient()
        context = get_project_context()
        ai_tasks = ai_client.generate_plan(goal_description, context)
        
        usage = load_usage()
        limit = 8 if usage.plan == "free" else 12
        
        week.tasks = [
            Task(
                task_id=f"TASK-{i+1}", 
                title=t["title"], 
                description=t.get("description", ""),
                estimation=TaskEstimation(
                    points=t.get("points", 1),
                    points_reasoning=t.get("points_reasoning", "Initial estimate")
                ),
                signals=TaskSignals(risk=t.get("risk", False))
            )
            for i, t in enumerate(ai_tasks[:limit])
        ]
        
        if len(ai_tasks) > limit:
            console.print(f"\n[bold yellow]Free Tier Limit Reached:[/bold yellow] Truncated to {limit} tasks.")
            console.print("Premium [bold cyan]Early Access[/bold cyan] is coming soon! Run `workplan upgrade` to see what's included.")
        
        save_week(week)
    
    console.print(f"[bold green]Goal set and {len(week.tasks)} tasks generated via 9-stage expansion![/bold green]")
    details(project=None)

@app.command()
def eod():
    """Generates a professional daily summary based on Git activity."""
    week = load_week()
    if not week:
        console.print("[yellow]No goal set. Run `workplan plan` first.[/yellow]")
        return

    with console.status("[bold blue]Analyzing Git activity and generating summary...", spinner="dots"):
        commits = get_recent_commits(days=1)
        if not commits:
            console.print("[yellow]No Git activity detected in the last 24 hours.[/yellow]")
            return

        ai_client = WorkplanAIClient()
        summary = ai_client.generate_eod_summary(commits, week.goal)
        
    console.print("\n[bold blue]End of Day Summary:[/bold blue]")
    console.print(f"\n{summary}\n")

@app.command()
def sync():
    """Synchronizes tasks with Git activity."""
    week = load_week()
    if not week or not week.tasks:
        console.print("[yellow]No tasks to sync. Run `workplan plan` first.[/yellow]")
        return
    
    console.print("[bold blue]Syncing with Git commits...[/bold blue]")
    # map_commits_to_tasks needs to be updated to handle WeekState
    week = map_commits_to_tasks(week)
    save_week(week)
    console.print("[bold green]Sync complete![/bold green]")
    details()

@app.command()
def export(filename: Optional[str] = None, format: str = typer.Option("csv", help="Export format (csv or json)")):
    """Exports weekly tasks to a clean, manager-ready CSV or JSON file."""
    usage = load_usage()
    if format.lower() == "sheets" and usage.plan != "premium":
        console.print("[bold red]Google Sheets Sync is a Premium Feature![/bold red]")
        console.print("Premium [bold cyan]Early Access[/bold cyan] is coming soon. Run `workplan upgrade` to see our roadmap.")
        return

    week = load_week()
    if not week or not week.tasks:
        console.print("[yellow]No tasks to export.[/yellow]")
        return
    
    # Define default filename based on format if not provided
    if not filename:
        filename = f"workplan_export.{format}"
    
    # Map to External Schema
    export_data = {
        "week_id": week.week_id,
        "goal": week.goal,
        "metrics": week.metrics.dict(),
        "tasks": [
            {
                "id": t.task_id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "points": t.estimation.points,
                "risk": t.signals.risk,
                "blocker": t.signals.dependency,
                "carryover": t.signals.carryover,
                "carryover_reason": t.signals.carryover_reason
            }
            for t in week.tasks
        ]
    }

    if format.lower() == "json":
        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)
    else:
        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Title", "Description", "Status", "Points", "Risk", "Blocker", "Carryover", "Carryover Reason"])
            for t in export_data["tasks"]:
                writer.writerow([
                    t["id"], 
                    t["title"], 
                    t["description"], 
                    t["status"], 
                    t["points"],
                    "Yes" if t["risk"] else "No",
                    "Yes" if t["blocker"] else "No",
                    "Yes" if t["carryover"] else "No",
                    t["carryover_reason"] or ""
                ])
            
    console.print(f"[bold green]Exported manager-ready report to {filename} ({format.upper()})[/bold green]")

@app.command()
def task(task_id: str, project: Optional[str] = typer.Option(None, help="Project name to view task from")):
    """Shows full details of a specific task. Use --project to view tasks from other projects."""
    
    # If project is specified, load from that project's directory
    if project:
        registry = load_registry()
        target_path = None
        for path_str in registry.project_paths:
            path = Path(path_str)
            if path.name.lower() == project.lower():
                target_path = path
                break
        
        if not target_path:
            console.print(f"[yellow]Project '{project}' not found in registry.[/yellow]")
            console.print("Run [cyan]workplan dashboard[/cyan] to see all registered projects.")
            return
        
        # Temporarily switch to that project's directory
        original_cwd = Path.cwd()
        try:
            os.chdir(target_path)
            week = load_week()
        finally:
            os.chdir(original_cwd)
    else:
        week = load_week()
    
    if not week:
        console.print(f"[yellow]No goal set for {'this week' if not project else f'project {project}'}.[/yellow]")
        return
    
    # Support both case-insensitive and numeric IDs
    selected_task = next((t for t in week.tasks if t.task_id.lower() == task_id.lower()), None)
    
    if not selected_task:
        # Fallback for just the number
        selected_task = next((t for t in week.tasks if t.task_id.split("-")[-1] == task_id), None)
        
    if not selected_task:
        console.print(f"[red]Task {task_id} not found.[/red]")
        return
    
    status_color = {
        "todo": "white",
        "in_progress": "yellow",
        "done": "green",
        "blocked": "red"
    }.get(selected_task.status, "white")

    console.print(Panel(
        f"\n[bold cyan]Description:[/bold cyan]\n{selected_task.description}\n\n"
        f"[bold cyan]Status:[/bold cyan] [{status_color}]{selected_task.status}[/{status_color}]\n"
        f"[bold cyan]Points:[/bold cyan] {selected_task.estimation.points}\n"
        f"[bold cyan]Signals:[/bold cyan] Risk: {'[red]Yes[/red]' if selected_task.signals.risk else 'No'}, "
        f"Blocker: {'[red]Yes[/red]' if selected_task.signals.dependency else 'No'}, "
        f"Carryover: {'[yellow]Yes[/yellow]' if selected_task.signals.carryover else 'No'}\n"
        f"[bold cyan]Carryover Reason:[/bold cyan] {selected_task.signals.carryover_reason or 'N/A'}\n",
        title=f"[white]Task {selected_task.task_id}:[/white] [bold magenta]{selected_task.title}[/bold magenta]",
        expand=False
    ))

@app.command()
def upgrade():
    """Shows Premium features and instructions for early access."""
    console.print(Panel.fit(
        "[bold cyan]Workplan AI Premium[/bold cyan] — [italic]Early Access Coming Soon[/italic]\n\n"
        "We are currently finalizing the infrastructure for our Corporate tier:\n\n"
        "🚀 [bold green]12+ Tasks per Week[/bold green] (Full Rhythm)\n"
        "🚀 [bold green]Google Sheets & Teams Sync[/bold green]\n"
        "🚀 [bold green]Unlimited Historical Memory[/bold green]\n"
        "🚀 [bold green]Priority AI Reasoning[/bold green]\n\n"
        "Stay tuned for the official launch! Follow @WorkplanAI for updates.",
        title="✨ Premium Roadmap",
        border_style="cyan"
    ))

@app.command()
def carryover(task_id: str, reason: str = typer.Option(..., prompt="Reason for carryover")):
    """Marks a task for carryover to the next period with a specific reason."""
    week = load_week()
    if not week:
        console.print("[yellow]No goal set for this week.[/yellow]")
        return
    
    # Support both case-insensitive and numeric IDs
    selected_task = next((t for t in week.tasks if t.task_id.lower() == task_id.lower()), None)
    if not selected_task:
        selected_task = next((t for t in week.tasks if t.task_id.split("-")[-1] == task_id), None)
        
    if not selected_task:
        console.print(f"[red]Task {task_id} not found.[/red]")
        return
    
    selected_task.signals.carryover = True
    selected_task.signals.carryover_reason = reason
    save_week(week)
    
    console.print(f"[bold green]Task {selected_task.task_id} marked as carryover.[/bold green]")
    console.print(f"[bold cyan]Reason:[/bold cyan] {reason}")

@app.command()
def git_hook(install: bool = typer.Option(False, "--install", help="Automatically install the post-commit hook")):
    """Set up a git post-commit hook for automatic syncing."""
    hook_content = "#!/bin/sh\nworkplan sync\n"
    hook_path = Path(".git/hooks/post-commit")
    
    if install:
        if not Path(".git").exists():
            console.print("[red]Error: Not a git repository.[/red]")
            return
        
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)
        console.print("[bold green]Post-commit hook installed successfully![/bold green]")
    else:
        if hook_path.exists() and hook_path.read_text() == hook_content:
            console.print("[bold green]✅ Post-commit hook is already installed and active.[/bold green]")
            console.print("Tasks will automatically sync every time you [bold cyan]git commit[/bold cyan].")
        else:
            console.print("[bold blue]Automatic Sync Setup:[/bold blue]")
            console.print("To sync tasks automatically on every commit, create a file at:")
            console.print(f"  [cyan]{hook_path}[/cyan]")
            console.print("With the following content:")
            console.print(f"  [white]{hook_content}[/white]")
            console.print("\nOr run: [bold cyan]workplan git-hook --install[/bold cyan]")

@app.command()
def health():
    """Analyzes recent performance to provide health metrics."""
    history = load_history()
    if not history.weeks:
        console.print("[yellow]Not enough history to analyze health. Keep planning![/yellow]")
        return
    
    total_planned = sum(w.planned_points for w in history.weeks)
    total_completed = sum(w.completed_points for w in history.weeks)
    avg_focus = sum(1.0 - w.unplanned_ratio for w in history.weeks) / len(history.weeks)
    
    console.print(Panel.fit(
        f"[bold cyan]Retrospective Health[/bold cyan]\n\n"
        f"Reliability: [green]{(total_completed/total_planned*100):.0f}%[/green]\n"
        f"Avg Focus: [green]{avg_focus:.2f}[/green]\n"
        f"Total Velocity: [white]{total_completed} points[/white]\n"
        f"Status: [bold green]Healthy[/bold green] (Keep it up!)",
        title="📊 Performance Analytics"
    ))

@app.command()
def check(days: int = typer.Option(1, help="Number of days to check back")):
    """Checks recent commits for proper Task ID hygiene (e.g., 'TASK-1')."""
    commits = get_recent_commits(days=days)
    if not commits:
        console.print("[yellow]No commits found in the last specified period.[/yellow]")
        return
    
    table = Table(title="Commit Hygiene Check", show_header=True, header_style="bold magenta")
    table.add_column("Hash", style="dim")
    table.add_column("Message")
    table.add_column("Status", justify="center")
    
    task_pattern = re.compile(r"TASK-\d+", re.IGNORECASE)
    all_valid = True
    
    for c in commits:
        is_valid = bool(task_pattern.search(c["message"]))
        status = "[bold green]PASS[/bold green]" if is_valid else "[bold red]FAIL[/bold red]"
        table.add_row(c["hash"][:7], c["message"], status)
        if not is_valid:
            all_valid = False
            
    console.print(table)
    
    if all_valid:
        console.print("\n[bold green]✅ All commits follow the professional Task-ID rhythm![/bold green]")
    else:
        console.print("\n[bold yellow]⚠️ Some commits are missing Task IDs.[/bold yellow]")
        console.print("Add [cyan]TASK-N[/cyan] to your commit messages to enable [bold]Auto-Sync[/bold]!")

@app.command()
def dashboard():
    """Shows a global view of all active weekly plans across your projects."""
    registry = load_registry()
    if not registry.project_paths:
        console.print("[yellow]No registered projects found. Run `workplan init` in a project directory.[/yellow]")
        return

    table = Table(title="Global Workplan Dashboard", show_header=True, header_style="bold cyan")
    table.add_column("Project", style="bold green")
    table.add_column("Goal", style="italic")
    table.add_column("Progress", justify="center")
    table.add_column("Pending Tasks", justify="right")

    for path_str in registry.project_paths:
        path = Path(path_str)
        if not path.exists():
            continue
        
        # Change CWD temporarily to load local week state
        original_cwd = Path.cwd()
        try:
            os.chdir(path)
            week = load_week()
            project = load_project()
            if week and project:
                done_tasks = len([t for t in week.tasks if t.status == "done"])
                total_tasks = len(week.tasks)
                progress = f"{done_tasks}/{total_tasks} ({int(done_tasks/total_tasks*100)}%)" if total_tasks > 0 else "0/0 (0%)"
                pending = total_tasks - done_tasks
                table.add_row(project.project_name, week.goal, progress, str(pending))
        except Exception:
            continue
        finally:
            os.chdir(original_cwd)

    if table.row_count == 0:
        console.print("[yellow]No active weekly plans found in your registered projects.[/yellow]")
    else:
        console.print(table)

def main():
    app()

if __name__ == "__main__":
    main()
